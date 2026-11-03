# -*- coding: utf-8 -*-
"""产线①：spec → HTML+SVG。

约束（继承自六步标准流程的交付物①）：
  - 全部文字为真实 <text>（可选中/复制/修改），禁止 <image> 与 data:image；
  - 每个元素是带 id 的独立最小单元（箭头拆为线段与三角两个单元，
    组件库复合元素拆为面片/格子/部件并携带 {id}{-后缀} 命名）；
  - viewBox 与画布 1:1，坐标系与产线②共享同一份 spec。
"""

import math
from xml.sax.saxutils import escape

from . import components

_ANCHOR = {"left": "start", "center": "middle", "right": "end"}


def _n(v):
    s = f"{float(v):.1f}"
    return s.rstrip("0").rstrip(".") if "." in s else s


def _rot(el):
    """元素旋转角（度、顺时针；盒子绕自身中心，自由文本绕锚点）。"""
    r = el.get("rotate")
    return float(r) % 360.0 if isinstance(r, (int, float)) and not isinstance(r, bool) else 0.0


def _rot_attr(deg, cx, cy):
    return f' transform="rotate({_n(deg)} {_n(cx)} {_n(cy)})"' if deg else ""


def _family(spec):
    font = spec.get("font") or {}
    return f"'{font.get('name', 'Noto Sans SC')}', '{font.get('fallback', 'Microsoft YaHei')}', sans-serif"


def _text_svg(el, spec, tid, cx, cy, centered, rot_c=None):
    pal = spec.get("palette") or {}
    size = float(el["size"])
    lines = el.get("lines") or [str(el.get("text", ""))]
    color = el.get("color") or pal.get("primary", "#1F2937")
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
    rot_attr = _rot_attr(rot_c[0], rot_c[1], rot_c[2]) if rot_c else ""
    return (f'<text id="{tid}" font-size="{_n(size)}" fill="{color}" '
            f'font-weight="{weight}" text-anchor="{anchor}"{rot_attr}>{tspans}</text>')


def _box_svg(el, spec):
    pal = spec.get("palette") or {}
    x, y, w, h = el["x"], el["y"], el["w"], el["h"]
    rot = _rot(el)
    rot_attr = _rot_attr(rot, x + w / 2.0, y + h / 2.0)
    raw_fill = el.get("fill")
    if raw_fill is None:
        # 键存在且为 None（VLM 的 none/transparent）→ 透明；键缺失 → 默认卡片色
        fill = "none" if "fill" in el else pal.get("card", "#FFFFFF")
    else:
        fill = raw_fill
    stroke = el.get("stroke")
    s_attr = (f' stroke="{stroke}" stroke-width="{el.get("stroke_width", 1)}"'
              if stroke else "")
    if el["type"] == "circle":
        out = (f'<ellipse id="{el["id"]}" cx="{_n(x + w / 2.0)}" cy="{_n(y + h / 2.0)}" '
               f'rx="{_n(w / 2.0)}" ry="{_n(h / 2.0)}" fill="{fill}"{s_attr}{rot_attr}/>')
    else:
        if el["type"] == "rect":
            rx = ""
        else:
            rx_v = h / 2.0 if el["type"] == "pill" else el.get("rx", min(w, h) * 0.1)
            rx = f' rx="{_n(rx_v)}"'
        out = (f'<rect id="{el["id"]}" x="{_n(x)}" y="{_n(y)}" '
               f'width="{_n(w)}" height="{_n(h)}"{rx} fill="{fill}"{s_attr}{rot_attr}/>')
    if el.get("text"):
        out += _text_svg(el, spec, f'{el["id"]}-text',
                         cx=x + w / 2.0, cy=y + h / 2.0, centered=True,
                         rot_c=(rot, x + w / 2.0, y + h / 2.0))
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


def _pts(pts):
    return " ".join(f"{_n(px)},{_n(py)}" for px, py in pts)


def _cube_svg(el, spec):
    """立方体：顶面（提亮）+ 侧面（加深）+ 正面（本色），色块由 components 演算。"""
    x, y, w, h = el["x"], el["y"], el["w"], el["h"]
    faces = components.cube_faces(x, y, w, h, el.get("depth"))
    base = el.get("fill") or (spec.get("palette") or {}).get("accent", "#2B6CB0")
    stroke = el.get("stroke")
    s_attr = (f' stroke="{stroke}" stroke-width="{el.get("stroke_width", 1)}"'
              if stroke else "")
    fx, fy, fw, fh = faces["front"]
    out = (f'<polygon id="{el["id"]}-top" points="{_pts(faces["top"])}" '
           f'fill="{components.shade(base, 0.25)}"{s_attr}/>'
           f'<polygon id="{el["id"]}-side" points="{_pts(faces["side"])}" '
           f'fill="{components.shade(base, -0.22)}"{s_attr}/>'
           f'<rect id="{el["id"]}" x="{_n(fx)}" y="{_n(fy)}" width="{_n(fw)}" '
           f'height="{_n(fh)}" fill="{base}"{s_attr}/>')
    if el.get("text"):
        out += _text_svg(el, spec, f'{el["id"]}-text',
                         cx=fx + fw / 2.0, cy=fy + fh / 2.0, centered=True)
    return out


def _matrix_svg(el, spec):
    """矩阵格子：逐格独立 <rect>（id 后缀 -rRcC），文字逐格居中。"""
    pal = spec.get("palette") or {}
    cells = components.matrix_cells(el["x"], el["y"], el["w"], el["h"],
                                    el["rows"], el["cols"], el.get("gap", 0))
    raw_fill = el.get("fill")
    fill = "none" if (raw_fill is None and "fill" in el) else (raw_fill or pal.get("card", "#FFFFFF"))
    stroke = el.get("stroke")
    s_attr = (f' stroke="{stroke}" stroke-width="{el.get("stroke_width", 1)}"'
              if stroke else "")
    out = []
    for k, (cx, cy, cw, ch) in enumerate(cells):
        r, c = divmod(k, el["cols"])
        cid = f'{el["id"]}-r{r + 1}c{c + 1}'
        rx_v = el.get("rx", min(cw, ch) * 0.12)
        out.append(f'<rect id="{cid}" x="{_n(cx)}" y="{_n(cy)}" width="{_n(cw)}" '
                   f'height="{_n(ch)}" rx="{_n(rx_v)}" fill="{fill}"{s_attr}/>')
    for k, txt in enumerate(el.get("texts") or []):
        cx, cy, cw, ch = cells[k]
        r, c = divmod(k, el["cols"])
        tcolor = el.get("color") or (components.contrast_text(fill) if fill != "none" else None) \
            or pal.get("primary", "#1F2937")
        cell_el = dict(el, text=str(txt), color=tcolor)
        out.append(_text_svg(cell_el, spec, f'{el["id"]}-r{r + 1}c{c + 1}-text',
                             cx=cx + cw / 2.0, cy=cy + ch / 2.0, centered=True))
    return "".join(out)


def _flowbox_svg(el, spec):
    """流程框：圆角主体 +（可选）顶部色带标题 + 正文区，文字全部真实 <text>。"""
    pal = spec.get("palette") or {}
    x, y, w, h = el["x"], el["y"], el["w"], el["h"]
    raw_fill = el.get("fill")
    base = "none" if (raw_fill is None and "fill" in el) else (raw_fill or pal.get("card", "#FFFFFF"))
    stroke = el.get("stroke")
    s_attr = (f' stroke="{stroke}" stroke-width="{el.get("stroke_width", 1)}"'
              if stroke else "")
    rx_v = el.get("rx", min(w, h) * 0.1)
    out = (f'<rect id="{el["id"]}" x="{_n(x)}" y="{_n(y)}" width="{_n(w)}" '
           f'height="{_n(h)}" rx="{_n(rx_v)}" fill="{base}"{s_attr}/>')
    bh = h * float(el.get("band", 0.30)) if el.get("title") else 0.0
    if bh:
        band_fill = el.get("band_fill") or components.shade(base if base != "none" else "#94A3B8", -0.18)
        r = min(rx_v, bh)
        band = (f'M {_n(x + r)} {_n(y)} L {_n(x + w - r)} {_n(y)} '
                f'Q {_n(x + w)} {_n(y)} {_n(x + w)} {_n(y + r)} '
                f'L {_n(x + w)} {_n(y + bh)} L {_n(x)} {_n(y + bh)} '
                f'L {_n(x)} {_n(y + r)} Q {_n(x)} {_n(y)} {_n(x + r)} {_n(y)} Z')
        out += f'<path id="{el["id"]}-band" d="{band}" fill="{band_fill}"/>'
        tcolor = el.get("title_color") or components.contrast_text(band_fill)
        title_el = {"size": el.get("title_size", el["size"]), "text": str(el["title"]),
                    "color": tcolor, "bold": True}
        out += _text_svg(title_el, spec, f'{el["id"]}-title',
                         cx=x + w / 2.0, cy=y + bh / 2.0, centered=True)
    if el.get("text") or el.get("lines"):
        cy = y + bh + (h - bh) / 2.0
        out += _text_svg(el, spec, f'{el["id"]}-text',
                         cx=x + w / 2.0, cy=cy, centered=True)
    return out


def _icon_svg(el, spec):
    """参数化图标：fill/ring/stroke 三种部件 → polygon/polyline，单色可编辑。"""
    pal = spec.get("palette") or {}
    color = el.get("fill") or pal.get("accent", "#2B6CB0")
    scale = min(el["w"], el["h"]) / 100.0
    sw = el.get("stroke_width") or max(1.0, 4.0 * scale)
    out = []
    for i, (kind, pts) in enumerate(components.icon_parts(el["name"], el["x"], el["y"], el["w"], el["h"])):
        pid = f'{el["id"]}-{i}'
        p = _pts(pts)
        if kind == "fill":
            out.append(f'<polygon id="{pid}" points="{p}" fill="{color}"/>')
        elif kind == "ring":
            out.append(f'<polygon id="{pid}" points="{p}" fill="none" '
                       f'stroke="{color}" stroke-width="{_n(sw)}"/>')
        else:  # stroke 开放折线
            out.append(f'<polyline id="{pid}" points="{p}" fill="none" '
                       f'stroke="{color}" stroke-width="{_n(sw)}" '
                       f'stroke-linecap="round" stroke-linejoin="round"/>')
    return "".join(out)


def render_element(el, spec):
    t = el["type"]
    if t in ("rect", "rrect", "pill", "circle"):
        return _box_svg(el, spec)
    if t == "text":
        rot = _rot(el)
        return _text_svg(el, spec, el["id"], cx=el["x"], cy=el["y"], centered=False,
                         rot_c=(rot, el["x"], el["y"]) if rot else None)
    if t == "line":
        pal = spec.get("palette") or {}
        return (f'<line id="{el["id"]}" x1="{_n(el["x1"])}" y1="{_n(el["y1"])}" '
                f'x2="{_n(el["x2"])}" y2="{_n(el["y2"])}" '
                f'stroke="{el.get("stroke", pal.get("muted", "#94A3B8"))}" '
                f'stroke-width="{el.get("stroke_width", 1)}"/>')
    if t == "arrow":
        return _arrow_svg(el, spec)
    if t == "cube":
        return _cube_svg(el, spec)
    if t == "matrix-cell":
        return _matrix_svg(el, spec)
    if t == "flow-box":
        return _flowbox_svg(el, spec)
    if t == "icon":
        return _icon_svg(el, spec)
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
