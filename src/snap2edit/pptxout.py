# -*- coding: utf-8 -*-
"""产线②：spec → 原生 PPTX（文本框 + 形状，Picture = 0）。

关键规则（继承自六步标准流程的交付物②）：
  - 坐标：px → EMU（geometry.Mapper，两条公式）；
  - 字号：px → pt；文本框统一 word_wrap=False、四边 margin=0；
  - 中文字体双保险：font.name 之外必须补 a:ea / a:cs 东亚字体；
  - 所有形状关闭继承阴影（shadow.inherit=False）；
  - 箭头用连接线 + tailEnd 三角头，不用贴图；
  - 组件库（F6）：cube 面片与 icon 部件用原生 Freeform 任意多边形，
    matrix-cell 逐格圆角矩形，flow-box 主体+ROUND_2_SAME 色带，均无 Picture。
"""

import math

from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR, MSO_AUTO_SIZE
from pptx.oxml.ns import qn
from pptx.dml.color import RGBColor

from .components import contrast_text, cube_faces, icon_parts, matrix_cells, shade
from .geometry import Mapper, resolve_slide_emu

_ALIGN = {"left": PP_ALIGN.LEFT, "center": PP_ALIGN.CENTER, "right": PP_ALIGN.RIGHT}


def _C(h):
    return RGBColor.from_string(str(h).lstrip("#").upper())


def _noshadow(sp):
    try:
        sp.shadow.inherit = False
    except Exception:
        pass


def _cjk_font(run, name, size_pt, color, bold):
    f = run.font
    f.name = name
    f.size = Pt(size_pt)
    f.bold = bool(bold)
    f.color.rgb = color
    rPr = run._r.get_or_add_rPr()
    for tag in ("a:ea", "a:cs"):
        e = rPr.find(qn(tag))
        if e is None:
            e = rPr.makeelement(qn(tag), {})
            rPr.append(e)
        e.set("typeface", name)


def _fill(sp, color):
    if color:
        sp.fill.solid()
        sp.fill.fore_color.rgb = _C(color)
    else:
        sp.fill.background()


def _outline(sp, color, width_px, m):
    if color:
        sp.line.color.rgb = _C(color)
        sp.line.width = Emu(m.emu(width_px))
    else:
        sp.line.fill.background()


def _rot(el):
    """元素旋转角（度、顺时针；与 svgout._rot 同语义）。"""
    r = el.get("rotate")
    return float(r) % 360.0 if isinstance(r, (int, float)) and not isinstance(r, bool) else 0.0


def _rot_pt(px, py, cx, cy, deg):
    """点 (px,py) 绕 (cx,cy) 顺时针旋转 deg 度。"""
    a = math.radians(deg)
    dx, dy = px - cx, py - cy
    return (cx + dx * math.cos(a) - dy * math.sin(a),
            cy + dx * math.sin(a) + dy * math.cos(a))


def _add_text(shapes, el, m, fname, pal, box=None, valign="top", rot=0.0, pivot=None):
    lines = el.get("lines") or [str(el.get("text", ""))]
    size = float(el["size"])
    lh = float(el.get("line_height", 1.45)) * size
    centered_box = box is not None
    if box is not None:
        bx, by, bw, bh = (float(v) for v in box)
    else:
        x, y = float(el["x"]), float(el["y"])
        bw = float(el.get("w") or 0) or 2000.0
        bh = (len(lines) - 1) * lh + size * 1.3
        if el.get("align") == "center":
            bx = x - bw / 2.0
        elif el.get("align") == "right":
            bx = x - bw
        else:
            bx = x
        by = y
    if rot and not centered_box and pivot is not None:
        # 自由文本旋转中心 = 锚点（与 SVG 同语义）：把文本框平移到
        # 「原中心绕锚点旋转后的位置」，再叠加 rotation 属性，结果与 SVG 精确一致
        ncx, ncy = _rot_pt(bx + bw / 2.0, by + bh / 2.0, pivot[0], pivot[1], rot)
        bx, by = ncx - bw / 2.0, ncy - bh / 2.0
    tb = shapes.add_textbox(Emu(m.emu(bx)), Emu(m.emu(by)), Emu(m.emu(bw)), Emu(m.emu(bh)))
    tb.name = el["id"] if box is None else f'{el["id"]}-text'
    if rot:
        tb.rotation = rot
    tf = tb.text_frame
    tf.word_wrap = False
    try:
        tf.auto_size = MSO_AUTO_SIZE.NONE
    except Exception:  # pragma: no cover —— 防御：个别查看器/版本对 auto_size 属性缺失的容错
        pass
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE if valign == "middle" else MSO_ANCHOR.TOP
    color = el.get("color", pal.get("primary", "#1F2937"))
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = _ALIGN[el.get("align", "left")]
        p.line_spacing = Pt(m.pt(lh))
        r = p.add_run()
        r.text = str(ln)
        _cjk_font(r, fname, m.pt(size), _C(color), el.get("bold", False))
    return tb


def _add_line(shapes, el, m, pal, arrow):
    color = el.get("stroke") or (pal.get("accent", "#2B6CB0") if arrow
                                 else pal.get("muted", "#94A3B8"))
    conn = shapes.add_connector(
        MSO_CONNECTOR.STRAIGHT,
        Emu(m.emu(el["x1"])), Emu(m.emu(el["y1"])),
        Emu(m.emu(el["x2"])), Emu(m.emu(el["y2"])))
    conn.name = el["id"]
    conn.line.color.rgb = _C(color)
    conn.line.width = Emu(m.emu(el.get("stroke_width", 2)))
    _noshadow(conn)
    if arrow:
        ln = conn._element.spPr.get_or_add_ln()
        tail = ln.makeelement(qn("a:tailEnd"),
                              {"type": "triangle", "w": "med", "len": "med"})
        ln.append(tail)


# ---------------- 组件库（F6）----------------

def _freeform(shapes, el, m, suffix, pts, close=True):
    """多边形 → 原生 Freeform（本地 px 坐标 + scale=EMU/px，位置自动落位）。"""
    fb = shapes.build_freeform(float(pts[0][0]), float(pts[0][1]), scale=m.emu_px)
    fb.add_line_segments([(float(px), float(py)) for px, py in pts[1:]], close=close)
    sp = fb.convert_to_shape()
    sp.name = f'{el["id"]}{suffix}'
    _noshadow(sp)
    return sp


def _add_cube(shapes, el, m, fname, pal):
    """立方体：顶面提亮 / 侧面加深 / 正面本色，三块独立面片 + 正面文字。"""
    faces = cube_faces(el["x"], el["y"], el["w"], el["h"], el.get("depth"))
    base = el.get("fill") or pal.get("accent", "#2B6CB0")
    stroke, sw = el.get("stroke"), el.get("stroke_width", 1)
    top = _freeform(shapes, el, m, "-top", faces["top"])
    _fill(top, shade(base, 0.25))
    _outline(top, stroke, sw, m)
    side = _freeform(shapes, el, m, "-side", faces["side"])
    _fill(side, shade(base, -0.22))
    _outline(side, stroke, sw, m)
    fx, fy, fw, fh = faces["front"]
    sp = shapes.add_shape(MSO_SHAPE.RECTANGLE, Emu(m.emu(fx)), Emu(m.emu(fy)),
                          Emu(m.emu(fw)), Emu(m.emu(fh)))
    sp.name = el["id"]
    _fill(sp, base)
    _outline(sp, stroke, sw, m)
    _noshadow(sp)
    if el.get("text"):
        el.setdefault("align", "center")
        _add_text(shapes, el, m, fname, pal, box=faces["front"], valign="middle")


def _add_matrix(shapes, el, m, fname, pal):
    """矩阵格子：逐格独立圆角矩形 + 逐格文字框（id 后缀 -rRcC）。"""
    cells = matrix_cells(el["x"], el["y"], el["w"], el["h"],
                         el["rows"], el["cols"], el.get("gap", 0))
    raw_fill = el.get("fill")
    fill = None if (raw_fill is None and "fill" in el) else (raw_fill or pal.get("card") or "#FFFFFF")
    stroke, sw = el.get("stroke"), el.get("stroke_width", 1)
    tcolor = el.get("color") or (contrast_text(fill) if fill else pal.get("primary", "#1F2937"))
    for k, (cx, cy, cw, ch) in enumerate(cells):
        r, c = divmod(k, el["cols"])
        sp = shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Emu(m.emu(cx)), Emu(m.emu(cy)),
                              Emu(m.emu(cw)), Emu(m.emu(ch)))
        sp.name = f'{el["id"]}-r{r + 1}c{c + 1}'
        try:
            rx_v = el.get("rx", min(cw, ch) * 0.12)
            sp.adjustments[0] = max(0.0, min(0.5, float(rx_v) / min(cw, ch)))
        except Exception:
            pass
        _fill(sp, fill)
        _outline(sp, stroke, sw, m)
        _noshadow(sp)
    for k, txt in enumerate(el.get("texts") or []):
        cx, cy, cw, ch = cells[k]
        r, c = divmod(k, el["cols"])
        # 文本框 id 与 svgout 同名：{id}-rRcC-text，两产线单元一一对应
        cell_el = dict(el, id=f'{el["id"]}-r{r + 1}c{c + 1}', text=str(txt),
                       color=tcolor, align="center")
        _add_text(shapes, cell_el, m, fname, pal, box=(cx, cy, cw, ch), valign="middle")


def _add_flowbox(shapes, el, m, fname, pal):
    """流程框：圆角主体 +（可选）ROUND_2_SAME 色带标题 + 正文区。"""
    x, y, w, h = el["x"], el["y"], el["w"], el["h"]
    raw_fill = el.get("fill")
    base = None if (raw_fill is None and "fill" in el) else (raw_fill or pal.get("card") or "#FFFFFF")
    stroke, sw = el.get("stroke"), el.get("stroke_width", 1)
    rx_v = el.get("rx", min(w, h) * 0.1)
    body = shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Emu(m.emu(x)), Emu(m.emu(y)),
                            Emu(m.emu(w)), Emu(m.emu(h)))
    body.name = el["id"]
    try:
        body.adjustments[0] = max(0.0, min(0.5, float(rx_v) / min(w, h)))
    except Exception:
        pass
    _fill(body, base)
    _outline(body, stroke, sw, m)
    _noshadow(body)
    bh = h * float(el.get("band", 0.30)) if el.get("title") else 0.0
    if bh:
        band_fill = el.get("band_fill") or shade(base if base else "#94A3B8", -0.18)
        band = shapes.add_shape(MSO_SHAPE.ROUND_2_SAME_RECTANGLE, Emu(m.emu(x)), Emu(m.emu(y)),
                                Emu(m.emu(w)), Emu(m.emu(bh)))
        band.name = f'{el["id"]}-band'
        try:
            band.adjustments[0] = max(0.0, min(0.5, min(float(rx_v), bh) / min(w, bh)))
        except Exception:
            pass
        _fill(band, band_fill)
        band.line.fill.background()
        _noshadow(band)
        tcolor = el.get("title_color") or contrast_text(band_fill)
        title_el = {"id": el["id"], "text": str(el["title"]), "align": "center",
                    "size": el.get("title_size", el["size"]), "color": tcolor, "bold": True}
        tb = _add_text(shapes, title_el, m, fname, pal, box=(x, y, w, bh), valign="middle")
        tb.name = f'{el["id"]}-title'
    if el.get("text") or el.get("lines"):
        el.setdefault("align", "center")
        _add_text(shapes, el, m, fname, pal, box=(x, y + bh, w, h - bh), valign="middle")


def _add_icon(shapes, el, m, pal):
    """参数化图标：fill 实心 / ring 空心描边 / stroke 开放折线 → 原生 Freeform。"""
    color = el.get("fill") or pal.get("accent", "#2B6CB0")
    scale = min(el["w"], el["h"]) / 100.0
    sw = el.get("stroke_width") or max(1.0, 4.0 * scale)
    for i, (kind, pts) in enumerate(icon_parts(el["name"], el["x"], el["y"], el["w"], el["h"])):
        if kind == "fill":
            sp = _freeform(shapes, el, m, f"-{i}", pts)
            _fill(sp, color)
            sp.line.fill.background()
        elif kind == "ring":
            sp = _freeform(shapes, el, m, f"-{i}", pts)
            sp.fill.background()
            sp.line.color.rgb = _C(color)
            sp.line.width = Emu(m.emu(sw))
        else:  # stroke 开放折线
            sp = _freeform(shapes, el, m, f"-{i}", pts, close=False)
            sp.fill.background()
            sp.line.color.rgb = _C(color)
            sp.line.width = Emu(m.emu(sw))


def render_pptx(spec, out_path):
    cw, ch = spec["canvas"]["width"], spec["canvas"]["height"]
    slide_emu = resolve_slide_emu(spec)
    m = Mapper(cw, ch, slide_emu)
    font = spec.get("font") or {}
    # PPTX 面向 PowerPoint/WPS 环境，默认用雅黑；浏览器侧仍用 Noto
    fname = font.get("pptx_name", "Microsoft YaHei")
    pal = spec.get("palette") or {}

    prs = Presentation()
    prs.slide_width = Emu(slide_emu[0])
    prs.slide_height = Emu(slide_emu[1])
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    shapes = slide.shapes

    for el in spec["elements"]:
        t = el["type"]
        if t in ("rect", "rrect", "pill", "circle"):
            shp = (MSO_SHAPE.RECTANGLE if t == "rect"
                   else MSO_SHAPE.OVAL if t == "circle"
                   else MSO_SHAPE.ROUNDED_RECTANGLE)
            sp = shapes.add_shape(shp, Emu(m.emu(el["x"])), Emu(m.emu(el["y"])),
                                  Emu(m.emu(el["w"])), Emu(m.emu(el["h"])))
            sp.name = el["id"]
            rot = _rot(el)
            if rot:
                sp.rotation = rot
            if t == "pill":
                sp.adjustments[0] = 0.5
            elif t == "rrect" and el.get("rx") is not None:
                try:
                    sp.adjustments[0] = max(0.0, min(0.5, float(el["rx"]) / min(el["w"], el["h"])))
                except Exception:
                    pass
            # fill 语义与 svgout 对齐：键存在且为 None（VLM 的 none/transparent）→ 透明；
            # 键缺失 → 回退 palette.card / 白色
            raw_fill = el.get("fill")
            if raw_fill is None and "fill" not in el:
                raw_fill = pal.get("card") or "#FFFFFF"
            _fill(sp, raw_fill)
            _outline(sp, el.get("stroke"), el.get("stroke_width", 1), m)
            _noshadow(sp)
            if el.get("text"):
                el.setdefault("align", "center")
                _add_text(shapes, el, m, fname, pal,
                          box=(el["x"], el["y"], el["w"], el["h"]), valign="middle",
                          rot=rot)
        elif t == "text":
            _add_text(shapes, el, m, fname, pal, rot=_rot(el), pivot=(el["x"], el["y"]))
        elif t in ("line", "arrow"):
            _add_line(shapes, el, m, pal, arrow=(t == "arrow"))
        elif t == "cube":
            _add_cube(shapes, el, m, fname, pal)
        elif t == "matrix-cell":
            _add_matrix(shapes, el, m, fname, pal)
        elif t == "flow-box":
            _add_flowbox(shapes, el, m, fname, pal)
        elif t == "icon":
            _add_icon(shapes, el, m, pal)
        else:
            raise ValueError(f"未知元素类型: {t}")

    prs.save(out_path)
    return out_path
