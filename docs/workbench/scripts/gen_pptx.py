# -*- coding: utf-8 -*-
"""德勤AI落地方法论拆解 - PPTX 生成（原生文本框+形状，每单元可独立拖动编辑）
坐标系：原图 1728x972 px -> 16:9 幻灯片(12192000x6858000 EMU)
"""
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.dml import MSO_LINE_DASH_STYLE as MSO_LINE
from pptx.dml.color import RGBColor
from pptx.oxml.ns import qn

EMU_PX = 12192000 / 1728.0          # 7055.556 EMU per px
PT_PX = 54.0 / 97.2                 # 0.5556 pt per px

def E(px):
    return Emu(int(round(px * EMU_PX)))

def FS(pt):
    return Pt(pt)   # 调用方直接传最终 pt 值

def C(h):
    return RGBColor.from_string(h)

FONT = 'Microsoft YaHei'

prs = Presentation()
prs.slide_width = Emu(12192000)
prs.slide_height = Emu(6858000)
slide = prs.slides.add_slide(prs.slide_layouts[6])
SH = slide.shapes

# ---------------- 基础绘制助手 ----------------
def _font(run, size, color, bold=False):
    f = run.font
    f.name = FONT
    f.size = FS(size)
    f.bold = bold
    f.color.rgb = C(color)
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn('a:ea'))
    if ea is None:
        ea = rPr.makeelement(qn('a:ea'), {})
        rPr.append(ea)
    ea.set('typeface', FONT)

def _noshadow(sp):
    try:
        sp.shadow.inherit = False
    except Exception:
        pass

def text(x, y, w, h, lines, size, color, bold=False, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, spacing=1.0, space_after=0):
    """lines: 字符串 或 [字符串...]，多行=多段落"""
    tb = SH.add_textbox(E(x), E(y), E(w), E(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    if isinstance(lines, str):
        lines = [lines]
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = spacing
        if space_after:
            p.space_after = Pt(space_after)
        r = p.add_run()
        r.text = ln
        _font(r, size, color, bold)
    return tb

def rect(x, y, w, h, fill=None, line=None, lw=1.0, shape=MSO_SHAPE.RECTANGLE, adj=None):
    sp = SH.add_shape(shape, E(x), E(y), E(w), E(h))
    if adj is not None:
        try:
            sp.adjustments[0] = adj
        except Exception:
            pass
    if fill:
        sp.fill.solid(); sp.fill.fore_color.rgb = C(fill)
    else:
        sp.fill.background()
    if line:
        sp.line.color.rgb = C(line); sp.line.width = Pt(lw)
    else:
        sp.line.fill.background()
    _noshadow(sp)
    return sp

def oval(x, y, w, h, fill=None, line=None, lw=1.0):
    return rect(x, y, w, h, fill, line, lw, shape=MSO_SHAPE.OVAL)

def poly(pts, fill=None, line=None, lw=1.0, close=True, dash=None):
    """pts: [(px,py)...] 绝对像素坐标；close=False 时为开放折线"""
    fb = SH.build_freeform(pts[0][0], pts[0][1], EMU_PX)
    fb.add_line_segments([(px, py) for px, py in pts[1:]], close=close)
    sp = fb.convert_to_shape()
    if fill:
        sp.fill.solid(); sp.fill.fore_color.rgb = C(fill)
    else:
        sp.fill.background()
    if line:
        sp.line.color.rgb = C(line); sp.line.width = Pt(lw)
        if dash:
            sp.line.dash_style = dash
    else:
        sp.line.fill.background()
    _noshadow(sp)
    return sp

def seg(x1, y1, x2, y2, color, lw=1.2, dash=None):
    sp = SH.add_connector(MSO_CONNECTOR.STRAIGHT, E(x1), E(y1), E(x2), E(y2))
    sp.line.color.rgb = C(color)
    sp.line.width = Pt(lw)
    if dash:
        sp.line.dash_style = dash
    _noshadow(sp)
    return sp

def curve(p0, c1, c2, p3, color, lw=1.2, n=8):
    """三次贝塞尔 -> 折线(open freeform)"""
    pts = []
    for i in range(n + 1):
        t = i / n
        mt = 1 - t
        x = mt**3*p0[0] + 3*mt*mt*t*c1[0] + 3*mt*t*t*c2[0] + t**3*p3[0]
        y = mt**3*p0[1] + 3*mt*mt*t*c1[1] + 3*mt*t*t*c2[1] + t**3*p3[1]
        pts.append((x, y))
    return poly(pts, line=color, lw=lw, close=False)

# ================= 背景 =================
rect(0, 0, 1728, 972, fill='FCFDFE')

# ================= 标题 =================
text(34, 30, 900, 200, ['德勤AI落地方法论拆解', '评估、路线图、治理。'],
     size=36.5, color='0D2139', bold=True, spacing=1.3)

# ================= 三列数据 =================
COLS = [
    dict(x=34,  head='3E586C', num='2C4254', badge='2A4056', card='EBEFF2', icon='46617A',
         title='评估',   sub='识别价值与可行性，明确AI落地起点'),
    dict(x=384, head='75814E', num='5D6940', badge='6D7154', card='EFEFEC', icon='6D7154',
         title='路线图', sub='从试点到规模化，规划可执行的实施路径'),
    dict(x=734, head='858192', num='655E74', badge='7B7587', card='F0EEF3', icon='7B7587',
         title='治理',   sub='建立负责任的AI治理体系，保障可持续发展'),
]
CARDS = [
    [('战略对齐', '结合业务战略，明确AI的价值方向与关键问题'),
     ('机会识别', '梳理业务场景，评估价值空间与可行性'),
     ('能力评估', '评估数据、技术、人才与组织现状'),
     ('风险与合规评估', '识别技术、数据、法律、伦理等潜在风险'),
     ('优先级排序', '基于价值、可行性与风险确定优先落地场景')],
    [('目标与愿景', '明确阶段性目标与预期价值，设定可衡量的里程碑'),
     ('场景与用例规划', '选择高价值场景，设计试点与推广路径'),
     ('实施路径', '制定从试点到规模化的阶段计划，明确关键任务与依赖关系'),
     ('资源与能力建设', '规划数据、技术、人才与生态合作的风入与建设'),
     ('价值衡量', '建立量化指标体系，跟踪进展并持续优化')],
    [('治理框架', '明确治理原则、组织架构与决策机制'),
     ('风险管理', '覆盖数据安全、模型风险、合规与伦理'),
     ('政策与标准', '制定AI相关政策、流程与技术标准'),
     ('监控与审计', '建立全生命周期监控、审计与问责机制'),
     ('文化与人才', '推动负责任的AI文化，提升员工意识与专业能力')],
]
ICON_KEYS = [['target', 'bulb', 'bars', 'shield', 'doc'],
             ['target', 'network', 'flow', 'people', 'chartup'],
             ['orgtree', 'warn', 'doc', 'mag', 'people']]

CT, CY, CW, CH = 256, 256, 333, 608   # 列容器

def draw_icon(key, ix, iy, color):
    """步骤卡图标（66x44 框内，全部为独立形状）"""
    w = 1.6
    if key == 'target':
        oval(ix+8, iy+8, 26, 26, line=color, lw=w)
        oval(ix+15, iy+15, 12, 12, line=color, lw=w)
        oval(ix+19.5, iy+19.5, 3, 3, fill=color)
        seg(ix+44, iy+3, ix+30, iy+17, color, w)
        seg(ix+30, iy+17, ix+38, iy+15, color, w)
        seg(ix+30, iy+17, ix+32, iy+9, color, w)
    elif key == 'bulb':
        oval(ix+20, iy+2, 20, 20, line=color, lw=w)
        seg(ix+26, iy+27, ix+34, iy+27, color, w)
        seg(ix+27.5, iy+32, ix+32.5, iy+32, color, w)
        seg(ix+30, iy-2, ix+30, iy+0.5, color, w)
        seg(ix+8, iy+12, ix+11, iy+12, color, w)
        seg(ix+52, iy+12, ix+49, iy+12, color, w)
    elif key == 'bars':
        seg(ix+8, iy+37, ix+58, iy+37, color, w)
        rect(ix+13, iy+25, 10, 12, line=color, lw=w)
        rect(ix+27, iy+15, 10, 22, line=color, lw=w)
        rect(ix+41, iy+5, 10, 32, line=color, lw=w)
    elif key == 'shield':
        poly([(ix+33, iy+2), (ix+49, iy+8), (ix+49, iy+21), (ix+33, iy+41),
              (ix+17, iy+21), (ix+17, iy+8)], line=color, lw=w)
        seg(ix+33, iy+13, ix+33, iy+24, color, w)
        oval(ix+31.5, iy+28, 3, 3, fill=color)
    elif key == 'doc':
        rect(ix+18, iy+2, 28, 38, line=color, lw=w, shape=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.12)
        seg(ix+24, iy+11, ix+40, iy+11, color, w)
        seg(ix+24, iy+19, ix+40, iy+19, color, w)
        seg(ix+24, iy+27, ix+33, iy+27, color, w)
    elif key == 'network':
        oval(ix+10, iy+5, 11, 11, line=color, lw=w)
        oval(ix+40, iy+3, 11, 11, line=color, lw=w)
        oval(ix+25, iy+27, 13, 13, line=color, lw=w)
        seg(ix+19, iy+12, ix+28, iy+29, color, w)
        seg(ix+43, iy+13, ix+34, iy+30, color, w)
        seg(ix+21, iy+10, ix+40, iy+9, color, w)
    elif key == 'flow':
        rect(ix+4, iy+3, 14, 11, line=color, lw=w, shape=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.25)
        rect(ix+46, iy+3, 14, 11, line=color, lw=w, shape=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.25)
        rect(ix+25, iy+29, 14, 11, line=color, lw=w, shape=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.25)
        seg(ix+11, iy+14, ix+11, iy+20, color, w)
        seg(ix+53, iy+14, ix+53, iy+20, color, w)
        seg(ix+11, iy+20, ix+53, iy+20, color, w)
        seg(ix+32, iy+20, ix+32, iy+29, color, w)
    elif key == 'people':
        oval(ix+12, iy+7, 11, 11, line=color, lw=w)
        oval(ix+40, iy+7, 11, 11, line=color, lw=w)
        oval(ix+25, iy+3, 12, 12, line=color, lw=w)
        poly([(ix+9, iy+36), (ix+11, iy+27), (ix+17, iy+24), (ix+18, iy+28),
              (ix+18, iy+36)], line=color, lw=w, close=False)
        poly([(ix+51, iy+36), (ix+49, iy+27), (ix+43, iy+24), (ix+42, iy+28),
              (ix+42, iy+36)], line=color, lw=w, close=False)
        poly([(ix+21, iy+36), (ix+23, iy+25), (ix+31, iy+22), (ix+39, iy+25),
              (ix+41, iy+36)], line=color, lw=w, close=False)
    elif key == 'chartup':
        seg(ix+6, iy+38, ix+56, iy+38, color, w)
        rect(ix+11, iy+30, 8, 8, line=color, lw=w)
        rect(ix+23, iy+24, 8, 14, line=color, lw=w)
        rect(ix+35, iy+16, 8, 22, line=color, lw=w)
        poly([(ix+9, iy+16), (ix+20, iy+9), (ix+34, iy+5), (ix+44, iy+3)],
             line=color, lw=w, close=False)
        poly([(ix+50, iy+1), (ix+40, iy+2), (ix+45, iy+9)], fill=color)
    elif key == 'orgtree':
        rect(ix+24, iy+2, 13, 10, line=color, lw=w, shape=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.25)
        rect(ix+6, iy+31, 13, 10, line=color, lw=w, shape=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.25)
        rect(ix+44, iy+31, 13, 10, line=color, lw=w, shape=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.25)
        seg(ix+30.5, iy+12, ix+30.5, iy+18, color, w)
        seg(ix+12.5, iy+31, ix+12.5, iy+25, color, w)
        seg(ix+50.5, iy+31, ix+50.5, iy+25, color, w)
        seg(ix+12.5, iy+25, ix+50.5, iy+25, color, w)
        seg(ix+30.5, iy+18, ix+30.5, iy+31, color, w)
    elif key == 'warn':
        poly([(ix+31, iy+3), (ix+53, iy+40), (ix+9, iy+40)], line=color, lw=w)
        seg(ix+31, iy+16, ix+31, iy+26, color, w)
        oval(ix+29.5, iy+31, 3, 3, fill=color)
    elif key == 'mag':
        oval(ix+13, iy+6, 24, 24, line=color, lw=w)
        seg(ix+33, iy+28, ix+46, iy+41, color, 2.2)

def draw_header_icon(idx, hx, hy):
    w = 1.9
    if idx == 0:   # 文档+放大镜
        rect(hx+8, hy+2, 27, 35, line='FFFFFF', lw=w, shape=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.12)
        seg(hx+15, hy+11, hx+30, hy+11, 'FFFFFF', w)
        seg(hx+15, hy+18, hx+25, hy+18, 'FFFFFF', w)
        oval(hx+27, hy+23, 15, 15, line='FFFFFF', lw=w)
        seg(hx+39, hy+37, hx+45, hy+43, 'FFFFFF', w)
    elif idx == 1:  # 折叠地图+定位
        poly([(hx+6, hy+10), (hx+20, hy+5), (hx+20, hy+41), (hx+6, hy+46)], line='FFFFFF', lw=w)
        poly([(hx+20, hy+5), (hx+34, hy+10), (hx+34, hy+46), (hx+20, hy+41)], line='FFFFFF', lw=w)
        poly([(hx+34, hy+10), (hx+48, hy+5), (hx+48, hy+41), (hx+34, hy+46)], line='FFFFFF', lw=w)
        oval(hx+30, hy+16, 8, 8, line='FFFFFF', lw=w)
    else:           # 盾牌+箭头
        poly([(hx+24, hy+2), (hx+41, hy+9), (hx+41, hy+22), (hx+24, hy+42),
              (hx+7, hy+22), (hx+7, hy+9)], line='FFFFFF', lw=w)
        seg(hx+15, hy+22, hx+29, hy+22, 'FFFFFF', w)
        seg(hx+29, hy+22, hx+24, hy+17, 'FFFFFF', w)
        seg(hx+29, hy+22, hx+24, hy+27, 'FFFFFF', w)

# ---------------- 三列组装 ----------------
for ci, col in enumerate(COLS):
    x = col['x']
    # 容器
    rect(x, CY, CW, CH, fill='FDFDFE', line='E7EBF1', lw=1,
         shape=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.045)
    # 头部（上圆角矩形）
    rect(x, CY, CW, 77, fill=col['head'],
         shape=MSO_SHAPE.ROUND_2_SAME_RECTANGLE, adj=0.22)
    # 序号块（右侧斜切）
    poly([(x, CY), (x+84, CY), (x+70, CY+77), (x, CY+77)], fill=col['num'])
    text(x, CY, 70, 77, f'0{ci+1}', size=17, color='FFFFFF', bold=True,
         align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    text(x+96, CY, 140, 77, col['title'], size=17.5, color='FFFFFF', bold=True,
         anchor=MSO_ANCHOR.MIDDLE)
    draw_header_icon(ci, x+CW-56, CY+15)
    # 副标题
    text(x+14, CY+91, 306, 24, col['sub'], size=8.5, color='152A40', bold=True)
    # 卡片
    for i, (t, d) in enumerate(CARDS[ci]):
        cy = 382 + i * 94
        rect(x+12, cy, 309, 84, fill=col['card'],
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.10)
        b = oval(x+22, cy+25, 34, 34, fill=col['badge'])
        tf = b.text_frame
        tf.word_wrap = False
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
        r = p.add_run(); r.text = str(i+1)
        _font(r, 9.5, 'FFFFFF', True)
        draw_icon(ICON_KEYS[ci][i], x+70, cy+20, col['icon'])
        # 单文本框双段落：标题加粗 + 描述灰字
        tb = SH.add_textbox(E(x+142), E(cy+11), E(172), E(66))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p1 = tf.paragraphs[0]; p1.line_spacing = 1.1
        r1 = p1.add_run(); r1.text = t; _font(r1, 9.5, '15273C', True)
        p2 = tf.add_paragraph(); p2.line_spacing = 1.28; p2.space_before = Pt(2.6)
        r2 = p2.add_run(); r2.text = d; _font(r2, 7, '57626F', False)

# ================= 右侧插图（X0=1050，局部坐标+1050=画布坐标） =================
X0 = 1050

def L(px, py):
    return (px + X0, py)

def K(px, py):
    return (px, py)   # 画布绝对坐标（图标区直接使用）

# ---- 光晕（扁平色块近似，两层椭圆） ----
oval(*L(190, 215), 220, 180, fill='EAF2F8')
oval(*L(172, 440), 156, 34, fill='C5DDEF')

# ---- 四层基座 ----
def slab(cx, cy, hw, hh, d, top, left, right):
    poly([L(cx, cy-hh), L(cx+hw, cy), L(cx, cy+hh), L(cx-hw, cy)], fill=top)
    poly([L(cx-hw, cy), L(cx, cy+hh), L(cx, cy+hh+d), L(cx-hw, cy+d)], fill=left)
    poly([L(cx+hw, cy), L(cx, cy+hh), L(cx, cy+hh+d), L(cx+hw, cy+d)], fill=right)

slab(300, 550, 230, 115, 16, 'F6F8FC', 'E3E9F2', 'EDF1F7')   # 白底层
slab(300, 511, 208, 104, 24, 'D5DEE9', 'AEBCCD', 'C4CFDD')   # 浅层
slab(300, 474, 176, 88, 30, '93A5BA', '6E8299', '7F92A8')    # 中层
slab(300, 438, 142, 71, 34, '5E7189', '3E5068', '4A5C74')    # 暗顶层
# 台阶块
poly([L(190,474), L(216,486), L(216,514), L(190,502)], fill='4E6076')
poly([L(190,474), L(203,468), L(229,480), L(216,486)], fill='5E7188')
poly([L(388,478), L(414,490), L(414,518), L(388,506)], fill='4E6076')
poly([L(388,478), L(401,472), L(427,484), L(414,490)], fill='5E7188')

# ---- 连接线与虚线弧（位于基座之上、立方体之下） ----
curve(L(262,108), L(225,165), L(215,220), L(218,258), 'A9B4C4', 1.2)
curve(L(545,236), L(545,258), L(490,254), L(420,270), 'A9B4C4', 1.2)
poly([L(115,332), L(126,400), L(131,470), L(118,530), L(105,585), L(102,620),
      L(110,653), L(125,672), L(142,690)], line='A9B4C4', lw=1.2, close=False)
curve(L(196,642), L(230,702), L(246,724), L(262,745), 'A9B4C4', 1.2)
curve(L(346,816), L(420,846), L(472,820), L(518,774), 'A9B4C4', 1.2)
curve(L(576,539), L(576,589), L(562,645), L(549,687), 'A9B4C4', 1.2)
curve(L(430,330), L(478,356), L(510,386), L(544,418), 'A9B4C4', 1.2)
poly([L(121,470), L(100,525), L(100,590), L(130,640), L(182,658)],
     line='8B99AB', lw=1.5, close=False, dash=MSO_LINE.ROUND_DOT)
poly([L(480,655), L(522,596), L(550,530), L(560,472)],
     line='8B99AB', lw=1.5, close=False, dash=MSO_LINE.ROUND_DOT)
poly([L(108,598), L(126,640), L(160,672), L(208,694)],
     line='8B99AB', lw=1.5, close=False, dash=MSO_LINE.ROUND_DOT)
for nx, ny, nr in [(262,108,4),(218,258,4.5),(545,206,4),(420,270,4.5),(115,332,4),
                   (131,470,4.5),(105,585,4),(142,690,4.5),(262,745,4.5),(518,774,4.5),
                   (576,505,4),(576,539,4.5),(549,687,4),(544,418,4.5),(95,300,4),
                   (470,178,4),(60,588,4),(612,640,4)]:
    oval(*L(nx-nr, ny-nr), nr*2, nr*2, fill='5F7086')

# ---- AI 立方体 ----
poly([L(300,235), L(410,290), L(300,345), L(190,290)], fill='9FB6CD')          # 顶
cube_glow = oval(*L(262,274), 76, 32, fill='CFE6F4')                            # 顶面青光
oval(*L(285,283), 30, 14, fill='E2F3FB')
poly([L(190,290), L(300,345), L(300,480), L(190,425)], fill='54708C')          # 左
poly([L(410,290), L(300,345), L(300,480), L(410,425)], fill='3D5470')          # 右
# 右面电路
for (a, b) in [((420,323),(323,371)), ((417,355),(327,403)), ((413,387),(331,429))]:
    seg(*L(*a), *L(*b), '9FD4EF', 1.0)
poly([L(345,360), L(383,341), L(383,405), L(345,424)], line='9FD4EF', lw=1.0)
oval(*L(357,375), 14, 14, line='9FD4EF', lw=1.0)
oval(*L(361.5,379.5), 5, 5, fill='BFE6F8')
# 顶部芯片
poly([L(300,272), L(332,290), L(300,308), L(268,290)], fill='7FA6C2')
poly([L(300,279), L(318,290), L(300,301), L(282,290)], fill='BFE3F5')
oval(*L(296,286), 8, 8, fill='E8F7FF')
seg(*L(300,264), *L(300,256), '9FC9E2', 1.2)
seg(*L(332,290), *L(340,290), '9FC9E2', 1.2)
seg(*L(300,308), *L(300,316), '9FC9E2', 1.2)
seg(*L(268,290), *L(260,290), '9FC9E2', 1.2)
# AI 文字（注意用 L() 加插图偏移）
ai = text(*L(202, 352), 90, 62, 'AI', size=30, color='F5FAFD', bold=True,
          align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
ai.rotation = 12

# ---- 云与基础设施·云图标 ----
poly([K(1262,88), K(1258,74), K(1270,63), K(1283,51), K(1301,45), K(1321,47),
      K(1335,57), K(1345,70), K(1343,83), K(1330,92), K(1272,92)],
     fill='F2F5FA', line='C9D2DE', lw=1.5)
rect(*K(1297,62), 22, 16, fill='4A5A70', shape=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.2)
rect(*K(1302,66), 12, 7, fill='9BD8F2', shape=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.3)
for a, b in [((1302,58),(1302,54)), ((1308,58),(1308,54)), ((1314,58),(1314,54)),
             ((1293,70),(1289,70)), ((1293,76),(1289,76)), ((1323,70),(1327,70)),
             ((1323,76),(1327,76))]:
    seg(*K(*a), *K(*b), '4A5A70', 1.2)

# ---- 数据层·数据库图标 ----
poly([K(1543,157), K(1593,182), K(1593,190), K(1543,165), K(1493,190), K(1493,157)],
     fill='E4EAF2')
poly([K(1543,207), K(1593,182), K(1593,190), K(1543,215), K(1493,190), K(1493,182)],
     fill='D8E0EB')
poly([K(1543,157), K(1593,182), K(1543,207), K(1493,182)], fill='EDF1F7')
oval(*K(1510,133), 56, 22, line='B9C5D4', lw=1.0)
oval(*K(1510,147), 56, 22, line='B9C5D4', lw=1.0)
poly([K(1510,119), K(1510,148), K(1524,157), K(1552,157), K(1566,148), K(1566,119)],
     fill='D7E0EA', line='C0CBD9', lw=1.2)
oval(*K(1510,108), 56, 22, fill='EEF3F9', line='C0CBD9', lw=1.2)
oval(*K(1520,113), 36, 12, fill='D5DFEB')

# ---- 模型与技术层·柱状图标 ----
seg(*K(1070,234), *K(1070,308), 'B9C3D2', 1.3)
seg(*K(1070,308), *K(1082,308), 'B9C3D2', 1.3)
seg(*K(1070,234), *K(1080,234), 'B9C3D2', 1.3)
oval(*K(1066.5,224.5), 7, 7, fill='8B99AB')
oval(*K(1060.5,304.5), 7, 7, fill='8B99AB')
poly([K(1096,254), K(1108,248), K(1108,302), K(1096,308)], fill='6C8098')
poly([K(1108,248), K(1118,253), K(1118,307), K(1108,302)], fill='9FAFBF')
poly([K(1118,268), K(1130,262), K(1130,296), K(1118,302)], fill='6C8098')
poly([K(1130,262), K(1140,267), K(1140,301), K(1130,296)], fill='9FAFBF')
poly([K(1084,316), K(1144,286), K(1156,292), K(1096,322)], fill='E8EDF4')

# ---- 应用层·网格+胶片图标 ----
rect(*K(1594,432), 26, 26, fill='8496AA', shape=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.25)
rect(*K(1626,432), 26, 26, fill='5F7288', shape=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.25)
rect(*K(1594,466), 26, 26, fill='5F7288', shape=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.25)
rect(*K(1626,466), 26, 26, fill='9AAABB', shape=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.25)
rect(*K(1553,443), 20, 56, fill='F2F5F9', line='9AA7B8', lw=1.3,
     shape=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.18)
for yy in (449, 467, 485):
    rect(*K(1558, yy), 10, 9, fill='B9C4D3', shape=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.3)

# ---- 组织与人才·楼宇图标 ----
poly([K(1142,738), K(1204,769), K(1204,775), K(1142,744), K(1080,775), K(1080,769)], fill='D3DCE7')
poly([K(1080,769), K(1142,800), K(1142,806), K(1080,775)], fill='D3DCE7')
poly([K(1204,769), K(1142,800), K(1142,806), K(1204,775)], fill='DEE5EE')
poly([K(1142,738), K(1204,769), K(1142,800), K(1080,769)], fill='E8EDF4')
rect(*K(1102,718), 20, 54, fill='647690')
rect(*K(1122,723), 8, 52, fill='8B9CB1')
rect(*K(1134,698), 24, 76, fill='55687F')
rect(*K(1158,704), 9, 72, fill='93A3B6')
rect(*K(1172,730), 16, 44, fill='7C8DA3')
rect(*K(1188,734), 7, 42, fill='A9B7C6')
for wx, wy in [(1140,706),(1149,706),(1140,720),(1149,720),(1140,734),(1149,734)]:
    rect(*K(wx, wy), 5, 6, fill='D9E2EC')

# ---- 治用与合规·人员图标 ----
poly([K(1287,798), K(1339,824), K(1339,828), K(1287,802)], fill='D3DCE7')
poly([K(1391,798), K(1339,824), K(1339,828), K(1391,802)], fill='DEE5EE')
poly([K(1339,798), K(1391,824), K(1339,850), K(1287,824)], fill='E8EDF4')
poly([K(1287,798), K(1339,824), K(1339,820), K(1287,794)], fill='EDF1F7')
oval(*K(1297,771), 18, 18, fill='8C9CB0')
poly([K(1293,816), K(1297,800), K(1310,795), K(1323,800), K(1327,816)], fill='8C9CB0')
oval(*K(1357,771), 18, 18, fill='9AA9BB')
poly([K(1353,816), K(1357,800), K(1370,795), K(1383,800), K(1387,816)], fill='9AA9BB')
oval(*K(1319,757), 22, 22, fill='55687F')
poly([K(1311,812), K(1316,792), K(1339,792), K(1344,812), K(1339,816), K(1316,816)], fill='55687F')

# ---- 业务价值·增长图标 ----
poly([K(1559,777), K(1613,804), K(1613,808), K(1559,781)], fill='D3DCE7')
poly([K(1667,777), K(1613,804), K(1613,808), K(1667,781)], fill='DEE5EE')
poly([K(1613,750), K(1667,777), K(1613,804), K(1559,777)], fill='E8EDF4')
rect(*K(1570,750), 11, 18, fill='98A8BA', shape=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.3)
rect(*K(1587,738), 11, 30, fill='8799AD', shape=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.3)
rect(*K(1604,726), 11, 42, fill='6C82A0', shape=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.3)
rect(*K(1621,712), 11, 56, fill='4E647E', shape=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.3)
poly([K(1568,728), K(1586,706), K(1604,696), K(1630,690)], line='3E5470', lw=2.2, close=False)
poly([K(1638,684), K(1622,686), K(1630,698)], fill='3E5470')

# ---- 插图标签（真实文本） ----
def lbl(x, y, s, size=11, color='12263C', bold=True, w=260):
    text(x, y, w, size*2.2, s, size=size, color=color, bold=bold)

def isub(x, y, lines_):
    text(x, y, 250, 46, lines_, size=7.5, color='4C5B6E', spacing=1.32)

lbl(*L(300,104), '云与基础设施'); isub(*L(300,134), '算力｜存储｜平台')
lbl(*L(500,206), '数据层'); isub(*L(500,236), ['数据治理｜数据安全', '数据资产｜高质量数据'])
lbl(*L(28,324), '模型与技术层'); isub(*L(28,354), ['基础模型｜行业模型', '工具链｜MLOps'])
lbl(*L(502,500), '应用层'); isub(*L(502,530), ['业务场景｜智能体', '产品与服务'])
lbl(*L(26,806), '组织与人才'); isub(*L(26,836), ['组织架构｜人才能力', '文化变革'])
lbl(*L(192,850), '治用与合规'); isub(*L(192,880), ['政策标准｜风险管理', '监控审计｜伦理责任'])
lbl(*L(500,806), '业务价值'); isub(*L(500,836), ['效率提升｜创新增长', '客户体验｜社会价值'])

# ================= 页脚 =================
text(34, 927, 360, 22, '基于德勤公开资料的独立研究。', size=8.5, color='4A5C74')
rect(404, 943, 1290, 1.4, fill='C7CEDA')

OUT = '/home/z/my-project/download/德勤AI落地方法论拆解.pptx'
prs.save(OUT)
print('saved:', OUT)
