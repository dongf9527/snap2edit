#!/usr/bin/env python3
"""PPTX 助手库 —— 坐标换算 / 中文字体双保险 / PIL 量宽 / 统一关阴影
画布 1728x972 px → 16:9 幻灯片 12192000x6858000 EMU
"""
from PIL import ImageFont
from pptx.util import Emu, Pt

EMU_W, EMU_H = 12192000, 6858000
CANVAS_W, CANVAS_H = 1728, 972
EMU_PX = EMU_W / CANVAS_W          # 7055.56
PT_PX = (EMU_H / 12700) / CANVAS_H  # 540pt / 972px = 0.5556

FONT = 'Noto Sans SC'
_FONT_CACHE = {}

def E(px):
    """px → EMU"""
    return Emu(int(round(px * EMU_PX)))

def PT(px):
    """px 字号 → pt"""
    return Pt(px * PT_PX)

def rgb(hexstr):
    from pptx.dml.color import RGBColor
    hexstr = hexstr.lstrip('#')
    return RGBColor(int(hexstr[0:2], 16), int(hexstr[2:4], 16), int(hexstr[4:6], 16))

def text_width(text, size_px, weight=400):
    """PIL 实测文本宽度(px)，与 PowerPoint 度量基本一致"""
    key = weight
    if key not in _FONT_CACHE:
        path = '/usr/share/fonts/truetype/chinese/NotoSansSC-Bold.ttf' if weight >= 600 \
            else '/usr/share/fonts/truetype/chinese/NotoSansSC-Regular.ttf'
        _FONT_CACHE[key] = ImageFont.truetype(path, 1000)
    f = _FONT_CACHE[key]
    return f.getlength(text) / 1000 * size_px

def set_text(tf, text, size_px, weight, color, align='l', spacing=1.0, spacing_pt=None,
             spc_px=None):
    """写入文本框：统一 word_wrap=False、margin=0、关自动收缩；spc_px 为字距（px）"""
    from pptx.enum.text import PP_ALIGN
    tf.word_wrap = False
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    try:
        from pptx.enum.text import MSO_AUTO_SIZE
        tf.auto_size = MSO_AUTO_SIZE.NONE
    except Exception:
        pass
    p = tf.paragraphs[0]
    p.alignment = {'l': PP_ALIGN.LEFT, 'c': PP_ALIGN.CENTER, 'r': PP_ALIGN.RIGHT}[align]
    if spacing_pt:
        p.line_spacing = spacing_pt
    elif spacing:
        p.line_spacing = spacing
    run = p.add_run()
    run.text = text
    f = run.font
    f.name = FONT
    f.size = PT(size_px)
    f.bold = weight >= 600
    f.color.rgb = rgb(color)
    # 中文字体双保险：a:ea + a:cs
    rPr = run._r.get_or_add_rPr()
    from pptx.oxml.ns import qn
    ea = rPr.find(qn('a:ea'))
    if ea is None:
        ea = rPr.makeelement(qn('a:ea'), {})
        rPr.append(ea)
    ea.set('typeface', FONT)
    cs = rPr.find(qn('a:cs'))
    if cs is None:
        cs = rPr.makeelement(qn('a:cs'), {})
        rPr.append(cs)
    cs.set('typeface', FONT)
    if spc_px:
        rPr.set('spc', str(int(round(spc_px * PT_PX * 100))))
    return run

def no_shadow(shape):
    """所有形状统一关阴影：inherit=False + 剥离 p:style 主题引用
    （LibreOffice 会按 style 的 effectRef 给形状加默认阴影，必须连 style 一起剥掉）"""
    try:
        shape.shadow.inherit = False
    except Exception:
        pass
    try:
        from pptx.oxml.ns import qn
        el = shape._element
        st = el.find(qn('p:style'))
        if st is not None:
            el.remove(st)
    except Exception:
        pass

def add_rect(shapes, x, y, w, h, fill=None, line=None, line_w=None, radius=None, shape_type=None):
    """通用矩形/圆角矩形/椭圆；radius 为 px"""
    from pptx.enum.shapes import MSO_SHAPE
    if shape_type is not None:
        sp = shapes.add_shape(shape_type, E(x), E(y), E(w), E(h))
    elif radius:
        sp = shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, E(x), E(y), E(w), E(h))
        try:
            # adjustment = 半径 / min(w,h)
            sp.adjustments[0] = min(0.5, radius / min(w, h))
        except Exception:
            pass
    else:
        sp = shapes.add_shape(MSO_SHAPE.RECTANGLE, E(x), E(y), E(w), E(h))
    if fill:
        sp.fill.solid()
        sp.fill.fore_color.rgb = rgb(fill)
    else:
        sp.fill.background()
    if line:
        sp.line.color.rgb = rgb(line)
        sp.line.width = Emu(int(round((line_w or 1) * EMU_PX)))
    else:
        sp.line.fill.background()
    no_shadow(sp)
    return sp

def add_text(shapes, x, y, w, h, text, size_px, weight=400, color='#253E56',
             align='l', anchor='t', spacing=1.0, spc_px=None):
    """文本框：给 box 后留足宽度（量宽校验在调用侧）"""
    from pptx.enum.text import MSO_ANCHOR
    tb = shapes.add_textbox(E(x), E(y), E(w), E(h))
    tf = tb.text_frame
    set_text(tf, text, size_px, weight, color, align=align, spacing=spacing, spc_px=spc_px)
    try:
        tf.vertical_anchor = {'t': MSO_ANCHOR.TOP, 'm': MSO_ANCHOR.MIDDLE, 'b': MSO_ANCHOR.BOTTOM}[anchor]
    except Exception:
        pass
    no_shadow(tb)
    return tb

def add_line(shapes, x1, y1, x2, y2, color, w_pt=None, w_px=1):
    from pptx.enum.shapes import MSO_CONNECTOR
    ln = shapes.add_connector(MSO_CONNECTOR.STRAIGHT, E(x1), E(y1), E(x2), E(y2))
    ln.line.color.rgb = rgb(color)
    ln.line.width = Pt(w_pt if w_pt else max(0.75, w_px * PT_PX))
    no_shadow(ln)
    return ln

def add_oval(shapes, cx, cy, r, fill=None, line=None, line_w=None):
    from pptx.enum.shapes import MSO_SHAPE
    return add_rect(shapes, cx - r, cy - r, 2 * r, 2 * r, fill=fill, line=line,
                    line_w=line_w, shape_type=MSO_SHAPE.OVAL)

def freeform(shapes, points_px, fill=None, line=None, line_w=None, close=True):
    """多边形（px 点列）：局部坐标 + origin 正确放置"""
    xs = [p[0] for p in points_px]
    ys = [p[1] for p in points_px]
    x0, y0 = min(xs), min(ys)
    local = [(Emu(int(round((px - x0) * EMU_PX))), Emu(int(round((py - y0) * EMU_PX))))
             for px, py in points_px]
    builder = shapes.build_freeform(local[0][0], local[0][1], scale=1.0)
    builder.add_line_segments(local[1:], close=close)
    sp = builder.convert_to_shape(origin_x=E(x0), origin_y=E(y0))
    if fill:
        sp.fill.solid()
        sp.fill.fore_color.rgb = rgb(fill)
    else:
        sp.fill.background()
    if line:
        sp.line.color.rgb = rgb(line)
        sp.line.width = Emu(int(round((line_w or 1) * EMU_PX)))
    else:
        sp.line.fill.background()
    no_shadow(sp)
    return sp


def add_ellipse(shapes, cx, cy, rx, ry, fill=None, line=None, line_w=None):
    from pptx.enum.shapes import MSO_SHAPE
    sp = shapes.add_shape(MSO_SHAPE.OVAL, E(cx - rx), E(cy - ry), E(2 * rx), E(2 * ry))
    if fill:
        sp.fill.solid()
        sp.fill.fore_color.rgb = rgb(fill)
    else:
        sp.fill.background()
    if line:
        sp.line.color.rgb = rgb(line)
        sp.line.width = Emu(int(round((line_w or 1) * EMU_PX)))
    else:
        sp.line.fill.background()
    no_shadow(sp)
    return sp
