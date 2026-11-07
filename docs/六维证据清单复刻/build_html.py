#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
004《准备度评估的六维证据清单》— 交付物① HTML+SVG 复刻生成脚本
画布 1728x972（与原图 1:1），全真实 <text>，零位图；
每个可编辑最小单元为独立 <g class="unit" data-unit="...">。
共享几何（gear_pts/shield_pts/arc_pts）供 build_pptx.py 复用。
"""
import math
import os

W, H = 1728, 972

# ---------- 配色（原图采样） ----------
NAVY = '#26445C'      # 表头/评分标签/徽标1
TITLE_C = '#0D2036'   # 标题深藏青
INK = '#111827'       # 正文黑
GRAY = '#6B7280'      # 卡片副标题灰
SEP = '#DCE3E9'       # 表格分隔线
HSEP = '#3D5A73'      # 表头内列分隔
FOOT_BG = '#EFF3F7'   # 页脚条
WM = '#A9ABAE'        # 水印灰
ACCENTS = ['#27445B', '#687355', '#988270', '#7B748F', '#6C775A', '#8C8075']  # 行1-6 徽标/图标
EICONS = ['#26455C', '#687355', '#26455C', '#5A6B80', '#26455C', '#26455C']   # 证据列图标
SCORE_BG = ['#EFF2F6', '#F0F1F0', '#F4F3F0', '#F0F1F6', '#F1F3EF']            # 评分卡背景
SCORE_ACC = ['#8B8A97', '#687355', '#988270', '#7B748F', '#6C775A']           # 评分徽标

# ---------- 版面几何（原图实测） ----------
COLS = [12, 353, 810, 1335, 1716]           # 列边界
HEADER_Y, HEADER_H = 110, 55
ROWS_Y, ROW_B = 165, 766
ROW_H = (ROW_B - ROWS_Y) / 6
SCORE_Y, SCORE_H = 784, 104
FOOT_Y, FOOT_H = 900, 50
CARDS_X = [(188, 484), (492, 792), (800, 1112), (1120, 1428), (1436, 1708)]

ROWS = [
    ('战略', '业务目标和预算是否明确', ['目标与项目章程', '相关规划文件'], '经营负责人'),
    ('流程', '任务可界定且有人负责', ['流程图与工单', '角色与职责说明'], '业务'),
    ('数据', '质量权限与更新机制', ['样本与目录', '数据质量规则与更新机制'], '数据'),
    ('技术', '接口成本与监测能力', ['架构及压测', '接口清单与监测方案'], '科技'),
    ('人才', '岗位能力与采用意愿', ['访谈培训', '能力评估与采用情况'], '人力业务'),
    ('治理', '风险分级与审批退出', ['制度与台账', '风险清单与审批流程'], '风险法务'),
]
SCORES = [
    ('1', '无机制', '尚未建立相关机制'),
    ('2', '局部试验', '在部分范围开展试验'),
    ('3', '形成标准', '形成明确的标准与规范'),
    ('4', '跨部门复用', '在多部门/多场景复用'),
    ('5', '持续优化', '机制持续迭代与优化'),
]

# ---------- 共享几何（HTML 与 PPTX 共用） ----------
def gear_pts(cx, cy, s, teeth=8):
    """齿轮外轮廓多边形（直边近似，饱满齿身）"""
    R, r1 = s * 0.50, s * 0.385
    step = 360.0 / teeth
    pts = []
    for k in range(teeth):
        a = k * step
        for ang, rr in [(a - 11, R), (a + 11, R), (a + 18, r1), (a + step - 18, r1)]:
            rad = math.radians(ang)
            pts.append((cx + rr * math.cos(rad), cy + rr * math.sin(rad)))
    return pts

def shield_pts(cx, cy, s):
    """盾牌轮廓多边形"""
    return [(cx, cy - s * .44), (cx + s * .36, cy - s * .28), (cx + s * .36, cy + s * .06),
            (cx + s * .18, cy + s * .32), (cx, cy + s * .46), (cx - s * .18, cy + s * .32),
            (cx - s * .36, cy + s * .06), (cx - s * .36, cy - s * .28)]

def arc_pts(cx, cy, rx, ry, a0, a1, n=16):
    """椭圆弧采样点（角度制，0=右，90=下）"""
    pts = []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        pts.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
    return pts

# ---------- SVG 基元 ----------
def T(x, y, size, text, fill, weight=400, anchor='start', ls=None):
    """anchor: start/center/end（center 映射为 SVG 合法值 middle）"""
    a = {'start': 'start', 'center': 'middle', 'end': 'end'}[anchor]
    lsattr = f' letter-spacing="{ls}"' if ls else ''
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" '
            f'font-weight="{weight}" text-anchor="{a}"{lsattr}>{text}</text>')

def poly(pts, fill, extra=''):
    p = ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
    return f'<polygon points="{p}" fill="{fill}"{extra}/>'

def pline(pts, stroke, w, fill='none'):
    p = ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
    return f'<polyline points="{p}" fill="{fill}" stroke="{stroke}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>'

def rrect(x, y, w, h, rx, fill=None, stroke=None, sw=0):
    a = f' fill="{fill}"' if fill else ' fill="none"'
    b = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ''
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}"{a}{b}/>'

def circle(cx, cy, r, fill=None, stroke=None, sw=0):
    a = f' fill="{fill}"' if fill else ' fill="none"'
    b = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ''
    return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.2f}"{a}{b}/>'

def line(x1, y1, x2, y2, stroke, w, cap='round'):
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" '
            f'stroke-width="{w}" stroke-linecap="{cap}"/>')

# ---------- 图标（中心 cx,cy；盒尺寸 s） ----------
def ic_target(cx, cy, s, c):
    """战略：靶心 + 飞镖"""
    o = [circle(cx, cy, s * .46, stroke=c, sw=s * .10),
         circle(cx, cy, s * .27, stroke=c, sw=s * .09),
         circle(cx, cy, s * .08, fill=c)]
    x1, y1 = cx + s * .52, cy - s * .52
    o.append(line(x1, y1, cx + s * .06, cy - s * .06, c, s * .07))
    o.append(poly([(x1 + s * .10, y1 - s * .02), (x1 - s * .02, y1 + s * .10),
                   (x1 - s * .10, y1 - s * .10)], c))
    return ''.join(o)

def ic_gear(cx, cy, s, c):
    return poly(gear_pts(cx, cy, s), c) + circle(cx, cy, s * .115, fill='#FFFFFF')

def ic_database(cx, cy, s, c):
    """数据：线稿圆柱"""
    rx, ry = s * .40, s * .15
    top, bot = cy - s * .30, cy + s * .30
    o = [f'<ellipse cx="{cx}" cy="{top:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="none" stroke="{c}" stroke-width="{s*.085:.2f}"/>',
         pline(arc_pts(cx, top + s * .30, rx, ry, 0, 180), c, s * .085),
         pline(arc_pts(cx, top + s * .60, rx, ry, 0, 180), c, s * .085),
         line(cx - rx, top, cx - rx, bot, c, s * .085, cap='butt'),
         line(cx + rx, top, cx + rx, bot, c, s * .085, cap='butt')]
    return ''.join(o)

def ic_cloud(cx, cy, s, c):
    """技术：实心云（三圆+矩形并集）"""
    return (''.join([circle(cx - s * .22, cy + s * .04, s * .21, fill=c),
                     circle(cx + s * .02, cy - s * .12, s * .27, fill=c),
                     circle(cx + s * .26, cy + s * .02, s * .20, fill=c),
                     rrect(cx - s * .30, cy - s * .02, s * .72, s * .30, s * .12, fill=c)]))

def ic_people(cx, cy, s, c):
    """人才：双人实心"""
    def person(px, py, k):
        return (circle(px, py - s * .20 * k, s * .15 * k, fill=c) +
                rrect(px - s * .21 * k, py - s * .02 * k, s * .42 * k, s * .26 * k,
                      s * .13 * k, fill=c))
    return person(cx + s * .18, cy + s * .08, 0.82) + person(cx - s * .14, cy + s * .02, 1.0)

def ic_shield_check(cx, cy, s, c):
    chk = pline([(cx - s * .15, cy - s * .02), (cx - s * .04, cy + s * .12),
                 (cx + s * .18, cy - s * .16)], '#FFFFFF', s * .11)
    return poly(shield_pts(cx, cy, s), c) + chk

def ic_person_fill(cx, cy, s, c):
    """负责人：实心人形"""
    return (circle(cx, cy - s * .17, s * .16, fill=c) +
            f'<path d="M {cx - s*.30:.1f} {cy + s*.40:.1f} L {cx - s*.30:.1f} {cy + s*.30:.1f} '
            f'A {s*.30:.1f} {s*.30:.1f} 0 0 1 {cx + s*.30:.1f} {cy + s*.30:.1f} '
            f'L {cx + s*.30:.1f} {cy + s*.40:.1f} Z" fill="{c}"/>')

def ic_doc_base(cx, cy, s, c):
    """线稿文档底版（含折角）。返回 (主体path, 折角线, x0, y0, w, h)"""
    x0, y0 = cx - s * .36, cy - s * .44
    w, h = s * .72, s * .88
    f = s * .16
    d = (f'M {x0:.1f} {y0:.1f} L {x0 + w - f:.1f} {y0:.1f} L {x0 + w:.1f} {y0 + f:.1f} '
         f'L {x0 + w:.1f} {y0 + h:.1f} L {x0:.1f} {y0 + h:.1f} Z')
    fold = pline([(x0 + w - f, y0), (x0 + w - f, y0 + f), (x0 + w, y0 + f)], c, s * .07)
    body = (f'<path d="{d}" fill="none" stroke="{c}" stroke-width="{s*.085:.2f}" '
            f'stroke-linejoin="round"/>')
    return body, fold, x0, y0, w, h

def ic_doc_chart(cx, cy, s, c):
    base, fold, x0, y0, w, h = ic_doc_base(cx, cy, s, c)
    bw = s * .11
    bars = ''.join([rrect(x0 + w * .18, y0 + h * .52, bw, h * .30, 1, fill=c),
                    rrect(x0 + w * .40, y0 + h * .40, bw, h * .42, 1, fill=c),
                    rrect(x0 + w * .62, y0 + h * .28, bw, h * .54, 1, fill=c)])
    return base + fold + bars

def ic_doc_search(cx, cy, s, c):
    base, fold, x0, y0, w, h = ic_doc_base(cx, cy, s, c)
    lns = ''.join([line(x0 + w * .16, y0 + h * .20, x0 + w * .80, y0 + h * .20, c, s * .065, 'butt'),
                   line(x0 + w * .16, y0 + h * .34, x0 + w * .66, y0 + h * .34, c, s * .065, 'butt'),
                   line(x0 + w * .16, y0 + h * .48, x0 + w * .58, y0 + h * .48, c, s * .065, 'butt')])
    mg = (circle(cx + s * .20, cy + s * .22, s * .155, stroke=c, sw=s * .075) +
          line(cx + s * .31, cy + s * .33, cx + s * .42, cy + s * .44, c, s * .075))
    return base + fold + lns + mg

def ic_doc_shield(cx, cy, s, c):
    base, fold, x0, y0, w, h = ic_doc_base(cx, cy, s, c)
    lns = ''.join([line(x0 + w * .16, y0 + h * .22, x0 + w * .80, y0 + h * .22, c, s * .07, 'butt'),
                   line(x0 + w * .16, y0 + h * .38, x0 + w * .72, y0 + h * .38, c, s * .07, 'butt'),
                   line(x0 + w * .16, y0 + h * .54, x0 + w * .58, y0 + h * .54, c, s * .07, 'butt')])
    sh = poly(shield_pts(cx + s * .18, cy + s * .22, s * .42), c)
    chk = pline([(cx + s * .18 - s * .09, cy + s * .21), (cx + s * .18 - s * .02, cy + s * .29),
                 (cx + s * .18 + s * .12, cy + s * .12)], '#FFFFFF', s * .075)
    return base + fold + lns + sh + chk

def ic_flowchart(cx, cy, s, c):
    """流程证据：组织树（三方块连线）"""
    bs = s * .22
    top = (cx - bs / 2, cy - s * .40)
    bl_ = (cx - s * .36 - bs / 2, cy + s * .16)
    br_ = (cx + s * .36 - bs / 2, cy + s * .16)
    boxes = ''.join([rrect(top[0], top[1], bs, bs, 2.5, fill=c),
                     rrect(bl_[0], bl_[1], bs, bs, 2.5, fill=c),
                     rrect(br_[0], br_[1], bs, bs, 2.5, fill=c)])
    ln = ''.join([line(cx, top[1] + bs, cx, cy + s * .04, c, s * .06, 'butt'),
                  line(cx - s * .36 + bs / 2, cy + s * .04, cx + s * .36 - bs / 2, cy + s * .04, c, s * .06, 'butt'),
                  line(cx - s * .36 + bs / 2, cy + s * .04, cx - s * .36 + bs / 2, bl_[1], c, s * .06, 'butt'),
                  line(cx + s * .36 - bs / 2, cy + s * .04, cx + s * .36 - bs / 2, br_[1], c, s * .06, 'butt')])
    return boxes + ln

def ic_server(cx, cy, s, c):
    """技术证据：服务器堆（实心）"""
    o = []
    for yy in [-0.335, -0.02, 0.295]:
        ry = cy + s * yy
        o.append(rrect(cx - s * .40, ry, s * .80, s * .24, s * .05, fill=c))
        o.append(circle(cx - s * .26, ry + s * .12, s * .045, fill='#FFFFFF'))
        o.append(circle(cx - s * .13, ry + s * .12, s * .045, fill='#FFFFFF'))
        o.append(line(cx + s * .08, ry + s * .12, cx + s * .30, ry + s * .12, '#FFFFFF', s * .05, 'butt'))
    return ''.join(o)

def ic_presenter(cx, cy, s, c):
    """人才证据：人 + 展板"""
    bd = s * .58
    bx, by = cx + s * .06, cy - s * .36
    board = (rrect(bx, by, bd, s * .46, 2.5, stroke=c, sw=s * .07) +
             rrect(bx + s * .08, by + s * .20, s * .07, s * .16, 1, fill=c) +
             rrect(bx + s * .20, by + s * .12, s * .07, s * .24, 1, fill=c) +
             rrect(bx + s * .32, by + s * .24, s * .07, s * .12, 1, fill=c))
    man = (circle(cx - s * .26, cy - s * .18, s * .12, fill=c) +
           rrect(cx - s * .38, cy - s * .02, s * .24, s * .42, s * .10, fill=c) +
           line(cx - s * .14, cy + s * .02, bx + s * .02, by + s * .14, c, s * .055))
    return board + man

def ic_dockey(cx, cy, s, c):
    """页脚小图标：文档+勾"""
    x0, y0 = cx - s * .34, cy - s * .40
    w, h = s * .68, s * .80
    d = f'M {x0:.1f} {y0:.1f} L {x0+w:.1f} {y0:.1f} L {x0+w:.1f} {y0+h:.1f} L {x0:.1f} {y0+h:.1f} Z'
    return (f'<path d="{d}" fill="none" stroke="{c}" stroke-width="{s*.10:.2f}" stroke-linejoin="round"/>' +
            pline([(x0 + w * .22, y0 + h * .48), (x0 + w * .42, y0 + h * .68),
                   (x0 + w * .78, y0 + h * .28)], c, s * .10))

def ic_wechat(cx, cy, s, c):
    """微信双气泡（水印）"""
    o = [f'<ellipse cx="{cx - s*.14:.1f}" cy="{cy - s*.08:.1f}" rx="{s*.30:.1f}" ry="{s*.24:.1f}" fill="{c}"/>',
         poly([(cx - s * .30, cy + s * .06), (cx - s * .30, cy + s * .26),
               (cx - s * .12, cy + s * .12)], c),
         circle(cx - s * .22, cy - s * .12, s * .035, fill='#FFFFFF'),
         circle(cx - s * .06, cy - s * .12, s * .035, fill='#FFFFFF'),
         f'<ellipse cx="{cx + s*.22:.1f}" cy="{cy + s*.10:.1f}" rx="{s*.24:.1f}" ry="{s*.19:.1f}" fill="{c}"/>',
         poly([(cx + s * .34, cy + s * .20), (cx + s * .36, cy + s * .34),
               (cx + s * .20, cy + s * .24)], c),
         circle(cx + s * .16, cy + s * .06, s * .03, fill='#FFFFFF'),
         circle(cx + s * .29, cy + s * .06, s * .03, fill='#FFFFFF')]
    return ''.join(o)

# ---------- 组装 ----------
units = []

def unit(uid, inner):
    units.append(f'  <g id="{uid}" class="unit" data-unit="{uid}">\n    {inner}\n  </g>')

# 画布外框（圆角细边）
unit('frame', rrect(3, 3, W - 6, H - 6, 22, stroke='#E4E7EA', sw=2))

# 标题
unit('title', T(864, 79, 66, '准备度评估的六维证据清单', TITLE_C, 700, 'center'))

# 表头（圆角顶）
hdr = (f'<path d="M 12 {HEADER_Y+HEADER_H} L 12 {HEADER_Y+12} Q 12 {HEADER_Y} 22 {HEADER_Y} '
       f'L 1706 {HEADER_Y} Q 1716 {HEADER_Y} 1716 {HEADER_Y+12} L 1716 {HEADER_Y+HEADER_H} Z" '
       f'fill="{NAVY}"/>')
for cx_ in COLS[1:-1]:
    hdr += line(cx_, HEADER_Y + 4, cx_, HEADER_Y + HEADER_H - 4, HSEP, 2, 'butt')
hdr += T((COLS[0] + COLS[1]) / 2, 148, 28, '维度', '#FFFFFF', 700, 'center')
hdr += T((COLS[1] + COLS[2]) / 2, 148, 28, '关键问题', '#FFFFFF', 700, 'center')
hdr += T((COLS[2] + COLS[3]) / 2, 148, 28, '证据（示例）', '#FFFFFF', 700, 'center')
hdr += T((COLS[3] + COLS[4]) / 2, 148, 28, '负责人', '#FFFFFF', 700, 'center')
unit('header', hdr)

# 表格网格线
grid = ''
for i in range(1, 6):
    y = round(ROWS_Y + ROW_H * i, 1)
    grid += line(12, y, 1716, y, SEP, 2, 'butt')
for cx_ in COLS[1:-1]:
    grid += line(cx_, ROWS_Y, cx_, ROW_B, SEP, 2, 'butt')
unit('grid', grid)

# 六行内容
ICONS1 = [ic_target, ic_gear, ic_database, ic_cloud, ic_people, ic_shield_check]
ICONS3 = [ic_doc_chart, ic_flowchart, ic_doc_search, ic_server, ic_presenter, ic_doc_shield]

for i, (name, question, evids, owner) in enumerate(ROWS):
    top = ROWS_Y + ROW_H * i
    cy = top + ROW_H / 2
    acc = ACCENTS[i]
    unit(f'r{i+1}_badge',
         rrect(53, top + 8, 78, 78, 12, fill=acc) +
         T(92, top + 60, 40, str(i + 1), '#FFFFFF', 700, 'center'))
    unit(f'r{i+1}_icon', ICONS1[i](170, cy - 2, 52, acc))
    unit(f'r{i+1}_name', T(234, cy + 10, 30, name, INK, 700))
    unit(f'r{i+1}_question', T(394, cy + 9, 32, question, INK, 500))
    unit(f'r{i+1}_eicon', ICONS3[i](895, cy, 64, EICONS[i]))
    ev = ''
    for j, txt in enumerate(evids):
        by = top + (39 if j == 0 else 74)
        ev += circle(958, by - 9, 4.5, fill=NAVY) + T(975, by, 28, txt, INK, 400)
    unit(f'r{i+1}_evidence', ev)
    unit(f'r{i+1}_owner', ic_person_fill(1440, cy, 52, '#1C3B52') +
         T(1494, cy + 13, 30, owner, INK, 400))

# 评分五档
unit('score_label',
     rrect(20, 792, 152, 88, 10, fill=NAVY) +
     T(96, 848, 32, '评分五档', '#FFFFFF', 700, 'center'))
for i, (num, tit, sub) in enumerate(SCORES):
    x0, x1 = CARDS_X[i]
    card = rrect(x0, SCORE_Y, x1 - x0, SCORE_H, 10, fill=SCORE_BG[i])
    card += rrect(x0 + 14, 798, 62, 62, 12, fill=SCORE_ACC[i])
    card += T(x0 + 45, 841, 34, num, '#FFFFFF', 700, 'center')
    card += T(x0 + 103, 823, 26, tit, INK, 700)
    card += T(x0 + 103, 860, 19, sub, GRAY, 400)
    unit(f'score_card{i+1}', card)

# 页脚
unit('footer',
     rrect(12, FOOT_Y, 1698, FOOT_H, 6, fill=FOOT_BG) +
     ic_dockey(58, FOOT_Y + 25, 30, '#1F3A52') +
     T(92, 935, 25, '每项须证据支持，不以访谈印象替代验证。', INK, 400))
unit('watermark',
     ic_wechat(1074, 893, 62, WM) +
     T(1693, 923, 54, '公众号·解决方案研究所', WM, 700, 'end'))

# ---------- 输出 ----------
html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>准备度评估的六维证据清单</title>
<style>
  html,body {{ margin:0; padding:0; background:#FDFDFD; }}
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

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '六维证据清单复刻.html')
with open(out, 'w', encoding='utf-8') as f:
    f.write(html)
print('written:', out, len(html), 'bytes')
