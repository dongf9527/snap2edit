# -*- coding: utf-8 -*-
"""产线②：spec → 原生 PPTX（文本框 + 形状，Picture = 0）。

关键规则（继承自六步标准流程的交付物②）：
  - 坐标：px → EMU（geometry.Mapper，两条公式）；
  - 字号：px → pt；文本框统一 word_wrap=False、四边 margin=0；
  - 中文字体双保险：font.name 之外必须补 a:ea / a:cs 东亚字体；
  - 所有形状关闭继承阴影（shadow.inherit=False）；
  - 箭头用连接线 + tailEnd 三角头，不用贴图。
"""

import math

from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR, MSO_AUTO_SIZE
from pptx.oxml.ns import qn
from pptx.dml.color import RGBColor

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
    except Exception:
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
        else:
            raise ValueError(f"未知元素类型: {t}")

    prs.save(out_path)
    return out_path
