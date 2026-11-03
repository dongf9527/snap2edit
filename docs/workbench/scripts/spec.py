# -*- coding: utf-8 -*-
"""
《公开框架与实施工具的对应关系》布局规格（1728 x 972）
所有组件 = 独立最小单元，供 build_html.py(SVG) 与 build_pptx.py 共用。

基元格式:
  ('rect',  x, y, w, h, fill, rx, stroke, sw, opacity, dash)
  ('circle',cx, cy, r, fill, stroke, sw)
  ('ellipse',cx,cy, rx, ry, fill, stroke, sw)
  ('line',  x1, y1, x2, y2, stroke, sw, dash)
  ('poly',  pts, fill, stroke, sw)          # 闭合多边形
  ('pline', pts, stroke, sw)                # 开放折线
  ('text',  x, cy, s, size, fill, weight, anchor)  # cy=垂直中心
"""

# ---------------- 调色板（原图采样） ----------------
PAGE      = '#FDFDFD'
NAVY      = '#1B3A5C'   # 主文字/线条
NAVY_DK   = '#0A2340'   # 数字圆
TITLE_C   = '#13294B'
CHEV1     = '#1C3C5E'   # 公开研究
CHEV2     = '#7E8869'   # 可信AI
CHEV3     = '#998C85'   # 董事会治理
CHEV4     = '#8A819B'   # 规模化实践
SRC_HDR   = '#E4E8EB'
GRID      = '#D8DEE3'
LABEL_BG  = '#EDF1F3'
CARD_BG   = '#F1F4F6'
CARD_BR   = '#E0E5E9'
OLIVE     = '#818B6B'
SLATE     = '#4A6481'
MAUVE     = '#8E869E'
TAUPE     = '#9C8F87'
PH1, PH2, PH3 = '#D6DDE4', '#748BA2', '#264867'
EV1, EV2, EV3 = '#939B80', '#8D8B7B', '#8E829A'
R4CARD    = '#E9EDF0'
R4BOX_BG, R4BOX_BR = '#F0F0F0', '#BBBEBE'
ORG_BR    = '#A79B7E'
ORG_FILL  = '#F8F7F3'
TBL_HDR   = '#E8ECEE'
TBL_BR    = '#C9CED3'
BAR_NAVY  = '#3A5A7A'
TRACK     = '#E6E9EB'
BAR_TAUPE = '#A4907F'
DOT_G     = '#7E8D62'
DOT_GRAY  = '#8D9297'
PRI_HI_BG, PRI_HI_TX = '#D3E3C2', '#2E6B47'
PRI_MID_BG, PRI_MID_TX = '#FBF3E4', '#C07A2E'
ICON_B    = '#2E5070'
FOOT_BR   = '#9AA2AC'
WHITE     = '#FFFFFF'

W, H = 1728, 972
FONT = "Noto Sans SC, Microsoft YaHei, PingFang SC, sans-serif"


def T(x, cy, s, size, fill=NAVY, weight=400, anchor='start'):
    return ('text', x, cy, s, size, fill, weight, anchor)


def R(x, y, w, h, fill, rx=0, stroke=None, sw=0, opacity=1, dash=None):
    return ('rect', x, y, w, h, fill, rx, stroke, sw, opacity, dash)


def C(cx, cy, r, fill, stroke=None, sw=0):
    return ('circle', cx, cy, r, fill, stroke, sw)


def chev_poly(x, y1, y2, band_w, tip=12, notch=0):
    """箭头带：band_w 为矩形段宽度, tip 为右侧尖角深度, notch 为左侧凹口深度"""
    m = (y1 + y2) / 2
    pts = [(x, y1), (x + band_w, y1), (x + band_w + tip, m), (x + band_w, y2), (x, y2)]
    if notch:
        pts.append((x + notch, m))
    return pts


C = None  # 防止遮蔽,重新绑定
def CIRC(cx, cy, r, fill, stroke=None, sw=0):
    return ('circle', cx, cy, r, fill, stroke, sw)


def LINE(x1, y1, x2, y2, stroke, sw, dash=None):
    return ('line', x1, y1, x2, y2, stroke, sw, dash)


def POLY(pts, fill, stroke=None, sw=0):
    return ('poly', pts, fill, stroke, sw)


def PLINE(pts, stroke, sw):
    return ('pline', pts, stroke, sw)


# ---------------- 图标库（独立最小单元,全部矢量基元） ----------------

def icon_book(x, y, s, color=WHITE):
    """翻开的书"""
    u = s / 36.0
    p = []
    p.append(('path', f"M{x},{y+6*u} C{x+6*u},{y+2*u} {x+13*u},{y+2*u} {x+18*u},{y+6*u} "
                      f"C{x+23*u},{y+2*u} {x+30*u},{y+2*u} {x+36*u},{y+6*u} "
                      f"L{x+36*u},{y+28*u} C{x+30*u},{y+24*u} {x+23*u},{y+24*u} {x+18*u},{y+28*u} "
                      f"C{x+13*u},{y+24*u} {x+6*u},{y+24*u} {x},{y+28*u} Z", color, None, 0))
    p.append(('rect', x+17*u, y+5*u, 2*u, 24*u, color, 0, None, 0, 1, None))
    return p


def icon_shield(x, y, s, color=WHITE):
    """盾牌+对勾"""
    u = s / 36.0
    return [('path', f"M{x+18*u},{y+1*u} L{x+33*u},{y+6*u} L{x+33*u},{y+18*u} "
                     f"C{x+33*u},{y+27*u} {x+27*u},{y+33*u} {x+18*u},{y+36*u} "
                     f"C{x+9*u},{y+33*u} {x+3*u},{y+27*u} {x+3*u},{y+18*u} "
                     f"L{x+3*u},{y+6*u} Z", color, None, 0),
            ('pline', [(x+11*u, y+18*u), (x+16*u, y+23*u), (x+26*u, y+12*u)], color, 2.6*u)]


def icon_people(x, y, s, color=WHITE):
    """三个人物(头部+圆润身体)"""
    u = s / 36.0
    p = []
    # 左右两人
    for cx in (8.2, 27.8):
        p.append(CIRC(x+cx*u, y+10.5*u, 4.6*u, color))
        p.append(('path', f"M{x+(cx-6)*u},{y+23.5*u} C{x+(cx-6)*u},{y+16.5*u} {x+(cx-3.2)*u},{y+16*u} "
                          f"{x+cx*u},{y+16*u} C{x+(cx+3.2)*u},{y+16*u} {x+(cx+6)*u},{y+16.5*u} "
                          f"{x+(cx+6)*u},{y+23.5*u} Z", color, None, 0))
    # 中间人(稍高稍大)
    p.append(CIRC(x+18*u, y+8.6*u, 5.4*u, color))
    p.append(('path', f"M{x+11.2*u},{y+23*u} C{x+11.2*u},{y+15*u} {x+14.4*u},{y+14.2*u} {x+18*u},{y+14.2*u} "
                      f"C{x+21.6*u},{y+14.2*u} {x+24.8*u},{y+15*u} {x+24.8*u},{y+23*u} Z", color, None, 0))
    return p


def icon_chart_arrow(x, y, s, color=WHITE):
    """三柱+上升箭头(白色剪影,用于规模化实践)"""
    u = s / 36.0
    p = []
    for bx, bh in ((3, 11), (11.5, 17), (20, 23)):
        p.append(('rect', x+bx*u, y+35*u-bh*u, 6.5*u, bh*u, color, 0, None, 0, 1, None))
    p.append(('path', f"M{x+3*u},{y+19*u} C{x+13*u},{y+16*u} {x+23*u},{y+11*u} {x+31*u},{y+4.5*u}",
              None, color, 2.8*u))
    p.append(POLY([(x+28.5*u, y+1*u), (x+36*u, y+2.5*u), (x+31*u, y+8.5*u)], color))
    return p


def icon_docout(x, y, s, color):
    """描边文档(白底+彩线)用于瓦片"""
    u = s / 36.0
    p = [('path', f"M{x+7*u},{y+3*u} L{x+22*u},{y+3*u} L{x+29*u},{y+10*u} L{x+29*u},{y+33*u} "
                  f"L{x+7*u},{y+33*u} Z", WHITE, color, 2.6*u),
         ('path', f"M{x+22*u},{y+3*u} L{x+22*u},{y+10*u} L{x+29*u},{y+10*u}", None, color, 2.2*u)]
    for i in range(3):
        p.append(('rect', x+11*u, y+(15+i*5.5)*u, (13 if i < 2 else 8)*u, 2.2*u, color,
                  0, None, 0, 1, None))
    return p


def icon_doclines(x, y, s, color, lines=3, fold=True):
    """文档+横线"""
    u = s / 36.0
    p = [('path', f"M{x+4*u},{y+1.5*u} L{x+24*u},{y+1.5*u} L{x+32*u},{y+9.5*u} "
                  f"L{x+32*u},{y+34.5*u} L{x+4*u},{y+34.5*u} Z", color, None, 0)]
    if fold:
        p.append(('path', f"M{x+24*u},{y+1.5*u} L{x+24*u},{y+9.5*u} L{x+32*u},{y+9.5*u} Z",
                  WHITE, None, 0))
    for i in range(lines):
        ly = y + (15 + i*6) * u
        wd = 18 if i < lines-1 else 12
        p.append(('rect', x+8*u, ly, wd*u, 2.4*u, WHITE, 0, None, 0, 1, None))
    return p


def icon_docmag(x, y, s, color):
    """文档+放大镜"""
    u = s / 36.0
    p = icon_doclines(x, y, s*0.92, color, lines=3)
    p.append(CIRC(x+24*u, y+24*u, 8*u, WHITE, color, 3.2*u))
    p.append(LINE(x+30.5*u, y+30.5*u, x+36*u, y+36*u, color, 3.6*u))
    return p


def icon_meeting(x, y, s, color):
    """会议(三人+桌)"""
    u = s / 36.0
    p = []
    for cx, cy, r in ((8, 10, 4.6), (28, 10, 4.6), (18, 8.5, 5.6)):
        p.append(CIRC(x+cx*u, y+cy*u, r*u, color))
    p.append(('path', f"M{x+3*u},{y+22*u} C{x+3*u},{y+17*u} {x+5.5*u},{y+15*u} {x+8*u},{y+15*u} "
                      f"C{x+10.5*u},{y+15*u} {x+13*u},{y+17*u} {x+13*u},{y+22*u} Z", color, None, 0))
    p.append(('path', f"M{x+23*u},{y+22*u} C{x+23*u},{y+17*u} {x+25.5*u},{y+15*u} {x+28*u},{y+15*u} "
                      f"C{x+30.5*u},{y+15*u} {x+33*u},{y+17*u} {x+33*u},{y+22*u} Z", color, None, 0))
    p.append(('path', f"M{x+11.5*u},{y+21*u} C{x+11.5*u},{y+15.5*u} {x+14.5*u},{y+13.5*u} {x+18*u},{y+13.5*u} "
                      f"C{x+21.5*u},{y+13.5*u} {x+24.5*u},{y+15.5*u} {x+24.5*u},{y+21*u} Z", color, None, 0))
    p.append(POLY([(x+4*u, y+25*u), (x+32*u, y+25*u), (x+28*u, y+33*u), (x+8*u, y+33*u)], color))
    return p


def icon_search(x, y, s, color):
    u = s / 36.0
    return [CIRC(x+15*u, y+15*u, 9.5*u, None, color, 3.4*u),
            LINE(x+22*u, y+22*u, x+31*u, y+31*u, color, 4*u)]


def icon_chat(x, y, s, color):
    u = s / 36.0
    p = [('path', f"M{x+3*u},{y+5*u} L{x+33*u},{y+5*u} L{x+33*u},{y+25*u} L{x+14*u},{y+25*u} "
                  f"L{x+7*u},{y+31*u} L{x+7*u},{y+25*u} L{x+3*u},{y+25*u} Z", color, None, 0)]
    for i in range(3):
        p.append(CIRC(x+(11+i*7)*u, y+15*u, 2*u, WHITE))
    return p


def icon_gear(x, y, s, color):
    u = s / 36.0
    p = [CIRC(x+18*u, y+18*u, 10.5*u, color)]
    for k in range(8):
        import math
        a = k * math.pi / 4
        x1, y1 = x+18*u + 10*u*math.cos(a), y+18*u + 10*u*math.sin(a)
        x2, y2 = x+18*u + 15.5*u*math.cos(a), y+18*u + 15.5*u*math.sin(a)
        p.append(LINE(x1, y1, x2, y2, color, 5.2*u))
    p.append(CIRC(x+18*u, y+18*u, 4.2*u, WHITE))
    return p


def icon_clipboard(x, y, s, color):
    """剪贴板+勾选"""
    u = s / 36.0
    p = [('path', f"M{x+5*u},{y+6*u} L{x+31*u},{y+6*u} L{x+31*u},{y+34*u} L{x+5*u},{y+34*u} Z",
          None, color, 3.4*u),
         ('rect', x+12*u, y+2*u, 12*u, 7*u, color, 1.5*u, None, 0, 1, None)]
    for i, (ix, lw) in enumerate(((7, 0), (7, 0), (7, 0), (7, 0))):
        ly = y + (13 + i*6) * u
        p.append(('rect', x+ix*u, ly, 4.5*u, 3.2*u, color, 0.8*u, None, 0, 1, None))
        p.append(('rect', x+14.5*u, ly, 12*u, 3.2*u, color, 0.8*u, None, 0, 1, None))
    p.append(CIRC(x+30*u, y+30*u, 9*u, color))
    p.append(('pline', [(x+25.5*u, y+30*u), (x+29*u, y+33.5*u), (x+35*u, y+26.5*u)], WHITE, 2.8*u))
    return p


def icon_shielddown(x, y, s, color):
    """盾牌+向下箭头"""
    u = s / 36.0
    p = icon_shield(x, y, s, color)
    p = [p[0]]
    p.append(('pline', [(x+18*u, y+11*u), (x+18*u, y+22*u)], color, 2.8*u))
    p.append(POLY([(x+13.5*u, y+19*u), (x+22.5*u, y+19*u), (x+18*u, y+25*u)], color))
    return p


def bars6(x, y_base, color_navy, light):
    """r1c1 六柱图标"""
    p = []
    xs = [x, x+21, x+42, x+63, x+84, x+105]
    hs = [44, 60, 76, 92, 86, 106]
    cols = ['#9FB0C0', '#33566F', '#3D607E', '#2C4C68', '#5B7C9C', '#A9BACA']
    for i in range(6):
        p.append(('rect', xs[i], y_base-hs[i], 16, hs[i], cols[i], 0, None, 0, 1, None))
    p.append(('rect', x, y_base-62, 121, 2.4, WHITE, 0, None, 0, 0.85, None))
    p.append(('rect', x, y_base, 121, 2.6, color_navy, 0, None, 0, 1, None))
    return p


def growth4(x, y_base, s=1.0, c_main='#89809A', c_light='#A49BB5'):
    """四柱+弧线箭头(紫)"""
    p = []
    bw, gap = 22*s, 8*s
    hs = [36*s, 56*s, 76*s, 98*s]
    for i in range(4):
        p.append(('rect', x+i*(bw+gap), y_base-hs[i], bw, hs[i],
                  c_main if i < 3 else c_light, 0, None, 0, 1, None))
    p.append(('path', f"M{x+4*s},{y_base-20*s} C{x+34*s},{y_base-40*s} {x+62*s},{y_base-58*s} "
                      f"{x+92*s},{y_base-76*s}", None, c_main, 5*s))
    p.append(POLY([(x+88*s, y_base-84*s), (x+104*s, y_base-72*s), (x+86*s, y_base-66*s)], c_main))
    return p


# ---------------- 组件清单 ----------------
G = []  # (group_id, primitives, z)  z 越大越后画


def add(gid, prims, z=0):
    G.append((gid, prims, z))


# ===== 标题 =====
add('title', [T(31, 45.5, '公开框架与实施工具的对应关系', 60, TITLE_C, 700)])

# ===== 顶部箭头带 =====
add('chev1', [POLY(chev_poly(186, 102, 168, 308, 14), CHEV1)])
add('chev1_icon', icon_book(212, 117, 36))
add('chev1_txt', [T(378, 135, '公开研究 / 能力评估', 22.5, WHITE, 700, 'middle')])
add('chev2', [POLY(chev_poly(505, 102, 168, 295, 14, 14), CHEV2)])
add('chev2_icon', icon_shield(528, 117, 36))
add('chev2_txt', [T(663, 135, '可信 AI', 22.5, WHITE, 700, 'middle')])
add('chev3', [POLY(chev_poly(816, 102, 168, 285, 14, 14), CHEV3)])
add('chev3_icon', icon_people(838, 117, 36))
add('chev3_txt', [T(1005, 135, '董事会治理', 22.5, WHITE, 700, 'middle')])
add('chev4', [POLY(chev_poly(1116, 102, 168, 288, 14, 14), CHEV4)])
add('chev4_icon', icon_chart_arrow(1138, 117, 36))
add('chev4_txt', [T(1292, 135, '规模化实践', 22.5, WHITE, 700, 'middle')])

# ===== 主要来源 头部 =====
add('src_head_box', [R(1442, 102, 276, 68, SRC_HDR, 8)])
add('src_head_icon', icon_doclines(1462, 114, 40, NAVY, lines=3))
add('src_head_txt', [T(1510, 134.5, '主要来源（公开资料）', 21, NAVY, 700)])

# ===== 主网格线 =====
gl = []
for x in (187, 503, 806, 1122):
    gl.append(LINE(x, 160, x, 922, GRID, 2))
gl.append(LINE(1434, 160, 1434, 771, GRID, 2))
gl.append(LINE(1716, 160, 1716, 922, GRID, 2))
for y in (160, 312, 465, 619, 771, 922):
    gl.append(LINE(187, y, 1716, y, GRID, 2))
add('grid', gl, z=-10)

# ===== 左侧行标签 =====
def rowlabel(gid, y1, y2, num, lines, circ_cy, text_cys):
    m = (y1 + y2) / 2
    p = [POLY([(14, y1), (160, y1), (178, m), (160, y2), (14, y2)], LABEL_BG)]
    p.append(CIRC(44, circ_cy, 18, NAVY_DK))
    p.append(T(44, circ_cy, num, 20, WHITE, 700, 'middle'))
    for tc, tx in zip(text_cys, lines):
        p.append(T(30, tc, tx, 21, NAVY_DK, 700))
    add(gid, p)

rowlabel('rowlabel1', 177, 310, '1', ['本报告拆解 /', '现状证据'], 207, [246, 276])
rowlabel('rowlabel2', 319, 463, '2', ['场景组合'], 358, [404])
rowlabel('rowlabel3', 471, 615, '3', ['分阶段交付'], 512, [557])
rowlabel('rowlabel4', 623, 767, '4', ['责任与控制'], 664, [708])
rowlabel('rowlabel5', 775, 919, '5', ['企业应用'], 809, [853])


# ===== 通用:三条项目符号 =====
def bullets(gid, dot_x, text_x, ys, texts, size=16, weight=400):
    p = []
    for i, (yy, tt) in enumerate(zip(ys, texts)):
        p.append(CIRC(dot_x, yy, 3.6, NAVY))
        p.append(T(text_x, yy, tt, size, '#274767', weight))
    add(gid, p)


# ================= 行1 =================
add('r1c1_icon', bars6(197, 288, NAVY, None))
bullets('r1c1_b', 345, 357, [217, 243, 268],
        ['行业水平与标杆对比', '企业能力现状评估', '差距与改进方向'], 15.5)

add('r1c2_icon', icon_docmag(535, 192, 60, OLIVE))
bullets('r1c2_b', 648, 661, [217, 243, 268],
        ['风险类型与典型案例', '可信特征与能力要求', '现状证据与差距分析'], 15.5)

add('r1c3_icon', icon_meeting(838, 196, 62, CHEV3))
bullets('r1c3_b', 953, 966, [217, 243, 268],
        ['治理重点与监督议题', '监管要求与合规趋势', '董事会关注点分析'], 15.5)

add('r1c4_icon', growth4(1152, 272))
bullets('r1c4_b', 1268, 1281, [217, 243, 268],
        ['规模化应用趋势', '行业实践与成效证据', '成功要素与挑战'], 15.5)

# ================= 行2 =================
tiles = [R(200, 332, 50, 52, '#DDE3E9', 10), R(263, 332, 50, 52, '#DDE3E9', 10),
         R(200, 391, 50, 52, '#DDE3E9', 10), R(263, 391, 50, 52, '#DDE3E9', 10)]
add('r2c1_tiles', tiles)
add('r2c1_ic1', icon_search(211, 343, 28, ICON_B))
add('r2c1_ic2', icon_chat(274, 343, 28, ICON_B))
add('r2c1_ic3', icon_docout(212, 402, 30, ICON_B))
add('r2c1_ic4', icon_gear(275, 402, 28, ICON_B))
bullets('r2c1_b', 345, 358, [359, 385, 411],
        ['高价值场景识别', '场景优先级排序', '能力匹配与差距'], 16)

pills2 = []
for i, t in enumerate(['公平性', '安全性', '可解释性', '隐私保护']):
    yy = 331 + i*31
    pills2.append(R(519, yy, 110, 28, OLIVE, 5))
    pills2.append(T(574, yy+14, t, 16.5, WHITE, 700, 'middle'))
add('r2c2_pills', pills2)
bullets('r2c2_b', 647, 660, [359, 385, 411],
        ['场景可信要求', '风险与缓解措施', '可信能力组合'], 16)

add('r2c3_boxes', [
    R(854, 335, 82, 32, ORG_FILL, 3, ORG_BR, 1.6),
    R(820, 397, 78, 32, ORG_FILL, 3, ORG_BR, 1.6),
    R(910, 397, 78, 32, ORG_FILL, 3, ORG_BR, 1.6)])
add('r2c3_conn', [
    PLINE([(895, 367), (895, 382)], NAVY, 2),
    LINE(859, 382, 949, 382, NAVY, 2),
    LINE(859, 382, 859, 397, NAVY, 2),
    LINE(949, 382, 949, 397, NAVY, 2)])
add('r2c3_txt', [
    T(895, 351, '董事会', 14.5, NAVY, 700, 'middle'),
    T(859, 413, '审计委员会', 13.5, NAVY, 700, 'middle'),
    T(949, 413, '管理层', 13.5, NAVY, 700, 'middle')])
bullets('r2c3_b', 990, 1003, [360, 385, 413],
        ['场景的治理要求', '决策与监督机制', '汇报与审查安排'], 16)

add('r2c4_pills', [
    R(1132, 337, 79, 49, SLATE, 8), T(1171, 361, '客户服务', 15, WHITE, 700, 'middle'),
    R(1217, 337, 78, 49, MAUVE, 8), T(1256, 361, '营销增长', 15, WHITE, 700, 'middle'),
    R(1132, 390, 79, 49, SLATE, 8), T(1171, 414, '运营提效', 15, WHITE, 700, 'middle'),
    R(1217, 390, 78, 49, TAUPE, 8), T(1256, 414, '产品创新', 15, WHITE, 700, 'middle')])
bullets('r2c4_b', 1311, 1324, [359, 385, 411],
        ['场景组合策略', '跨部门协同', '规模化推广路径'], 15.5)

# ================= 行3 =================
ph = []
for i, (bx, bw, t, fill, tc) in enumerate((
        (204, 83, '探索期', PH1, NAVY), (301, 83, '试点期', PH2, WHITE),
        (398, 85, '规模化期', PH3, WHITE))):
    ph.append(POLY(chev_poly(bx, 484, 518, bw, 12, 12 if i else 0), fill))
    ph.append(T(bx+bw/2+4, 501, t, 16, tc, 700, 'middle'))
ph.append(LINE(205, 530.5, 490, 530.5, NAVY, 3))
for cx in (241, 337, 433):
    ph.append(CIRC(cx, 530.5, 6.5, NAVY))
add('r3c1_phases', ph)
bullets('r3c1_b', 224, 237, [553, 579, 604],
        ['各阶段目标与范围', '关键里程碑', '资源与能力建设'], 16)

ev = []
for i, (bx, bw, t) in enumerate(((517, 83, '评估'), (614, 82, '加固'), (710, 83, '监控'))):
    ev.append(POLY(chev_poly(bx, 484, 518, bw, 12, 12 if i else 0),
                   (EV1, EV2, EV3)[i]))
    ev.append(T(bx+bw/2+4, 501, t, 16, WHITE, 700, 'middle'))
add('r3c2_phases', ev)
bullets('r3c2_b', 528, 541, [551, 577, 602],
        ['可信能力分阶段落地', '风险控制里程碑', '验证与持续改进'], 16)

tl = [T(862, 486, '阶段1', 17, NAVY, 700, 'middle'),
      T(957, 486, '阶段2', 17, NAVY, 700, 'middle'),
      T(1052, 486, '阶段3', 17, NAVY, 700, 'middle'),
      LINE(826, 515, 1096, 515, NAVY, 3),
      POLY([(1094, 507), (1112, 515), (1094, 523)], NAVY)]
for cx in (864, 959, 1054):
    tl.append(CIRC(cx, 515, 8.5, WHITE, NAVY, 3.5))
add('r3c3_timeline', tl)
bullets('r3c3_b', 838, 851, [551, 578, 604],
        ['治理体系建设节奏', '董事会审查节点', '关键决策事项'], 16)

add('r3c4_icon', growth4(1163, 590, 1.18))
bullets('r3c4_b', 1305, 1318, [513, 540, 566],
        ['试点到规模化路径', '能力复制与推广', '组织与工具准备'], 15.5)

# ================= 行4 =================
add('r4c1_boxes', [
    R(246, 638, 114, 32, WHITE, 3, '#35597B', 1.8),
    R(193, 709, 64, 28, WHITE, 3, '#35597B', 1.8),
    R(262, 709, 63, 28, WHITE, 3, '#35597B', 1.8),
    R(330, 709, 62, 28, WHITE, 3, '#35597B', 1.8)])
add('r4c1_conn', [
    LINE(303, 670, 303, 690, NAVY, 2),
    LINE(225, 690, 361, 690, NAVY, 2),
    LINE(225, 690, 225, 709, NAVY, 2),
    LINE(293, 690, 293, 709, NAVY, 2),
    LINE(361, 690, 361, 709, NAVY, 2)])
add('r4c1_txt', [
    T(303, 654, '业务负责人', 15, NAVY, 700, 'middle'),
    T(225, 723, '技术团队', 13, NAVY, 700, 'middle'),
    T(293, 723, '数据团队', 13, NAVY, 700, 'middle'),
    T(361, 723, '运营团队', 13, NAVY, 700, 'middle')])
bullets('r4c1_b', 396, 409, [671, 695, 720],
        ['角色与分工', '关键控制点', '三道防线协同'], 14.5)

cards3 = []
for i, (cx0, t, ic) in enumerate(((523, '风险控制', 's'), (615, '合规审查', 'd'), (710, '持续监控', 'g'))):
    cards3.append(R(cx0, 629, 80, 80, R4CARD, 10))
    cards3.append(T(cx0+40, 692, t, 16.5, NAVY, 700, 'middle'))
add('r4c2_cards', cards3)
add('r4c2_ic1', icon_shielddown(543, 637, 42, '#1F3F60'))
add('r4c2_ic2', icon_doclines(634, 639, 40, '#1F3F60', lines=3))
add('r4c2_ic3', icon_gear(730, 638, 42, '#1F3F60'))
bullets('r4c2_b', 583, 596, [720, 740, 760],
        ['模型全生命周期控制', '数据与隐私管理', '事件响应机制'], 15)

add('r4c3_boxes', [
    R(860, 639, 118, 34, R4BOX_BG, 6, R4BOX_BR, 1.5),
    R(860, 682, 118, 34, R4BOX_BG, 6, R4BOX_BR, 1.5),
    R(860, 725, 118, 34, R4BOX_BG, 6, R4BOX_BR, 1.5)])
add('r4c3_bracket', [
    LINE(838, 656, 830, 656, NAVY, 2),
    LINE(830, 656, 830, 742, NAVY, 2),
    LINE(830, 699, 830, 699, NAVY, 2),
    LINE(830, 656, 854, 656, NAVY, 2),
    LINE(830, 699, 854, 699, NAVY, 2),
    LINE(830, 742, 854, 742, NAVY, 2),
    POLY([(854, 652), (862, 656), (854, 660)], NAVY),
    POLY([(854, 695), (862, 699), (854, 703)], NAVY),
    POLY([(854, 738), (862, 742), (854, 746)], NAVY)])
add('r4c3_txt', [
    T(919, 656, '董事会监督', 16.5, NAVY, 700, 'middle'),
    T(919, 699, '管理层执行', 16.5, NAVY, 700, 'middle'),
    T(919, 742, '内审与监督', 16.5, NAVY, 700, 'middle')])
bullets('r4c3_b', 993, 1006, [667, 697, 726],
        ['治理责任划分', '汇报机制与频率', '审计与独立评估'], 15.5)

add('r4c4_icon', icon_clipboard(1155, 636, 78, MAUVE))
bullets('r4c4_b', 1276, 1289, [667, 695, 723],
        ['上线关卡设置', '规模化风险控制', '持续监测与优化'], 16)

# ================= 行5:四个表格 =================
def table_base(gid_title, title, x1):
    add(gid_title, [T(x1, 789, title, 17, NAVY, 700)])

def header_cells(gid, xs, hs_, y1=801, y2=824):
    """xs: 列边界列表, hs_: 表头文字"""
    p = []
    for i in range(len(xs)-1):
        p.append(R(xs[i], y1, xs[i+1]-xs[i], y2-y1, TBL_HDR, 0, TBL_BR, 1))
    for i, h in enumerate(hs_):
        p.append(T((xs[i]+xs[i+1])/2, (y1+y2)/2+0.5, h, 14.5, NAVY, 700, 'middle'))
    add(gid, p)

# --- 表1 能力评估表  x 200-497 ---
table_base('t1_title', '能力评估表', 200)
header_cells('t1_head', [200, 284, 354, 434, 497], ['评估维度', '现状评分', '目标水平', '差距'])
rows1 = ['战略与组织', '数据与技术', '人才与能力', '流程与运营']
navy_w = [58, 38, 56, 38]
taupe_w = [35, 19, 21, 25]
p = []
for i, rname in enumerate(rows1):
    cy = 836 + i*24
    p.append(R(200, 824+i*24, 297, 24, WHITE, 0, TBL_BR, 1))
    p.append(T(210, cy, rname, 14.5, NAVY, 700))
    p.append(R(291, cy-5, 56, 10, TRACK, 2))
    p.append(R(291, cy-5, navy_w[i], 10, BAR_NAVY, 2))
    p.append(R(439, cy-5, 52, 10, TRACK, 2))
    p.append(R(439, cy-5, taupe_w[i], 10, BAR_TAUPE, 2))
add('t1_rows', p)

# --- 表2 场景清单  x 519-839 ---
table_base('t2_title', '场景清单', 519)
header_cells('t2_head', [519, 612, 680, 759, 839], ['场景名称', '业务价值', '可信要求', '优先级'], 799, 822)
rows2 = ['智能客服', '营销内容生成', '运营流程优化', '产品研发辅助']
pri = [('高', PRI_HI_BG, PRI_HI_TX), ('高', PRI_HI_BG, PRI_HI_TX),
       ('中', PRI_MID_BG, PRI_MID_TX), ('中', PRI_MID_BG, PRI_MID_TX)]
dot2 = [DOT_G, DOT_G, DOT_GRAY, DOT_GRAY]
p = []
for i, rname in enumerate(rows2):
    cy = 834.5 + i*25
    p.append(R(519, 822+i*25, 320, 25, WHITE, 0, TBL_BR, 1))
    p.append(T(529, cy, rname, 14.5, NAVY, 700))
    p.append(CIRC(646, cy, 7, DOT_G))
    p.append(CIRC(719, cy, 7, dot2[i]))
    p.append(R(759, 822+i*25, 80, 25, pri[i][1], 0, TBL_BR, 1))
    p.append(T(799, cy, pri[i][0], 15, pri[i][2], 700, 'middle'))
add('t2_rows', p)

# --- 表3 路线图与上线关卡  x 862-1208 ---
table_base('t3_title', '路线图与上线关卡', 862)
header_cells('t3_head', [862, 966, 1087, 1208], ['阶段', '关键任务', '上线关卡'], 804, 828)
rows3 = [('探索期', '场景验证', '价值评估'), ('试点期', '小规模上线', '风险审查'),
         ('规模化期', '全面推广', '效果评估')]
p = []
for i, (a, b, c_) in enumerate(rows3):
    cy = 842 + i*29
    p.append(R(862, 828+i*29, 346, 29, WHITE, 0, TBL_BR, 1))
    for j, t in enumerate((a, b, c_)):
        p.append(T((862, 966, 1087)[j] + ((966, 1087, 1208)[j] - (862, 966, 1087)[j]) / 2,
                   cy, t, 15, NAVY, 400, 'middle'))
add('t3_rows', p)

# --- 表4 价值台账  x 1231-1704 ---
table_base('t4_title', '价值台账', 1231)
header_cells('t4_head', [1231, 1350, 1471, 1593, 1704], ['场景', '预期价值', '衡量指标', '负责人'], 800, 822)
rows4 = [('智能客服', '效率提升', '处理时长', '客服部'),
         ('营销内容生成', '收入增长', '转化率', '市场部'),
         ('运营流程优化', '成本降低', '人效提升', '运营部'),
         ('产品研发辅助', '创新加速', '上市周期', '产品部')]
p = []
for i, row in enumerate(rows4):
    cy = 833.5 + i*23.4
    p.append(R(1231, 822+i*23.4, 473, 23.4, WHITE, 0, TBL_BR, 1))
    for j, t in enumerate(row):
        p.append(T((1231, 1350, 1471, 1593)[j] + ((1350, 1471, 1593, 1704)[j] - (1231, 1350, 1471, 1593)[j]) / 2,
                   cy, t, 14.5, NAVY, 400, 'middle'))
add('t4_rows', p)

# ================= 右侧来源卡 =================
def cover(gid, cy_top, main, l1, l2, tiny):
    """迷你报告封面:白框+几何切面+底部白条+微缩文字(真实文本)"""
    x, w_, h_ = 1463, 78, 98
    p = [R(x, cy_top, w_, h_, WHITE, 2, '#C9CED4', 1.4),
         R(x+5, cy_top+5, w_-10, h_-24, main, 0)]
    p.append(POLY([(x+5, cy_top+5), (x+w_-5, cy_top+5), (x+5, cy_top+42)], l1))
    p.append(POLY([(x+w_-5, cy_top+5), (x+w_-5, cy_top+60), (x+18, cy_top+5)], l2))
    p.append(POLY([(x+5, cy_top+60), (x+w_-5, cy_top+28), (x+w_-5, cy_top+74), (x+5, cy_top+74)], l1))
    p.append(T(x+9, cy_top+16, tiny[0], 5, WHITE, 700))
    p.append(T(x+9, cy_top+23, tiny[1], 4, WHITE, 400))
    p.append(T(x+9, cy_top+29, tiny[2], 3.6, WHITE, 400, )if len(tiny) > 2 else T(x+9, cy_top+29, '', 3.6, WHITE))
    p.append(R(x+5, cy_top+h_-19, w_-10, 14, WHITE, 0))
    p.append(T(x+9, cy_top+h_-11, tiny[-1], 4.2, '#8A8F96', 400))
    add(gid, p)

add('srccard1', [R(1442, 177, 276, 133, CARD_BG, 8, CARD_BR, 1.2)])
cover('srccard1_cover', 196, '#33566F', '#47698A', '#7C97AE',
      ['AI capability', 'assessment', '2026 Edition', 'Deloitte Digital'])
add('srccard1_txt', [T(1560, 223, 'AI capability', 19, NAVY, 700),
                     T(1560, 244.5, 'assessment', 19, NAVY, 700),
                     T(1560, 266.5, '数字渠道能力评估', 17, '#33566F', 400)])

add('srccard2', [R(1442, 317, 276, 146, CARD_BG, 8, CARD_BR, 1.2)])
cover('srccard2_cover', 341, '#64794F', '#8CA06F', '#A9BC8B',
      ['Trustworthy AI', 'Trusted features', '', 'Deloitte AI Institute'])
add('srccard2_txt', [T(1560, 377, 'Trustworthy AI', 19, NAVY, 700),
                     T(1560, 404.5, '可信特征', 17, '#4A5D3A', 400)])

add('srccard3', [R(1442, 470, 276, 144, CARD_BG, 8, CARD_BR, 1.2)])
cover('srccard3_cover', 493, '#97897F', '#B3A79D', '#CFC5BD',
      ['AI Governance', 'Roadmap', 'Board oversight', 'Deloitte Governance'])
add('srccard3_txt', [T(1560, 513.5, 'AI Governance', 19, NAVY, 700),
                     T(1560, 541, 'Roadmap', 19, NAVY, 700),
                     T(1560, 567, '董事会监督', 17, '#6B5D52', 400)])

add('srccard4', [R(1442, 622, 276, 143, CARD_BG, 8, CARD_BR, 1.2)])
cover('srccard4_cover', 646, '#87829C', '#A09BB4', '#BDB8CC',
      ['State of AI 2026', 'Scaling topics', '', 'Deloitte Insights'])
add('srccard4_txt', [T(1560, 683, 'State of AI 2026', 19, NAVY, 700),
                     T(1560, 711, '规模化议题', 17, '#5A5570', 400)])

# ================= 底部注释 =================
add('footer_box', [R(24, 927, 1688, 36, WHITE, 6, FOOT_BR, 1.5, 1, '7,5')])
add('footer_icon', [CIRC(44, 945, 10.5, NAVY),
                    T(44, 945, '!', 15, WHITE, 700, 'middle')])
add('footer_txt', [T(68, 945, '评分权重、预算和排期为本报告设计的实施工具，不属于德勤官方统一模板。',
                    16.5, NAVY, 400)])

# 按 z 稳定排序 (z 小的先画)
COMPONENTS = sorted(G, key=lambda t: t[2])
