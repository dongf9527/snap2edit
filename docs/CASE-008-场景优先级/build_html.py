#!/usr/bin/env python3
"""Step2: CASE-008 组装 HTML+SVG（全真实文本、无位图、组件带 id）"""
import os, sys, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spec import *
from svg_lib import text, rrect, rect, circle, line, tri, band_top_rounded, wechat_logo, esc

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '场景优先级复刻.html')

S = []
S.append('<svg id="stage" viewBox="0 0 1728 972" width="1728" height="972" '
         'xmlns="http://www.w3.org/2000/svg" font-family="Noto Sans SC, sans-serif">')
S.append(rect('bg', 0, 0, W, H, C['bg']))

# ---------- 大标题 ----------
T = TITLE
sp = f' letter-spacing="{T["spacing"]}"' if T['spacing'] else ''
S.append(f'<text id="main-title" x="{T["x"]}" y="{T["y"]}" font-family="Noto Sans SC, sans-serif" '
         f'font-size="{T["size"]}" font-weight="{T["weight"]}" fill="{T["color"]}" '
         f'text-anchor="start"{sp}>{esc(T["text"])}</text>')

# ---------- 四张面板卡 ----------
for ci, (card, band) in enumerate([(P1_CARD, BAND_TITLES[0]), (P2_CARD, BAND_TITLES[1]),
                                   (P3_CARD, BAND_TITLES[2]), (P4_CARD, BAND_TITLES[3])], 1):
    S.append(rrect(f'card{ci}', card['x'], card['y'], card['w'], card['h'], 10,
                   C['white'], stroke=C['card_border'], sw=1.5))
    S.append(band_top_rounded(f'card{ci}-band', band['x'], band['y'], band['w'], band['h'],
                              8, C['navy']))
    S.append(text(f'card{ci}-title', band['tx'], band['ty'], band['text'], band['size'],
                  band['weight'], C['white'], spacing=band.get('spacing')))
    if band.get('suffix'):
        S.append(text(f'card{ci}-suffix', band['suffix_x'], band['ty'], band['suffix'],
                      band['suffix_size'], band['suffix_weight'], band['suffix_color']))

# ---------- P1 芯片区 ----------
for i, ch in enumerate(CHIPS, 1):
    x, bw = ch['x'], ch['w']
    S.append(rrect(f'chip{i}-body', x, ch['y'], bw, ch['band_h'] + ch['body_h'], 8, C['chip_body']))
    S.append(band_top_rounded(f'chip{i}-band', x, ch['y'], bw, ch['band_h'], 8, ch['band']))
    S.append(text(f'chip{i}-label', ch['label_c'], CHIP_LABEL_BASELINE, ch['label'],
                  CHIP_LABEL_SIZE, 700, C['white'], anchor='middle'))
    S.append(text(f'chip{i}-pct', ch['pct_c'], CHIP_LABEL_BASELINE, ch['pct'],
                  CHIP_PCT_SIZE, 700, C['white'], anchor='middle'))
    for li, ln in enumerate(ch['lines']):
        if ln is None:
            continue
        S.append(text(f'chip{i}-line-{li+1}', x + CHIP_TEXT_X_INSET, CHIP_BASELINES[li],
                      ln, CHIP_TEXT_SIZE, CHIP_TEXT_WEIGHT, C['chip_text']))

# ---------- P1 评分表 ----------
t = T1
# 表头带
S.append(rect('t1-header', t['x'], t['y'], t['w'], t['header_h'], C['navy']))
for si, sx in enumerate(t['col_seps'], 1):
    S.append(rect(f't1-hdrsep-{si}', sx - 1, t['sep_y0'], 2, t['sep_y1'] - t['sep_y0'], C['white']))
for hi, (txt, cx, by, sz, wt, col) in enumerate(t['hdr_text']):
    S.append(text(f't1-htxt-{hi}', cx, by, txt, sz, wt, col, anchor='middle'))
S.append(rect('t1-under', t['x'], t['hdr_under_line']['y'], t['w'], t['hdr_under_line']['h'],
              t['hdr_under_line']['color']))
# 行条纹（奇偶反相 + 总分列再反相）
for ri, (y0, y1) in enumerate(t['rows']):
    main_fill = t['stripe_odd'] if ri % 2 == 0 else t['stripe_even']
    score_fill = t['score_odd'] if ri % 2 == 0 else t['score_even']
    S.append(rect(f't1-row{ri+1}-main', t['x'], y0, t['score_x0'] - t['x'], y1 - y0, main_fill))
    S.append(rect(f't1-row{ri+1}-score', t['score_x0'], y0, t['x'] + t['w'] - t['score_x0'],
                  y1 - y0, score_fill))
# 行内容
for ri, (name, v1, v2, v3, sc, bcol) in enumerate(t['data']):
    cy = t['row_cy'][ri]
    n = ri + 1
    S.append(circle(f't1-badge-{n}', t['badge_cx'], cy, t['badge_r'], bcol))
    S.append(text(f't1-badge-num-{n}', t['badge_cx'], cy + 6.5, str(n), t['badge_num_size'],
                  700, C['white'], anchor='middle'))
    S.append(text(f't1-name-{n}', t['name_x'], t['text_baseline'][ri], name, t['name_size'],
                  t['name_weight'], C['name_navy']))
    for di, val in enumerate((v1, v2, v3)):
        S.append(text(f't1-num-{n}-{di+1}', t['num_cx'][di], t['num_baseline'][ri], val,
                      t['num_size'], t['num_weight'], C['num_navy'], anchor='middle'))
    S.append(text(f't1-score-{n}', t['score_cx'], t['score_baseline'][ri], sc, t['score_size'],
                  t['score_weight'], C['score_navy'], anchor='middle'))

# ---------- P2 矩阵 ----------
m = MATRIX
for qi, (qx, qy, qw, qh, fill) in enumerate(m['quads'], 1):
    S.append(rect(f'quad-{qi}', qx, qy, qw, qh, fill))
ya, xa = m['y_axis'], m['x_axis']
S.append(line('axis-y', ya['x'], ya['y0'], ya['x'], ya['y1'], C['axis'], 2.4))
S.append(tri('axis-y-arrow', [(ya['x'], ya['arrow_tip']),
                              (ya['x'] - ya['arrow_half'], ya['arrow_tip'] + 13),
                              (ya['x'] + ya['arrow_half'], ya['arrow_tip'] + 13)], C['axis']))
S.append(line('axis-x', xa['x0'], xa['y'], xa['x1'], xa['y'], C['axis'], 2.4))
S.append(tri('axis-x-arrow', [(xa['arrow_tip'], xa['y']),
                              (xa['arrow_tip'] - 13, xa['y'] - xa['arrow_half']),
                              (xa['arrow_tip'] - 13, xa['y'] + xa['arrow_half'])], C['axis']))
for li, (txt, lx, by, sz, anch) in enumerate(m['labels']):
    S.append(text(f'm-label-{li}', lx, by, txt, sz, m['label_weight'], C['axis_label'], anchor=anch))
for bi, (bx, byy, bw, bh, fill, ttl, sub, tb, sb) in enumerate(m['badges'], 1):
    S.append(rrect(f'm-badge-{bi}', bx, byy, bw, bh, 8, fill))
    S.append(text(f'm-badge-{bi}-title', bx + bw / 2, tb, ttl, m['badge_title_size'], 700,
                  C['white'], anchor='middle'))
    S.append(text(f'm-badge-{bi}-sub', bx + bw / 2, sb, sub, m['badge_sub_size'], 400,
                  C['white'], anchor='middle'))

# ---------- P3 / P4 表格：先画全部矩形（含水印下层），文字最后画 ----------
TABLES = [(T3, 't3'), (T4, 't4')]
for t, prefix in TABLES:
    S.append(rect(f'{prefix}-header', t['x'], t['y'], t['w'], t['header_h'], C['navy']))
    for si, sx in enumerate(t['col_seps'], 1):
        S.append(rect(f'{prefix}-hdrsep-{si}', sx - 1, t['sep_y0'], 2, t['sep_y1'] - t['sep_y0'],
                      C['white']))
    for hi, (txt, hx_) in enumerate(t['hdr_text']):
        S.append(text(f'{prefix}-htxt-{hi}', hx_, t['hdr_baseline'], txt, t['hdr_size'], 700,
                      C['white']))
    # 行条纹（偶数行 r2/r4）
    for ri, (y0, y1) in enumerate(t['rows']):
        if ri % 2 == 1:
            S.append(rect(f'{prefix}-stripe-{ri+1}', t['x'], y0, t['w'], y1 - y0, t['stripe']))
    # 行分隔线
    for si, sy in enumerate(t['sep_ys'], 1):
        S.append(rect(f'{prefix}-sep-{si}', t['x'], sy - 1, t['w'], 2, C['row_sep']))
    # 结论/决策整列色块（盖在分隔线上，与原图一致）
    for ri, row in enumerate(t['data']):
        cell = row[-2]
        S.append(rect(f'{prefix}-cell-{ri+1}', t['cell_x'], t['rows'][ri][0], t['cell_w'],
                      t['rows'][ri][1] - t['rows'][ri][0], cell))

# ---------- 水印（色块之上、文字之下） ----------
wm = WATERMARK
S.append(f'<g id="watermark-group">')
S.append(wechat_logo('watermark-logo', wm['logo_cx'], wm['logo_cy'], wm['color'], C['wm_dot']))
S.append(text('watermark-1', wm['x1'], wm['baseline'], wm['text1'], wm['size1'], wm['weight1'],
              wm['color']))
S.append(text('watermark-2', wm['x2'], wm['baseline'], wm['text2'], wm['size2'], wm['weight2'],
              wm['color'], spacing=wm['spacing2']))
S.append('</g>')

# ---------- P3 / P4 表格文字（压在水印之上，与原图层级一致） ----------
for tk, (t, prefix) in enumerate(TABLES):
    for ri, row in enumerate(t['data']):
        n = ri + 1
        pill_c = row[-1]
        if tk == 0:
            name, risk, gate, pill = row[0], row[1], row[2], row[3]
            S.append(text(f'{prefix}-name-{n}', t['name_x'], t['name_baseline'][ri], name,
                          t['name_size'], t['name_weight'], C['name_navy2']))
            S.append(text(f'{prefix}-risk-{n}', t['body_x1'], t['body_baseline'][ri], risk,
                          t['text_size'], 400, C['body_text']))
            S.append(text(f'{prefix}-gate-{n}', t['body_x2'], t['body_baseline'][ri], gate,
                          t['text_size'], 400, C['body_text']))
        else:
            name, pill, strategy = row[0], row[1], row[2]
            S.append(text(f'{prefix}-name-{n}', t['name_x'], t['name_baseline'][ri], name,
                          t['name_size'], t['name_weight'], C['name_navy2']))
            S.append(text(f'{prefix}-strategy-{n}', t['body_x1'], t['body_baseline'][ri],
                          strategy, t['text_size'], 400, C['body_text']))
        S.append(text(f'{prefix}-pill-{n}', t['cell_x'] + t['cell_w'] / 2,
                      t['pill_baseline'][ri], pill, t['pill_size'], 700, pill_c, anchor='middle'))

S.append('</svg>')

html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>场景优先级与组合决策 · 复刻（CASE-008）</title>
<style>
  html,body {{ margin:0; padding:0; background:#FDFDFD; }}
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
print(f'N2 自检: <text>={texts}  id={ids}  位图命中={imgs}  (要求: text>=60, id>=80, 位图=0)')
missing = [p for p in PHRASES if p not in html]
print('文案缺失:', missing if missing else '无')
print('输出:', OUT, len(html), 'bytes')
