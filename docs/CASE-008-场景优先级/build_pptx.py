#!/usr/bin/env python3
"""Step4: CASE-008 python-pptx 原生 PPTX（文本框+形状，Picture=0）
同一份 spec.py 喂养；坐标 px→EMU；基线→文本框顶 = baseline - 0.86*size。
z-order 与 HTML 一致：底→卡→芯片→P1→P2→P3/P4 矩形→水印→P3/P4 文字。
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spec import *
from pptx import Presentation
from pptx.util import Emu
from pptx_lib import (E, PT, rgb, text_width, set_text, add_rect, add_text, add_line,
                      add_oval, add_ellipse, freeform, EMU_W, EMU_H, PT_PX)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '场景优先级复刻.pptx')
WARN = []

prs = Presentation()
prs.slide_width = Emu(EMU_W)
prs.slide_height = Emu(EMU_H)
slide = prs.slides.add_slide(prs.slide_layouts[6])   # 空白版式
sh = slide.shapes

def T(x, baseline, w, text, size, weight, color, align='l', tag='', spc=None):
    """按基线落位的左对齐文本框（LibreOffice 实测：top = baseline - 0.98*size）"""
    tw = text_width(text, size, weight)
    if tw > w + 1:
        WARN.append(f'溢出[{tag or text[:8]}]: 需{tw:.0f} > 框{w:.0f}px')
    top = baseline - size * 0.98
    return add_text(sh, x, top, w, size * 1.7, text, size, weight, color, align, 't',
                    spc_px=spc)

def TM(cx, baseline, text, size, weight, color, tag='', spc=None):
    """按基线+水平居中落位（center 对齐，对称框）"""
    tw = text_width(text, size, weight)
    return T(cx - tw / 2 - 2, baseline, tw + 4, text, size, weight, color, align='c',
             tag=tag, spc=spc)

# ---------- 背景 ----------
add_rect(sh, 0, 0, W, H, fill=C['bg'])

# ---------- 大标题 ----------
T(TITLE['x'], TITLE['y'], 700, TITLE['text'], TITLE['size'], TITLE['weight'], TITLE['color'],
  tag='标题', spc=TITLE['spacing'])

# ---------- 四张面板卡 ----------
for ci, (card, band) in enumerate([(P1_CARD, BAND_TITLES[0]), (P2_CARD, BAND_TITLES[1]),
                                   (P3_CARD, BAND_TITLES[2]), (P4_CARD, BAND_TITLES[3])], 1):
    add_rect(sh, card['x'], card['y'], card['w'], card['h'], fill=C['white'],
             line=C['card_border'], line_w=1.5, radius=10)
    # 头带（上圆角：圆角矩形+下半覆盖）
    add_rect(sh, band['x'], band['y'], band['w'], band['h'], fill=C['navy'], radius=8)
    add_rect(sh, band['x'], band['y'] + 8, band['w'], band['h'] - 8, fill=C['navy'])
    T(band['tx'], band['ty'], 400, band['text'], band['size'], band['weight'], C['white'],
      tag=f'带标题{ci}', spc=band.get('spacing'))
    if band.get('suffix'):
        T(band['suffix_x'], band['ty'], 260, band['suffix'], band['suffix_size'],
          band['suffix_weight'], band['suffix_color'], tag='后缀')

# ---------- P1 芯片区 ----------
for i, ch in enumerate(CHIPS, 1):
    x, bw = ch['x'], ch['w']
    add_rect(sh, x, ch['y'], bw, ch['band_h'] + ch['body_h'], fill=C['chip_body'], radius=8)
    add_rect(sh, x, ch['y'], bw, ch['band_h'], fill=ch['band'], radius=8)
    add_rect(sh, x, ch['y'] + 8, bw, ch['band_h'] - 8, fill=ch['band'])
    TM(ch['label_c'], CHIP_LABEL_BASELINE, ch['label'], CHIP_LABEL_SIZE, 700, C['white'],
       tag=f'chip{i}名')
    TM(ch['pct_c'], CHIP_LABEL_BASELINE, ch['pct'], CHIP_PCT_SIZE, 700, C['white'],
       tag=f'chip{i}pct')
    for li, ln in enumerate(ch['lines']):
        if ln is None:
            continue
        T(x + CHIP_TEXT_X_INSET, CHIP_BASELINES[li], bw - CHIP_TEXT_X_INSET - 8, ln,
          CHIP_TEXT_SIZE, CHIP_TEXT_WEIGHT, C['chip_text'], tag=f'chip{i}L{li+1}')

# ---------- P1 评分表 ----------
t = T1
add_rect(sh, t['x'], t['y'], t['w'], t['header_h'], fill=C['navy'])
for si, sx in enumerate(t['col_seps'], 1):
    add_rect(sh, sx - 1, t['sep_y0'], 2, t['sep_y1'] - t['sep_y0'], fill=C['white'])
for hi, (txt, cx, by, sz, wt, col) in enumerate(t['hdr_text']):
    TM(cx, by, txt, sz, wt, col, tag=f'P1表头{txt}')
u = t['hdr_under_line']
add_rect(sh, t['x'], u['y'], t['w'], u['h'], fill=u['color'])
for ri, (y0, y1) in enumerate(t['rows']):
    main_fill = t['stripe_odd'] if ri % 2 == 0 else t['stripe_even']
    score_fill = t['score_odd'] if ri % 2 == 0 else t['score_even']
    add_rect(sh, t['x'], y0, t['score_x0'] - t['x'], y1 - y0, fill=main_fill)
    add_rect(sh, t['score_x0'], y0, t['x'] + t['w'] - t['score_x0'], y1 - y0, fill=score_fill)
for ri, (name, v1, v2, v3, sc, bcol) in enumerate(t['data']):
    cy = t['row_cy'][ri]
    n = ri + 1
    add_oval(sh, t['badge_cx'], cy, t['badge_r'], fill=bcol)
    TM(t['badge_cx'], cy + 6.5, str(n), t['badge_num_size'], 700, C['white'], tag=f'徽章{n}')
    T(t['name_x'], t['text_baseline'][ri], 150, name, t['name_size'], t['name_weight'],
      C['name_navy'], tag=f'P1名{n}')
    for di, val in enumerate((v1, v2, v3)):
        TM(t['num_cx'][di], t['num_baseline'][ri], val, t['num_size'], t['num_weight'],
           C['num_navy'], tag=f'P1数字{n}')
    TM(t['score_cx'], t['score_baseline'][ri], sc, t['score_size'], t['score_weight'],
       C['score_navy'], tag=f'P1总分{n}')

# ---------- P2 矩阵 ----------
m = MATRIX
for qi, (qx, qy, qw, qh, fill) in enumerate(m['quads'], 1):
    add_rect(sh, qx, qy, qw, qh, fill=fill)
ya, xa = m['y_axis'], m['x_axis']
add_line(sh, ya['x'], ya['y0'], ya['x'], ya['y1'], C['axis'], w_px=2.4)
freeform(sh, [(ya['x'], ya['arrow_tip']), (ya['x'] - ya['arrow_half'], ya['arrow_tip'] + 13),
              (ya['x'] + ya['arrow_half'], ya['arrow_tip'] + 13)], fill=C['axis'])
add_line(sh, xa['x0'], xa['y'], xa['x1'], xa['y'], C['axis'], w_px=2.4)
freeform(sh, [(xa['arrow_tip'], xa['y']), (xa['arrow_tip'] - 13, xa['y'] - xa['arrow_half']),
              (xa['arrow_tip'] - 13, xa['y'] + xa['arrow_half'])], fill=C['axis'])
for li, (txt, lx, by, sz, anch) in enumerate(m['labels']):
    TM(lx, by, txt, sz, m['label_weight'], C['axis_label'], tag=f'轴标签{txt}')
for bi, (bx, byy, bw, bh, fill, ttl, sub, tb, sb) in enumerate(m['badges'], 1):
    add_rect(sh, bx, byy, bw, bh, fill=fill, radius=8)
    TM(bx + bw / 2, tb, ttl, m['badge_title_size'], 700, C['white'], tag=f'P2徽章{bi}题')
    TM(bx + bw / 2, sb, sub, m['badge_sub_size'], 400, C['white'], tag=f'P2徽章{bi}副')

# ---------- P3 / P4 矩形层 ----------
TABLES = [(T3, 'P3'), (T4, 'P4')]
for t, prefix in TABLES:
    add_rect(sh, t['x'], t['y'], t['w'], t['header_h'], fill=C['navy'])
    for si, sx in enumerate(t['col_seps'], 1):
        add_rect(sh, sx - 1, t['sep_y0'], 2, t['sep_y1'] - t['sep_y0'], fill=C['white'])
    for hi, (txt, hx_) in enumerate(t['hdr_text']):
        T(hx_, t['hdr_baseline'], 200, txt, t['hdr_size'], 700, C['white'],
          tag=f'{prefix}表头{txt}')
    for ri, (y0, y1) in enumerate(t['rows']):
        if ri % 2 == 1:
            add_rect(sh, t['x'], y0, t['w'], y1 - y0, fill=t['stripe'])
    for si, sy in enumerate(t['sep_ys'], 1):
        add_rect(sh, t['x'], sy - 1, t['w'], 2, fill=C['row_sep'])
    for ri, row in enumerate(t['data']):
        add_rect(sh, t['cell_x'], t['rows'][ri][0], t['cell_w'],
                 t['rows'][ri][1] - t['rows'][ri][0], fill=row[-2])

# ---------- 水印（色块之上、文字之下） ----------
wm = WATERMARK
lcx, lcy = wm['logo_cx'], wm['logo_cy']
add_rect(sh, lcx - 31.5, lcy - 24, 44, 44, fill=wm['color'], radius=10)
add_oval(sh, lcx - 15.5, lcy - 9, 3, fill=C['wm_dot'])
add_oval(sh, lcx - 1.5, lcy - 9, 3, fill=C['wm_dot'])
add_rect(sh, lcx - 2.5, lcy - 1, 35, 28, fill=wm['color'], radius=8)
add_oval(sh, lcx + 8.5, lcy + 10, 2.6, fill=C['wm_dot'])
add_oval(sh, lcx + 19.5, lcy + 10, 2.6, fill=C['wm_dot'])
T(wm['x1'], wm['baseline'], 200, wm['text1'], wm['size1'], wm['weight1'], wm['color'],
  tag='水印1')
T(wm['x2'], wm['baseline'], 400, wm['text2'], wm['size2'], wm['weight2'], wm['color'],
  tag='水印2', spc=wm['spacing2'])

# ---------- P3 / P4 文字层 ----------
for ti, (t, prefix) in enumerate(TABLES):
    for ri, row in enumerate(t['data']):
        n = ri + 1
        pill_c = row[-1]
        if ti == 0:
            name, risk, gate, pill = row[0], row[1], row[2], row[3]
            T(t['name_x'], t['name_baseline'][ri], 160, name, t['name_size'], t['name_weight'],
              C['name_navy2'], tag=f'{prefix}名{n}')
            T(t['body_x1'], t['body_baseline'][ri], 230, risk, t['text_size'], 400,
              C['body_text'], tag=f'{prefix}风险{n}')
            T(t['body_x2'], t['body_baseline'][ri], 310, gate, t['text_size'], 400,
              C['body_text'], tag=f'{prefix}门槛{n}')
        else:
            name, pill, strategy = row[0], row[1], row[2]
            T(t['name_x'], t['name_baseline'][ri], 160, name, t['name_size'], t['name_weight'],
              C['name_navy2'], tag=f'{prefix}名{n}')
            T(t['body_x1'], t['body_baseline'][ri], 410, strategy, t['text_size'], 400,
              C['body_text'], tag=f'{prefix}策略{n}')
        TM(t['cell_x'] + t['cell_w'] / 2, t['pill_baseline'][ri], pill, t['pill_size'], 700,
           pill_c, tag=f'{prefix}结论{n}')

prs.save(OUT)
print(f'N4 自检: 输出 {OUT}')
print(f'量宽溢出警告: {len(WARN)}')
for w in WARN[:10]:
    print('  ', w)
