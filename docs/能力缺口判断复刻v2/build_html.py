#!/usr/bin/env python3
"""Step2: 组装 HTML+SVG（全真实文本、无位图、组件带 id）"""
import os, sys, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spec import *
from svg_lib import text, rrect, hbar, circle, ICONS, ROW_ICON_KIND, esc, icon_wechat

OUT = '/home/z/my-project/download/能力缺口判断复刻v2.html'

S = []
S.append('<svg id="stage" viewBox="0 0 1728 972" width="1728" height="972" '
         'xmlns="http://www.w3.org/2000/svg" font-family="Noto Sans SC, sans-serif">')
S.append(rrect('bg', 0, 0, W, H, 0, C['bg']))

# ---------- 大标题 ----------
S.append(f'<text id="main-title" x="{TITLE["x"]}" y="{TITLE["y"]}" font-family="Noto Sans SC, sans-serif" font-size="{TITLE["size"]}" font-weight="{TITLE["weight"]}" fill="{TITLE["color"]}" stroke="{TITLE["color"]}" stroke-width="1.6" text-anchor="start" letter-spacing="-1.4">{TITLE["text"]}</text>')

# ---------- 左表容器 ----------
S.append(rrect('tbl-container', TBL['x'], TBL['y'], TBL['w'], TBL['h'], TBL['r'],
               C['white'], stroke=C['rborder'], sw=2))
# 表头带（只圆上角）
S.append(f'<path id="tbl-header" d="M {TBL["x"]} {HDR["y"]+HDR["h"]} L {TBL["x"]} {HDR["y"]+TBL["r"]} '
         f'Q {TBL["x"]} {HDR["y"]} {TBL["x"]+TBL["r"]} {HDR["y"]} L {TBL["x"]+TBL["w"]-TBL["r"]} {HDR["y"]} '
         f'Q {TBL["x"]+TBL["w"]} {HDR["y"]} {TBL["x"]+TBL["w"]} {HDR["y"]+TBL["r"]} '
         f'L {TBL["x"]+TBL["w"]} {HDR["y"]+HDR["h"]} Z" fill="{HDR["bg"]}"/>')
for i, sx in enumerate(HDR_SEPS):
    S.append(f'<rect id="hdr-sep-{i+1}" x="{sx}" y="{HDR["y"]+14}" width="2" height="{HDR["h"]-28}" fill="#FFFFFF"/>')
for i, t in enumerate(HDR_TEXT):
    S.append(text(f'hdr-t-{i}', t['cx'], t['cy'], t['t'], t['size'], t['weight'], t['color'], anchor='middle'))

# 行分隔线 + 行背景交替
hdr_bot = HDR['y'] + HDR['h']           # 208
row_h = (SUM['y'] - hdr_bot) / 6.0      # ≈76.83
for i in range(6):
    top = hdr_bot + i * row_h
    if i % 2 == 0:
        S.append(f'<rect id="row-stripe-{i+1}" x="{TBL["x"]+2}" y="{top:.1f}" width="{TBL["w"]-4}" height="{row_h:.1f}" fill="{C["stripe"]}"/>')
    if i > 0:
        S.append(f'<rect id="row-sep-{i}" x="{TBL["x"]+2}" y="{top:.1f}" width="{TBL["w"]-4}" height="2" fill="{C["sep_line"]}"/>')

# ---------- 6 行内容 ----------
for i, r in enumerate(ROWS):
    cy = ROW_CY[i]
    top = hdr_bot + i * row_h
    # 图标
    ic_x, ic_y, d = 78, cy, 62
    S.append(circle(f'row{i+1}-icon-circle', ic_x, ic_y, d // 2, r['icon']))
    kind = 'db_fill' if ROW_ICON_KIND[i] == 'db' else ROW_ICON_KIND[i]
    kw = {'bg': r['icon']} if kind == 'db_fill' else {}
    S.append(f'<g id="row{i+1}-icon" transform="translate({ic_x},{ic_y})">' +
             ICONS[kind](f'row{i+1}-icon-glyph', r=31, **kw) + '</g>')
    # 名称 / 权重
    S.append(text(f'row{i+1}-name', 130, cy + 12, r['name'], 27, 500, C['navy']))
    S.append(text(f'row{i+1}-weight', 311, cy - 4, r['w'], 25, 500, C['navy'], anchor='middle'))
    # 分数 + 条（现状）
    by1, by2 = BAR_Y(cy)
    S.append(text(f'row{i+1}-score-cur', CUR_X0 + 1, by1 - 7, r['cur'], 25, 700, C['navy']))
    S.append(hbar(f'row{i+1}-cur-track', CUR_X0, by1, CUR_TRK - CUR_X0, by2 - by1, C['track']))
    S.append(hbar(f'row{i+1}-cur-fill', CUR_X0 + 1, by1, r['fw'], by2 - by1, r['cur_c']))
    # 分数 + 条（目标）
    S.append(text(f'row{i+1}-score-tgt', TGT_X0 + 1, by1 - 7, r['tgt'], 25, 700, C['navy']))
    S.append(hbar(f'row{i+1}-tgt-track', TGT_X0, by1, TGT_TRK - TGT_X0, by2 - by1, C['track_b']))
    if r['name'] == '战略':
        S.append(hbar(f'row{i+1}-tgt-fill-a', TGT_X0 + 1, by1, STRATEGY_TGT_SPLIT - TGT_X0, by2 - by1, C['steel_dk']))
        S.append(hbar(f'row{i+1}-tgt-fill-b', STRATEGY_TGT_SPLIT, by1, r['tw'] - (STRATEGY_TGT_SPLIT - TGT_X0), by2 - by1, C['steel']))
    else:
        S.append(hbar(f'row{i+1}-tgt-fill', TGT_X0 + 1, by1, r['tw'], by2 - by1, r['tgt_c']))

# ---------- 合计行 ----------
sy = SUM['y']
S.append(f'<path id="sum-band" d="M {TBL["x"]} {sy} L {TBL["x"]+TBL["w"]} {sy} L {TBL["x"]+TBL["w"]} {sy+SUM["h"]-TBL["r"]} '
         f'Q {TBL["x"]+TBL["w"]} {sy+SUM["h"]} {TBL["x"]+TBL["w"]-TBL["r"]} {sy+SUM["h"]} '
         f'L {TBL["x"]+TBL["r"]} {sy+SUM["h"]} Q {TBL["x"]} {sy+SUM["h"]} {TBL["x"]} {sy+SUM["h"]-TBL["r"]} Z" '
         f'fill="{SUM["bg"]}"/>')
for it in SUM['items']:
    anchor = 'middle'
    S.append(text(f'sum-{it["t"]}', it['cx'], it['cy'], it['t'], it['size'], it['weight'],
                  it['color'], anchor=anchor))

# ---------- 右面板 ----------
P = RPANEL
S.append(rrect('rpanel-body', P['x'], P['y'], P['w'], P['h'], P['r'], C['white'],
               stroke=C['rborder'], sw=2))
S.append(f'<path id="rpanel-band" d="M {P["x"]} {P["y"]+P["band_h"]} L {P["x"]} {P["y"]+P["r"]} '
         f'Q {P["x"]} {P["y"]} {P["x"]+P["r"]} {P["y"]} L {P["x"]+P["w"]-P["r"]} {P["y"]} '
         f'Q {P["x"]+P["w"]} {P["y"]} {P["x"]+P["w"]} {P["y"]+P["r"]} '
         f'L {P["x"]+P["w"]} {P["y"]+P["band_h"]} Z" fill="{P["bg_band"]}"/>')
S.append(text('rpanel-title', P['title_x'], P['title_cy'], P['title'], P['title_size'], 700, C['navy']))
S.append(text('rpanel-note1', P['note1_x'], P['note1_cy'], P['note1'], P['note1_size'], 500,
              '#5A6472', anchor='end'))
S.append(text('rpanel-note2', P['note2_x'], P['note2_cy'], P['note2'], P['note2_size'], 400,
              '#6B7280', anchor='end'))
for i, g in enumerate(GAPS):
    cy = g['cy']
    bx, bw, bh = BADGE['x'], BADGE['w'], BADGE['h']
    S.append(rrect(f'gap{i+1}-badge', bx, cy - bh // 2, bw, bh, BADGE['r'], g['badge']))
    S.append(text(f'gap{i+1}-badge-num', bx + bw // 2, cy + 10, str(i + 1), 28, 700, C['white'], anchor='middle'))
    S.append(text(f'gap{i+1}-name', 1127, cy + 10, g['name'], 26, 500, C['navy']))
    by1 = cy - GAP_BAR_H // 2
    S.append(hbar(f'gap{i+1}-track', GAP_BAR_X0, by1, GAP_BAR_END - GAP_BAR_X0, GAP_BAR_H, C['track'], r=6))
    S.append(hbar(f'gap{i+1}-fill', GAP_BAR_X0, by1, g['vw'], GAP_BAR_H, g['bar'], r=6))
    S.append(text(f'gap{i+1}-val', 1680, cy + 14, g['val'], 38, 700, g['vc'], anchor='end'))

# ---------- 底部面板 ----------
B = BOT
S.append(rrect('bot-panel', B['x'], B['y'], B['w'], B['h'], B['r'], B['bg']))
S.append(text('bot-title', B['title_x'], B['title_cy'], B['title'], B['title_size'], 700, C['navy']))
S.append(text('bot-note', B['note_x2'], B['note_cy'], B['note'], B['note_size'], 400,
              '#6A7280', anchor='end'))
for i, cd in enumerate(CARDS):
    S.append(rrect(f'card{i+1}', cd['x'], cd['y'], cd['w'], cd['h'], cd['r'], cd['bg']))
    S.append(circle(f'card{i+1}-icon-circle', cd['icon_cx'], cd['icon_cy'], 35, cd['icon_bg']))
    kw = {'bg': cd['icon_bg']} if cd['icon'] == 'db' else {}
    S.append(f'<g id="card{i+1}-icon" transform="translate({cd["icon_cx"]},{cd["icon_cy"]})">' +
             ICONS[cd['icon']](f'card{i+1}-icon-glyph', r=25, **kw) + '</g>')
    bxx = cd['x'] + 13
    S.append(rrect(f'card{i+1}-badge', bxx, cd['y'] + 21, BADGE_S['w'], BADGE_S['h'], BADGE_S['r'], cd['badge_bg']))
    S.append(text(f'card{i+1}-badge-num', bxx + 24, cd['y'] + 21 + 33, cd['badge'], BADGE_S['size'], 700,
                  C['white'], anchor='middle'))
    S.append(text(f'card{i+1}-label', bxx + 66, cd['y'] + 55, cd['label'], 25, 700, C['navy']))
    S.append(text(f'card{i+1}-divider', bxx + 66 + 58, cd['y'] + 53, '|', 24, 300, '#B9C0C9'))
    S.append(text(f'card{i+1}-text', cd['text_x'], cd['y'] + 52, cd['text'], 20, 400, '#3A4450'))

# ---------- 水印 ----------
S.append(f'<g id="watermark-group" opacity="{WATERMARK["opacity"]}">')
S.append(f'<g id="watermark-wechat" transform="translate({WATERMARK["wx"]},{WATERMARK["wy"]})">' +
         icon_wechat('watermark-wechat-glyph', r=WATERMARK['wr']) + '</g>')
S.append(text('watermark', WATERMARK['x2'], WATERMARK['cy'], WATERMARK['text'], WATERMARK['size'],
              700, WATERMARK['color'], anchor='end', spacing='1.3'))
S.append('</g>')

S.append('</svg>')

html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>准备度评分与能力缺口诊断 · 复刻 v2</title>
<style>
  html,body {{ margin:0; padding:0; background:#FEFEFE; }}
  #canvas {{ width:1728px; height:972px; overflow:hidden; }}
  text {{ font-family:'Noto Sans SC','Noto Sans CJK SC',sans-serif; }}
</style>
</head>
<body>
<div id="canvas">
{chr(10).join(S)}
</div>
</body>
</html>
'''

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(html)

# ---------- N2 自检 ----------
texts = len(re.findall(r'<text', html))
ids = len(re.findall(r'id="', html))
imgs = len(re.findall(r'<image|data:image', html))
kv = len(re.findall(r'>(.*?)</text>', html))
print(f'N2 自检: <text>={texts}  id={ids}  位图命中={imgs}  (要求: text>=40, id>=60, 位图=0)')
print('输出:', OUT, len(html), 'bytes')
