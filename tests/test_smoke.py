# -*- coding: utf-8 -*-
"""冒烟测试：python tests/test_smoke.py 或 pytest"""
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from snap2edit import pptxout, spec as specmod, svgout, verify  # noqa: E402

DEMO = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "..", "examples", "demo", "spec.yaml")


def test_build_and_verify():
    sp = specmod.load(DEMO)

    # 产线①：HTML 全真实文本、无位图
    html = svgout.render_html(sp)
    assert "<image" not in html and "data:image" not in html, "HTML 不允许位图"
    assert html.count("<text") >= 10, "HTML 文本元素数量不足"
    assert all(r[1] for r in verify.check_html(html, sp)), "HTML 校验门未通过"

    # 产线②：PPTX 原生形状、Picture=0、文案齐全
    with tempfile.TemporaryDirectory() as td:
        pptx_path = os.path.join(td, "demo.pptx")
        pptxout.render_pptx(sp, pptx_path)
        res = verify.check_pptx(pptx_path, sp)
        assert all(ok for _, ok, _ in res), res

    # 门3：demo 自身不得有边界溢出
    assert verify.check_bounds(sp) == [], "demo 存在文本溢出"


def test_safe_project():
    """project 名消毒：空格/斜杠/特殊字符 → _，中文保留，限长。"""
    assert specmod.safe_project({"project": "AI 技术/对比 图 v2?"}) == "AI_技术_对比_图_v2"
    assert specmod.safe_project({}) == "output"
    assert specmod.safe_project({"project": None}) == "output"
    assert len(specmod.safe_project({"project": "x" * 200})) <= 60


def test_norm_color():
    """颜色规范化：#RGB 补全、缺 # 补全、none→None、非法值报可读错误。"""
    assert specmod.norm_color("e1", "fill", "#2b6cb0") == "#2B6CB0"
    assert specmod.norm_color("e1", "fill", "#abc") == "#AABBCC"
    assert specmod.norm_color("e1", "fill", "2B6CB0") == "#2B6CB0"
    assert specmod.norm_color("e1", "fill", "none") is None
    assert specmod.norm_color("e1", "fill", "transparent", drop_none=True) is None
    try:
        specmod.norm_color("e1", "stroke", "blue")
        raise AssertionError("非法颜色应抛 SpecError")
    except specmod.SpecError as e:
        assert "需 #RRGGBB" in str(e)


def test_validate_spec_transparent_fill_and_circle():
    """fill:none/transparent → 透明语义；circle 类型可校验通过并双渲染。"""
    raw = """
project: "透明语义测试"
canvas: {width: 300, height: 200}
palette: {primary: "#111111", accent: "#2B6CB0", card: "#FFFFFF", bg: "none"}
texts: ["圆"]
elements:
  - {id: e1, type: circle, x: 20, y: 20, w: 60, h: 60, fill: "#2B6CB0"}
  - {id: e2, type: rrect, x: 100, y: 20, w: 120, h: 50, fill: transparent, text: "圆", size: 14}
  - {id: e3, type: text, x: 20, y: 120, size: 16, color: none, text: "圆"}
"""
    import yaml

    sp = specmod.validate(yaml.safe_load(raw))
    assert sp["palette"]["accent"] == "#2B6CB0"          # 缺 # 补全
    assert "bg" not in sp["palette"] or sp["palette"]["bg"] is None
    html = svgout.render_html(sp)
    assert "<ellipse" in html and 'fill="none"' in html  # 透明语义落在 SVG
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "t.pptx")
        pptxout.render_pptx(sp, p)                        # PPTX OVAL + 透明填充不抛错
        assert os.path.getsize(p) > 0


def test_rotate_end_to_end():
    """rotate 字段端到端：校验规范化 + SVG transform + PPTX rotation 同语义。"""
    import io
    import yaml

    raw = """
project: "旋转语义测试"
canvas: {width: 400, height: 300}
palette: {primary: "#111111", accent: "#2B6CB0", card: "#FFFFFF", bg: "#FFFFFF"}
texts: ["斜标题", "盒内文"]
elements:
  - {id: e1, type: rect, x: 40, y: 40, w: 120, h: 60, fill: "#2B6CB0", rotate: 30, text: "盒内文", size: 14}
  - {id: e2, type: text, x: 200, y: 60, size: 20, rotate: -15, text: "斜标题"}
  - {id: e3, type: line, x1: 40, y1: 200, x2: 300, y2: 200, rotate: 999}
"""
    sp = specmod.validate(yaml.safe_load(raw))
    e1, e2, e3 = sp["elements"]
    assert e1["rotate"] == 30
    assert e2["rotate"] == 345.0                       # -15 → 345（归一化到 [0,360)）
    assert "rotate" not in e3                          # 线段端点承载几何，rotate 被剔除
    try:
        bad = yaml.safe_load(raw.replace("rotate: 30", "rotate: 竖直"))
        specmod.validate(bad)
        raise AssertionError("非数字 rotate 应报 SpecError")
    except specmod.SpecError as e:
        assert "rotate" in str(e)

    html = svgout.render_html(sp)
    assert 'transform="rotate(30 100 70)"' in html      # 盒子绕自身中心
    assert 'transform="rotate(30 100 70)"' in html and html.count('rotate(30 100 70)') == 2  # 盒内文本同步旋转
    assert 'transform="rotate(345 200 60)"' in html     # 自由文本绕锚点

    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "r.pptx")
        pptxout.render_pptx(sp, p)
        from pptx import Presentation

        prs = Presentation(p)
        rot = {s.name: s.rotation for s in prs.slides[0].shapes}
        assert rot["e1"] == 30 and rot["e1-text"] == 30
        assert rot["e2"] == 345.0


def test_collect_checks_and_cli_json():
    """collect_checks 结构化报告 + CLI check --json 同源输出。"""
    with tempfile.TemporaryDirectory() as td:
        sp = specmod.load(DEMO)
        name = specmod.safe_project(sp)
        build = os.path.join(td, "build")
        os.makedirs(build)
        pptxout.render_pptx(sp, os.path.join(build, f"{name}.pptx"))
        with open(os.path.join(build, f"{name}.html"), "w", encoding="utf-8") as f:
            f.write(svgout.render_html(sp))
        data = verify.collect_checks(td, sp, do_shot=False)
        assert data["ok"] is True and data["gates"] and data["failures"] == []
        assert set(data["artifacts"]) == {"html", "pptx", "shot"}
        # CLI --json 与 collect_checks 同源（CLI 需要目录内 spec.yaml）
        import shutil

        shutil.copy(DEMO, os.path.join(td, "spec.yaml"))
        r = subprocess.run([sys.executable, "-m", "snap2edit.cli", "check", td, "--json", "--no-shot"],
                           capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        assert json.loads(r.stdout)["ok"] is True


if __name__ == "__main__":
    test_build_and_verify()
    test_safe_project()
    test_norm_color()
    test_validate_spec_transparent_fill_and_circle()
    test_rotate_end_to_end()
    test_collect_checks_and_cli_json()
    print("smoke test passed ✓")
