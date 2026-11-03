# -*- coding: utf-8 -*-
"""单元测试：spec 校验分支 / verify 各门 / CLI / geometry / 渲染分支。
运行：pytest tests/ -q
覆盖：coverage run --source=src/snap2edit -m pytest tests/ -q && coverage report
"""
import os
import subprocess
import sys
import tempfile

import pytest
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from snap2edit import cli, geometry, pptxout, spec as specmod, svgout, verify  # noqa: E402

DEMO = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "..", "examples", "demo", "spec.yaml")


def min_spec(elements=None, texts=None):
    """最小合法 spec（可按需覆写 elements/texts）。"""
    return {
        "project": "单元测试",
        "canvas": {"width": 1280, "height": 720},
        "palette": {"primary": "#111111", "accent": "#2B6CB0", "card": "#FFFFFF", "bg": "#FFFFFF"},
        "texts": ["文案A"] if texts is None else texts,
        "elements": [
            {"id": "e1", "type": "rect", "x": 0, "y": 0, "w": 100, "h": 50, "fill": "#2B6CB0"},
        ] if elements is None else elements,
    }


# ---------------- spec.validate 分支 ----------------

def test_validate_rejects_bad_roots():
    with pytest.raises(specmod.SpecError, match="映射"):
        specmod.validate(None)
    with pytest.raises(specmod.SpecError, match="canvas"):
        specmod.validate({"elements": [{"id": "e1", "type": "rect", "x": 0, "y": 0, "w": 1, "h": 1}]})
    with pytest.raises(specmod.SpecError, match="elements"):
        specmod.validate(min_spec(elements=[]))


def test_validate_rejects_bad_elements():
    with pytest.raises(specmod.SpecError, match="不支持的类型"):
        specmod.validate(min_spec(elements=[{"id": "e1", "type": "hexagon", "x": 0, "y": 0, "w": 1, "h": 1}]))
    with pytest.raises(specmod.SpecError, match="缺少 id"):
        specmod.validate(min_spec(elements=[{"type": "rect", "x": 0, "y": 0, "w": 1, "h": 1}]))
    with pytest.raises(specmod.SpecError, match="id 重复"):
        specmod.validate(min_spec(elements=[
            {"id": "e1", "type": "rect", "x": 0, "y": 0, "w": 1, "h": 1},
            {"id": "e1", "type": "rect", "x": 5, "y": 5, "w": 1, "h": 1},
        ]))
    with pytest.raises(specmod.SpecError, match="缺少几何字段"):
        specmod.validate(min_spec(elements=[{"id": "e1", "type": "line", "x1": 0, "y1": 0, "x2": 5}]))


def test_validate_text_rules_and_blacklist():
    with pytest.raises(specmod.SpecError, match="text 或 lines"):
        specmod.validate(min_spec(elements=[{"id": "t", "type": "text", "x": 0, "y": 0, "size": 14}]))
    with pytest.raises(specmod.SpecError, match="需要 size"):
        specmod.validate(min_spec(elements=[{"id": "t", "type": "text", "x": 0, "y": 0, "text": "无字号"}]))
    with pytest.raises(specmod.SpecError, match="占位符"):
        specmod.validate(min_spec(elements=[{"id": "t", "type": "text", "x": 0, "y": 0, "size": 14, "text": "待补充的说明"}]))


def test_validate_palette_color_and_rotate_bool():
    # palette 走 drop_none=True：非法色降级为 None（透明语义），不抛错
    bad = min_spec()
    bad["palette"]["accent"] = "blue"
    sp = specmod.validate(bad)
    assert sp["palette"]["accent"] is None
    # palette 值本就是 None → 原样保留（continue）
    bad2 = min_spec()
    bad2["palette"]["muted"] = None
    assert specmod.validate(bad2)["palette"]["muted"] is None
    # rotate 布尔值（YAML true）→ SpecError
    rot = min_spec(elements=[{"id": "e1", "type": "rect", "x": 0, "y": 0, "w": 10, "h": 10,
                             "fill": "#2B6CB0", "rotate": True}])
    with pytest.raises(specmod.SpecError, match="rotate 必须是数字"):
        specmod.validate(rot)


def test_norm_color_extremes():
    assert specmod.norm_color("e1", "fill", "#2B6CB080") == "#2B6CB080"   # 8 位原样大写
    assert specmod.norm_color("e1", "fill", "abc") == "#AABBCC"           # 十六进制杂讯：无 # 的 3 位
    assert specmod.norm_color("e1", "fill", "blue", drop_none=True) is None  # drop_none 兜底
    with pytest.raises(specmod.SpecError, match="需 #RRGGBB"):
        specmod.norm_color("e1", "stroke", "not-a-color")


def test_texts_of_listed_and_auto():
    assert specmod.texts_of(min_spec(texts=["清单1", "清单2"])) == ["清单1", "清单2"]
    auto = min_spec(elements=[
        {"id": "t1", "type": "text", "x": 0, "y": 0, "size": 14, "lines": ["行一", "行二"]},
        {"id": "t2", "type": "text", "x": 0, "y": 40, "size": 14, "text": "单行"},
        {"id": "b1", "type": "rect", "x": 0, "y": 0, "w": 10, "h": 10},
    ])
    auto.pop("texts")
    assert specmod.texts_of(auto) == ["行一", "行二", "单行"]


# ---------------- geometry ----------------

def test_resolve_slide_emu():
    assert geometry.resolve_slide_emu(min_spec()) == geometry.SLIDE_16_9
    assert geometry.resolve_slide_emu({}) == geometry.SLIDE_16_9
    explicit = {"slide": {"emu_w": 12192000, "emu_h": 6858000}}
    assert geometry.resolve_slide_emu(explicit) == (12192000, 6858000)
    with pytest.raises(ValueError, match="preset"):
        geometry.resolve_slide_emu({"slide": {"preset": "4:3"}})


# ---------------- CLI（进程内） ----------------

def test_cli_new_build_check_roundtrip():
    with tempfile.TemporaryDirectory() as td:
        assert cli.main(["new", td]) == 0
        assert cli.main(["new", td]) == 1                     # 已存在
        spec_path = os.path.join(td, "spec.yaml")
        assert os.path.exists(spec_path)

        assert cli.main(["build", td]) == 0                   # 双渲染
        build = os.path.join(td, "build")
        assert any(f.endswith(".html") for f in os.listdir(build))
        assert any(f.endswith(".pptx") for f in os.listdir(build))

        assert cli.main(["check", td, "--no-shot", "--json"]) == 0    # 模板四门全绿
        assert cli.main(["check", td, "--no-shot"]) == 0              # 文本报告路径


def test_cli_check_failing_spec_returns_2():
    with tempfile.TemporaryDirectory() as td:
        bad = min_spec(elements=[
            {"id": "t1", "type": "text", "x": 40, "y": 40, "size": 20, "text": "真实文案"},
            {"id": "bg", "type": "rect", "x": 0, "y": 0, "w": 1280, "h": 720, "fill": "#FFFFFF"},
        ], texts=["清单里才有的一条文案"])
        with open(os.path.join(td, "spec.yaml"), "w", encoding="utf-8") as f:
            yaml.dump(bad, f, allow_unicode=True)
        assert cli.main(["build", td]) == 0                      # check 前需先产出双交付物
        assert cli.main(["check", td, "--no-shot", "--json"]) == 2   # 门1 文案缺失
        assert cli.main(["check", td, "--no-shot"]) == 2


def test_cli_argparse_wiring():
    with pytest.raises(SystemExit):
        cli.main(["--version"])
    with pytest.raises(SystemExit):
        cli.main([])


def test_python_dash_m_entry():
    r = subprocess.run([sys.executable, "-m", "snap2edit", "--version"],
                       capture_output=True, text=True)
    assert r.returncode == 0 and "snap2edit" in r.stdout


def test_module_main_entries():
    """runpy 以 __main__ 身份执行：覆盖 cli.py / __main__.py 的 sys.exit(main()) 尾行。"""
    import runpy

    with pytest.raises(SystemExit):
        runpy.run_module("snap2edit.cli", run_name="__main__", alter_sys=True)
    with pytest.raises(SystemExit):
        runpy.run_module("snap2edit", run_name="__main__", alter_sys=True)


# ---------------- 渲染分支（svgout / pptxout） ----------------

def test_svgout_unknown_type_raises():
    with pytest.raises(ValueError, match="未知元素类型"):
        svgout.render_element({"id": "x", "type": "blob"}, min_spec())


def test_render_align_and_fill_fallback_both_lines():
    sp = specmod.validate(min_spec(elements=[
        {"id": "t-c", "type": "text", "x": 400, "y": 100, "size": 18, "align": "center", "text": "居中文本"},
        {"id": "t-r", "type": "text", "x": 1200, "y": 140, "size": 18, "align": "right", "text": "右对齐文本"},
        {"id": "card", "type": "rrect", "x": 100, "y": 300, "w": 300, "h": 100, "rx": 10, "text": "卡片", "size": 16},
    ]))
    html = svgout.render_html(sp)
    assert 'text-anchor="middle"' in html and 'text-anchor="end"' in html
    # card 无 fill 键 → 回退 palette.card
    assert "#FFFFFF" in html

    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "a.pptx")
        pptxout.render_pptx(sp, p)
        assert os.path.getsize(p) > 0


def test_pptxout_unknown_type_raises():
    bad = min_spec(elements=[{"id": "x", "type": "blob", "x": 0, "y": 0, "w": 1, "h": 1}])
    with tempfile.TemporaryDirectory() as td:
        with pytest.raises(ValueError, match="未知元素类型"):
            pptxout.render_pptx(bad, os.path.join(td, "b.pptx"))


def test_noshadow_tolerates_weird_shapes():
    """_noshadow 的防御分支：shadow 属性抛异常时吞掉不炸。"""
    class Boom:
        @property
        def shadow(self):
            raise RuntimeError("no shadow here")

    pptxout._noshadow(Boom())  # 不抛错


# ---------------- verify 单元 ----------------

def test_text_width_px_fallback_without_font(monkeypatch):
    monkeypatch.setattr(verify, "_font", lambda: None)
    # 中文/全角 >0x2E7F → 1.0；半角字符 0.56；空格 0.30
    assert verify.text_width_px("AB 中", 10) == pytest.approx((0.56 + 0.56 + 0.30 + 1.0) * 10)
    assert verify.text_width_px("a b", 10) == pytest.approx((0.56 + 0.30 + 0.56) * 10)


def test_font_returns_none_without_candidates(monkeypatch):
    monkeypatch.setattr(verify, "FONT_CANDIDATES", ["/nonexistent/font.ttf"])
    assert verify._font() is None


def test_check_html_failure_branches():
    sp = min_spec(elements=[{"id": "t1", "type": "text", "x": 0, "y": 0, "size": 14, "text": "真实文案"}],
                  texts=["真实文案"])
    html = '<image href="x.png"/><text>XXX</text>'          # 位图 + 占位符 + 文案缺失
    items = verify.check_html(html, sp)
    passed = {label: ok for label, ok, _ in items}
    assert passed["HTML <text> 元素数量覆盖"] is True         # 1/1 数量够但内容错
    assert passed["无位图（<image>/data:image 零命中）"] is False
    assert passed["文案清单全部在场"] is False
    assert passed["无残留占位符"] is False
    assert "XXX" in items[3][2]


def test_check_bounds_branches():
    cw = 1280
    els = [
        # 左对齐无 w：可用宽 = cw - x，超宽 → 溢出
        {"id": "a", "type": "text", "x": 1200, "y": 10, "size": 40, "text": "很长很长的一段中文文案"},
        # 显式 w：可用宽 = w，超宽 → 溢出
        {"id": "b", "type": "text", "x": 10, "y": 10, "w": 10, "size": 20, "align": "center", "text": "超宽文案"},
        # 盒内文本超出盒宽 - 8 → 溢出
        {"id": "c", "type": "rrect", "x": 0, "y": 0, "w": 50, "h": 30, "text": "三个字超宽", "size": 20},
        # 居中且无 w：不校验（可用宽未知）
        {"id": "d", "type": "text", "x": 640, "y": 400, "size": 30, "align": "center", "text": "居中不校验"},
    ]
    over = verify.check_bounds({"canvas": {"width": cw}, "elements": els})
    ids = {o[0] for o in over}
    assert {"a", "b", "c"} <= ids and "d" not in ids


def test_screenshot_and_ratio_and_diff():
    from PIL import Image
    with tempfile.TemporaryDirectory() as td:
        html = os.path.join(td, "s.html")
        with open(html, "w", encoding="utf-8") as f:
            f.write('<html><body style="margin:0"><div id="stage" '
                    'style="width:200px;height:100px;background:#cc2222"></div></body></html>')
        png = os.path.join(td, "shot.png")
        path, err = verify.screenshot(html, png, wait_ms=100)
        assert path == png and err is None
        assert verify.not_blank_ratio(png) > 0.002

        # 与原图块差异：同色图差异 ≈ 0
        ref = os.path.join(td, "ref.png")
        Image.new("RGB", (200, 100), "#cc2222").save(ref)
        mean, _ = verify.block_diff(ref, png, block=16)
        assert mean < 3

        # 无 #stage → 明确错误
        html2 = os.path.join(td, "empty.html")
        with open(html2, "w", encoding="utf-8") as f:
            f.write("<html><body></body></html>")
        path2, err2 = verify.screenshot(html2, os.path.join(td, "x.png"), wait_ms=50)
        assert path2 is None and "未找到 #stage" in err2


def test_screenshot_import_error(monkeypatch):
    monkeypatch.setitem(sys.modules, "playwright.sync_api", None)   # from ... import → ImportError
    path, err = verify.screenshot("x.html", "y.png")
    assert path is None and "未安装 playwright" in err


def test_screenshot_unexpected_exception(monkeypatch):
    """sync_playwright 调用本身抛异常 → 捕获为可读错误（except Exception 分支）。"""
    import types

    def boom():
        raise RuntimeError("playwright crashed")

    monkeypatch.setitem(sys.modules, "playwright.sync_api", types.SimpleNamespace(sync_playwright=boom))
    path, err = verify.screenshot("x.html", "y.png")
    assert path is None and "截图失败" in err and "playwright crashed" in err


def test_collect_checks_screenshot_failure_marks_skip(monkeypatch):
    """门4：截图失败 → 记「截图（跳过）」且不阻断整体。"""
    with tempfile.TemporaryDirectory() as td:
        sp = specmod.load(DEMO)
        name = specmod.safe_project(sp)
        build = os.path.join(td, "build")
        os.makedirs(build)
        with open(os.path.join(build, f"{name}.html"), "w", encoding="utf-8") as f:
            f.write(svgout.render_html(sp))
        pptxout.render_pptx(sp, os.path.join(build, f"{name}.pptx"))
        monkeypatch.setattr(verify, "screenshot", lambda *a, **k: (None, "模拟截图失败"))
        data = verify.collect_checks(td, sp, do_shot=True, log=None)
        gate4 = [g for g in data["gates"] if "门4" in g["gate"]][0]
        assert gate4["items"][0]["label"].startswith("截图（跳过）")
        assert data["artifacts"]["shot"] is None


def test_collect_checks_with_screenshot_and_original():
    with tempfile.TemporaryDirectory() as td:
        from PIL import Image
        sp = specmod.load(DEMO)
        name = specmod.safe_project(sp)
        build = os.path.join(td, "build")
        os.makedirs(build)
        with open(os.path.join(build, f"{name}.html"), "w", encoding="utf-8") as f:
            f.write(svgout.render_html(sp))
        pptxout.render_pptx(sp, os.path.join(build, f"{name}.pptx"))
        original = os.path.join(td, "ref.png")
        Image.new("RGB", (640, 360), "#8899aa").save(original)

        data = verify.collect_checks(td, sp, original=original, do_shot=True, log=None)
        assert len(data["gates"]) == 5                            # 门1-4 + 附加原图差异
        assert data["artifacts"]["shot"] and os.path.exists(data["artifacts"]["shot"])
        assert os.path.exists(data["report_md"])


def test_collect_checks_original_without_shot_marks_failure():
    with tempfile.TemporaryDirectory() as td:
        sp = specmod.load(DEMO)
        name = specmod.safe_project(sp)
        build = os.path.join(td, "build")
        os.makedirs(build)
        with open(os.path.join(build, f"{name}.html"), "w", encoding="utf-8") as f:
            f.write(svgout.render_html(sp))
        pptxout.render_pptx(sp, os.path.join(build, f"{name}.pptx"))
        data = verify.collect_checks(td, sp, original="ref.png", do_shot=False, log=None)
        extra = [g for g in data["gates"] if "原图差异" in g["gate"]][0]
        assert extra["items"][0]["passed"] is False               # 需先完成截图


def test_run_checks_logs_and_returns_bool(capsys):
    with tempfile.TemporaryDirectory() as td:
        sp = specmod.load(DEMO)
        name = specmod.safe_project(sp)
        build = os.path.join(td, "build")
        os.makedirs(build)
        with open(os.path.join(build, f"{name}.html"), "w", encoding="utf-8") as f:
            f.write(svgout.render_html(sp))
        pptxout.render_pptx(sp, os.path.join(build, f"{name}.pptx"))
        logs = []
        ok = verify.run_checks(td, sp, do_shot=False, log=logs.append)
        assert ok is True and any("全部校验通过" in m for m in logs)
