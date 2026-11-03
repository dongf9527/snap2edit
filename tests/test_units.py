# -*- coding: utf-8 -*-
"""单元测试：spec 校验分支 / verify 各门 / CLI / geometry / 渲染分支。
运行：pytest tests/ -q
覆盖：coverage run --source=src/snap2edit -m pytest tests/ -q && coverage report
"""
import functools
import json
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


@functools.lru_cache(maxsize=1)
def _chromium_available():
    """真实 chromium 可用性探测（整会话仅一次）。

    Playwright 属可选依赖（D5）：装了浏览器则实跑集成路径，
    未装则跳过而非失败——与引擎"缺省优雅降级"语义一致。"""
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return False
    try:
        with sync_playwright() as p:
            p.chromium.launch().close()
        return True
    except Exception:
        return False


_real_browser = pytest.mark.skipif(
    not _chromium_available(),
    reason="未安装 playwright/chromium（可选依赖 D5，跳过真实浏览器集成）")


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


@_real_browser
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


@_real_browser
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


# ---------------- F6 组件库：components ----------------

def test_components_shade_and_contrast():
    from snap2edit import components
    assert components.shade("#2B6CB0", 0.25) != "#2B6CB0"
    assert components.shade("#2B6CB0", 0.0) == "#2B6CB0"
    assert components.shade("#FFFFFF", -0.5) == "#808080"
    assert components.shade("#000000", 1.0) == "#FFFFFF"      # 亮部不越界
    assert components.shade("#FFFFFF", -1.0) == "#000000"     # 暗部不越界
    assert components.contrast_text("#FFFFFF") == "#1F2937"   # 浅底 → 墨字
    assert components.contrast_text("#2B6CB0") == "#FFFFFF"   # 深底 → 白字


def test_components_cube_faces():
    from snap2edit import components
    f = components.cube_faces(10, 20, 100, 80, 16)
    assert f["depth"] == 16
    assert f["front"] == (10, 36, 84, 64)
    assert len(f["top"]) == 4 and len(f["side"]) == 4
    d = components.cube_faces(0, 0, 100, 100, None)["depth"]   # 缺省 min*0.2
    assert d == 20.0
    assert components.cube_faces(0, 0, 40, 40, 99)["depth"] == 20.0  # 钳制 ≤ min/2
    assert components.cube_faces(0, 0, 40, 40, -5)["depth"] == 0.0


def test_components_matrix_cells():
    from snap2edit import components
    cells = components.matrix_cells(0, 0, 210, 100, rows=2, cols=3, gap=10)
    assert len(cells) == 6
    assert cells[0] == (0.0, 0.0, (210 - 20) / 3, (100 - 10) / 2)
    r1c1 = cells[3]  # 第二行第一格
    assert r1c1[1] == cells[0][3] + 10                          # 第二行 y = 第一行高 + gap
    assert components.matrix_cells(0, 0, 100, 50, 1, 1, gap=99) == [(0.0, 0.0, 100.0, 50.0)]


def test_components_icons_fit_and_names():
    from snap2edit import components
    assert set(components.ICON_NAMES) >= {"brain", "chart", "network", "sparkle",
                                          "lightning", "gear", "doc", "user", "check", "target"}
    parts = components.icon_parts("chart", 0, 0, 50, 100)      # contain：按 min 边缩放
    assert parts and parts[0][0] == "fill"
    xs = [p[0] for _, pts in parts for p in pts]
    ys = [p[1] for _, pts in parts for p in pts]
    assert min(xs) >= 0 - 1e-6 and max(xs) <= 50.0 + 1e-6       # 水平撑满 50 宽盒
    assert min(ys) >= 25.0 - 1e-6 and max(ys) <= 75.0 + 1e-6    # 垂直居中于 100 高盒
    gear = components.icon_parts("gear", 0, 0, 100, 100)
    assert any(k == "ring" for k, _ in gear)                   # gear 有空心描边部件
    brain = components.icon_parts("brain", 0, 0, 100, 100)
    assert any(k == "stroke" for k, _ in brain)                # brain 有开放折线部件
    with pytest.raises(KeyError):
        components.icon_parts("no-such-icon", 0, 0, 10, 10)


# ---------------- F6 组件库：spec 校验 ----------------

def test_spec_component_validation_errors():
    E = lambda el: specmod.validate(min_spec(elements=[el]))
    with pytest.raises(specmod.SpecError, match="rows"):
        E({"id": "m", "type": "matrix-cell", "x": 0, "y": 0, "w": 10, "h": 10,
           "rows": 0, "cols": 2})
    with pytest.raises(specmod.SpecError, match="texts 共"):
        E({"id": "m", "type": "matrix-cell", "x": 0, "y": 0, "w": 10, "h": 10,
           "rows": 1, "cols": 1, "texts": ["一", "二"], "size": 10})
    with pytest.raises(specmod.SpecError, match="未知图标"):
        E({"id": "i", "type": "icon", "x": 0, "y": 0, "w": 10, "h": 10, "name": "rocket"})
    with pytest.raises(specmod.SpecError, match="band"):
        E({"id": "f", "type": "flow-box", "x": 0, "y": 0, "w": 10, "h": 10,
           "title": "T", "size": 10, "band": 1.5})
    with pytest.raises(specmod.SpecError, match="title 或 text"):
        E({"id": "f", "type": "flow-box", "x": 0, "y": 0, "w": 10, "h": 10})
    with pytest.raises(specmod.SpecError, match="depth"):
        E({"id": "c", "type": "cube", "x": 0, "y": 0, "w": 10, "h": 10, "depth": -1})
    with pytest.raises(specmod.SpecError, match="size"):
        E({"id": "f", "type": "flow-box", "x": 0, "y": 0, "w": 10, "h": 10, "title": "无字号"})


def test_spec_composite_rotate_popped_and_texts_collected():
    sp = specmod.validate(min_spec(
        elements=[
            {"id": "m", "type": "matrix-cell", "x": 0, "y": 0, "w": 60, "h": 30,
             "rows": 1, "cols": 2, "rotate": 30, "texts": ["甲", "乙"], "size": 10},
            {"id": "f", "type": "flow-box", "x": 0, "y": 40, "w": 60, "h": 30,
             "rotate": 30, "title": "流程", "text": "正文", "size": 10},
        ],
        texts=[]))                               # texts=[] → 自动收集全部组件文字
    m, f = sp["elements"]
    assert "rotate" not in m and "rotate" not in f              # 复合组件 rotate 剔除
    assert specmod.texts_of(sp) == ["甲", "乙", "流程", "正文"]  # 标题先于正文，组件文字自动进清单
    assert specmod.text_tag_count(sp) == 4


# ---------------- F6 组件库：svgout / pptxout 渲染 ----------------

GALLERY_MIN_ELEMENTS = [
    {"id": "c", "type": "cube", "x": 0, "y": 0, "w": 80, "h": 70, "fill": "#2B6CB0",
     "depth": 12, "text": "立", "size": 12, "color": "#FFFFFF"},
    {"id": "m", "type": "matrix-cell", "x": 100, "y": 0, "w": 90, "h": 60,
     "rows": 2, "cols": 3, "gap": 4, "fill": "#2B6CB0", "texts": ["一", "二", "三"], "size": 10},
    {"id": "f", "type": "flow-box", "x": 210, "y": 0, "w": 120, "h": 70,
     "fill": "#EFF6FF", "title": "标题", "text": "正文", "size": 10, "band": 0.3},
    {"id": "i", "type": "icon", "x": 350, "y": 0, "w": 60, "h": 60, "name": "gear", "fill": "#2F855A"},
]


def test_svgout_component_render_units():
    sp = specmod.validate(min_spec(elements=GALLERY_MIN_ELEMENTS, texts=["立"]))
    html = svgout.render_html(sp)
    assert html.count('<polygon id="c-top"') == 1 and html.count('<polygon id="c-side"') == 1
    assert html.count('<rect id="c" ') == 1                     # 立方体正面
    assert html.count('<rect id="m-r1c1"') == 1 and html.count('<rect id="m-r2c3"') == 1
    assert html.count('<text id="m-r1c1-text"') == 1            # 逐格文字
    assert html.count('<path id="f-band"') == 1                 # 流程框色带
    assert html.count('<text id="f-title"') == 1 and html.count('<text id="f-text"') == 1
    assert html.count('<polygon id="i-0"') == 1 and html.count('<polygon id="i-1"') == 1
    assert specmod.text_tag_count(sp) == html.count("<text")    # 门1 期望值与实际一致


def test_pptxout_component_render_native():
    sp = specmod.validate(min_spec(elements=GALLERY_MIN_ELEMENTS, texts=["立"]))
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "c.pptx")
        pptxout.render_pptx(sp, path)
        from pptx import Presentation
        prs = Presentation(path)
        shapes = list(prs.slides[0].shapes)
        assert not any(s.shape_type == 13 or s.__class__.__name__ == "Picture"
                       for s in shapes)                          # 全原生形状
        names = [s.name for s in shapes]
        for want in ("c", "c-top", "c-side", "m-r1c1", "m-r1c1-text",
                     "f", "f-band", "f-title", "i-0"):
            assert want in names, f"缺少形状 {want}"
        freeforms = [s for s in shapes if "FREEFORM" in str(s.shape_type)]
        assert len(freeforms) >= 3                               # cube 面片 + gear 齿形/中环


# ---------------- F6 组件库：verify 门1/门3 ----------------

def test_verify_bounds_for_components():
    sp = specmod.validate(min_spec(elements=[
        {"id": "m", "type": "matrix-cell", "x": 0, "y": 0, "w": 40, "h": 20,
         "rows": 1, "cols": 1, "texts": ["特别长的格子文案会溢出"], "size": 12},
        {"id": "c", "type": "cube", "x": 0, "y": 40, "w": 60, "h": 50, "depth": 20,
         "text": "特别长的立方体文字溢出", "size": 12},
        {"id": "f", "type": "flow-box", "x": 0, "y": 100, "w": 80, "h": 60,
         "title": "特别长的流程框标题会溢出", "text": "正文", "size": 12},
    ], texts=None))
    over = verify.check_bounds(sp)
    ids = {o[0] for o in over}
    assert "m-r1c1" in ids and "c" in ids and "f-title" in ids
    # 正常尺寸不报溢出
    ok_sp = specmod.validate(min_spec(elements=[
        {"id": "m", "type": "matrix-cell", "x": 0, "y": 0, "w": 200, "h": 40,
         "rows": 1, "cols": 1, "texts": ["短"], "size": 12},
    ], texts=None))
    assert verify.check_bounds(ok_sp) == []


def test_verify_gate1_counts_component_texts():
    sp = specmod.validate(min_spec(elements=GALLERY_MIN_ELEMENTS, texts=[]))
    with tempfile.TemporaryDirectory() as td:
        build = os.path.join(td, "build")
        os.makedirs(build)
        name = specmod.safe_project(sp)
        html = svgout.render_html(sp)
        with open(os.path.join(build, f"{name}.html"), "w", encoding="utf-8") as f:
            f.write(html)
        pptxout.render_pptx(sp, os.path.join(build, f"{name}.pptx"))
        data = verify.collect_checks(td, sp, do_shot=False, log=None)
        g1 = data["gates"][0]["items"]
        assert g1[0]["passed"]                                  # <text> 数量覆盖（含组件文字）
        assert "文案清单全部在场" in g1[2]["label"] and g1[2]["passed"]


# ---------------- F5 loop 命令 ----------------

def _write_loop_project(td, spec_dict):
    os.makedirs(td, exist_ok=True)
    with open(os.path.join(td, "spec.yaml"), "w", encoding="utf-8") as f:
        yaml.safe_dump(spec_dict, f, allow_unicode=True)


LOOP_OK_SPEC = {
    "project": "loopdemo",
    "canvas": {"width": 640, "height": 360},
    "texts": ["标题文字"],
    "elements": [
        {"id": "t", "type": "text", "x": 40, "y": 40, "size": 20, "text": "标题文字"},
    ],
}


def test_loop_converges_first_iter(tmp_path, capsys):
    _write_loop_project(str(tmp_path), LOOP_OK_SPEC)
    rc = cli.main(["loop", str(tmp_path), "--no-shot"])
    out = capsys.readouterr().out
    assert rc == 0 and "[iter 1/3] ✓ 收敛" in out
    assert os.path.exists(os.path.join(str(tmp_path), "build", "report.md"))


def test_loop_no_fix_returns_2_and_keeps_best(tmp_path, capsys):
    bad = dict(LOOP_OK_SPEC, texts=["标题文字", "不存在的文案"])
    _write_loop_project(str(tmp_path), bad)
    rc = cli.main(["loop", str(tmp_path), "--no-shot"])
    out = capsys.readouterr().out
    assert rc == 2 and "未指定 --fix" in out
    assert os.path.exists(os.path.join(str(tmp_path), "loop", "best-spec.yaml"))
    assert os.path.exists(os.path.join(str(tmp_path), "loop", "spec-iter1.yaml"))


def test_loop_fixer_converges_second_iter(tmp_path, capsys):
    bad = dict(LOOP_OK_SPEC, texts=["标题文字", "不存在的文案"])
    _write_loop_project(str(tmp_path), bad)
    fixer = tmp_path / "fixer.py"
    fixer.write_text(
        "import os, yaml\n"
        "p = os.environ['SNAP2EDIT_SPEC']\n"
        "s = yaml.safe_load(open(p, encoding='utf-8'))\n"
        "s['texts'] = ['标题文字']\n"
        "yaml.safe_dump(s, open(p, 'w', encoding='utf-8'), allow_unicode=True)\n",
        encoding="utf-8")
    rc = cli.main(["loop", str(tmp_path), "--no-shot", "--fix", f"python3 {fixer}"])
    out = capsys.readouterr().out
    assert rc == 0 and "[iter 2/3] ✓ 收敛" in out and "执行修正命令" in out
    # spec.yaml 已被 fixer 改写为可收敛版本
    with open(os.path.join(str(tmp_path), "spec.yaml"), encoding="utf-8") as f:
        assert "不存在的文案" not in f.read()


def test_loop_json_summary_and_max_iters(tmp_path, capsys):
    bad = dict(LOOP_OK_SPEC, texts=["标题文字", "不存在的文案"])
    _write_loop_project(str(tmp_path), bad)
    rc = cli.main(["loop", str(tmp_path), "--no-shot", "--max-iters", "1", "--json"])
    out = capsys.readouterr().out
    assert rc == 2
    data = json.loads(out.strip().splitlines()[-1])
    assert data["ok"] is False and data["converged"] is False
    assert data["iterations"] == 1 and data["history"][0]["ok"] is False


def test_loop_recovers_from_spec_error(tmp_path, capsys):
    bad = {"project": "baddemo", "canvas": {"width": 640, "height": 360},
           "elements": [
               {"id": "t", "type": "text", "x": 40, "y": 40, "size": 20, "text": "标题文字"},
               {"id": "b", "type": "rect", "x": 40, "y": 100, "w": 100, "h": 50, "fill": "紫色"},
           ]}
    _write_loop_project(str(tmp_path), bad)
    fixer = tmp_path / "fixer2.py"
    fixer.write_text(
        "import os, yaml\n"
        "p = os.environ['SNAP2EDIT_SPEC']\n"
        "s = yaml.safe_load(open(p, encoding='utf-8'))\n"
        "s['elements'][1]['fill'] = '#7C3AED'\n"
        "yaml.safe_dump(s, open(p, 'w', encoding='utf-8'), allow_unicode=True)\n",
        encoding="utf-8")
    rc = cli.main(["loop", str(tmp_path), "--no-shot", "--max-iters", "2",
                   "--fix", f"python3 {fixer}"])
    out = capsys.readouterr().out
    assert rc == 0 and "spec 解析失败" in out and "[iter 2/2] ✓ 收敛" in out


def test_loop_fixer_timeout_and_missing_cmd(tmp_path, capsys):
    _write_loop_project(str(tmp_path), dict(LOOP_OK_SPEC, texts=["标题文字", "不存在的文案"]))
    rc = cli.main(["loop", str(tmp_path), "--no-shot", "--max-iters", "2",
                   "--fix", "/nonexistent-fix-cmd-xyz", "--fix-timeout", "5"])
    out = capsys.readouterr().out
    assert rc == 2 and "修正命令无法执行" in out


# ---------------- F5/F6 补充分支 ----------------

def test_spec_component_more_validation_branches():
    E = lambda el: specmod.validate(min_spec(elements=[el]))
    with pytest.raises(specmod.SpecError, match="gap"):
        E({"id": "m", "type": "matrix-cell", "x": 0, "y": 0, "w": 10, "h": 10,
           "rows": 1, "cols": 1, "gap": -2})
    with pytest.raises(specmod.SpecError, match="texts 必须是"):
        E({"id": "m", "type": "matrix-cell", "x": 0, "y": 0, "w": 10, "h": 10,
           "rows": 1, "cols": 1, "texts": "不是列表"})
    with pytest.raises(specmod.SpecError, match="需要 size"):
        E({"id": "m", "type": "matrix-cell", "x": 0, "y": 0, "w": 10, "h": 10,
           "rows": 1, "cols": 1, "texts": ["无字号"]})
    with pytest.raises(specmod.SpecError, match="rx 必须是非负数字"):
        E({"id": "r", "type": "rrect", "x": 0, "y": 0, "w": 10, "h": 10, "rx": "abc"})
    # palette 非法值容错语义：静默降级为 None（视为未设置，回退默认色）
    bad = min_spec()
    bad["palette"] = {"accent": "红色"}
    out = specmod.validate(bad)
    assert out["palette"]["accent"] is None


def test_component_stroke_parts_render_both_lines():
    # brain 含 stroke 折线部件（svgout polyline / pptxout 开放 freeform）
    sp = specmod.validate(min_spec(elements=GALLERY_MIN_ELEMENTS + [
        {"id": "b", "type": "icon", "x": 420, "y": 0, "w": 60, "h": 60, "name": "brain", "fill": "#2B6CB0"},
    ], texts=[]))
    html = svgout.render_html(sp)
    assert html.count("<polyline") >= 5                       # brain 的 5 条折线部件
    with tempfile.TemporaryDirectory() as td:
        pptxout.render_pptx(sp, os.path.join(td, "x.pptx"))
        from pptx import Presentation
        names = [s.name for s in Presentation(os.path.join(td, "x.pptx")).slides[0].shapes]
        assert any(n.startswith("b-") for n in names)


def test_pptxout_zero_size_adjustments_tolerated():
    # 零尺寸触发 adjustments 除零防御分支（真实 pptx 形状可达），不应抛异常
    sp = specmod.validate(min_spec(elements=[
        {"id": "mz", "type": "matrix-cell", "x": 0, "y": 0, "w": 0, "h": 30, "rows": 1, "cols": 1},
        {"id": "fz", "type": "flow-box", "x": 40, "y": 0, "w": 0, "h": 60, "title": "T", "text": "B", "size": 10},
        {"id": "rz", "type": "rrect", "x": 100, "y": 0, "w": 0, "h": 20, "rx": 5},
    ], texts=[]))
    with tempfile.TemporaryDirectory() as td:
        pptxout.render_pptx(sp, os.path.join(td, "z.pptx"))


def test_verify_flowbox_body_overflow():
    sp = specmod.validate(min_spec(elements=[
        {"id": "f", "type": "flow-box", "x": 0, "y": 0, "w": 80, "h": 60,
         "title": "短", "text": "特别长的流程框正文文案会溢出边界", "size": 12},
    ], texts=None))
    over = verify.check_bounds(sp)
    assert any(o[0] == "f-text" for o in over)


def test_loop_fixer_nonzero_exit_still_retries(tmp_path, capsys):
    _write_loop_project(str(tmp_path), dict(LOOP_OK_SPEC, texts=["标题文字", "不存在的文案"]))
    rc = cli.main(["loop", str(tmp_path), "--no-shot", "--max-iters", "2",
                   "--fix", "python3 -c 'import sys; sys.exit(3)'"])
    out = capsys.readouterr().out
    assert rc == 2 and "退出码 3" in out and "[iter 2/2]" in out


def test_loop_fixer_timeout(tmp_path, capsys):
    _write_loop_project(str(tmp_path), dict(LOOP_OK_SPEC, texts=["标题文字", "不存在的文案"]))
    rc = cli.main(["loop", str(tmp_path), "--no-shot", "--max-iters", "2",
                   "--fix", "sleep 2", "--fix-timeout", "1"])
    out = capsys.readouterr().out
    assert rc == 2 and "修正命令超时" in out


def test_loop_many_failures_ellipsis(tmp_path, capsys, monkeypatch):
    _write_loop_project(str(tmp_path), LOOP_OK_SPEC)
    from snap2edit import verify as verify_mod
    fake = {"ok": False, "failures": [f"失败{i}" for i in range(7)], "report_md": None}
    monkeypatch.setattr(verify_mod, "collect_checks", lambda *a, **k: fake)
    rc = cli.main(["loop", str(tmp_path), "--no-shot", "--max-iters", "1"])
    out = capsys.readouterr().out
    assert rc == 2 and "以及另外 2 项" in out


def test_loop_json_converged(tmp_path, capsys):
    _write_loop_project(str(tmp_path), LOOP_OK_SPEC)
    rc = cli.main(["loop", str(tmp_path), "--no-shot", "--json"])
    data = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert rc == 0 and data["converged"] is True and data["iterations"] == 1


# ---------------- F7 可视化报告（report.py） ----------------

def test_report_node_status_mapping():
    """状态灯映射：门1→N2、门4(+附加)→N3、门2→N4、门3→N5、全绿→N6；缺席=skip。"""
    from snap2edit import report

    def gate(name, *passed):
        return {"gate": name, "title": "t",
                "items": [{"label": "x", "passed": p, "detail": ""} for p in passed]}

    g = [gate("门1 交付物① HTML+SVG", True), gate("门2 交付物② PPTX", True),
         gate("门3 文本边界", True), gate("门4 渲染截图", True)]
    assert report.node_status(g) == {"N2": "pass", "N3": "pass", "N4": "pass",
                                     "N5": "pass", "N6": "pass"}
    g.append(gate("附加 与原图差异", False))
    st = report.node_status(g)
    assert st["N3"] == "fail" and st["N6"] == "fail" and st["N2"] == "pass"
    st = report.node_status([g[0], g[1], g[2]])          # 门4 缺席（--no-shot）
    assert st["N3"] == "skip" and st["N6"] == "skip" and st["N5"] == "pass"
    st = report.node_status([gate("门1 交付物① HTML+SVG", False), g[1], g[2], g[3]])
    assert st["N2"] == "fail" and st["N6"] == "fail"
    assert all(v == "skip" for v in report.node_status([]).values())
    assert all(v == "skip" for v in report.node_status(None).values())


def test_report_overflow_marks_and_svg():
    """溢出项回映射画布坐标：matrix-cell 子项 id→格子框；SVG 红色高亮＋id 标签。"""
    from snap2edit import report

    long_txt = "这是一个远超格子宽度的超长文本"
    sp = specmod.validate({
        "project": "溢出标注", "canvas": {"width": 800, "height": 600},
        "palette": {"primary": "#111111", "accent": "#2B6CB0", "card": "#FFFFFF", "bg": "#FFFFFF"},
        "texts": [long_txt],
        "elements": [
            {"id": "mx", "type": "matrix-cell", "x": 40, "y": 40, "w": 200, "h": 100,
             "rows": 2, "cols": 2, "size": 14, "texts": [long_txt, "", "", ""]},
            {"id": "fb", "type": "flow-box", "x": 300, "y": 40, "w": 160, "h": 80,
             "size": 13, "title": "流程", "text": "正文"},
        ],
    })
    marks = report.overflow_marks(sp)
    assert marks and marks[0]["id"] == "mx-r1c1" and marks[0]["box"] is not None
    boxes = report.elem_boxes(sp)
    assert boxes["fb-title"] == boxes["fb"] == boxes["fb-text"]
    svg = report.canvas_svg(sp, marks)
    assert 'stroke="#dc2626"' in svg and "mx-r1c1" in svg
    # 无溢出 spec：零标注，SVG 仅底稿
    ok_sp = specmod.load(DEMO)
    assert report.overflow_marks(ok_sp) == []


def test_report_heatmap_png(tmp_path):
    """热力图：同色图差异≈0；异色图差异>0 且输出 PNG 非空。"""
    from PIL import Image

    from snap2edit import report, verify

    a = os.path.join(str(tmp_path), "a.png")
    b = os.path.join(str(tmp_path), "b.png")
    rendered = os.path.join(str(tmp_path), "rendered.png")
    out = os.path.join(str(tmp_path), "heat.png")
    Image.new("RGB", (70, 50), "#aa0000").save(a)   # 非 16 倍数 → 含残余边缘块
    Image.new("RGB", (80, 40), "#00aa00").save(b)   # 与 rendered 同色 → 热力图均值对齐
    Image.new("RGB", (80, 40), "#00aa00").save(rendered)
    mean, grid = verify.block_diff_grid(a, b)
    assert len(grid) == 4 and len(grid[0]) == 5     # ceil(50/16) x ceil(70/16)
    assert report.heatmap_png(a, rendered, out) == pytest.approx(mean, abs=1e-6)
    assert os.path.exists(out) and os.path.getsize(out) > 0
    same = report.heatmap_png(a, a, out)
    assert same == pytest.approx(0.0, abs=1e-6)


def test_report_write_html_contains_four_elements(tmp_path):
    """单文件 HTML 四要素：状态灯 / 并排图 / 热力图 / 溢出标注；转义安全；无外链。"""
    from snap2edit import report

    tricky = "A<b>&\"引号\"文"
    sp = specmod.validate({
        "project": "报告四要素", "canvas": {"width": 640, "height": 360},
        "palette": {"primary": "#111111", "accent": "#2B6CB0", "card": "#FFFFFF", "bg": "#FFFFFF"},
        "texts": [tricky],
        "elements": [
            # 窄容器强制门3溢出 → 敏感字符进入溢出表，同时验证转义
            {"id": "t1", "type": "rect", "x": 40, "y": 40, "w": 30, "h": 20,
             "fill": "#2B6CB0", "text": tricky, "size": 16},
        ],
    })
    build = os.path.join(str(tmp_path), "build")
    os.makedirs(build)
    data = {"ok": True, "project": "报告四要素",
            "gates": [{"gate": "门1 交付物① HTML+SVG", "title": "HTML 检查",
                       "items": [{"label": "含<b>与&的标签文本", "passed": True,
                                  "detail": "d<1>"}]}],
            "failures": [], "artifacts": {"html": os.path.join(build, "x.html"),
                                          "pptx": None, "shot": None},
            "report_md": os.path.join(build, "report.md")}
    path = report.write_html(build, data, sp, original=None)
    assert os.path.abspath(path) == os.path.join(os.path.abspath(build), "report.html")
    html = open(path, encoding="utf-8").read()
    assert "结点状态灯" in html and "N6" in html and "并排图" in html
    assert "diff 热力图" in html and "文本溢出标注" in html and "四道门明细" in html
    assert "A&lt;b&gt;&amp;&quot;引号&quot;文" in html and "A<b>" not in html
    assert "d&lt;1&gt;" in html
    assert "未执行截图" in html and "未提供原图" in html      # 无 shot/原图 → 跳过说明
    assert 'src="http' not in html and 'href="http' not in html  # 单文件无外链资源（xmlns 除外）


def test_report_escape_in_overflow_table():
    """溢出表内文本含 HTML 敏感字符时转义（门3 溢出路径）。"""
    from snap2edit import report

    sp = specmod.validate({
        "project": "转义", "canvas": {"width": 200, "height": 100},
        "palette": {"primary": "#111111", "accent": "#2B6CB0", "card": "#FFFFFF", "bg": "#FFFFFF"},
        "texts": ["<i>宽</i>"],
        "elements": [
            {"id": "t", "type": "rect", "x": 10, "y": 10, "w": 20, "h": 20,
             "fill": "#2B6CB0", "text": "<i>宽</i>", "size": 14},
        ],
    })
    doc = report.render_html({"ok": False, "project": "转义", "gates": [],
                              "failures": [], "artifacts": {}, "report_md": None},
                             sp, original=None)
    assert "<i>宽</i>" not in doc.replace("&lt;i&gt;宽&lt;/i&gt;", "")
    assert "&lt;i&gt;宽&lt;/i&gt;" in doc


def test_collect_checks_writes_report_html(tmp_path):
    """collect_checks 集成：落盘 report.html 且与 report.md 并存；状态灯 N3=skip（无截图）。"""
    with tempfile.TemporaryDirectory() as td:
        sp = specmod.load(DEMO)
        name = specmod.safe_project(sp)
        build = os.path.join(td, "build")
        os.makedirs(build)
        with open(os.path.join(build, f"{name}.html"), "w", encoding="utf-8") as f:
            f.write(svgout.render_html(sp))
        pptxout.render_pptx(sp, os.path.join(build, f"{name}.pptx"))
        data = verify.collect_checks(td, sp, do_shot=False, log=None)
        assert data["report_html"] and os.path.exists(data["report_html"])
        assert os.path.exists(data["report_md"])
        html = open(data["report_html"], encoding="utf-8").read()
        assert "结点状态灯" in html and "四道门明细" in html
        assert "未执行截图" in html  # --no-shot 时并排图/热力图给出跳过说明


def test_loop_snapshots_report_html(tmp_path, capsys, monkeypatch):
    """loop 失败轮快照：report-iter{N}.html 与 report-iter{N}.md 并存。"""
    from snap2edit import verify as verify_mod

    _write_loop_project(str(tmp_path), dict(LOOP_OK_SPEC, texts=["标题文字", "缺失文案"]))
    build = os.path.join(str(tmp_path), "build")
    os.makedirs(build)
    md = os.path.join(build, "report.md")
    htm = os.path.join(build, "report.html")
    with open(md, "w", encoding="utf-8") as f:
        f.write("# md 报告")
    with open(htm, "w", encoding="utf-8") as f:
        f.write("<html>F7 报告</html>")
    fake = {"ok": False, "failures": ["a"], "report_md": md, "report_html": htm}
    monkeypatch.setattr(verify_mod, "collect_checks", lambda *a, **k: fake)
    rc = cli.main(["loop", str(tmp_path), "--no-shot", "--max-iters", "1"])
    assert rc == 2
    snap = os.path.join(str(tmp_path), "loop", "report-iter1.html")
    assert os.path.exists(snap) and "F7 报告" in open(snap, encoding="utf-8").read()
    assert os.path.exists(os.path.join(str(tmp_path), "loop", "report-iter1.md"))


def test_loop_tolerates_missing_report_html(tmp_path, capsys, monkeypatch):
    """旧结构 fake（无 report_html 键）→ loop 不报错（.get 兜底）。"""
    from snap2edit import verify as verify_mod

    _write_loop_project(str(tmp_path), LOOP_OK_SPEC)
    fake = {"ok": True, "failures": [], "report_md": None}
    monkeypatch.setattr(verify_mod, "collect_checks", lambda *a, **k: fake)
    rc = cli.main(["loop", str(tmp_path), "--no-shot", "--json"])
    data = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert rc == 0 and data["artifacts"]["report_html"] is None


def test_report_elem_boxes_skips_invalid_and_unmapped_marks():
    """防御分支：坐标缺失/非法元素静默跳过；无坐标的溢出记录不入 SVG。"""
    from snap2edit import report

    boxes = report.elem_boxes({
        "canvas": {"width": 100, "height": 100},
        "elements": [
            {"id": "bad1", "type": "rect", "y": 5, "w": 3, "h": 3},           # 缺 x
            {"id": "bad2", "type": "rect", "x": "x", "y": 0, "w": 3, "h": 3},  # x 非数字
            {"id": "bad3", "type": "circle", "x": 0, "y": 0, "w": 10, "h": None},  # h None
        ],
    })
    assert boxes == {}
    svg = report.canvas_svg(specmod.load(DEMO),
                            [{"id": "ghost", "text": "t", "need": 9, "avail": 1, "box": None}])
    assert 'stroke="#dc2626"' not in svg  # 未定位 → 不画红框（仍会进明细表）


def test_collect_checks_report_failure_is_non_blocking(monkeypatch):
    """F7 报告生成失败 → 不阻断校验结论：report_html=None 且记日志。"""
    import snap2edit.report as report_mod

    with tempfile.TemporaryDirectory() as td:
        sp = specmod.load(DEMO)
        name = specmod.safe_project(sp)
        build = os.path.join(td, "build")
        os.makedirs(build)
        with open(os.path.join(build, f"{name}.html"), "w", encoding="utf-8") as f:
            f.write(svgout.render_html(sp))
        pptxout.render_pptx(sp, os.path.join(build, f"{name}.pptx"))
        logs = []

        def boom(*a, **k):
            raise RuntimeError("boom")

        monkeypatch.setattr(report_mod, "write_html", boom)
        data = verify.collect_checks(td, sp, do_shot=False, log=logs.append)
        assert data["ok"] is True and data["report_html"] is None
        assert any("HTML 可视化报告生成失败" in m for m in logs)
