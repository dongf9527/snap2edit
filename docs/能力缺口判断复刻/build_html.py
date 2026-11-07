#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
005《准备度评分与能力缺口诊断》— 交付物① HTML+SVG 复刻生成脚本
画布 1728x972（与原图 1:1），全真实 <text>，零位图；
每个可编辑最小单元为独立 <g class="unit" data-unit="...">。
共享几何（gear_pts/arc_pts）供 build_pptx.py 复用。

版面三段：左·准备度评分表（含进度条与合计行）
          右·能力缺口差距排序条形图（灰标题条 + 白色主体）
          底·重点行动与优先事项（灰带 + 三个行动盒）+ 水印
"""
import math
import os

W, H = 1728, 972

# ---------- 配色（原图采样） ----------
TITLE_C = '#0B2140'    # 标题深藏青
INK = '#14263F'        # 深藏青正文（维度名/行动文字）
NUM_C = '#0E1F3C'      # 评分数字
WEIGHT_C = '#1A2C4B'   # 权重/维度名
HEADER_NAVY = '#253E56'  # 表头
SEP = '#E9ECF1'        # 行分隔线
VSEP = '#F0F2F5'       # 表内纵向淡分隔
TOT_BG = '#EAEDF1'     # 合计行底
TOT_SEP = '#DFE3E9'    # 合计行顶线
TRACK = '#D7DDE4'      # 表格进度条轨道
STRIP_BG = '#EEF1F4'   # 右面板标题条
PANEL_LINE = '#E3E7EB' # 面板竖分隔线
PTRACK = '#E7EBEE'     # 右面板条轨道
BAND_BG = '#F2F4F7'    # 底部灰带
NOTE_C = '#90949C'     # 底部右侧小字
WM = '#ACAFB4'         # 水印灰

# 六行（表格）主题色：图标圆 / 现状条 / 目标条
ROWS = [
    # 名称, 权重, 现状, 目标, 图标色, 现状条色, 现状条宽, 目标条色, 目标条宽, 目标深色段宽(0=无)
    ('战略', '20%', '3.5', '4.0', '#223952', '#455E7A', 192, '#455E7A', 205, 53),
    ('流程', '20%', '3.0', '4.0', '#616A4E', '#828B6E', 162, '#818B6D', 205, 0),
    ('数据', '20%', '2.5', '4.0', '#6A594A', '#99897A', 134, '#9A8A7B', 205, 0),
    ('技术', '15%', '3.0', '4.0', '#76718D', '#88849D', 162, '#88849E', 205, 0),
    ('人才', '10%', '2.0', '3.5', '#283A52', '#4A637D', 102, '#2B455F', 175, 0),
    ('治理', '15%', '2.0', '4.0', '#61694C', '#848C6F', 102, '#818A6B', 205, 0),
]
ROW_CY = [251, 323, 397, 475, 553, 630]          # 行中心（原图实测）
ROW_SEP = [286, 359, 436, 514, 592]              # 行分隔线 y

# 右面板六行（原图实测，行序=差距排序）
PBARS = [
    # 排名, 名称, 数值, 徽标色, 条色, 条宽
    ('1', '治理', '2.0', '#5F684A', '#7A8364', 321),
    ('2', '数据', '1.5', '#7C6B59', '#978678', 242),
    ('3', '人才', '1.5', '#7A7491', '#88859D', 242),
    ('4', '流程', '1.0', '#293D55', '#3A5672', 171),
    ('5', '技术', '1.0', '#616A4B', '#7B8565', 171),
    ('6', '战略', '0.5', '#7C6957', '#978677', 87),
]
PBAR_CY = [262, 339, 420, 502, 582, 664]

# 底部行动项
ACTIONS = [
    # 图标cx, 图标色, 盒x0, 盒x1, 盒底色, 徽标x0, 徽标色, 维度名, 名字x, 分隔x, 行动文字, 文字x, 字号
    (82,  '#776350', 143, 572, '#F0EBE6', 155, '#6D5946', '数据', 215, 282, '先完成数据授权和质量核验', 296, 20),
    (654, '#636C4B', 714, 1137, '#ECEDE8', 730, '#5D6648', '治理', 792, 858, '先明确上线责任', 872, 25),
    (1206, '#2C3D52', 1272, 1711, '#F1EFF4', 1292, '#77738B', '人才', 1356, 1422, '先培训业务主责', 1438, 23),
]

# ---------- 表格列几何（原图实测） ----------
TBL_X0, TBL_X1 = 19, 1016
HDR_Y, HDR_H = 129, 77
COLS = [19, 233, 389, 705, 1016]                 # 列边界
NOW_BAR_X, NOW_BAR_W = 424, 248                  # 现状条轨道
TGT_BAR_X, TGT_BAR_W = 743, 246                  # 目标条轨道
TOT_Y0, TOT_Y1 = 672, 766                        # 合计行
TOT_SEPS = [597, 810]                            # 合计行白色子分隔

# 右面板几何
STRIP = (1032, 127, 1711, 210)
PBAR_X0, PBAR_W = 1206, 434                      # 面板条轨道
PVAL_X = 1681                                    # 数值右锚

# ---------- 共享几何（HTML 与 PPTX 共用） ----------
def gear_pts(cx, cy, s, teeth=8):
    """齿轮外轮廓多边形（直边近似）"""
    R, r1 = s * 0.50, s * 0.385
    step = 360.0 / teeth
    pts = []
    for k in range(teeth):
        a = k * step
        for ang, rr in [(a - 11, R), (a + 11, R), (a + 18, r1), (a + step - 18, r1)]:
            rad = math.radians(ang)
            pts.append((cx + rr * math.cos(rad), cy + rr * math.sin(rad)))
    return pts

def arc_pts(cx, cy, rx, ry, a0, a1, n=16):
    """椭圆弧采样点（角度制，0=右，90=下）"""
    pts = []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        pts.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
    return pts

# ---------- SVG 基元 ----------
def T(x, y, size, text, fill, weight=400, anchor='start', ls=None):
    a = {'start': 'start', 'center': 'middle', 'end': 'end'}[anchor]
    lsattr = f' letter-spacing="{ls}"' if ls else ''
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" '
            f'font-weight="{weight}" text-anchor="{a}"{lsattr}>{text}</text>')

def poly(pts, fill, extra=''):
    p = ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
    return f'<polygon points="{p}" fill="{fill}"{extra}/>'

def pline(pts, stroke, w, fill='none'):
    p = ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
    return (f'<polyline points="{p}" fill="{fill}" stroke="{stroke}" stroke-width="{w}" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')

def rrect(x, y, w, h, rx, fill=None, stroke=None, sw=0):
    a = f' fill="{fill}"' if fill else ' fill="none"'
    b = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ''
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}"{a}{b}/>'

def circle(cx, cy, r, fill=None, stroke=None, sw=0):
    a = f' fill="{fill}"' if fill else ' fill="none"'
    b = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ''
    return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.2f}"{a}{b}/>'

def ellipse(cx, cy, rx, ry, fill=None, stroke=None, sw=0):
    a = f' fill="{fill}"' if fill else ' fill="none"'
    b = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ''
    return f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}"{a}{b}/>'

def line(x1, y1, x2, y2, stroke, w, cap='round'):
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" '
            f'stroke-width="{w}" stroke-linecap="{cap}"/>')

# ---------- 图标（白色线稿，绘于彩色圆内；中心 cx,cy） ----------
def ic_target(cx, cy, s, c='#FFFFFF'):
    """战略：白色靶心 + 飞镖（细线稿）"""
    o = [circle(cx - s * .05, cy + s * .05, s * .29, stroke=c, sw=s * .055),
         circle(cx - s * .05, cy + s * .05, s * .16, stroke=c, sw=s * .05),
         circle(cx - s * .05, cy + s * .05, s * .042, fill=c)]
    x1, y1 = cx + s * .40, cy - s * .40
    o.append(line(x1, y1, cx + s * .01, cy - s * .01, c, s * .055))
    o.append(poly([(x1 + s * .085, y1 - s * .025), (x1 - s * .025, y1 + s * .085),
                   (x1 - s * .095, y1 - s * .095)], c))
    return ''.join(o)

def ic_gear(cx, cy, s, c='#FFFFFF', bg=None):
    """流程：白色齿轮（饱满短齿）+ 圆心孔"""
    b = bg or _CIRCLE_BG
    return poly(gear_pts(cx, cy, s * .74), c) + circle(cx, cy, s * .105, fill=b)

def circle_bg():
    """齿轮中心孔透出底色——SVG 中用深色近似（由调用处主题色决定）"""
    return _CIRCLE_BG

_CIRCLE_BG = '#616A4E'

def ic_database(cx, cy, s, c='#FFFFFF', bg=None):
    """数据：白色实心圆柱（底色分隔线）"""
    b = bg or _CIRCLE_BG
    rx, ry = s * .30, s * .105
    top, bot = cy - s * .30, cy + s * .34
    body = (f'M {cx - rx:.1f} {top:.1f} L {cx + rx:.1f} {top:.1f} L {cx + rx:.1f} {bot:.1f} '
            f'A {rx:.1f} {ry:.1f} 0 0 1 {cx - rx:.1f} {bot:.1f} Z')
    o = [f'<path d="{body}" fill="{c}"/>',
         ellipse(cx, top, rx, ry, fill=c),
         pline(arc_pts(cx, top + s * .22, rx, ry, 0, 180), b, s * .05),
         pline(arc_pts(cx, top + s * .44, rx, ry, 0, 180), b, s * .05)]
    return ''.join(o)

def ic_laptop(cx, cy, s, c='#FFFFFF'):
    """技术：白色线稿笔记本"""
    sw = s * .055
    o = [rrect(cx - s * .27, cy - s * .28, s * .54, s * .38, s * .04, stroke=c, sw=sw),
         line(cx - s * .38, cy + s * .24, cx + s * .38, cy + s * .24, c, s * .07)]
    return ''.join(o)

def ic_people(cx, cy, s, c='#FFFFFF'):
    """人才：白色双人（圆头 + 圆肩钟形身）"""
    def body(px, py, k):
        hw, hh = s * .21 * k, s * .26 * k
        d = (f'M {px - hw:.1f} {py + hh:.1f} L {px - hw:.1f} {py - hh * .18:.1f} '
             f'Q {px - hw:.1f} {py - hh * .62:.1f} {px - hw * .45:.1f} {py - hh * .62:.1f} '
             f'L {px + hw * .45:.1f} {py - hh * .62:.1f} '
             f'Q {px + hw:.1f} {py - hh * .62:.1f} {px + hw:.1f} {py - hh * .18:.1f} '
             f'L {px + hw:.1f} {py + hh:.1f} Z')
        return f'<path d="{d}" fill="{c}"/>'
    def person(px, py, k):
        return circle(px, py - s * .22 * k, s * .125 * k, fill=c) + body(px, py + s * .02, k)
    return person(cx + s * .17, cy + s * .05, 0.80) + person(cx - s * .12, cy, 1.0)

def ic_shield(cx, cy, s, c='#FFFFFF'):
    """治理：白色盾牌轮廓（细线）"""
    pts = [(cx, cy - s * .34), (cx + s * .27, cy - s * .23), (cx + s * .27, cy + s * .04),
           (cx + s * .145, cy + s * .25), (cx, cy + s * .37), (cx - s * .145, cy + s * .25),
           (cx - s * .27, cy + s * .04), (cx - s * .27, cy - s * .23)]
    return pline(pts + [pts[0]], c, s * .055)

def ic_wechat(cx, cy, w, c=WM):
    """微信双气泡（水印），按外包络 w×0.79w 绘制"""
    h = w * 0.79
    o = [ellipse(cx - w * .155, cy - h * .075, w * .315, h * .27, fill=c),
         poly([(cx - w * .30, cy + h * .10), (cx - w * .30, cy + h * .30),
               (cx - w * .125, cy + h * .16)], c),
         circle(cx - w * .225, cy - h * .11, w * .032, fill='#FFFFFF'),
         circle(cx - w * .085, cy - h * .11, w * .032, fill='#FFFFFF'),
         ellipse(cx + w * .17, cy + h * .10, w * .25, h * .215, fill=c),
         poly([(cx + w * .27, cy + h * .24), (cx + w * .29, cy + h * .42),
               (cx + w * .125, cy + h * .30)], c),
         circle(cx + w * .105, cy + h * .06, w * .027, fill='#FFFFFF'),
         circle(cx + w * .225, cy + h * .06, w * .027, fill='#FFFFFF')]
    return ''.join(o)

# ---------- 组装 ----------
units = []

def unit(uid, inner):
    units.append(f'  <g id="{uid}" class="unit" data-unit="{uid}">\n    {inner}\n  </g>')

# ===== 1. 主标题（加描边增粗以匹配原图字重） =====
unit('title', f'<text x="36" y="88" font-size="76" fill="{TITLE_C}" font-weight="700" '
              f'stroke="{TITLE_C}" stroke-width="2.0">准备度评分与能力缺口诊断</text>')

# ===== 2. 底部灰带（先画，位于底层） =====
unit('band_bg', rrect(18, 795, 1694, 43, 4, fill=BAND_BG))

# ===== 3. 左表格 =====
# 表头（顶部圆角）
hdr = (f'<path d="M {TBL_X0} {HDR_Y+HDR_H} L {TBL_X0} {HDR_Y+11} Q {TBL_X0} {HDR_Y} '
       f'{TBL_X0+11} {HDR_Y} L {TBL_X1-11} {HDR_Y} Q {TBL_X1} {HDR_Y} {TBL_X1} {HDR_Y+11} '
       f'L {TBL_X1} {HDR_Y+HDR_H} Z" fill="{HEADER_NAVY}"/>')
for cx_ in COLS[1:-1]:
    hdr += line(cx_ - 1.5, HDR_Y + 6, cx_ - 1.5, HDR_Y + HDR_H - 6, '#FFFFFF', 3, 'butt')
hdr += T(126, 180, 28, '维度', '#FFFFFF', 700, 'center')
hdr += T(311, 180, 28, '权重', '#FFFFFF', 700, 'center')
hdr += T(543, 164, 28, '现状评分', '#FFFFFF', 700, 'center')
hdr += T(543, 193, 21, '(满分5)', '#FFFFFF', 400, 'center')
hdr += T(865, 164, 28, '目标评分', '#FFFFFF', 700, 'center')
hdr += T(865, 193, 21, '(满分5)', '#FFFFFF', 400, 'center')
unit('table_header', hdr)

# 网格：行分隔 + 纵向淡分隔 + 合计行
grid = ''
for y in ROW_SEP:
    grid += line(TBL_X0, y, TBL_X1, y, SEP, 2.5, 'butt')
for cx_ in COLS[1:-1]:
    grid += line(cx_, HDR_Y + HDR_H, cx_, TOT_Y0, VSEP, 2, 'butt')
grid += rrect(TBL_X0, TOT_Y0, TBL_X1 - TBL_X0, TOT_Y1 - TOT_Y0, 0, fill=TOT_BG)
grid += line(TBL_X0, 670.5, TBL_X1, 670.5, TOT_SEP, 3, 'butt')
for cx_ in TOT_SEPS:
    grid += line(cx_ - 1.5, TOT_Y0, cx_ - 1.5, TOT_Y1, '#FFFFFF', 3, 'butt')
unit('table_grid', grid)

# 六行内容
ICONS = [ic_target, ic_gear, ic_database, ic_laptop, ic_people, ic_shield]
for i, (name, wt, now, tgt, iconc, nowc, noww, tgtc, tgtw, stubw) in enumerate(ROWS):
    cy = ROW_CY[i]
    # 图标圆（_CIRCLE_BG 供齿轮芯/圆柱分隔线透底色）
    globals()['_CIRCLE_BG'] = iconc
    unit(f'r{i+1}_icon', circle(76, cy, 29, fill=iconc) + ICONS[i](76, cy, 54, '#FFFFFF'))
    # 维度名 / 权重
    unit(f'r{i+1}_name', T(130, cy + 9, 27, name, WEIGHT_C, 700))
    unit(f'r{i+1}_weight', T(311, cy + 7, 26, wt, WEIGHT_C, 400, 'center'))
    # 现状评分：数字 + 条
    unit(f'r{i+1}_nownum', T(425, cy - 5, 26, now, NUM_C, 400))
    bar = rrect(NOW_BAR_X, cy + 2, NOW_BAR_W, 19, 2, fill=TRACK)
    bar += rrect(NOW_BAR_X, cy + 2, noww, 19, 2, fill=nowc)
    unit(f'r{i+1}_nowbar', bar)
    # 目标评分：数字 + 条（行1 有深色前段）
    unit(f'r{i+1}_tgtnum', T(744, cy - 5, 26, tgt, NUM_C, 400))
    tbar = rrect(TGT_BAR_X, cy + 2, TGT_BAR_W, 19, 2, fill=TRACK)
    if stubw:
        tbar += rrect(TGT_BAR_X, cy + 2, stubw, 19, 2, fill='#264059')
        tbar += rrect(TGT_BAR_X + stubw, cy + 2, tgtw - stubw, 19, 2, fill=tgtc)
    else:
        tbar += rrect(TGT_BAR_X, cy + 2, tgtw, 19, 2, fill=tgtc)
    unit(f'r{i+1}_tgtbar', tbar)

# 合计行
unit('total_label', T(126, 727, 28, '合计', '#0D223E', 700, 'center'))
unit('total_pct', T(311, 725, 26, '100%', '#17324E', 400, 'center'))
unit('total_h1', T(489, 706, 22, '加权现状评分', '#21324C', 500, 'center'))
unit('total_v1', T(487, 748, 36, '2.75', '#0E1F3C', 700, 'center'))
unit('total_h2', T(702, 706, 22, '加权目标评分', '#21324C', 500, 'center'))
unit('total_v2', T(702, 748, 36, '3.95', '#626E4B', 700, 'center'))
unit('total_h3', T(912, 705, 22, '差距', '#21324C', 500, 'center'))
unit('total_v3', T(913, 748, 36, '1.20', '#8F8177', 700, 'center'))

# ===== 4. 右面板 =====
sx0, sy0, sx1, sy1 = STRIP
strip = (f'<path d="M {sx0} {sy1} L {sx0} {sy0+10} Q {sx0} {sy0} {sx0+10} {sy0} '
         f'L {sx1-10} {sy0} Q {sx1} {sy0} {sx1} {sy0+10} L {sx1} {sy1} Z" fill="{STRIP_BG}"/>')
unit('panel_strip', strip)
unit('panel_title', f'<text x="1057" y="183" font-size="33" fill="#0E2440" font-weight="700" '
                    f'stroke="#0E2440" stroke-width="1.2">能力缺口差距排序</text>')
unit('panel_sub1', T(1687, 177, 21, '差距分值', '#22354E', 700, 'end'))
unit('panel_sub2', T(1687, 197, 17, '(目标-现状)', '#22354E', 400, 'end'))
unit('panel_vline', line(1206, 225, 1206, 703, PANEL_LINE, 2, 'butt'))

for i, (rank, name, val, bc, fc, fw) in enumerate(PBARS):
    cy = PBAR_CY[i]
    unit(f'p{i+1}_badge',
         rrect(1050, cy - 27, 54, 54, 12, fill=bc) +
         T(1077, cy + 11, 30, rank, '#FFFFFF', 700, 'center'))
    unit(f'p{i+1}_name', T(1128, cy + 10, 28, name, INK, 700))
    unit(f'p{i+1}_track', rrect(PBAR_X0, cy - 23.5, PBAR_W, 47, 3, fill=PTRACK))
    unit(f'p{i+1}_fill', rrect(PBAR_X0, cy - 23.5, fw, 47, 3, fill=fc))
    unit(f'p{i+1}_value', T(PVAL_X, cy + 11, 31, val, fc, 700, 'end'))

# ===== 5. 底部行动区 =====
unit('band_title', f'<text x="41" y="819" font-size="30" fill="#0E2440" font-weight="700" '
                   f'stroke="#0E2440" stroke-width="1.0">重点行动与优先事项</text>')
unit('band_note', T(1685, 819, 16, '分值与权重用于项目决策；非行业基准。', NOTE_C, 400, 'end'))

for i, (icx, icc, bx0, bx1, boxc, bdx, bdc, name, nx, dvx, txt, tx, tfs) in enumerate(ACTIONS):
    globals()['_CIRCLE_BG'] = icc
    unit(f'a{i+1}_icon', circle(icx, 882, 37.5, fill=icc) + ICONS[[2, 5, 4][i]](icx, 882, 58, '#FFFFFF'))
    unit(f'a{i+1}_box', rrect(bx0, 850, bx1 - bx0, 86, 14, fill=boxc))
    unit(f'a{i+1}_badge',
         rrect(bdx, 868, 48, 47, 10, fill=bdc) +
         T(bdx + 24, 901, 26, str(i + 1), '#FFFFFF', 700, 'center'))
    unit(f'a{i+1}_name', T(nx, 902, 27, name, INK, 700))
    unit(f'a{i+1}_div', line(dvx, 878, dvx, 906, '#A8A9AD', 2.5, 'butt'))
    unit(f'a{i+1}_text', T(tx, 902, tfs, txt, INK, 400))

# ===== 6. 水印 =====
unit('wm_icon', ic_wechat(1088, 901, 66, WM))
unit('wm_text', T(1134, 918, 50, '公众号·解决方案研究所', WM, 400))

# ---------- 输出 ----------
html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>准备度评分与能力缺口诊断</title>
<style>
  html,body {{ margin:0; padding:0; background:#FFFFFF; }}
  #stage {{ width:{W}px; height:{H}px; position:relative; }}
  svg {{ display:block; }}
  text {{ font-family:Noto Sans SC, Microsoft YaHei, PingFang SC, sans-serif; }}
</style>
</head>
<body>
<div id="stage">
<svg id="canvas" viewBox="0 0 {W} {H}" width="{W}" height="{H}" xmlns="http://www.w3.org/2000/svg">
  <rect x="0" y="0" width="{W}" height="{H}" fill="#FFFFFF"/>
{chr(10).join(units)}
</svg>
</div>
</body>
</html>
'''

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '能力缺口判断复刻.html')
with open(out, 'w', encoding='utf-8') as f:
    f.write(html)
print('written:', out, len(html), 'bytes')
