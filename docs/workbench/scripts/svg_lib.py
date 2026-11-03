# -*- coding: utf-8 -*-
"""SVG 图标库：每个图标都是独立的最小 SVG 单元（g 元素，带 id）。
所有图标以 (cx, cy) 为中心、按给定尺寸 s 绘制，颜色可指定。
统一使用 currentColor 不方便逐个上色，故直接传 color。
"""

def _s(x, v):
    return f'{x:.1f}'.rstrip('0').rstrip('.')


# ============ 七列卡片大图标（约 54px） ============

def icon_brain(gid, cx, cy, s, color):
    """AI：大脑（两半球 + 纹路）"""
    w = s * 0.92; h = s
    x0 = cx - w / 2; y0 = cy - h / 2
    sw = s * 0.075
    p = f'''
<g id="{gid}" stroke="{color}" fill="none" stroke-width="{sw:.2f}" stroke-linecap="round" stroke-linejoin="round">
  <path d="M {cx:.1f},{y0 + h * .06:.1f}
           C {x0 + w * .30:.1f},{y0 - h * .02:.1f} {x0 + w * .16:.1f},{y0 + h * .22:.1f} {x0 + w * .22:.1f},{y0 + h * .30:.1f}
           C {x0 + w * .02:.1f},{y0 + h * .40:.1f} {x0 + w * .04:.1f},{y0 + h * .72:.1f} {x0 + w * .26:.1f},{y0 + h * .78:.1f}
           C {x0 + w * .28:.1f},{y0 + h * .98:.1f} {x0 + w * .55:.1f},{y0 + h * 1.04:.1f} {cx:.1f},{y0 + h * .92:.1f} Z"
        fill="{color}" fill-opacity=".14"/>
  <path d="M {cx:.1f},{y0 + h * .06:.1f}
           C {x0 + w * .70:.1f},{y0 - h * .02:.1f} {x0 + w * .84:.1f},{y0 + h * .22:.1f} {x0 + w * .78:.1f},{y0 + h * .30:.1f}
           C {x0 + w * .98:.1f},{y0 + h * .40:.1f} {x0 + w * .96:.1f},{y0 + h * .72:.1f} {x0 + w * .74:.1f},{y0 + h * .78:.1f}
           C {x0 + w * .72:.1f},{y0 + h * .98:.1f} {x0 + w * .45:.1f},{y0 + h * 1.04:.1f} {cx:.1f},{y0 + h * .92:.1f} Z"
        fill="{color}" fill-opacity=".14"/>
  <path d="M {cx:.1f},{y0 + h * .06:.1f} L {cx:.1f},{y0 + h * .92:.1f}"/>
  <path d="M {x0 + w * .26:.1f},{y0 + h * .30:.1f} q {w * .12:.1f},{h * .06:.1f} {w * .20:.1f},{-.02:.1f}"/>
  <path d="M {x0 + w * .22:.1f},{y0 + h * .56:.1f} q {w * .14:.1f},{.01:.1f} {w * .22:.1f},{h * .08:.1f}"/>
  <path d="M {x0 + w * .74:.1f},{y0 + h * .34:.1f} q {(-w * .12):.1f},{h * .05:.1f} {(-w * .20):.1f},{-.01:.1f}"/>
  <path d="M {x0 + w * .78:.1f},{y0 + h * .58:.1f} q {(-w * .13):.1f},{.02:.1f} {(-w * .21):.1f},{h * .09:.1f}"/>
</g>'''
    return p


def icon_chart(gid, cx, cy, s, color):
    """ML：柱状图（4 柱渐高）"""
    w = s * 0.9; h = s
    x0 = cx - w / 2; y0 = cy - h / 2
    sw = s * 0.08
    bw = w * 0.16
    hs = [0.34, 0.50, 0.66, 0.82]
    by = y0 + h * .84
    bars = ''.join(
        f'<rect x="{x0 + w * .04 + k * (bw + w * .075):.1f}" y="{by - h * v:.1f}" width="{bw:.1f}" height="{h * v:.1f}" rx="{bw * .3:.1f}"/>'
        for k, v in enumerate(hs))
    return f"""
<g id="{gid}" stroke="{color}" fill="none" stroke-width="{sw:.2f}" stroke-linecap="round">
  {bars}
  <path d="M {x0 + w * .04:.1f},{by:.1f} H {x0 + w * .86:.1f}"/>
</g>"""


def icon_network(gid, cx, cy, s, color):
    """DL：神经网络（中心节点 + 环绕节点）"""
    r_out = s * 0.40; r_n = s * 0.105; r_c = s * 0.14
    import math
    pts = []
    for k in range(6):
        a = math.radians(90 + k * 60)
        pts.append((cx + r_out * math.cos(a), cy - r_out * math.sin(a)))
    lines = ''.join(
        f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{px:.1f}" y2="{py:.1f}"/>' for px, py in pts)
    dots = ''.join(
        f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{r_n:.1f}" fill="{color}" stroke="none"/>' for px, py in pts)
    return f'''
<g id="{gid}" stroke="{color}" stroke-width="{s * .06:.2f}" fill="none" stroke-linecap="round">
  {lines}
  {dots}
  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r_c * .8:.1f}" fill="{color}" stroke="none"/>
</g>'''


def icon_sparkle(gid, cx, cy, s, color):
    """GenAI：四角星闪光（一大两小）"""
    def star(x, y, r):
        r2 = r * 0.36
        return (f'M {x:.1f},{y - r:.1f} C {x + r2 * .2:.1f},{y - r2:.1f} {x + r2:.1f},{y - r2 * .2:.1f} '
                f'{x + r:.1f},{y:.1f} C {x + r2:.1f},{y + r2 * .2:.1f} {x + r2 * .2:.1f},{y + r2:.1f} '
                f'{x:.1f},{y + r:.1f} C {x - r2 * .2:.1f},{y + r2:.1f} {x - r2:.1f},{y + r2 * .2:.1f} '
                f'{x - r:.1f},{y:.1f} C {x - r2:.1f},{y - r2 * .2:.1f} {x - r2 * .2:.1f},{y - r2:.1f} Z')
    return f'''
<g id="{gid}" fill="{color}">
  <path d="{star(cx - s * .02, cy + s * .04, s * .34)}"/>
  <path d="{star(cx + s * .34, cy - s * .30, s * .15)}"/>
  <path d="{star(cx + s * .26, cy + s * .34, s * .10)}"/>
</g>'''


def icon_bubble(gid, cx, cy, s, color):
    """LLMs：对话气泡 + 横线"""
    w = s; h = s * .78
    x0 = cx - w / 2; y0 = cy - h / 2 - s * .04
    sw = s * .08
    return f'''
<g id="{gid}" fill="none" stroke="{color}" stroke-width="{sw:.2f}" stroke-linecap="round" stroke-linejoin="round">
  <path d="M {x0:.1f},{y0:.1f} H {x0 + w:.1f} V {y0 + h * .68:.1f} H {x0 + w * .38:.1f} L {x0 + w * .22:.1f},{y0 + h * .92:.1f} V {y0 + h * .68:.1f} H {x0:.1f} Z"
        fill="{color}" fill-opacity=".13"/>
  <line x1="{x0 + w * .22:.1f}" y1="{y0 + h * .30:.1f}" x2="{x0 + w * .78:.1f}" y2="{y0 + h * .30:.1f}"/>
  <line x1="{x0 + w * .22:.1f}" y1="{y0 + h * .48:.1f}" x2="{x0 + w * .60:.1f}" y2="{y0 + h * .48:.1f}"/>
</g>'''


def icon_database(gid, cx, cy, s, color):
    """RAG：数据库圆柱（3 层）"""
    w = s * .84; h = s
    x0 = cx - w / 2; y0 = cy - h / 2
    ry = s * .13; sw = s * .075
    return f'''
<g id="{gid}" fill="none" stroke="{color}" stroke-width="{sw:.2f}">
  <ellipse cx="{cx:.1f}" cy="{y0 + ry:.1f}" rx="{w / 2:.1f}" ry="{ry:.1f}"/>
  <path d="M {x0:.1f},{y0 + ry:.1f} V {y0 + h - ry:.1f}"/>
  <path d="M {x0 + w:.1f},{y0 + ry:.1f} V {y0 + h - ry:.1f}"/>
  <path d="M {x0:.1f},{y0 + h * .48:.1f} A {w / 2:.1f} {ry:.1f} 0 0 0 {x0 + w:.1f},{y0 + h * .48:.1f}"/>
  <path d="M {x0:.1f},{y0 + h - ry:.1f} A {w / 2:.1f} {ry:.1f} 0 0 0 {x0 + w:.1f},{y0 + h - ry:.1f}"/>
</g>'''


def icon_robot(gid, cx, cy, s, color):
    """Agentic AI：机器人头"""
    w = s * .92; h = s * .74
    x0 = cx - w / 2; y0 = cy - h / 2 + s * .06
    sw = s * .07
    return f'''
<g id="{gid}" fill="none" stroke="{color}" stroke-width="{sw:.2f}" stroke-linecap="round">
  <line x1="{cx:.1f}" y1="{y0 - s * .10:.1f}" x2="{cx:.1f}" y2="{y0:.1f}"/>
  <circle cx="{cx:.1f}" cy="{y0 - s * .13:.1f}" r="{s * .055:.1f}" fill="{color}" stroke="none"/>
  <rect x="{x0:.1f}" y="{y0:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{s * .16:.1f}" fill="{color}" fill-opacity=".12"/>
  <circle cx="{cx - w * .22:.1f}" cy="{y0 + h * .45:.1f}" r="{s * .075:.1f}" fill="{color}" stroke="none"/>
  <circle cx="{cx + w * .22:.1f}" cy="{y0 + h * .45:.1f}" r="{s * .075:.1f}" fill="{color}" stroke="none"/>
  <path d="M {cx - w * .16:.1f},{y0 + h * .74:.1f} Q {cx:.1f},{y0 + h * .86:.1f} {cx + w * .16:.1f},{y0 + h * .74:.1f}"/>
  <line x1="{x0 - s * .10:.1f}" y1="{y0 + h * .45:.1f}" x2="{x0:.1f}" y2="{y0 + h * .45:.1f}"/>
  <line x1="{x0 + w:.1f}" y1="{y0 + h * .45:.1f}" x2="{x0 + w + s * .10:.1f}" y2="{y0 + h * .45:.1f}"/>
</g>'''


# ============ 列表小图标（约 15px，线性） ============

def icon_gear(gid, cx, cy, s, color):
    import math
    teeth = ''.join(
        f'<line x1="{cx + s * .38 * math.cos(math.radians(a)):.1f}" y1="{cy + s * .38 * math.sin(math.radians(a)):.1f}" '
        f'x2="{cx + s * .50 * math.cos(math.radians(a)):.1f}" y2="{cy + s * .50 * math.sin(math.radians(a)):.1f}"/>'
        for a in range(0, 360, 60))
    return (f'<g id="{gid}" stroke="{color}" stroke-width="{s * .13:.2f}" fill="none" stroke-linecap="round">'
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{s * .30:.1f}"/>{teeth}</g>')


def icon_arm(gid, cx, cy, s, color):
    return (f'<g id="{gid}" stroke="{color}" fill="none" stroke-width="{s * .12:.2f}" stroke-linecap="round">'
            f'<path d="M {cx - s * .42:.1f},{cy + s * .40:.1f} H {cx + s * .42:.1f}"/>'
            f'<path d="M {cx - s * .28:.1f},{cy + s * .40:.1f} L {cx - s * .05:.1f},{cy - s * .05:.1f} L {cx + s * .28:.1f},{cy - s * .30:.1f}"/>'
            f'<circle cx="{cx - s * .05:.1f}" cy="{cy - s * .05:.1f}" r="{s * .10:.1f}" fill="{color}" stroke="none"/>'
            f'<circle cx="{cx + s * .32:.1f}" cy="{cy - s * .33:.1f}" r="{s * .12:.1f}"/></g>')


def icon_car(gid, cx, cy, s, color):
    return (f'<g id="{gid}" stroke="{color}" fill="none" stroke-width="{s * .11:.2f}" stroke-linecap="round" stroke-linejoin="round">'
            f'<path d="M {cx - s * .46:.1f},{cy + s * .10:.1f} L {cx - s * .32:.1f},{cy - s * .16:.1f} H {cx + s * .32:.1f} L {cx + s * .46:.1f},{cy + s * .10:.1f} V {cy + s * .30:.1f} H {cx - s * .46:.1f} Z"/>'
            f'<circle cx="{cx - s * .26:.1f}" cy="{cy + s * .34:.1f}" r="{s * .11:.1f}"/>'
            f'<circle cx="{cx + s * .26:.1f}" cy="{cy + s * .34:.1f}" r="{s * .11:.1f}"/></g>')


def icon_mail(gid, cx, cy, s, color):
    w = s * .88; h = s * .64
    return (f'<g id="{gid}" stroke="{color}" fill="none" stroke-width="{s * .11:.2f}" stroke-linejoin="round">'
            f'<rect x="{cx - w / 2:.1f}" y="{cy - h / 2:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{s * .08:.1f}"/>'
            f'<path d="M {cx - w / 2:.1f},{cy - h / 2:.1f} L {cx:.1f},{cy + h * .10:.1f} L {cx + w / 2:.1f},{cy - h / 2:.1f}"/></g>')


def icon_doc(gid, cx, cy, s, color, lines=3):
    w = s * .68; h = s * .84
    x0 = cx - w / 2; y0 = cy - h / 2
    ls = ''.join(
        f'<line x1="{x0 + w * .22:.1f}" y1="{y0 + h * (.28 + k * .20):.1f}" x2="{x0 + w * .78:.1f}" y2="{y0 + h * (.28 + k * .20):.1f}"/>'
        for k in range(lines))
    return (f'<g id="{gid}" stroke="{color}" fill="none" stroke-width="{s * .10:.2f}" stroke-linecap="round" stroke-linejoin="round">'
            f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{s * .08:.1f}"/>{ls}</g>')


def icon_shield(gid, cx, cy, s, color, check=False):
    c = (f'<path d="M {cx - s * .14:.1f},{cy:.1f} L {cx - s * .03:.1f},{cy + s * .13:.1f} L {cx + s * .16:.1f},{cy - s * .12:.1f}"/>'
         if check else '')
    return (f'<g id="{gid}" stroke="{color}" fill="none" stroke-width="{s * .11:.2f}" stroke-linecap="round" stroke-linejoin="round">'
            f'<path d="M {cx:.1f},{cy - s * .42:.1f} L {cx + s * .34:.1f},{cy - s * .28:.1f} V {cy + s * .04:.1f} '
            f'C {cx + s * .34:.1f},{cy + s * .26:.1f} {cx + s * .16:.1f},{cy + s * .40:.1f} {cx:.1f},{cy + s * .46:.1f} '
            f'C {cx - s * .16:.1f},{cy + s * .40:.1f} {cx - s * .34:.1f},{cy + s * .26:.1f} {cx - s * .34:.1f},{cy + s * .04:.1f} '
            f'V {cy - s * .28:.1f} Z"/>{c}</g>')


def icon_image(gid, cx, cy, s, color):
    w = s * .84; h = s * .68
    x0 = cx - w / 2; y0 = cy - h / 2
    return (f'<g id="{gid}" stroke="{color}" fill="none" stroke-width="{s * .10:.2f}" stroke-linecap="round" stroke-linejoin="round">'
            f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{s * .08:.1f}"/>'
            f'<circle cx="{x0 + w * .30:.1f}" cy="{y0 + h * .32:.1f}" r="{s * .07:.1f}"/>'
            f'<path d="M {x0:.1f},{y0 + h * .78:.1f} L {x0 + w * .34:.1f},{y0 + h * .46:.1f} L {x0 + w * .62:.1f},{y0 + h * .72:.1f} L {x0 + w * .80:.1f},{y0 + h * .56:.1f} L {x0 + w:.1f},{y0 + h * .74:.1f}"/></g>')


def icon_mic(gid, cx, cy, s, color):
    return (f'<g id="{gid}" stroke="{color}" fill="none" stroke-width="{s * .10:.2f}" stroke-linecap="round">'
            f'<rect x="{cx - s * .13:.1f}" y="{cy - s * .44:.1f}" width="{s * .26:.1f}" height="{s * .46:.1f}" rx="{s * .13:.1f}"/>'
            f'<path d="M {cx - s * .28:.1f},{cy + s * .02:.1f} A {s * .28:.1f} {s * .28:.1f} 0 0 0 {cx + s * .28:.1f},{cy + s * .02:.1f}"/>'
            f'<line x1="{cx:.1f}" y1="{cy + s * .30:.1f}" x2="{cx:.1f}" y2="{cy + s * .44:.1f}"/></g>')


def icon_music(gid, cx, cy, s, color):
    return (f'<g id="{gid}" stroke="{color}" fill="none" stroke-width="{s * .11:.2f}" stroke-linecap="round">'
            f'<path d="M {cx + s * .10:.1f},{cy - s * .38:.1f} V {cy + s * .22:.1f}"/>'
            f'<path d="M {cx + s * .10:.1f},{cy - s * .38:.1f} L {cx + s * .38:.1f},{cy - s * .30:.1f}"/>'
            f'<circle cx="{cx - s * .04:.1f}" cy="{cy + s * .24:.1f}" r="{s * .14:.1f}"/></g>')


def icon_video(gid, cx, cy, s, color):
    w = s * .84; h = s * .66
    return (f'<g id="{gid}" stroke="{color}" fill="none" stroke-width="{s * .10:.2f}" stroke-linejoin="round">'
            f'<rect x="{cx - w / 2:.1f}" y="{cy - h / 2:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{s * .12:.1f}"/>'
            f'<path d="M {cx - s * .07:.1f},{cy - s * .14:.1f} L {cx + s * .16:.1f},{cy:.1f} L {cx - s * .07:.1f},{cy + s * .14:.1f} Z" fill="{color}" stroke="none"/></g>')


def icon_person(gid, cx, cy, s, color):
    return (f'<g id="{gid}" stroke="{color}" fill="none" stroke-width="{s * .11:.2f}" stroke-linecap="round">'
            f'<circle cx="{cx:.1f}" cy="{cy - s * .16:.1f}" r="{s * .18:.1f}"/>'
            f'<path d="M {cx - s * .32:.1f},{cy + s * .40:.1f} C {cx - s * .32:.1f},{cy + s * .10:.1f} {cx + s * .32:.1f},{cy + s * .10:.1f} {cx + s * .32:.1f},{cy + s * .40:.1f}"/></g>')


def icon_monitor(gid, cx, cy, s, color):
    w = s * .84; h = s * .58
    return (f'<g id="{gid}" stroke="{color}" fill="none" stroke-width="{s * .10:.2f}" stroke-linecap="round" stroke-linejoin="round">'
            f'<rect x="{cx - w / 2:.1f}" y="{cy - h / 2 - s * .06:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{s * .08:.1f}"/>'
            f'<line x1="{cx:.1f}" y1="{cy + h / 2 - s * .06:.1f}" x2="{cx:.1f}" y2="{cy + s * .34:.1f}"/>'
            f'<line x1="{cx - s * .20:.1f}" y1="{cy + s * .36:.1f}" x2="{cx + s * .20:.1f}" y2="{cy + s * .36:.1f}"/></g>')


def icon_fork(gid, cx, cy, s, color):
    return (f'<g id="{gid}" stroke="{color}" fill="none" stroke-width="{s * .11:.2f}" stroke-linecap="round">'
            f'<circle cx="{cx - s * .28:.1f}" cy="{cy - s * .28:.1f}" r="{s * .11:.1f}"/>'
            f'<circle cx="{cx + s * .28:.1f}" cy="{cy - s * .28:.1f}" r="{s * .11:.1f}"/>'
            f'<circle cx="{cx:.1f}" cy="{cy + s * .30:.1f}" r="{s * .11:.1f}"/>'
            f'<path d="M {cx - s * .20:.1f},{cy - s * .20:.1f} L {cx - s * .06:.1f},{cy + s * .22:.1f}"/>'
            f'<path d="M {cx + s * .20:.1f},{cy - s * .20:.1f} L {cx + s * .06:.1f},{cy + s * .22:.1f}"/></g>')


def icon_bot_sm(gid, cx, cy, s, color):
    w = s * .74; h = s * .56
    return (f'<g id="{gid}" stroke="{color}" fill="none" stroke-width="{s * .10:.2f}" stroke-linecap="round">'
            f'<line x1="{cx:.1f}" y1="{cy - s * .38:.1f}" x2="{cx:.1f}" y2="{cy - h / 2:.1f}"/>'
            f'<circle cx="{cx:.1f}" cy="{cy - s * .42:.1f}" r="{s * .06:.1f}" fill="{color}" stroke="none"/>'
            f'<rect x="{cx - w / 2:.1f}" y="{cy - h / 2:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{s * .12:.1f}"/>'
            f'<circle cx="{cx - w * .20:.1f}" cy="{cy:.1f}" r="{s * .07:.1f}" fill="{color}" stroke="none"/>'
            f'<circle cx="{cx + w * .20:.1f}" cy="{cy:.1f}" r="{s * .07:.1f}" fill="{color}" stroke="none"/></g>')


# ============ 特定功能图标 ============

def icon_bulb(gid, cx, cy, s, color, bg):
    """核心观点：灯泡（圆底）"""
    r = s / 2
    return (f'<g id="{gid}">'
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{bg}"/>'
            f'<g stroke="{color}" fill="none" stroke-width="{s * .055:.2f}" stroke-linecap="round">'
            f'<circle cx="{cx:.1f}" cy="{cy - s * .06:.1f}" r="{s * .17:.1f}"/>'
            f'<path d="M {cx - s * .08:.1f},{cy + s * .16:.1f} V {cy + s * .24:.1f} H {cx + s * .08:.1f} V {cy + s * .16:.1f}"/>'
            f'<line x1="{cx:.1f}" y1="{cy - s * .34:.1f}" x2="{cx:.1f}" y2="{cy - s * .40:.1f}"/>'
            f'<line x1="{cx - s * .24:.1f}" y1="{cy - s * .26:.1f}" x2="{cx - s * .29:.1f}" y2="{cy - s * .31:.1f}"/>'
            f'<line x1="{cx + s * .24:.1f}" y1="{cy - s * .26:.1f}" x2="{cx + s * .29:.1f}" y2="{cy - s * .31:.1f}"/>'
            f'</g></g>')


def icon_check(gid, cx, cy, r, color):
    """绿色圆勾"""
    return (f'<g id="{gid}">'
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{color}"/>'
            f'<path d="M {cx - r * .45:.1f},{cy:.1f} L {cx - r * .10:.1f},{cy + r * .35:.1f} L {cx + r * .48:.1f},{cy - r * .32:.1f}" '
            f'stroke="#FFFFFF" stroke-width="{r * .30:.2f}" fill="none" stroke-linecap="round" stroke-linejoin="round"/></g>')


def icon_media(gid, cx, cy, s, c1, c2, c3):
    """多模态：图片 + 声波 + 播放"""
    u = s
    return (f'<g id="{gid}">'
            + icon_image(f'{gid}-img', cx - u * .80, cy, u * .68, c1).replace(f'id="{gid}-img" ', f'id="{gid}-img" opacity="1" ')
            + f'<g stroke="{c2}" stroke-width="{u * .055:.2f}" stroke-linecap="round" fill="none">'
            + ''.join(
                f'<line x1="{cx - u * .10 + k * u * .075:.1f}" y1="{cy - (u * .16 if k % 2 == 0 else u * .26):.1f}" '
                f'x2="{cx - u * .10 + k * u * .075:.1f}" y2="{cy + (u * .16 if k % 2 == 0 else u * .26):.1f}"/>'
                for k in range(5))
            + '</g>'
            + f'<circle cx="{cx + u * .52:.1f}" cy="{cy:.1f}" r="{u * .24:.1f}" fill="{c3}"/>'
            + f'<path d="M {cx + u * .46:.1f},{cy - u * .10:.1f} L {cx + u * .64:.1f},{cy:.1f} L {cx + u * .46:.1f},{cy + u * .10:.1f} Z" fill="#FFFFFF"/>'
            + '</g>')


def icon_db_plus(gid, cx, cy, s, c1, c2):
    """数据库 + 加号"""
    u = s
    db = icon_database(f'{gid}-db', cx - u * .16, cy, u * .78, c1).replace(
        f'id="{gid}-db" ', f'id="{gid}-db" ')
    return (f'<g id="{gid}">{db}'
            f'<g stroke="{c2}" stroke-width="{u * .10:.2f}" stroke-linecap="round">'
            f'<line x1="{cx + u * .40:.1f}" y1="{cy - u * .16:.1f}" x2="{cx + u * .40:.1f}" y2="{cy + u * .16:.1f}"/>'
            f'<line x1="{cx + u * .22:.1f}" y1="{cy:.1f}" x2="{cx + u * .58:.1f}" y2="{cy:.1f}"/></g></g>')


def icon_sliders(gid, cx, cy, s, color):
    """滑块（微调）"""
    u = s
    return (f'<g id="{gid}" stroke="{color}" stroke-width="{u * .075:.2f}" stroke-linecap="round" fill="none">'
            f'<line x1="{cx - u * .36:.1f}" y1="{cy - u * .18:.1f}" x2="{cx + u * .36:.1f}" y2="{cy - u * .18:.1f}"/>'
            f'<line x1="{cx - u * .36:.1f}" y1="{cy + u * .14:.1f}" x2="{cx + u * .36:.1f}" y2="{cy + u * .14:.1f}"/>'
            f'<circle cx="{cx - u * .10:.1f}" cy="{cy - u * .18:.1f}" r="{u * .10:.1f}" fill="#FFFFFF"/>'
            f'<circle cx="{cx + u * .16:.1f}" cy="{cy + u * .14:.1f}" r="{u * .10:.1f}" fill="#FFFFFF"/></g>')


def icon_chat_dots(gid, cx, cy, s, color):
    """气泡 + 三点（提示工程）"""
    u = s
    return (f'<g id="{gid}">'
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{u * .30:.1f}" fill="{color}"/>'
            f'<path d="M {cx - u * .16:.1f},{cy + u * .24:.1f} L {cx - u * .24:.1f},{cy + u * .40:.1f} L {cx - u * .04:.1f},{cy + u * .30:.1f} Z" fill="{color}"/>'
            + ''.join(f'<circle cx="{cx - u * .12 + k * u * .12:.1f}" cy="{cy:.1f}" r="{u * .035:.1f}" fill="#FFFFFF"/>' for k in range(3))
            + '</g>')


def icon_shield_check(gid, cx, cy, s, color, bg=None):
    """盾牌勾（可带底色）"""
    u = s
    base = f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{u * .5:.1f}" fill="{bg}"/>' if bg else ''
    return (f'<g id="{gid}">{base}'
            f'<path d="M {cx:.1f},{cy - u * .40:.1f} L {cx + u * .30:.1f},{cy - u * .27:.1f} V {cy + u * .02:.1f} '
            f'C {cx + u * .30:.1f},{cy + u * .22:.1f} {cx + u * .15:.1f},{cy + u * .34:.1f} {cx:.1f},{cy + u * .40:.1f} '
            f'C {cx - u * .15:.1f},{cy + u * .34:.1f} {cx - u * .30:.1f},{cy + u * .22:.1f} {cx - u * .30:.1f},{cy + u * .02:.1f} '
            f'V {cy - u * .27:.1f} Z" fill="{color}"/>'
            f'<path d="M {cx - u * .13:.1f},{cy - u * .02:.1f} L {cx - u * .03:.1f},{cy + u * .10:.1f} L {cx + u * .16:.1f},{cy - u * .12:.1f}" '
            f'stroke="#FFFFFF" stroke-width="{u * .07:.2f}" fill="none" stroke-linecap="round" stroke-linejoin="round"/></g>')


def icon_headset(gid, cx, cy, s, color):
    u = s
    return (f'<g id="{gid}" stroke="{color}" fill="none" stroke-width="{u * .09:.2f}" stroke-linecap="round">'
            f'<path d="M {cx - u * .30:.1f},{cy + u * .06:.1f} A {u * .30:.1f} {u * .30:.1f} 0 0 1 {cx + u * .30:.1f},{cy + u * .06:.1f}"/>'
            f'<rect x="{cx - u * .38:.1f}" y="{cy + u * .02:.1f}" width="{u * .14:.1f}" height="{u * .24:.1f}" rx="{u * .06:.1f}"/>'
            f'<rect x="{cx + u * .24:.1f}" y="{cy + u * .02:.1f}" width="{u * .14:.1f}" height="{u * .24:.1f}" rx="{u * .06:.1f}"/>'
            f'<path d="M {cx + u * .31:.1f},{cy + u * .26:.1f} Q {cx + u * .31:.1f},{cy + u * .40:.1f} {cx + u * .10:.1f},{cy + u * .40:.1f}"/></g>')


def icon_excl_solid(gid, cx, cy, r, color):
    """实心圆感叹号（红）"""
    return (f'<g id="{gid}"><circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{color}"/>'
            f'<line x1="{cx:.1f}" y1="{cy - r * .48:.1f}" x2="{cx:.1f}" y2="{cy + r * .10:.1f}" stroke="#FFFFFF" stroke-width="{r * .22:.2f}" stroke-linecap="round"/>'
            f'<circle cx="{cx:.1f}" cy="{cy + r * .45:.1f}" r="{r * .13:.1f}" fill="#FFFFFF"/></g>')


def icon_excl_ring(gid, cx, cy, r, color):
    """描边圆感叹号（红）"""
    return (f'<g id="{gid}"><circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r * .92:.1f}" fill="#FFFFFF" stroke="{color}" stroke-width="{r * .16:.2f}"/>'
            f'<line x1="{cx:.1f}" y1="{cy - r * .44:.1f}" x2="{cx:.1f}" y2="{cy + r * .08:.1f}" stroke="{color}" stroke-width="{r * .20:.2f}" stroke-linecap="round"/>'
            f'<circle cx="{cx:.1f}" cy="{cy + r * .42:.1f}" r="{r * .12:.1f}" fill="{color}"/></g>')


def icon_spark_deco(gid, cx, cy, s, color):
    """装饰闪光（四角细星）"""
    u = s
    return (f'<g id="{gid}" fill="{color}">'
            f'<path d="M {cx:.1f},{cy - u * .5:.1f} L {cx + u * .09:.1f},{cy - u * .09:.1f} L {cx + u * .5:.1f},{cy:.1f} '
            f'L {cx + u * .09:.1f},{cy + u * .09:.1f} L {cx:.1f},{cy + u * .5:.1f} L {cx - u * .09:.1f},{cy + u * .09:.1f} '
            f'L {cx - u * .5:.1f},{cy:.1f} L {cx - u * .09:.1f},{cy - u * .09:.1f} Z"/></g>')


# 列表小图标注册表
SMALL_ICONS = {
    'gear': icon_gear, 'arm': icon_arm, 'car': icon_car, 'mail': icon_mail,
    'doc': icon_doc, 'shield': icon_shield, 'image': icon_image, 'mic': icon_mic,
    'music': icon_music, 'video': icon_video, 'person': icon_person,
    'monitor': icon_monitor, 'fork': icon_fork, 'bot': icon_bot_sm,
    'bubble': lambda gid, cx, cy, s, c: icon_bubble(gid, cx, cy, s, c),
    'db': lambda gid, cx, cy, s, c: icon_database(gid, cx, cy, s, c),
}
