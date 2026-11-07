#!/usr/bin/env python3
"""Step4: python-pptx 原生 PPTX（文本框+形状，Picture=0）"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spec import *
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Emu
from spec import CANVAS_W, CANVAS_H
from pptx_lib import (E, PT, rgb, text_width, set_text, add_rect, add_text, add_line,
                      add_oval, add_ellipse, freeform, EMU_W, EMU_H)

OUT = '/home/z/my-project/download/能力缺口判断复刻v2.pptx'
WARN = []

prs = Presentation()
prs.slide_width = Emu(EMU_W)
prs.slide_height = Emu(EMU_H)
slide = prs.slides.add_slide(prs.slide_layouts[6])   # 空白版式
sh = slide.shapes

def T(x, y, w, text, size, weight, color, align='l', anchor='t', tag=''):
    tw = text_width(text, size, weight)
    if tw > w + 1:
        WARN.append(f'溢出[{tag or text}]: 需{tw:.0f}px > 框{w}px')
    return add_text(sh, x, y, w, size * 1.6, text, size, weight, color, align, anchor)


def shield_shape(ix, iy, R, line_w=2.6):
    rw = 0.70 * R
    pts = [(cx * rw, cy * R) for cx, cy in
           [(0, -0.74), (0.20, -0.665), (0.45, -0.585), (0.72, -0.525), (1.0, -0.50),
            (1.0, 0.14), (0.96, 0.315), (0.80, 0.52), (0.47, 0.70), (0, 0.78),
            (-0.47, 0.70), (-0.80, 0.52), (-0.96, 0.315), (-1.0, 0.14),
            (-1.0, -0.50), (-0.72, -0.525), (-0.45, -0.585), (-0.20, -0.665)]]
    pts = [(ix + px, iy + py) for px, py in pts]
    freeform(sh, pts, fill=None, line='#FFFFFF', line_w=line_w)

# ---------- 背景 ----------
add_rect(sh, 0, 0, CANVAS_W, CANVAS_H, fill=C['bg'])

# ---------- 大标题 ----------
T(TITLE['x'], TITLE['y'] - TITLE['size'] * 0.86, 1000, TITLE['text'], TITLE['size'],
  800, TITLE['color'], tag='标题')

# ---------- 左表容器 ----------
add_rect(sh, TBL['x'], TBL['y'], TBL['w'], TBL['h'], fill=C['white'], line=C['rborder'], line_w=2, radius=TBL['r'])
hdr_bot = HDR['y'] + HDR['h']
row_h = (SUM['y'] - hdr_bot) / 6.0
# 行条纹（1/3/5）
for i in (0, 2, 4):
    top = hdr_bot + i * row_h
    add_rect(sh, TBL['x'] + 2, top, TBL['w'] - 4, row_h, fill=C['stripe'])
# 表头带：圆角矩形 + 下半覆盖（等效仅上圆角）
add_rect(sh, TBL['x'], HDR['y'], TBL['w'], HDR['h'], fill=HDR['bg'], radius=TBL['r'])
add_rect(sh, TBL['x'], HDR['y'] + TBL['r'], TBL['w'], HDR['h'] - TBL['r'], fill=HDR['bg'])
for i, sx in enumerate(HDR_SEPS):
    add_rect(sh, sx, HDR['y'] + 14, 2, HDR['h'] - 28, fill='#FFFFFF')
for t in HDR_TEXT:
    T(t['cx'] - 80, t['cy'] - t['size'] * 0.55, 160, t['t'], t['size'], t['weight'],
      t['color'], align='c', anchor='m', tag='表头' + t['t'])
# 行分隔线
for i in range(1, 6):
    top = hdr_bot + i * row_h
    add_rect(sh, TBL['x'] + 2, top - 1, TBL['w'] - 4, 2, fill=C['sep_line'])

# ---------- 6 行 ----------
IC_R = 31           # 行图标圆半径
for i, r in enumerate(ROWS):
    cy = ROW_CY[i]
    kind = 'db_fill' if i == 2 else ['target', 'gear', 'db_fill', 'laptop', 'people', 'shield'][i]
    # 图标圆
    add_oval(sh, 78, cy, IC_R, fill=r['icon'])
    ix, iy = 78, cy
    if kind == 'target':
        add_oval(sh, ix, iy, 18, line='#FFFFFF', line_w=2.2)
        add_oval(sh, ix, iy, 10, line='#FFFFFF', line_w=2.2)
        add_oval(sh, ix, iy, 3.2, fill='#FFFFFF')
        add_line(sh, ix + 2.5, iy - 2.5, ix + 22, iy - 22, '#FFFFFF', w_px=2.6)
        add_line(sh, ix + 13, iy - 26, ix + 20, iy - 19, '#FFFFFF', w_px=2.2)
        add_line(sh, ix + 20, iy - 29, ix + 27, iy - 22, '#FFFFFF', w_px=2.2)
    elif kind == 'gear':
        donut = sh.add_shape(MSO_SHAPE.DONUT, E(ix - 17), E(iy - 17), E(34), E(34))
        donut.fill.solid(); donut.fill.fore_color.rgb = rgb('#FFFFFF')
        donut.line.fill.background()
        try:
            donut.adjustments[0] = 0.42
        except Exception:
            pass
        for k in range(8):
            tooth = add_rect(sh, ix - 5, iy - 23, 10, 7.5, fill='#FFFFFF', radius=1.5)
            tooth.rotation = k * 45
        add_oval(sh, ix, iy, 4.6, fill=r['icon'])
    elif kind in ('db_fill', 'db'):
        filled = (kind == 'db_fill')
        if filled:
            add_rect(sh, ix - 18, iy - 10, 36, 20, fill='#FFFFFF', radius=6)
            add_ellipse(sh, ix, iy - 9, 18, 7.5, fill='#FFFFFF')
            add_rect(sh, ix - 18, iy - 3, 36, 3, fill=r['icon'])
            add_rect(sh, ix - 18, iy + 5, 36, 3, fill=r['icon'])
        else:
            add_ellipse(sh, ix, iy - 9, 18, 7.5, fill=None, line='#FFFFFF', line_w=2.2)
            add_rect(sh, ix - 18, iy - 9, 36, 19, fill=None, line='#FFFFFF', line_w=2.2, radius=8)
    elif kind == 'laptop':
        add_rect(sh, ix - 19, iy - 17, 38, 23, fill=None, line='#FFFFFF', line_w=2.4, radius=2)
        add_rect(sh, ix - 25, iy + 6, 50, 8, fill='#FFFFFF', radius=3)
    elif kind == 'people':
        add_oval(sh, ix + 10.5, iy - 10.5, 6.5, fill='#FFFFFF')
        add_oval(sh, ix - 8, iy - 8, 8.5, fill='#FFFFFF')
        add_rect(sh, ix + 2, iy - 1, 17, 12, fill='#FFFFFF', radius=6)
        add_rect(sh, ix - 21, iy + 1, 26, 14, fill='#FFFFFF', radius=7)
    elif kind == 'shield':
        shield_shape(ix, iy, IC_R, 2.6)
    # 名称 / 权重
    T(130, cy - 13, 120, r['name'], 27, 500, C['navy'], tag='名称' + r['name'])
    T(311 - 60, cy - 4 - 14, 120, r['w'], 25, 500, C['navy'], align='c', tag='权重')
    # 现状
    by1, by2 = BAR_Y(cy)
    T(CUR_X0 + 1, by1 - 32, 120, r['cur'], 25, 700, C['navy'], tag='分数')
    add_rect(sh, CUR_X0, by1, CUR_TRK - CUR_X0, by2 - by1, fill=C['track'], radius=2)
    add_rect(sh, CUR_X0 + 1, by1, r['fw'], by2 - by1, fill=r['cur_c'], radius=2)
    # 目标
    T(TGT_X0 + 1, by1 - 32, 120, r['tgt'], 25, 700, C['navy'], tag='分数')
    add_rect(sh, TGT_X0, by1, TGT_TRK - TGT_X0, by2 - by1, fill=C['track_b'], radius=2)
    if r['name'] == '战略':
        add_rect(sh, TGT_X0 + 1, by1, STRATEGY_TGT_SPLIT - TGT_X0, by2 - by1, fill=C['steel_dk'], radius=2)
        add_rect(sh, STRATEGY_TGT_SPLIT, by1, r['tw'] - (STRATEGY_TGT_SPLIT - TGT_X0), by2 - by1, fill=C['steel'], radius=2)
    else:
        add_rect(sh, TGT_X0 + 1, by1, r['tw'], by2 - by1, fill=r['tgt_c'], radius=2)

# ---------- 合计行 ----------
sy = SUM['y']
add_rect(sh, TBL['x'], sy, TBL['w'], SUM['h'], fill=SUM['bg'], radius=TBL['r'])
add_rect(sh, TBL['x'], sy, TBL['w'], SUM['h'] - TBL['r'], fill=SUM['bg'])
for it in SUM['items']:
    if it['kind'] == 'label':
        T(it['cx'] - 90, it['cy'] - it['size'] * 0.62, 180, it['t'], it['size'], it['weight'],
          it['color'], align='c', anchor='m', tag='合计标签')
    else:
        T(it['cx'] - 90, it['cy'] - it['size'] * 0.88, 180, it['t'], it['size'], it['weight'],
          it['color'], align='c', tag='合计值')

# ---------- 右面板 ----------
P = RPANEL
add_rect(sh, P['x'], P['y'], P['w'], P['h'], fill=C['white'], line=C['rborder'], line_w=2, radius=P['r'])
add_rect(sh, P['x'], P['y'], P['w'], P['band_h'], fill=P['bg_band'], radius=P['r'])
add_rect(sh, P['x'], P['y'] + P['r'], P['w'], P['band_h'] - P['r'], fill=P['bg_band'])
T(P['title_x'], P['title_cy'] - P['title_size'] * 0.62, 400, P['title'], P['title_size'], 700,
  C['navy'], tag='右标题')
T(P['note1_x'] - 200, P['note1_cy'] - 14, 200, P['note1'], P['note1_size'], 500, '#5A6472',
  align='r', tag='注1')
T(P['note2_x'] - 200, P['note2_cy'] - 12, 200, P['note2'], P['note2_size'], 400, '#6B7280',
  align='r', tag='注2')
for i, g in enumerate(GAPS):
    cy = g['cy']
    bx, bw, bh = BADGE['x'], BADGE['w'], BADGE['h']
    add_rect(sh, bx, cy - bh // 2, bw, bh, fill=g['badge'], radius=BADGE['r'])
    T(bx, cy - 14, bw, str(i + 1), 28, 700, C['white'], align='c', tag='徽章数字')
    T(1127, cy - 13, 100, g['name'], 26, 500, C['navy'], tag='右名')
    by1 = cy - GAP_BAR_H // 2
    add_rect(sh, GAP_BAR_X0, by1, GAP_BAR_END - GAP_BAR_X0, GAP_BAR_H, fill=C['track'], radius=8)
    add_rect(sh, GAP_BAR_X0, by1, g['vw'], GAP_BAR_H, fill=g['bar'], radius=8)
    T(1560, cy - 19, 120, g['val'], 38, 700, g['vc'], align='r', tag='右值')

# ---------- 底部面板 ----------
B = BOT
add_rect(sh, B['x'], B['y'], B['w'], B['h'], fill=B['bg'], radius=B['r'])
T(B['title_x'], B['title_cy'] - B['title_size'] * 0.62, 400, B['title'], B['title_size'], 700,
  C['navy'], tag='底标题')
T(B['note_x2'] - 300, B['note_cy'] - 10, 300, B['note'], B['note_size'], 400, '#6A7280',
  align='r', tag='底注')
for i, cd in enumerate(CARDS):
    add_rect(sh, cd['x'], cd['y'], cd['w'], cd['h'], fill=cd['bg'], radius=cd['r'])
    add_oval(sh, cd['icon_cx'], cd['icon_cy'], 35, fill=cd['icon_bg'])
    ix, iy = cd['icon_cx'], cd['icon_cy']
    if cd['icon'] == 'db':
        add_ellipse(sh, ix, iy - 8.5, 14.5, 6, fill=None, line='#FFFFFF', line_w=2)
        add_rect(sh, ix - 14.5, iy - 8.5, 29, 17, fill=None, line='#FFFFFF', line_w=2, radius=5)
    elif cd['icon'] == 'shield':
        shield_shape(ix, iy, 25, 2.4)
    elif cd['icon'] == 'people':
        add_oval(sh, ix + 8, iy - 8.5, 5.2, fill='#FFFFFF')
        add_oval(sh, ix - 6.5, iy - 6.5, 6.8, fill='#FFFFFF')
        add_rect(sh, ix + 1.5, iy - 1, 13.5, 9.5, fill='#FFFFFF', radius=4.5)
        add_rect(sh, ix - 17, iy + 1, 21, 11, fill='#FFFFFF', radius=5.5)
    bxx = cd['x'] + 13
    add_rect(sh, bxx, cd['y'] + 21, BADGE_S['w'], BADGE_S['h'], fill=cd['badge_bg'], radius=BADGE_S['r'])
    T(bxx, cd['y'] + 21 + 24 - 14, BADGE_S['w'], cd['badge'], BADGE_S['size'], 700, C['white'],
      align='c', tag='卡徽章')
    T(bxx + 66, cd['y'] + 42 - 12, 80, cd['label'], 25, 700, C['navy'], tag='卡标签')
    T(bxx + 124, cd['y'] + 42 - 11, 20, '|', 24, 300, '#B9C0C9', align='c', tag='卡分隔')
    T(cd['text_x'], cd['y'] + 40 - 7, cd['x'] + cd['w'] - cd['text_x'] - 10, cd['text'], 20, 400,
      '#3A4450', tag='卡文本')

# ---------- 水印 ----------
WM_C = '#BBB9BC'
add_rect(sh, WATERMARK['wx'] - 29, WATERMARK['wy'] - 22, 40, 30, fill=WM_C, radius=9)
add_oval(sh, WATERMARK['wx'] - 16, WATERMARK['wy'] - 11, 2.8, fill='#EBEDE8')
add_oval(sh, WATERMARK['wx'] - 3, WATERMARK['wy'] - 11, 2.8, fill='#EBEDE8')
add_rect(sh, WATERMARK['wx'] - 3, WATERMARK['wy'] - 1.5, 33, 26, fill=WM_C, radius=8)
add_oval(sh, WATERMARK['wx'] + 8.7, WATERMARK['wy'] + 8, 2.5, fill='#EBEDE8')
add_oval(sh, WATERMARK['wx'] + 18.6, WATERMARK['wy'] + 8, 2.5, fill='#EBEDE8')
T(WATERMARK['x2'] - 620, WATERMARK['cy'] - WATERMARK['size'] * 0.62, 620, WATERMARK['text'],
  WATERMARK['size'], 700, WM_C, align='r', tag='水印')

prs.save(OUT)
print(f'N4 自检: 输出 {OUT}')
print(f'量宽溢出警告: {len(WARN)}')
for w in WARN[:10]:
    print('  ', w)
