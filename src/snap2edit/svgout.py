# -*- coding: utf-8 -*-
"""产线①：spec → HTML+SVG。

约束（继承自六步标准流程的交付物①）：
  - 全部文字为真实 <text>（可选中/复制/修改），禁止 <image> 与 data:image；
  - 每个元素是带 id 的独立最小单元（箭头拆为线段与三角两个单元）；
  - viewBox 与画布 1:1，坐标系与产线②共享同一份 spec。
"""

import math
from xml.sax.saxutils import escape

_ANCHOR = {"left": "start", "center": "middle", "right": "end"}


def _n(v):
    s = f"{float(v):.1f}"
    return s.rstrip("0").rstrip(".") if "." in s else s


def _family(spec):
    font = spec.get("font") or {}
    return f"'{font.get('name', 'Noto Sans SC')}', '{font.get('fallback', 'Microsoft YaHei')}', sans-serif"


def _text_svg(el, spec, tid, cx, cy, centered):
    pal = spec.get("palette") or {}
    size = float(el["size"])
    lines = el.get("lines") or [str(el.get("text", ""))]
    color = el.get("color", pal.get("primary", "#1F2937"))
    weight = "bold" if el.get("bold") else "normal"
    lh = float(el.get("line_height", 1.45)) * size
    if centered:
        anchor = "middle"
        first = cy - (len(lines) - 1) * lh / 2.0 + size * 0.34
    else:
        anchor = _ANCHOR[el.get("align", "left")]
        first = cy + size * 0.82
    tspans = "".join(
        f'<tspan x="{_n(cx)}" y="{_n(first + k * lh)}">{escape(str(ln))}</tspan>'
        for k, ln in enumerate(lines))
    return (f'<text id="{tid}" font-size="{_n(size)}" fill="{color}" '
            f'font-weight="{weight}" text-anchor="{anchor}">{tspans}</text>')


def _box_svg(el, spec):
    pal = spec.get("palette") or {}
    x, y, w, h = el["x"], el["y"], el["w"], el["h"]
    fill = el.get("fill", pal.get("card", "#FFFFFF"))
    stroke = el.get("stroke")
    s_attr = (f' stroke="{stroke}" stroke-width="{el.get("stroke_width", 1)}"'
              if stroke else "")
    if el["type"] == "rect":
        rx = ""
    else:
        rx_v = h / 2.0 if el["type"] == "pill" else el.get("rx", min(w, h) * 0.1)
        rx = f' rx="{_n(rx_v)}"'
    out = (f'<rect id="{el["id"]}" x="{_n(x)}" y="{_n(y)}" '
           f'width="{_n(w)}" height="{_n(h)}"{rx} fill="{fill}"{s_attr}/>')
    if el.get("text"):
        out += _text_svg(el, spec, f'{el["id"]}-text',
                         cx=x + w / 2.0, cy=y + h / 2.0, centered=True)
    return out


def _arrow_svg(el, spec):
    """箭头 = 线段 + 三角箭头头部，两个独立可编辑单元。"""
    pal = spec.get("palette") or {}
    x1, y1, x2, y2 = el["x1"], el["y1"], el["x2"], el["y2"]
    color = el.get("stroke", pal.get("accent", "#2B6CB0"))
    sw = el.get("stroke_width", 2)
    hs = float(el.get("head", 9))
    ang = math.atan2(y2 - y1, x2 - x1)
    bx, by = x2 - hs * math.cos(ang), y2 - hs * math.sin(ang)
    lx, ly = -hs * math.sin(ang), hs * math.cos(ang)
    tri = (f"{_n(x2)},{_n(y2)} {_n(bx + lx)},{_n(by + ly)} {_n(bx - lx)},{_n(by - ly)}")
    ex, ey = x2 - hs * 0.6 * math.cos(ang), y2 - hs * 0.6 * math.sin(ang)
    line = (f'<line id="{el["id"]}" x1="{_n(x1)}" y1="{_n(y1)}" x2="{_n(ex)}" '
            f'y2="{_n(ey)}" stroke="{color}" stroke-width="{sw}" stroke-linecap="round"/>')
    head = f'<polygon id="{el["id"]}-head" points="{tri}" fill="{color}"/>'
    return line + head


def render_element(el, spec):
    t = el["type"]
    if t in ("rect", "rrect", "pill"):
        return _box_svg(el, spec)
    if t == "text":
        return _text_svg(el, spec, el["id"], cx=el["x"], cy=el["y"], centered=False)
    if t == "line":
        pal = spec.get("palette") or {}
        return (f'<line id="{el["id"]}" x1="{_n(el["x1"])}" y1="{_n(el["y1"])}" '
                f'x2="{_n(el["x2"])}" y2="{_n(el["y2"])}" '
                f'stroke="{el.get("stroke", pal.get("muted", "#94A3B8"))}" '
                f'stroke-width="{el.get("stroke_width", 1)}"/>')
    if t == "arrow":
        return _arrow_svg(el, spec)
    raise ValueError(f"未知元素类型: {t}")


def render_html(spec):
    cw, ch = spec["canvas"]["width"], spec["canvas"]["height"]
    title = escape(str(spec.get("project", "Snap2Edit")))
    body = "\n".join(render_element(el, spec) for el in spec["elements"])
    return f'''<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8"/>
<title>{title}</title>
<style>
  body {{ margin: 0; background: #E9EDF3; display: flex; justify-content: center; padding: 24px; }}
  #stage {{ background: #fff; box-shadow: 0 8px 30px rgba(15, 23, 42, .18); }}
  text {{ font-family: {_family(spec)}; }}
</style>
</head>
<body>
<div id="stage">
<svg id="canvas" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {cw} {ch}" width="{cw}" height="{ch}">
{body}
</svg>
</div>
</body>
</html>
'''
