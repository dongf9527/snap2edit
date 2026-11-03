# -*- coding: utf-8 -*-
"""F7 可视化报告 —— build/report.html（单文件 HTML，零外部依赖）。

四要素（PRD F7）：
  ① 结点 N2–N6 状态灯   门1→N2、门4(＋原图 diff)→N3、门2→N4、门3→N5、全绿→N6
  ② 并排图              原图 vs 渲染截图（base64 内嵌，单文件可直接分发）
  ③ diff 热力图         16px 块差异全网格 → 绿→红半透明叠加在渲染截图上
  ④ 溢出标注            门3 溢出项回映射到画布坐标，SVG 标注图 ＋ 明细表

单文件策略：图片一律 base64 data URI 内嵌、样式内联、无 JS、无外链；
`report.md`（文本版，供 fixer/CI）与本文件并存，由 verify.collect_checks 同时落盘。
"""

import base64
import html as _html
import os
import time

# 状态灯语义：N1（布局规格书定稿）为人工结点，不在自动校验范围内（PRD F7 只要求 N2–N6）
LIGHTS = [
    ("N2", "HTML+SVG 生成", "门1 文本覆盖 / 无位图 / 文案 / 占位符"),
    ("N3", "HTML 校验收敛", "门4 截图非空白 ＋ 与原图块差异"),
    ("N4", "PPTX 生成", "门2 尺寸 / Picture=0 / 文案 / 占位符"),
    ("N5", "边界零溢出", "门3 实测文本宽度 vs 可用宽度"),
    ("N6", "终检交付", "以上结点全部通过"),
]

_DIFF_SAT = 60.0  # 热力图色饱和阈值（765 色阶；门3 判定线为总平均 < 10）


def esc(s):
    return _html.escape(str(s), quote=True)


# ---------------- ① 结点状态灯 ----------------

def node_status(gates):
    """gates（collect_checks 输出）→ {N2..N6: "pass"|"fail"|"skip"}。

    缺席的门记为 skip（如 --no-shot 时门4 缺席 → N3 未执行）；
    N6 仅在门1–门4 全部在场且全过（含可选原图 diff）时为 pass。
    """
    gates = gates or []

    def ok(prefix):
        for g in gates:
            if str(g.get("gate", "")).startswith(prefix):
                return all(bool(it.get("passed")) for it in g.get("items", []))
        return None

    g1, g2, g3, g4, ex = ok("门1"), ok("门2"), ok("门3"), ok("门4"), ok("附加")
    n3 = None if g4 is None else (g4 and (ex is None or ex))

    def st(v):
        return "pass" if v else ("fail" if v is not None else "skip")

    core = (g1, g2, g3, g4)
    if any(v is False for v in core) or ex is False:
        n6 = "fail"
    elif any(v is None for v in core):
        n6 = "skip"
    else:
        n6 = "pass"
    return {"N2": st(g1), "N3": st(n3), "N4": st(g2), "N5": st(g3), "N6": n6}


# ---------------- 图片内嵌与热力图 ----------------

def _data_uri(path):
    ext = os.path.splitext(path)[1].lower()
    mime = {".png": "image/png", ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg", ".webp": "image/webp"}.get(ext, "image/png")
    with open(path, "rb") as f:
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode("ascii")


def heatmap_png(original, rendered, out_path, block=16, sat=_DIFF_SAT):
    """差异热力图叠加图：以渲染截图为底，按 16px 块差异着色（绿→黄→红）。

    返回总平均差异（765 色阶，与门3「总平均差异 < 10」同口径）。
    """
    from PIL import Image, ImageDraw

    from .verify import block_diff_grid

    mean, grid = block_diff_grid(original, rendered, block=block)
    base = Image.open(rendered).convert("RGB").resize(Image.open(original).size)
    ov = Image.new("RGBA", base.size, (0, 0, 0, 0))
    dr = ImageDraw.Draw(ov)
    for gy, row in enumerate(grid):
        for gx, s in enumerate(row):
            if s < 2.0:  # 近零差异噪声不着色
                continue
            t = min(1.0, s / sat)
            r, g = (int(255 * 2 * t), 255) if t < 0.5 else (255, int(255 * 2 * (1 - t)))
            dr.rectangle([gx * block, gy * block,
                          (gx + 1) * block - 1, (gy + 1) * block - 1],
                         fill=(r, g, 40, int(45 + 150 * t)))
    Image.alpha_composite(base.convert("RGBA"), ov).convert("RGB").save(out_path)
    return mean


# ---------------- ④ 溢出标注（坐标回映射） ----------------

def elem_boxes(spec):
    """可标注元素的 id → (x, y, w, h) 基础框（组件子项 id 带后缀同框映射）。"""
    from .components import cube_faces, matrix_cells

    cw = float(spec["canvas"]["width"])
    boxes = {}
    for el in spec.get("elements") or []:
        t, eid = el.get("type"), str(el.get("id", ""))
        try:
            if t in ("rect", "rrect", "pill", "circle", "flow-box"):
                boxes[eid] = (float(el["x"]), float(el["y"]),
                              float(el["w"]), float(el["h"]))
                if t == "flow-box":  # 子项溢出（-title / -text）落在同一框上
                    boxes[eid + "-title"] = boxes[eid]
                    boxes[eid + "-text"] = boxes[eid]
            elif t == "text":
                lines = el.get("lines") or [str(el.get("text", ""))]
                w = el.get("w")
                if not w:
                    w = max(cw - float(el["x"]), float(el.get("size", 12)))
                h = float(el.get("size", 12)) * 1.35 * max(len(lines), 1)
                boxes[eid] = (float(el["x"]), float(el["y"]), float(w), h)
            elif t == "cube":  # 文字在正面面片内
                fx, fy, fw, fh = cube_faces(el["x"], el["y"], el["w"], el["h"],
                                            el.get("depth"))["front"]
                boxes[eid] = (float(fx), float(fy), float(fw), float(fh))
            elif t == "matrix-cell":
                cells = matrix_cells(el["x"], el["y"], el["w"], el["h"],
                                     el["rows"], el["cols"], el.get("gap", 0))
                for k, (cx, cy, cwid, chh) in enumerate(cells):
                    r, c = divmod(k, el["cols"])
                    boxes[f"{eid}-r{r + 1}c{c + 1}"] = (float(cx), float(cy),
                                                        float(cwid), float(chh))
        except (KeyError, TypeError, ValueError):
            continue  # 坐标缺失/非法的元素不参与标注
    return boxes


def overflow_marks(spec):
    """门3 溢出列表 → 带画布坐标的标注记录（用于 SVG 标注图与明细表）。"""
    from .verify import check_bounds

    boxes = elem_boxes(spec)
    marks = []
    for eid, txt, need, avail in check_bounds(spec):
        eid = str(eid)
        marks.append({"id": eid, "text": str(txt),
                      "need": float(need), "avail": float(avail),
                      "box": boxes.get(eid)})
    return marks


def canvas_svg(spec, marks, width=760):
    """画布溢出标注图：全部可标注元素淡描边做底，溢出元素红色高亮＋id 标签。"""
    cw = float(spec["canvas"]["width"])
    ch = float(spec["canvas"]["height"])
    fs = max(9.0, cw / 64.0)  # 标签字号（viewBox 坐标系）
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {cw:g} {ch:g}" '
         f'style="width:{width}px;max-width:100%;height:auto;background:#fff;'
         f'border:1px solid #e2e8f0;border-radius:8px" role="img" '
         f'aria-label="画布溢出标注图">']
    p.append(f'<rect x="0" y="0" width="{cw:g}" height="{ch:g}" fill="#ffffff"/>')
    boxes = elem_boxes(spec)
    mark_ids = {m["id"] for m in marks if m["box"]}
    for eid, (x, y, w, h) in boxes.items():
        if eid in mark_ids:
            continue
        p.append(f'<rect x="{x:g}" y="{y:g}" width="{max(w, 1):g}" height="{max(h, 1):g}" '
                 f'fill="none" stroke="#cbd5e1" stroke-width="{fs / 16:.2f}"/>')
    for m in marks:
        if not m["box"]:
            continue
        x, y, w, h = m["box"]
        p.append(f'<rect x="{x:g}" y="{y:g}" width="{max(w, 1):g}" height="{max(h, 1):g}" '
                 f'fill="rgba(220,38,38,.14)" stroke="#dc2626" stroke-width="{fs / 10:.2f}"/>')
        lx = max(2.0, min(x, cw - len(m["id"]) * fs * 0.62 - 2))
        ly = y - fs * 0.35 if y - fs * 0.35 >= fs else y + h + fs
        p.append(f'<text x="{lx:g}" y="{min(max(ly, fs), ch - 2):g}" font-size="{fs:g}" '
                 f'fill="#dc2626" font-family="sans-serif">{esc(m["id"])}</text>')
    p.append("</svg>")
    return "".join(p)


# ---------------- HTML 组装 ----------------

_CSS = """
:root{--ok:#16a34a;--bad:#dc2626;--skip:#94a3b8;--ink:#0f172a;--dim:#64748b;
      --line:#e2e8f0;--bg:#f6f8fb}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
     font-family:"PingFang SC","Microsoft YaHei","Noto Sans SC",system-ui,sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:24px 20px 6px}
h1{font-size:20px;margin:0}
h1 .badge{font-size:12px;vertical-align:3px;margin-left:10px;padding:2px 10px;
          border-radius:999px;color:#fff}
.badge.ok{background:var(--ok)} .badge.bad{background:var(--bad)}
.meta{color:var(--dim);font-size:12px;margin-top:6px}
section{background:#fff;border:1px solid var(--line);border-radius:12px;
        padding:16px 20px;margin-top:16px}
h2{font-size:15px;margin:0 0 12px}
h2 small{color:var(--dim);font-weight:400;font-size:12px;margin-left:8px}
.lights{display:flex;gap:10px;flex-wrap:wrap}
.light{background:#fff;border:1px solid var(--line);border-radius:10px;
       padding:10px 14px;min-width:180px;flex:1}
.light b{font-size:13px}
.light .why{color:var(--dim);font-size:11px;margin-top:4px;line-height:1.5}
.dot{width:11px;height:11px;border-radius:50%;display:inline-block;margin-right:6px}
.dot.pass{background:var(--ok)} .dot.fail{background:var(--bad)}
.dot.skip{background:var(--skip)}
.pair{display:flex;gap:14px;flex-wrap:wrap}
.pair figure{margin:0;flex:1;min-width:300px}
.pair img{width:100%;border:1px solid var(--line);border-radius:8px;display:block}
figcaption{font-size:12px;color:var(--dim);margin-top:6px}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;
      vertical-align:top}
th{color:var(--dim);font-weight:600;font-size:12px;white-space:nowrap}
td.mark{font-weight:700;width:34px} td.mark.ok{color:var(--ok)}
td.mark.bad{color:var(--bad)}
.dim{color:var(--dim)} .num{white-space:nowrap;font-variant-numeric:tabular-nums}
.over{color:var(--bad);font-weight:600}
.note{border-radius:8px;padding:8px 12px;font-size:13px;
      background:#fffbeb;border:1px solid #fde68a;color:#92400e}
.note.good{background:#f0fdf4;border-color:#bbf7d0;color:#166534}
.gate{margin-bottom:6px} .gate h3{font-size:13px;margin:10px 0 6px}
footer{color:var(--dim);font-size:12px;margin:16px 0 30px;line-height:1.7}
"""


def _lights_html(status):
    cards = []
    for nid, name, why in LIGHTS:
        s = status.get(nid, "skip")
        txt = {"pass": "通过", "fail": "未通过", "skip": "未执行"}[s]
        cards.append(
            f'<div class="light"><b><span class="dot {s}"></span>{nid} {esc(name)}</b>'
            f'<div class="why">{esc(why)}<br/>状态：<b>{txt}</b></div></div>')
    return f'<div class="lights">{"".join(cards)}</div>'


def _gates_html(gates):
    out = []
    for g in gates or []:
        rows = "".join(
            f'<tr><td class="mark {"ok" if it["passed"] else "bad"}">'
            f'{"✓" if it["passed"] else "✗"}</td>'
            f'<td>{esc(it["label"])}</td>'
            f'<td class="dim">{esc(it["detail"]) if it["detail"] else "—"}</td></tr>'
            for it in g.get("items", []))
        out.append(f'<div class="gate"><h3>{esc(g["gate"])} —— {esc(g["title"])}</h3>'
                   f'<table><tr><th>结果</th><th>检查项</th><th>说明</th></tr>'
                   f'{rows}</table></div>')
    return "".join(out)


def _pair_section(spec, data, original):
    arts = data.get("artifacts") or {}
    shot = arts.get("shot")
    figs, notes = [], []
    if original and os.path.exists(original):
        figs.append(("原图（对照基准）", _data_uri(original)))
    elif original:
        notes.append(f"原图路径不存在，跳过原图对照：{esc(original)}")
    else:
        notes.append("未提供原图（--original 可启用并排对照）。")
    if shot and os.path.exists(shot):
        figs.append(("渲染截图（门4 Playwright 实拍 #stage）", _data_uri(shot)))
    else:
        notes.append("未执行截图（--no-shot 或截图失败），并排对比与 diff 热力图不可用。")
    imgs = "".join(f"<figure><img src='{src}' alt='{esc(cap)}'/>"
                   f"<figcaption>{esc(cap)}</figcaption></figure>" for cap, src in figs)
    # figs 为空时 notes 必然非空（shot 缺失 → 「未执行截图」；original 缺失 → 对应说明）
    note = "".join(f'<p class="note">{n}</p>' for n in notes)
    return f'<h2>并排图 <small>原图 vs 渲染截图</small></h2>{note}<div class="pair">{imgs}</div>'


def _diff_section(spec, data, original, build):
    arts = data.get("artifacts") or {}
    shot = arts.get("shot")
    has_shot = shot and os.path.exists(shot)
    has_orig = original and os.path.exists(original)
    if not (has_shot and has_orig):
        why = "未提供原图（--original 可启用）" if not has_orig else "无渲染截图"
        return (f'<h2>diff 热力图 <small>16px 块差异叠加</small></h2>'
                f'<p class="note">跳过：{esc(why)}。</p>')
    hm = os.path.join(build, "heatmap.png")
    mean = heatmap_png(original, shot, hm)
    tone = ("good" if mean < 10 else "")
    return (f'<h2>diff 热力图 <small>16px 块差异叠加（绿→黄→红，饱和于 {_DIFF_SAT:g}）</small></h2>'
            f'<figure style="margin:0"><img src=\'{_data_uri(hm)}\' alt="diff 热力图"/>'
            f'<figcaption>总平均差异 <b>{mean:.1f}</b>（判定线 &lt; 10）；'
            f'TOP 差异块见「四道门明细 · 附加 与原图差异」。</figcaption></figure>'
            f'<p class="note {tone}">总平均差异 {mean:.1f} —— '
            f'{"低于判定线 10，收敛" if mean < 10 else "高于判定线 10，未收敛（按 TOP 差异块定位修正）"}。</p>')


def _overflow_section(spec):
    marks = overflow_marks(spec)
    if not marks:
        return (f'<h2>文本溢出标注 <small>门3 实测宽度 vs 可用宽度</small></h2>'
                f'<p class="note good">✓ 门3 零溢出：全部文本实测宽度在可用宽度内。</p>'
                f'{canvas_svg(spec, marks)}')
    rows = "".join(
        f'<tr><td>{esc(m["id"])}</td><td class="dim">{esc(m["text"])}</td>'
        f'<td class="num">{m["need"]:.1f}</td><td class="num">{m["avail"]:.1f}</td>'
        f'<td class="num over">+{m["need"] - m["avail"]:.1f}</td></tr>'
        for m in marks)
    placed = sum(1 for m in marks if m["box"])
    return (f'<h2>文本溢出标注 <small>门3 实测宽度 vs 可用宽度</small></h2>'
            f'<p class="note">{len(marks)} 处溢出（{placed} 处已定位到画布坐标，红色高亮）：</p>'
            f'{canvas_svg(spec, marks)}'
            f'<table><tr><th>元素 id</th><th>文本</th><th>需要(px)</th>'
            f'<th>可用(px)</th><th>超出(px)</th></tr>{rows}</table>')


def render_html(data, spec, original=None):
    """collect_checks 结果 + spec → 单文件 HTML 报告字符串。"""
    name = data.get("project") or "output"
    status = node_status(data.get("gates"))
    ok = bool(data.get("ok"))
    canvas = spec.get("canvas") or {}
    n_el = len(spec.get("elements") or [])
    arts = data.get("artifacts") or {}
    build = os.path.dirname(arts.get("html") or "") or "build"

    gates_html = _gates_html(data.get("gates"))
    summary = ('<p class="note good">✓ 全部校验通过 —— 六步流程 N2–N6 结点全绿，可交付。</p>'
               if ok else
               f'<p class="note">✗ 存在 {len(data.get("failures") or [])} 项未通过，'
               '未通过项见「四道门明细」。</p>')
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Snap2Edit 校验报告 · {esc(name)}</title><style>{_CSS}</style></head>
<body><div class="wrap">
<header><h1>Snap2Edit 可视化校验报告 · {esc(name)}
<span class="badge {'ok' if ok else 'bad'}">{'全部通过' if ok else '存在未通过'}</span></h1>
<div class="meta">生成时间 {time.strftime('%Y-%m-%d %H:%M:%S')} ·
画布 {esc(canvas.get('width', '?'))}×{esc(canvas.get('height', '?'))} px ·
元素 {n_el} 个 · spec project: {esc(spec.get('project') or name)}</div></header>
{summary}
<section><h2>结点状态灯 <small>N2–N6（N1 规格书定稿为人工结点）</small></h2>
{_lights_html(status)}</section>
<section>{_pair_section(spec, data, original)}</section>
<section>{_diff_section(spec, data, original, build)}</section>
<section>{_overflow_section(spec)}</section>
<section><h2>四道门明细 <small>与 report.md / check --json 同一数据源</small></h2>
{gates_html}</section>
<footer>产物目录：{esc(build)}／ ·
交付物① {esc(os.path.basename(arts.get('html') or 'output.html'))} ·
交付物② {esc(os.path.basename(arts.get('pptx') or 'output.pptx'))} ·
文本报告 report.md · 本报告 report.html（F7 单文件可视化，可直接分发）<br/>
Snap2Edit —— 一份 spec，双产线全可编辑复刻</footer>
</div></body></html>"""


def write_html(build_dir, data, spec, original=None):
    """渲染并落盘 build/report.html；返回绝对路径。"""
    os.makedirs(build_dir, exist_ok=True)
    out = os.path.join(build_dir, "report.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(render_html(data, spec, original=original))
    return os.path.abspath(out)
