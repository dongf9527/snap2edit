# -*- coding: utf-8 -*-
"""PPTX 生成辅助库：坐标换算、文本框、形状、渐变、原生图标组件。
坐标体系：px（1200x1600）→ EMU（1px = 0.01in = 9144 EMU）
字号：pt = px * 0.72
"""
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.oxml.ns import qn

EMU_PX = 9144  # 1px = 0.01 inch
FONT = 'Noto Sans SC'


_FONT_M = None

def _font_m():
    global _FONT_M
    if _FONT_M is None:
        from PIL import ImageFont
        _FONT_M = ImageFont.truetype(
            '/usr/share/fonts/truetype/chinese/NotoSansSC-Bold.ttf', 1000)
    return _FONT_M


def text_width(t, size):
    """字体真实渲染宽度(px)，与 PowerPoint 度量一致"""
    try:
        return _font_m().getlength(t) / 1000.0 * size
    except Exception:
        wv = 0.0
        for ch in t:
            wv += 1.0 if ord(ch) > 0x2E7F else (0.26 if ch == ' ' else 0.58)
        return wv * size


def E(px):
    return Emu(int(round(px * EMU_PX)))


def PT(px):
    return Pt(px * 0.72)


def rgb(hexstr):
    return RGBColor.from_string(hexstr.lstrip('#').upper())


def mix(c1, c2, t):
    """c1 向 c2 混合 t（0~1），hex 字符串"""
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    m = [round(x * (1 - t) + y * t) for x, y in zip(a, b)]
    return '#%02X%02X%02X' % tuple(m)


def _style_text(tf, lines, size, color, bold, align, lh, weight):
    """填充文本框：lines 为 [(text,)] 多行"""
    tf.word_wrap = False
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        if lh:
            p.line_spacing = PT(lh)
        p.space_before = Pt(0)
        p.space_after = Pt(0)
        r = p.add_run()
        r.text = ln
        f = r.font
        f.size = PT(size)
        f.bold = bold
        f.color.rgb = rgb(color)
        f.name = FONT
        rPr = r._r.get_or_add_rPr()
        for tag in ('a:ea', 'a:cs'):
            e = rPr.makeelement(qn(tag), {'typeface': FONT})
            rPr.append(e)
        if weight and weight >= 800:
            f.bold = True


def add_text(slide, x, y, text, size, color, bold=False, align='start',
             lh=None, weight=400, anchor='top', w=None, h=None):
    """添加文本框。x,y=左上角(px)；y 也可理解为按基线换算后的顶部。
    align: start/center/end"""
    amap = dict(start=PP_ALIGN.LEFT, center=PP_ALIGN.CENTER, end=PP_ALIGN.RIGHT)
    tw = w if w else max(len(text) * size * 1.1 + 40, size * 3)
    th = h if h else size * 1.5 * (1 if not lh else 0.4 + lh * 0.05)
    tb = slide.shapes.add_textbox(E(x), E(y), E(tw), E(th))
    tf = tb.text_frame
    tf.auto_size = None
    tf.vertical_anchor = MSO_ANCHOR.TOP
    _style_text(tf, text.split('\n'), size, color, bold, amap[align], lh, weight)
    return tb


def add_text_baseline(slide, x_base, y_base, text, size, color, bold=False,
                      align='start', lh=None, weight=400):
    """按基线定位：top = baseline - size*1.10（渲染后可校正）"""
    amap = dict(start=PP_ALIGN.LEFT, center=PP_ALIGN.CENTER, end=PP_ALIGN.RIGHT)
    tw = max(text_width(text, size) + 30, size * 3)
    n = text.count('\n') + 1
    th = size * 1.5 + (n - 1) * (lh or size * 1.45)
    top = y_base - size * 1.10
    if align == 'center':
        x0 = x_base - tw / 2
    elif align == 'end':
        x0 = x_base - tw
    else:
        x0 = x_base
    tb = slide.shapes.add_textbox(E(x0), E(top), E(tw), E(th))
    tf = tb.text_frame
    tf.auto_size = None
    tf.vertical_anchor = MSO_ANCHOR.TOP
    _style_text(tf, text.split('\n'), size, color, bold, amap[align], lh, weight)
    return tb


def add_mtext(slide, x, y_base, lines, size, color, bold=False, align='start',
              lh=None, weight=400):
    """多行文本（lines: list[str]），x 为锚点，按 align 解释"""
    if isinstance(lines, str):
        lines = lines.split('\n')
    amap = dict(start=PP_ALIGN.LEFT, center=PP_ALIGN.CENTER, end=PP_ALIGN.RIGHT)
    lh = lh or size * 1.45
    maxw = max(text_width(t, size) for t in lines) + 30
    if align == 'center':
        x0 = x - maxw / 2
    elif align == 'end':
        x0 = x - maxw
    else:
        x0 = x
    th = size * 1.5 + (len(lines) - 1) * lh
    top = y_base - size * 1.10
    tb = slide.shapes.add_textbox(E(x0), E(top), E(maxw), E(th))
    tf = tb.text_frame
    tf.auto_size = None
    tf.vertical_anchor = MSO_ANCHOR.TOP
    _style_text(tf, lines, size, color, bold, amap[align], lh, weight)
    return tb


def add_shape(slide, st, x, y, w, h, fill=None, line=None, lw=2, adj=None, shadow_off=True):
    sp = slide.shapes.add_shape(st, E(x), E(y), E(w), E(h))
    if fill:
        sp.fill.solid()
        sp.fill.fore_color.rgb = rgb(fill)
    else:
        sp.fill.background()
    if line:
        sp.line.color.rgb = rgb(line)
        sp.line.width = PT(lw)
    else:
        sp.line.fill.background()
    if adj is not None:
        try:
            sp.adjustments[0] = adj
        except Exception:
            pass
    if shadow_off:
        sp.shadow.inherit = False
    return sp


def add_grad(slide, st, x, y, w, h, c1, c2, angle=0, adj=None, line=None, lw=1.5):
    sp = slide.shapes.add_shape(st, E(x), E(y), E(w), E(h))
    sp.fill.gradient()
    stops = sp.fill.gradient_stops
    stops[0].color.rgb = rgb(c1)
    stops[0].position = 0.0
    stops[1].color.rgb = rgb(c2)
    stops[1].position = 1.0
    try:
        sp.fill.gradient_angle = angle
    except Exception:
        pass
    if line:
        sp.line.color.rgb = rgb(line)
        sp.line.width = PT(lw)
    else:
        sp.line.fill.background()
    sp.shadow.inherit = False
    if adj is not None:
        try:
            sp.adjustments[0] = adj
        except Exception:
            pass
    return sp


def add_line(slide, x1, y1, x2, y2, color, w=2.4, dash=None):
    ln = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, E(x1), E(y1), E(x2), E(y2))
    ln.line.color.rgb = rgb(color)
    ln.line.width = PT(w)
    ln.shadow.inherit = False
    return ln


def add_freeform(slide, pts, fill=None, line=None, lw=1.6, close=True):
    """pts: [(x,y)px] 多边形（直线段近似曲线）"""
    fb = slide.shapes.build_freeform(pts[0][0], pts[0][1], scale=EMU_PX)
    fb.add_line_segments(pts[1:], close=close)
    sp = fb.convert_to_shape()
    if fill:
        sp.fill.solid()
        sp.fill.fore_color.rgb = rgb(fill)
    else:
        sp.fill.background()
    if line:
        sp.line.color.rgb = rgb(line)
        sp.line.width = PT(lw)
    else:
        sp.line.fill.background()
    sp.shadow.inherit = False
    return sp


def bez(p0, p1, p2, p3, n=24):
    """三次贝塞尔采样"""
    out = []
    for i in range(1, n + 1):
        t = i / n
        mt = 1 - t
        x = mt**3 * p0[0] + 3 * mt**2 * t * p1[0] + 3 * mt * t**2 * p2[0] + t**3 * p3[0]
        y = mt**3 * p0[1] + 3 * mt**2 * t * p1[1] + 3 * mt * t**2 * p2[1] + t**3 * p3[1]
        out.append((x, y))
    return out


def qbez(p0, p1, p2, n=24):
    out = []
    for i in range(1, n + 1):
        t = i / n
        mt = 1 - t
        x = mt**2 * p0[0] + 2 * mt * t * p1[0] + t**2 * p2[0]
        y = mt**2 * p0[1] + 2 * mt * t * p1[1] + t**2 * p2[1]
        out.append((x, y))
    return out


# ============================ 图标（原生形状组合） ============================
# 每个图标一个 group，返回 group；成员形状使用绝对坐标。

def _g(slide):
    return slide.shapes.add_group_shape()


def _ell(g, cx, cy, rx, ry, fill=None, line=None, lw=2):
    return add_shape(g, MSO_SHAPE.OVAL, cx - rx, cy - ry, rx * 2, ry * 2, fill, line, lw)


def _rect(g, x, y, w, h, fill=None, line=None, lw=2, adj=None):
    return add_shape(g, MSO_SHAPE.RECTANGLE, x, y, w, h, fill, line, lw, adj)


def icon_brain(slide, cx, cy, s, color, bg):
    g = _g(slide)
    w = s * .92; h = s
    add_shape(g, MSO_SHAPE.OVAL, cx - w * .52, cy - h * .40, w * .52, h * .80,
              mix(color, bg, .82), color, s * .07)
    add_shape(g, MSO_SHAPE.OVAL, cx + w * .002, cy - h * .40, w * .52, h * .80,
              mix(color, bg, .82), color, s * .07)
    add_line(g, cx, cy - h * .40, cx, cy + h * .40, color, s * .07)
    return g


def icon_chart(slide, cx, cy, s, color):
    g = _g(slide)
    w = s * .9; h = s
    x0 = cx - w / 2; by = cy + h * .34
    hs = [.34, .50, .66, .82]
    bw = w * .16
    for k, v in enumerate(hs):
        add_shape(g, MSO_SHAPE.ROUNDED_RECTANGLE, x0 + w * .04 + k * (bw + w * .075),
                  by - h * v, bw, h * v, color, None, adj=.3)
    add_line(g, x0 + w * .04, by + s * .04, x0 + w * .86, by + s * .04, color, s * .08)
    return g


def icon_network(slide, cx, cy, s, color):
    import math
    g = _g(slide)
    r_out = s * .40
    for k in range(6):
        a = math.radians(90 + k * 60)
        px, py = cx + r_out * math.cos(a), cy - r_out * math.sin(a)
        add_line(g, cx, cy, px, py, color, s * .055)
        _ell(g, px, py, s * .105, s * .105, color)
    _ell(g, cx, cy, s * .11, s * .11, color)
    return g


def icon_sparkle(slide, cx, cy, s, color):
    g = _g(slide)
    add_shape(g, MSO_SHAPE.STAR_4_POINT, cx - s * .36, cy - s * .30, s * .68, s * .68, color)
    add_shape(g, MSO_SHAPE.STAR_4_POINT, cx + s * .19, cy - s * .45, s * .30, s * .30, color)
    add_shape(g, MSO_SHAPE.STAR_4_POINT, cx + s * .16, cy + s * .24, s * .20, s * .20, color)
    return g


def icon_bubble(slide, cx, cy, s, color):
    g = _g(slide)
    w = s; h = s * .72
    add_shape(g, MSO_SHAPE.ROUNDED_RECTANGLE, cx - w / 2, cy - h / 2 - s * .06,
              w, h, mix(color, '#FFFFFF', .85), color, s * .08, adj=.25)
    tri = add_shape(g, MSO_SHAPE.ISOSCELES_TRIANGLE, cx - w * .30, cy + h / 2 - s * .10,
                    s * .18, s * .16, color)
    tri.rotation = 180
    add_line(g, cx - w * .26, cy - s * .12, cx + w * .26, cy - s * .12, color, s * .07)
    add_line(g, cx - w * .26, cy + s * .04, cx + w * .10, cy + s * .04, color, s * .07)
    return g


def icon_database(slide, cx, cy, s, color):
    g = _g(slide)
    add_shape(g, MSO_SHAPE.CAN, cx - s * .40, cy - s * .46, s * .80, s * .92,
              mix(color, '#FFFFFF', .82), color, s * .07)
    return g


def icon_robot(slide, cx, cy, s, color):
    g = _g(slide)
    w = s * .92; h = s * .70
    x0 = cx - w / 2; y0 = cy - h / 2 + s * .04
    add_line(g, cx, y0 - s * .14, cx, y0, color, s * .06)
    _ell(g, cx, y0 - s * .16, s * .055, s * .055, color)
    add_shape(g, MSO_SHAPE.ROUNDED_RECTANGLE, x0, y0, w, h,
              mix(color, '#FFFFFF', .85), color, s * .07, adj=.22)
    _ell(g, cx - w * .22, y0 + h * .42, s * .07, s * .07, color)
    _ell(g, cx + w * .22, y0 + h * .42, s * .07, s * .07, color)
    return g


def icon_gear(slide, cx, cy, s, color):
    g = _g(slide)
    add_shape(g, MSO_SHAPE.GEAR_6, cx - s * .5, cy - s * .5, s, s, color)
    return g


def icon_arm(slide, cx, cy, s, color):
    g = _g(slide)
    add_line(g, cx - s * .40, cy + s * .42, cx + s * .40, cy + s * .42, color, s * .11)
    add_line(g, cx - s * .26, cy + s * .42, cx - s * .04, cy - s * .02, color, s * .11)
    add_line(g, cx - s * .04, cy - s * .02, cx + s * .26, cy - s * .28, color, s * .11)
    _ell(g, cx - s * .04, cy - s * .02, s * .09, s * .09, color)
    _ell(g, cx + s * .30, cy - s * .31, s * .11, s * .11, None, color, s * .10)
    return g


def icon_car(slide, cx, cy, s, color):
    g = _g(slide)
    add_freeform(g, [(cx - s * .44, cy + s * .12), (cx - s * .30, cy - s * .14),
                     (cx + s * .30, cy - s * .14), (cx + s * .44, cy + s * .12),
                     (cx + s * .44, cy + s * .28), (cx - s * .44, cy + s * .28)],
                 None, color, s * .10)
    _ell(g, cx - s * .24, cy + s * .32, s * .10, s * .10, None, color, s * .10)
    _ell(g, cx + s * .24, cy + s * .32, s * .10, s * .10, None, color, s * .10)
    return g


def icon_mail(slide, cx, cy, s, color):
    g = _g(slide)
    w = s * .88; h = s * .64
    add_shape(g, MSO_SHAPE.RECTANGLE, cx - w / 2, cy - h / 2, w, h, None, color, s * .10)
    add_line(g, cx - w / 2, cy - h / 2, cx, cy + h * .12, color, s * .10)
    add_line(g, cx + w / 2, cy - h / 2, cx, cy + h * .12, color, s * .10)
    return g


def icon_doc(slide, cx, cy, s, color):
    g = _g(slide)
    w = s * .68; h = s * .84
    add_shape(g, MSO_SHAPE.ROUNDED_RECTANGLE, cx - w / 2, cy - h / 2, w, h,
              None, color, s * .10, adj=.15)
    for k in range(3):
        yy = cy - h * .22 + k * h * .22
        add_line(g, cx - w * .26, yy, cx + w * .26, yy, color, s * .09)
    return g


def icon_shield(slide, cx, cy, s, color, check=False):
    g = _g(slide)
    pts = [(cx, cy - s * .42), (cx + s * .34, cy - s * .28), (cx + s * .34, cy + s * .04),
           (cx + s * .18, cy + s * .30), (cx, cy + s * .44), (cx - s * .18, cy + s * .30),
           (cx - s * .34, cy + s * .04), (cx - s * .34, cy - s * .28)]
    add_freeform(g, pts, None, color, s * .10)
    if check:
        add_line(g, cx - s * .13, cy - s * .02, cx - s * .03, cy + s * .10, color, s * .11)
        add_line(g, cx - s * .03, cy + s * .10, cx + s * .16, cy - s * .13, color, s * .11)
    return g


def icon_image(slide, cx, cy, s, color):
    g = _g(slide)
    w = s * .84; h = s * .68
    add_shape(g, MSO_SHAPE.ROUNDED_RECTANGLE, cx - w / 2, cy - h / 2, w, h,
              None, color, s * .10, adj=.12)
    _ell(g, cx - w * .22, cy - h * .16, s * .06, s * .06, color)
    add_line(g, cx - w * .42, cy + h * .26, cx - w * .10, cy - h * .04, color, s * .09)
    add_line(g, cx - w * .10, cy - h * .04, cx + w * .14, cy + h * .18, color, s * .09)
    add_line(g, cx + w * .14, cy + h * .18, cx + w * .30, cy + h * .04, color, s * .09)
    return g


def icon_mic(slide, cx, cy, s, color):
    g = _g(slide)
    add_shape(g, MSO_SHAPE.ROUNDED_RECTANGLE, cx - s * .13, cy - s * .44,
              s * .26, s * .44, None, color, s * .10, adj=.5)
    arc = add_shape(g, MSO_SHAPE.BLOCK_ARC, cx - s * .28, cy - s * .12, s * .56, s * .44, None, color, s * .10)
    arc.rotation = 0
    add_line(g, cx, cy + s * .28, cx, cy + s * .44, color, s * .10)
    return g


def icon_music(slide, cx, cy, s, color):
    g = _g(slide)
    add_line(g, cx + s * .10, cy - s * .40, cx + s * .10, cy + s * .18, color, s * .11)
    add_line(g, cx + s * .10, cy - s * .40, cx + s * .36, cy - s * .32, color, s * .11)
    _ell(g, cx - s * .04, cy + s * .22, s * .14, s * .11, color)
    return g


def icon_video(slide, cx, cy, s, color):
    g = _g(slide)
    w = s * .84; h = s * .64
    add_shape(g, MSO_SHAPE.ROUNDED_RECTANGLE, cx - w / 2, cy - h / 2, w, h,
              None, color, s * .10, adj=.2)
    tri = add_shape(g, MSO_SHAPE.ISOSCELES_TRIANGLE, cx - s * .08, cy - s * .15, s * .22, s * .30, color)
    tri.rotation = 90
    return g


def icon_person(slide, cx, cy, s, color):
    g = _g(slide)
    _ell(g, cx, cy - s * .16, s * .17, s * .17, None, color, s * .11)
    arc = add_shape(g, MSO_SHAPE.CHORD, cx - s * .32, cy + s * .02, s * .64, s * .48,
                    None, color, s * .11)
    arc.adjustments[0] = 0.12
    arc.adjustments[1] = 0.88
    return g


def icon_monitor(slide, cx, cy, s, color):
    g = _g(slide)
    w = s * .84; h = s * .56
    add_shape(g, MSO_SHAPE.ROUNDED_RECTANGLE, cx - w / 2, cy - h / 2 - s * .06,
              w, h, None, color, s * .10, adj=.15)
    add_line(g, cx, cy + h / 2 - s * .06, cx, cy + s * .34, color, s * .10)
    add_line(g, cx - s * .18, cy + s * .36, cx + s * .18, cy + s * .36, color, s * .10)
    return g


def icon_fork(slide, cx, cy, s, color):
    g = _g(slide)
    _ell(g, cx - s * .28, cy - s * .26, s * .10, s * .10, None, color, s * .11)
    _ell(g, cx + s * .28, cy - s * .26, s * .10, s * .10, None, color, s * .11)
    _ell(g, cx, cy + s * .30, s * .10, s * .10, None, color, s * .11)
    add_line(g, cx - s * .21, cy - s * .18, cx - s * .06, cy + s * .22, color, s * .11)
    add_line(g, cx + s * .21, cy - s * .18, cx + s * .06, cy + s * .22, color, s * .11)
    return g


def icon_bot_sm(slide, cx, cy, s, color):
    return icon_robot(slide, cx, cy, s * .92, color)


def icon_bulb(slide, cx, cy, s, color, bg):
    g = _g(slide)
    _ell(g, cx, cy, s * .5, s * .5, bg)
    _ell(g, cx, cy - s * .06, s * .17, s * .17, None, color, s * .055)
    add_shape(g, MSO_SHAPE.RECTANGLE, cx - s * .08, cy + s * .13, s * .16, s * .11,
              None, color, s * .05)
    for dx, dy in ((0, -.34), (-.24, -.26), (.24, -.26)):
        add_line(g, cx + dx * .9, cy + dy * .9, cx + dx * 1.2, cy + dy * 1.2, color, s * .05)
    return g


def icon_check(slide, cx, cy, r, color):
    g = _g(slide)
    _ell(g, cx, cy, r, r, color)
    add_line(g, cx - r * .42, cy, cx - r * .08, cy + r * .34, '#FFFFFF', r * .28)
    add_line(g, cx - r * .08, cy + r * .34, cx + r * .46, cy - r * .30, '#FFFFFF', r * .28)
    return g


def icon_shield_check(slide, cx, cy, s, color):
    g = _g(slide)
    pts = [(cx, cy - s * .42), (cx + s * .32, cy - s * .28), (cx + s * .32, cy + s * .02),
           (cx + s * .17, cy + s * .30), (cx, cy + s * .42), (cx - s * .17, cy + s * .30),
           (cx - s * .32, cy + s * .02), (cx - s * .32, cy - s * .28)]
    add_freeform(g, pts, color)
    add_line(g, cx - s * .13, cy - s * .02, cx - s * .03, cy + s * .10, '#FFFFFF', s * .08)
    add_line(g, cx - s * .03, cy + s * .10, cx + s * .16, cy - s * .13, '#FFFFFF', s * .08)
    return g


def icon_media(slide, cx, cy, s, color):
    g = _g(slide)
    w = s * .50; h = s * .40
    add_shape(g, MSO_SHAPE.ROUNDED_RECTANGLE, cx - s * .82, cy - h / 2, w, h,
              None, color, s * .07, adj=.15)
    _ell(g, cx - s * .70, cy - s * .08, s * .04, s * .04, color)
    add_line(g, cx - s * .80, cy + s * .12, cx - s * .60, cy - s * .04, color, s * .06)
    add_line(g, cx - s * .60, cy - s * .04, cx - s * .46, cy + s * .10, color, s * .06)
    for k in range(4):
        xx = cx - s * .22 + k * s * .075
        add_line(g, xx, cy - (s * .16 if k % 2 else s * .24),
                 xx, cy + (s * .16 if k % 2 else s * .24), color, s * .055)
    _ell(g, cx + s * .46, cy, s * .17, s * .17, color)
    tri = add_shape(g, MSO_SHAPE.ISOSCELES_TRIANGLE, cx + s * .42, cy - s * .06, s * .10, s * .12, '#FFFFFF')
    tri.rotation = 90
    return g


def icon_db_plus(slide, cx, cy, s, color, color2):
    g = _g(slide)
    add_shape(g, MSO_SHAPE.CAN, cx - s * .34, cy - s * .34, s * .52, s * .68,
              mix(color, '#FFFFFF', .82), color, s * .06)
    add_line(g, cx + s * .30, cy - s * .16, cx + s * .30, cy + s * .16, color2, s * .09)
    add_line(g, cx + s * .14, cy, cx + s * .46, cy, color2, s * .09)
    return g


def icon_sliders(slide, cx, cy, s, color):
    g = _g(slide)
    add_line(g, cx - s * .34, cy - s * .16, cx + s * .34, cy - s * .16, color, s * .07)
    add_line(g, cx - s * .34, cy + s * .14, cx + s * .34, cy + s * .14, color, s * .07)
    _ell(g, cx - s * .10, cy - s * .16, s * .10, s * .10, '#FFFFFF', color, s * .065)
    _ell(g, cx + s * .14, cy + s * .14, s * .10, s * .10, '#FFFFFF', color, s * .065)
    return g


def icon_chat_dots(slide, cx, cy, s, color):
    g = _g(slide)
    _ell(g, cx, cy, s * .28, s * .28, color)
    tri = add_shape(g, MSO_SHAPE.ISOSCELES_TRIANGLE, cx - s * .20, cy + s * .20, s * .12, s * .14, color)
    tri.rotation = 200
    for k in range(3):
        _ell(g, cx - s * .10 + k * s * .10, cy, s * .028, s * .028, '#FFFFFF')
    return g


def icon_headset(slide, cx, cy, s, color):
    g = _g(slide)
    arc = add_shape(g, MSO_SHAPE.BLOCK_ARC, cx - s * .30, cy - s * .34, s * .60, s * .52,
                    None, color, s * .09)
    arc.rotation = 0
    add_shape(g, MSO_SHAPE.ROUNDED_RECTANGLE, cx - s * .38, cy - s * .04, s * .13, s * .24,
              None, color, s * .09, adj=.4)
    add_shape(g, MSO_SHAPE.ROUNDED_RECTANGLE, cx + s * .25, cy - s * .04, s * .13, s * .24,
              None, color, s * .09, adj=.4)
    return g


def icon_excl_solid(slide, cx, cy, r, color):
    g = _g(slide)
    _ell(g, cx, cy, r, r, color)
    add_line(g, cx, cy - r * .48, cx, cy + r * .08, '#FFFFFF', r * .20)
    _ell(g, cx, cy + r * .42, r * .12, r * .12, '#FFFFFF')
    return g


def icon_excl_ring(slide, cx, cy, r, color):
    g = _g(slide)
    _ell(g, cx, cy, r * .92, r * .92, '#FFFFFF', color, r * .16)
    add_line(g, cx, cy - r * .44, cx, cy + r * .08, color, r * .18)
    _ell(g, cx, cy + r * .42, r * .12, r * .12, color)
    return g


def icon_spark_deco(slide, cx, cy, s, color):
    g = _g(slide)
    add_shape(g, MSO_SHAPE.STAR_4_POINT, cx - s * .5, cy - s * .5, s, s, color)
    return g
