#!/usr/bin/env python3
"""SVG 组件库 —— CASE-008。每个组件返回带 id 的独立最小单元（全矢量，无位图）。"""

def esc(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def text(id, x, y, s, size, weight=400, color='#253E56', anchor='start',
         spacing=None, opacity=None, extra=''):
    sp = f' letter-spacing="{spacing}"' if spacing else ''
    op = f' opacity="{opacity}"' if opacity else ''
    return (f'<text id="{id}" x="{x}" y="{y}" font-family="Noto Sans SC, sans-serif" '
            f'font-size="{size}" font-weight="{weight}" fill="{color}" '
            f'text-anchor="{anchor}"{sp}{op}{extra}>{esc(s)}</text>')

def rrect(id, x, y, w, h, r, fill, stroke=None, sw=0, opacity=None):
    st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ''
    op = f' opacity="{opacity}"' if opacity else ''
    return f'<rect id="{id}" x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}"{st}{op}/>'

def rect(id, x, y, w, h, fill, opacity=None):
    op = f' opacity="{opacity}"' if opacity else ''
    return f'<rect id="{id}" x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"{op}/>'

def circle(id, cx, cy, r, fill):
    return f'<circle id="{id}" cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"/>'

def line(id, x1, y1, x2, y2, color, w):
    return (f'<line id="{id}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{color}" stroke-width="{w}"/>')

def tri(id, points, fill):
    pts = ' '.join(f'{p[0]},{p[1]}' for p in points)
    return f'<polygon id="{id}" points="{pts}" fill="{fill}"/>'

# 头带（仅上圆角）：容器圆角矩形 + 矩形盖下半部
def band_top_rounded(id, x, y, w, h, r, fill):
    return (rrect(id, x, y, w, h, r, fill) +
            rect(id + '-sq', x, y + r, w, h - r, fill))

def wechat_logo(id, cx, cy, color='#ACADAE', dot='#E3E1DF'):
    """微信双气泡水印 logo：以 (cx,cy) 为中心，总宽 64px（实测 [1056,1121]x[872,928]）"""
    return (f'<g id="{id}">'
            f'<rect x="{cx-31.5}" y="{cy-24}" width="44" height="44" rx="10" fill="{color}"/>'
            f'<circle cx="{cx-15.5}" cy="{cy-9}" r="3" fill="{dot}"/>'
            f'<circle cx="{cx-1.5}" cy="{cy-9}" r="3" fill="{dot}"/>'
            f'<rect x="{cx-2.5}" y="{cy-1}" width="35" height="28" rx="8" fill="{color}"/>'
            f'<circle cx="{cx+8.5}" cy="{cy+10}" r="2.6" fill="{dot}"/>'
            f'<circle cx="{cx+19.5}" cy="{cy+10}" r="2.6" fill="{dot}"/>'
            f'</g>')
