# -*- coding: utf-8 -*-
"""校验门 —— 六步标准流程结点 N2–N6 的工具化。

  门1 HTML 检查     文本元素覆盖 / 无位图 / 文案清单 / 占位符黑名单
  门2 PPTX 检查     幻灯片尺寸 / Picture=0 / 文案清单 / 占位符黑名单
  门3 边界校验      PIL 实测文本宽度 vs 可用宽度（防溢出）
  门4 截图与差异    Playwright 截图 + 非空白率 +（可选）与原图 16px 块差异
"""

import os
import re

from .spec import texts_of

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/chinese/NotoSansSC-Regular.ttf",
    "/usr/share/fonts/truetype/chinese/NotoSansSC-Bold.ttf",
]
BLACKLIST = ("XXX", "TODO", "待补充", "【", "undefined", "NaN")

_font_cache = {}


def _font():
    from PIL import ImageFont
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            if p not in _font_cache:
                _font_cache[p] = ImageFont.truetype(p, 100)
            return _font_cache[p]
    return None


def text_width_px(text, size_px):
    """实测文本宽度(px)，与 PowerPoint 度量基本一致；无字体时按字符宽度估算。"""
    f = _font()
    if f is not None:
        return f.getlength(text) / 100.0 * size_px
    w = 0.0
    for ch in text:
        w += 1.0 if ord(ch) > 0x2E7F else (0.30 if ch == " " else 0.56)
    return w * size_px


# ---------------- 门1：HTML ----------------

def check_html(html, spec):
    res = []
    texts = texts_of(spec)
    n_have = len(re.findall(r"<text[^>]*>", html))
    n_want = sum(1 for el in spec["elements"] if el["type"] == "text" or el.get("text"))
    res.append(("HTML <text> 元素数量覆盖", n_have >= n_want, f"{n_have}/{n_want}"))
    no_bitmap = ("<image" not in html) and ("data:image" not in html)
    res.append(("无位图（<image>/data:image 零命中）", no_bitmap, ""))
    joined = "".join(re.findall(r"<text[^>]*>(.*?)</text>", html, re.S))
    missing = [t for t in texts if t not in joined]
    res.append(("文案清单全部在场", not missing,
                f"缺失: {missing}" if missing else f"{len(texts)} 条全覆盖"))
    bad = [b for b in BLACKLIST if b in joined]
    res.append(("无残留占位符", not bad, str(bad) if bad else ""))
    return res


# ---------------- 门2：PPTX ----------------

def check_pptx(path, spec):
    from pptx import Presentation
    from .geometry import resolve_slide_emu
    from .spec import texts_of

    res = []
    prs = Presentation(path)
    want = resolve_slide_emu(spec)
    size_ok = (int(prs.slide_width), int(prs.slide_height)) == tuple(want)
    res.append(("幻灯片尺寸 EMU 正确", size_ok,
                f"{prs.slide_width}x{prs.slide_height}（期望 {want[0]}x{want[1]}）"))
    shapes = list(prs.slides[0].shapes)
    n_pic = sum(1 for sp in shapes
                if sp.shape_type == 13 or sp.__class__.__name__ == "Picture")
    res.append(("无嵌入图片（Picture = 0，100% 原生形状）", n_pic == 0, f"Picture: {n_pic}"))
    joined = "".join(sp.text_frame.text for sp in shapes if sp.has_text_frame)
    texts = texts_of(spec)
    missing = [t for t in texts if t not in joined]
    res.append(("文本框文案清单全部在场", not missing,
                f"缺失: {missing}" if missing else f"{len(texts)} 条全覆盖"))
    bad = [b for b in BLACKLIST if b in joined]
    res.append(("无残留占位符", not bad, str(bad) if bad else ""))
    return res


# ---------------- 门3：边界 ----------------

def check_bounds(spec):
    """返回溢出列表 [(id, 文本, 需要宽度, 可用宽度), ...]"""
    cw = spec["canvas"]["width"]
    over = []
    for el in spec["elements"]:
        if el["type"] == "text":
            lines = el.get("lines") or [str(el.get("text", ""))]
            for ln in lines:
                need = text_width_px(ln, float(el["size"]))
                avail = el.get("w")
                if not avail and el.get("align", "left") == "left":
                    avail = cw - el["x"]
                if avail and need > avail:
                    over.append((el["id"], ln, round(need, 1), round(avail, 1)))
        elif el.get("text") and el["type"] in ("rect", "rrect", "pill", "circle"):
            need = text_width_px(str(el["text"]), float(el["size"]))
            if need > el["w"] - 8:
                over.append((el["id"], el["text"], round(need, 1), el["w"]))
    return over


# ---------------- 门4：截图与差异 ----------------

def screenshot(html_path, out_png, wait_ms=800):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None, "未安装 playwright（pip install playwright && playwright install chromium）"
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            page = b.new_page(viewport={"width": 1600, "height": 1000},
                              device_scale_factor=1)
            page.goto("file://" + os.path.abspath(html_path))
            page.wait_for_timeout(wait_ms)
            el = page.query_selector("#stage")
            if el is None:
                b.close()
                return None, "HTML 中未找到 #stage 容器"
            el.screenshot(path=out_png)
            b.close()
        return out_png, None
    except Exception as e:  # noqa: BLE001
        return None, f"截图失败: {e}"


def not_blank_ratio(png_path):
    from PIL import Image
    import numpy as np
    im = np.array(Image.open(png_path).convert("L"))
    return float((im < 245).mean())


def block_diff(original_png, rendered_png, block=16, top=15):
    """与原图的 16px 块聚合差异；返回 (总平均差异, [(score, bx, by), ...])"""
    from PIL import Image
    import numpy as np
    a = Image.open(original_png).convert("RGB")
    b = Image.open(rendered_png).convert("RGB").resize(a.size)
    d = np.abs(np.array(a, dtype=int) - np.array(b, dtype=int)).sum(axis=2)
    H, W = d.shape
    scores = []
    for by in range(0, H - block, block):
        for bx in range(0, W - block, block):
            scores.append((float(d[by:by + block, bx:bx + block].mean()), bx, by))
    scores.sort(reverse=True)
    return float(d.mean()), scores[:top]


# ---------------- 汇总执行 ----------------

def collect_checks(project_dir, spec, original=None, do_shot=True, log=None):
    """四道校验门 —— 结构化结果（web API 与 CLI --json 使用）。

    返回:
        {
          "ok": bool,
          "project": 安全化的项目名,
          "gates": [{"gate": "门1 交付物① HTML+SVG", "title": "HTML 检查",
                     "items": [{"label", "passed", "detail"}, ...]}, ...],
          "failures": ["门1 · HTML 检查 · 文案清单全部在场（缺失: [...]）", ...],
          "artifacts": {"html": path, "pptx": path, "shot": path|None},
        }
    同时把 markdown 报告写入 build/report.md。
    """

    def say(msg):
        if log:
            log(msg)

    from .spec import safe_project

    name = safe_project(spec)
    build = os.path.join(project_dir, "build")
    html_path = os.path.join(build, f"{name}.html")
    pptx_path = os.path.join(build, f"{name}.pptx")
    ok = True
    gates = []

    def section(gate, title, items):
        nonlocal ok
        ok = ok and all(p for _, p, _ in items)
        gates.append({
            "gate": gate,
            "title": title,
            "items": [{"label": l, "passed": p, "detail": d} for l, p, d in items],
        })

    say("== 门1 交付物① HTML+SVG ==")
    with open(html_path, encoding="utf-8") as f:
        html = f.read()
    section("门1 交付物① HTML+SVG", "HTML 检查", check_html(html, spec))

    say("== 门2 交付物② PPTX ==")
    section("门2 交付物② PPTX", "PPTX 检查", check_pptx(pptx_path, spec))

    say("== 门3 文本边界 ==")
    over = check_bounds(spec)
    section("门3 文本边界", "边界校验（实测宽度 vs 可用宽度）", [
        ("全部文本在边界内", not over,
         "; ".join(f"{i}:「{t}」需{n}>有{v}" for i, t, n, v in over[:5]) if over else "")])

    shot_path = None
    if do_shot:
        say("== 门4 渲染截图 ==")
        png = os.path.join(build, "shot.png")
        path, err = screenshot(html_path, png)
        if path:
            shot_path = path
            ratio = not_blank_ratio(path)
            section("门4 渲染截图", "截图校验", [
                ("截图非空白（非白像素 > 0.2%，拦截整页空白渲染）", ratio > 0.002, f"{ratio:.1%}"),
                ("截图已保存", True, png)])
        else:
            section("门4 渲染截图", "截图校验", [("截图（跳过）", True, err or "")])

    if original:
        say("== 附加 与原图差异 ==")
        png = os.path.join(build, "shot.png")
        if os.path.exists(png):
            mean, top = block_diff(original, png)
            section("附加 与原图差异", "块差异（16px 聚合）", [
                ("总平均差异 < 10/255", mean < 10, f"{mean:.1f}"),
                ("TOP 差异块（信息项）", True,
                 " ".join(f"({bx},{by})={s:.0f}" for s, bx, by in top[:5]))])
        else:
            section("附加 与原图差异", "与原图差异", [("需先完成截图", False, "")])

    failures = [f"{g['gate']} · {g['title']} · {it['label']}" + (f"（{it['detail']}）" if it["detail"] else "")
                for g in gates for it in g["items"] if not it["passed"]]

    # markdown 报告落盘（与 CLI 文本报告同一格式）
    rep = [f"# Snap2Edit 校验报告 · {name}", ""]
    for g in gates:
        rep.append(f"## {g['gate']} —— {g['title']}")
        for it in g["items"]:
            mark = "✓" if it["passed"] else "✗"
            rep.append(f"- {mark} {it['label']}" + (f"（{it['detail']}）" if it["detail"] else ""))
        rep.append("")
    os.makedirs(build, exist_ok=True)
    rep_path = os.path.join(build, "report.md")
    with open(rep_path, "w", encoding="utf-8") as f:
        f.write("\n".join(rep) + "\n")

    return {
        "ok": ok,
        "project": name,
        "gates": gates,
        "failures": failures,
        "artifacts": {"html": html_path, "pptx": pptx_path, "shot": shot_path},
        "report_md": rep_path,
    }


def run_checks(project_dir, spec, original=None, do_shot=True, log=print):
    """CLI 入口：打印过程日志与结论，返回布尔（0/2 退出码）。"""
    from .spec import safe_project

    data = collect_checks(project_dir, spec, original=original, do_shot=do_shot, log=log)
    log(("\n✓ 全部校验通过" if data["ok"] else "\n✗ 存在未通过项")
        + f"，报告: {data['report_md']}")
    return data["ok"]
