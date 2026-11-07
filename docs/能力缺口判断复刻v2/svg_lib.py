#!/usr/bin/env python3
"""SVG 组件库 —— 每个组件返回带 id 的独立 <g> 最小单元（全矢量，无位图）"""

def esc(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def text(id, x, y, s, size, weight=400, color='#253E56', anchor='start', spacing=None, opacity=None):
    sp = f' letter-spacing="{spacing}"' if spacing else ''
    op = f' opacity="{opacity}"' if opacity else ''
    return (f'<text id="{id}" x="{x}" y="{y}" font-family="Noto Sans SC, sans-serif" '
            f'font-size="{size}" font-weight="{weight}" fill="{color}" text-anchor="{anchor}"{sp}{op}>{esc(s)}</text>')

def rrect(id, x, y, w, h, r, fill, stroke=None, sw=0, opacity=None):
    st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ''
    op = f' opacity="{opacity}"' if opacity else ''
    return f'<rect id="{id}" x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}"{st}{op}/>'

def hbar(id, x, y, w, h, fill, r=2):
    return f'<rect id="{id}" x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}"/>'

def circle(id, cx, cy, r, fill):
    return f'<circle id="{id}" cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"/>'

# ---------- 图标（白色 glyph，画在以 (0,0) 为圆心的局部坐标系，调用方 translate） ----------

def icon_target(id, r=27, sw=2.6):
    """战略：靶心 + 右上箭头（带箭羽）"""
    return (f'<g id="{id}">'
            f'<circle cx="0" cy="0" r="{r*0.60}" fill="none" stroke="#FFFFFF" stroke-width="{sw}"/>'
            f'<circle cx="0" cy="0" r="{r*0.33}" fill="none" stroke="#FFFFFF" stroke-width="{sw}"/>'
            f'<circle cx="0" cy="0" r="{r*0.10}" fill="#FFFFFF"/>'
            f'<line x1="{r*0.08}" y1="{-r*0.08}" x2="{r*0.72}" y2="{-r*0.72}" stroke="#FFFFFF" stroke-width="{sw+0.6}" stroke-linecap="round"/>'
            f'<line x1="{r*0.44}" y1="{-r*0.88}" x2="{r*0.66}" y2="{-r*0.66}" stroke="#FFFFFF" stroke-width="{sw}" stroke-linecap="round"/>'
            f'<line x1="{r*0.66}" y1="{-r*0.98}" x2="{r*0.88}" y2="{-r*0.76}" stroke="#FFFFFF" stroke-width="{sw}" stroke-linecap="round"/>'
            f'</g>')

def icon_gear(id, r=27, sw=2.6):
    """流程：粗短齿齿轮 + 中心孔"""
    teeth = []
    for k in range(8):
        a = k * 45
        teeth.append(f'<rect x="-{r*0.16:.2f}" y="-{r*0.74:.2f}" width="{r*0.32:.2f}" height="{r*0.24:.2f}" rx="{r*0.05:.2f}" fill="#FFFFFF" transform="rotate({a})"/>')
    return (f'<g id="{id}">' + ''.join(teeth) +
            f'<circle cx="0" cy="0" r="{r*0.54:.2f}" fill="none" stroke="#FFFFFF" stroke-width="{r*0.26:.2f}"/>'
            f'<circle cx="0" cy="0" r="{r*0.15:.2f}" fill="#FFFFFF"/>'
            f'</g>')

def icon_db(id, r=27, bg='#7A6853'):
    """数据：空心轮廓圆柱（描边式）"""
    return (f'<g id="{id}">'
            f'<ellipse cx="0" cy="{-r*0.34}" rx="{r*0.62}" ry="{r*0.26}" fill="none" stroke="#FFFFFF" stroke-width="3"/>'
            f'<path d="M {-r*0.62} {-r*0.34} L {-r*0.62} {r*0.34} A {r*0.62} {r*0.26} 0 0 0 {r*0.62} {r*0.34} '
            f'L {r*0.62} {-r*0.34}" fill="none" stroke="#FFFFFF" stroke-width="3"/>'
            f'<path d="M {-r*0.62} {r*0.02} A {r*0.62} {r*0.26} 0 0 0 {r*0.62} {r*0.02}" fill="none" stroke="#FFFFFF" stroke-width="3"/>'
            f'</g>')

def icon_laptop(id, r=27, sw=2.6):
    """技术：笔记本（宽屏）"""
    return (f'<g id="{id}">'
            f'<rect x="{-r*0.62}" y="{-r*0.54}" width="{r*1.24}" height="{r*0.76}" rx="{r*0.08}" fill="none" stroke="#FFFFFF" stroke-width="{sw}"/>'
            f'<path d="M {-r*0.80} {r*0.44} L {r*0.80} {r*0.44} L {r*0.64} {r*0.20} L {-r*0.64} {r*0.20} Z" fill="#FFFFFF"/>'
            f'</g>')

def icon_people(id, r=27):
    """人才：双人（前大后小）"""
    return (f'<g id="{id}">'
            f'<circle cx="{r*0.34}" cy="{-r*0.34}" r="{r*0.21}" fill="#FFFFFF"/>'
            f'<path d="M {r*0.06} {r*0.30} A {r*0.34} {r*0.34} 0 0 1 {r*0.34} {-r*0.08} A {r*0.34} {r*0.34} 0 0 1 {r*0.62} {r*0.30} Z" fill="#FFFFFF"/>'
            f'<circle cx="{-r*0.26}" cy="{-r*0.26}" r="{r*0.27}" fill="#FFFFFF"/>'
            f'<path d="M {-r*0.68} {r*0.48} A {r*0.44} {r*0.44} 0 0 1 {-r*0.26} {-r*0.02} A {r*0.44} {r*0.44} 0 0 1 {r*0.16} {r*0.48} Z" fill="#FFFFFF"/>'
            f'</g>')

def icon_shield(id, r=27, sw=2.6):
    """治理：宽盾牌空心轮廓（厚描边）"""
    return (f'<g id="{id}">'
            f'<path d="M 0 {-r*0.74} C {r*0.26} {-r*0.60} {r*0.54} {-r*0.52} {r*0.70} {-r*0.50} '
            f'L {r*0.70} {r*0.14} C {r*0.70} {r*0.46} {r*0.34} {r*0.66} 0 {r*0.78} '
            f'C {-r*0.34} {r*0.66} {-r*0.70} {r*0.46} {-r*0.70} {r*0.14} '
            f'L {-r*0.70} {-r*0.50} C {-r*0.54} {-r*0.52} {-r*0.26} {-r*0.60} 0 {-r*0.74} Z" '
            f'fill="none" stroke="#FFFFFF" stroke-width="4.2" stroke-linejoin="round"/>'
            f'</g>')

def icon_wechat(id, r=31, color='#A9A7AA', bg='#EBEDE8'):
    """微信双气泡（水印用）"""
    return (f'<g id="{id}">'
            f'<rect x="{-r*0.95}" y="{-r*0.72}" width="{r*1.30}" height="{r*0.98}" rx="{r*0.30}" fill="{color}"/>'
            f'<circle cx="{-r*0.52}" cy="{-r*0.34}" r="{r*0.09}" fill="{bg}"/>'
            f'<circle cx="{-r*0.10}" cy="{-r*0.34}" r="{r*0.09}" fill="{bg}"/>'
            f'<rect x="{-r*0.10}" y="{-r*0.05}" width="{r*1.05}" height="{r*0.82}" rx="{r*0.26}" fill="{color}"/>'
            f'<circle cx="{r*0.28}" cy="{r*0.26}" r="{r*0.08}" fill="{bg}"/>'
            f'<circle cx="{r*0.60}" cy="{r*0.26}" r="{r*0.08}" fill="{bg}"/>'
            f'</g>')

def icon_shield_fill(id, r=27):
    """治理：实心盾牌（卡片用）"""
    return (f'<g id="{id}">'
            f'<path d="M 0 {-r*0.70} C {r*0.28} {-r*0.56} {r*0.52} {-r*0.48} {r*0.64} {-r*0.46} '
            f'L {r*0.64} {r*0.12} C {r*0.64} {r*0.44} {r*0.30} {r*0.62} 0 {r*0.74} '
            f'C {-r*0.30} {r*0.62} {-r*0.64} {r*0.44} {-r*0.64} {r*0.12} '
            f'L {-r*0.64} {-r*0.46} C {-r*0.52} {-r*0.48} {-r*0.28} {-r*0.56} 0 {-r*0.70} Z" fill="#FFFFFF"/>'
            f'</g>')

def icon_db_fill(id, r=27, bg='#7A6853'):
    """数据：实心圆柱（表格行用，椭圆顶+深色弧线分隔）"""
    return (f'<g id="{id}">'
            f'<path d="M {-r*0.58} {-r*0.28} L {-r*0.58} {r*0.36} A {r*0.58} {r*0.24} 0 0 0 {r*0.58} {r*0.36} '
            f'L {r*0.58} {-r*0.28} Z" fill="#FFFFFF"/>'
            f'<ellipse cx="0" cy="{-r*0.28}" rx="{r*0.58}" ry="{r*0.24}" fill="#FFFFFF"/>'
            f'<path d="M {-r*0.58} {-r*0.04} A {r*0.58} {r*0.24} 0 0 0 {r*0.58} {-r*0.04}" fill="none" stroke="{bg}" stroke-width="2.6"/>'
            f'<path d="M {-r*0.58} {r*0.18} A {r*0.58} {r*0.24} 0 0 0 {r*0.58} {r*0.18}" fill="none" stroke="{bg}" stroke-width="2.6"/>'
            f'</g>')

ICONS = {'target': icon_target, 'gear': icon_gear, 'db': icon_db,
         'laptop': icon_laptop, 'people': icon_people, 'shield': icon_shield,
         'shield_fill': icon_shield_fill, 'db_fill': icon_db_fill}

ROW_ICON_KIND = ['target', 'gear', 'db', 'laptop', 'people', 'shield']
