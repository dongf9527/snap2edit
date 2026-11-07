#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
004《准备度评估的六维证据清单》— 交付物② 原生 PPTX 生成脚本
坐标系：1728x972 px → 13.333x7.5 英寸（16:9），全原生文本框+形状，Picture=0。
复用 build_html 的数据与共享几何（gear_pts/shield_pts/arc_pts），
复用 docs/workbench/scripts/pptx_lib.py 的文本框/形状/自由多边形基元。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# append 而非 insert(0)：本目录的 build_html 必须优先于 workbench 里的同名历史脚本
sys.path.append(os.path.join(HERE, '..', 'workbench', 'scripts'))

import pptx_lib as L
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.enum.shapes import MSO_SHAPE

from build_html import (W, H, NAVY, TITLE_C, INK, GRAY, SEP, HSEP, FOOT_BG, WM,
                        ACCENTS, EICONS, SCORE_BG, SCORE_ACC,
                        COLS, HEADER_Y, HEADER_H, ROWS_Y, ROW_H,
                        SCORE_Y, SCORE_H, FOOT_Y, FOOT_H, CARDS_X,
                        ROWS, SCORES, gear_pts, shield_pts, arc_pts)

# ---- 坐标系适配：1728x972 px → 13.333x7.5 in ----
PXE = 12192000 / W            # EMU per px = 7055.556
L.EMU_PX = PXE
L.PT = lambda px: Pt(px * PXE / 12700)   # 1px = 0.5556pt

prs = Presentation()
prs.slide_width = Emu(12192000)
prs.slide_height = Emu(6858000)
slide = prs.slides.add_slide(prs.slide_layouts[6])

# ---------- 基元封装 ----------
def shape(st, x, y, w, h, fill=None, line=None, lw=2, adj=None):
    return L.add_shape(slide, st, x, y, w, h, fill, line, lw, adj)

def fline(x1, y1, x2, y2, c, w):
    L.add_line(slide, x1, y1, x2, y2, c, w)

def free(pts, fill=None, line=None, lw=1.6, close=True):
    return L.add_freeform(slide, pts, fill, line, lw, close)

def txt(x, y_base, s, size, color, bold=False, align='start', weight=400):
    return L.add_text_baseline(slide, x, y_base, s, size, color, bold, align, weight=weight)

def oval(cx, cy, rx, ry, fill=None, line=None, lw=2):
    return shape(MSO_SHAPE.OVAL, cx - rx, cy - ry, rx * 2, ry * 2, fill, line, lw)

# ---------- 图标 ----------
def ic_target(cx, cy, s, c):
    oval(cx, cy, s * .46, s * .46, None, c, s * .10)
    oval(cx, cy, s * .27, s * .27, None, c, s * .09)
    oval(cx, cy, s * .08, s * .08, c)
    x1, y1 = cx + s * .52, cy - s * .52
    fline(x1, y1, cx + s * .06, cy - s * .06, c, s * .07)
    free([(x1 + s * .10, y1 - s * .02), (x1 - s * .02, y1 + s * .10),
          (x1 - s * .10, y1 - s * .10)], c)

def ic_gear(cx, cy, s, c):
    free(gear_pts(cx, cy, s), c)
    oval(cx, cy, s * .115, s * .115, '#FFFFFF')

def ic_database(cx, cy, s, c):
    rx, ry = s * .40, s * .15
    top, bot = cy - s * .30, cy + s * .30
    oval(cx, top, rx, ry, None, c, s * .085)
    free(arc_pts(cx, top + s * .30, rx, ry, 0, 180), None, c, s * .085, close=False)
    free(arc_pts(cx, top + s * .60, rx, ry, 0, 180), None, c, s * .085, close=False)
    fline(cx - rx, top, cx - rx, bot, c, s * .085)
    fline(cx + rx, top, cx + rx, bot, c, s * .085)

def ic_cloud(cx, cy, s, c):
    oval(cx - s * .22, cy + s * .04, s * .21, s * .21, c)
    oval(cx + s * .02, cy - s * .12, s * .27, s * .27, c)
    oval(cx + s * .26, cy + s * .02, s * .20, s * .20, c)
    shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx - s * .30, cy - s * .02, s * .72, s * .30, c,
          adj=0.5)

def ic_people(cx, cy, s, c):
    def person(px, py, k):
        oval(px, py - s * .20 * k, s * .15 * k, s * .15 * k, c)
        shape(MSO_SHAPE.ROUNDED_RECTANGLE, px - s * .21 * k, py - s * .02 * k,
              s * .42 * k, s * .26 * k, c, adj=0.5)
    person(cx + s * .18, cy + s * .08, 0.82)
    person(cx - s * .14, cy + s * .02, 1.0)

def ic_shield_check(cx, cy, s, c):
    free(shield_pts(cx, cy, s), c)
    fline(cx - s * .15, cy - s * .02, cx - s * .04, cy + s * .12, '#FFFFFF', s * .11)
    fline(cx - s * .04, cy + s * .12, cx + s * .18, cy - s * .16, '#FFFFFF', s * .11)

def ic_person_fill(cx, cy, s, c):
    oval(cx, cy - s * .17, s * .16, s * .16, c)
    pts = arc_pts(cx, cy + s * .30, s * .30, s * .30, 180, 360)
    pts += [(cx + s * .30, cy + s * .40), (cx - s * .30, cy + s * .40)]
    free(pts, c)

def ic_doc_base(cx, cy, s, c):
    """文档底版：五边形轮廓 + 折角线。返回 (x0,y0,w,h)"""
    x0, y0 = cx - s * .36, cy - s * .44
    w, h, f = s * .72, s * .88, s * .16
    free([(x0, y0), (x0 + w - f, y0), (x0 + w, y0 + f), (x0 + w, y0 + h), (x0, y0 + h)],
         None, c, s * .085)
    fline(x0 + w - f, y0, x0 + w - f, y0 + f, c, s * .07)
    fline(x0 + w - f, y0 + f, x0 + w, y0 + f, c, s * .07)
    return x0, y0, w, h

def ic_doc_chart(cx, cy, s, c):
    x0, y0, w, h = ic_doc_base(cx, cy, s, c)
    bw = s * .11
    shape(MSO_SHAPE.RECTANGLE, x0 + w * .18, y0 + h * .52, bw, h * .30, c)
    shape(MSO_SHAPE.RECTANGLE, x0 + w * .40, y0 + h * .40, bw, h * .42, c)
    shape(MSO_SHAPE.RECTANGLE, x0 + w * .62, y0 + h * .28, bw, h * .54, c)

def ic_doc_search(cx, cy, s, c):
    x0, y0, w, h = ic_doc_base(cx, cy, s, c)
    fline(x0 + w * .16, y0 + h * .20, x0 + w * .80, y0 + h * .20, c, s * .065)
    fline(x0 + w * .16, y0 + h * .34, x0 + w * .66, y0 + h * .34, c, s * .065)
    fline(x0 + w * .16, y0 + h * .48, x0 + w * .58, y0 + h * .48, c, s * .065)
    oval(cx + s * .20, cy + s * .22, s * .155, s * .155, None, c, s * .075)
    fline(cx + s * .31, cy + s * .33, cx + s * .42, cy + s * .44, c, s * .075)

def ic_doc_shield(cx, cy, s, c):
    x0, y0, w, h = ic_doc_base(cx, cy, s, c)
    fline(x0 + w * .16, y0 + h * .22, x0 + w * .80, y0 + h * .22, c, s * .07)
    fline(x0 + w * .16, y0 + h * .38, x0 + w * .72, y0 + h * .38, c, s * .07)
    fline(x0 + w * .16, y0 + h * .54, x0 + w * .58, y0 + h * .54, c, s * .07)
    sx, sy = cx + s * .18, cy + s * .22
    free(shield_pts(sx, sy, s * .42), c)
    fline(sx - s * .09, sy + s * .00 - s * .01, sx - s * .02, sy + s * .08, '#FFFFFF', s * .075)
    fline(sx - s * .02, sy + s * .08, sx + s * .12, sy - s * .10, '#FFFFFF', s * .075)

def ic_flowchart(cx, cy, s, c):
    bs = s * .22
    shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx - bs / 2, cy - s * .40, bs, bs, c, adj=0.2)
    shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx - s * .36 - bs / 2, cy + s * .16, bs, bs, c, adj=0.2)
    shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx + s * .36 - bs / 2, cy + s * .16, bs, bs, c, adj=0.2)
    fline(cx, cy - s * .40 + bs, cx, cy + s * .04, c, s * .06)
    fline(cx - s * .36 + bs / 2, cy + s * .04, cx + s * .36 - bs / 2, cy + s * .04, c, s * .06)
    fline(cx - s * .36 + bs / 2, cy + s * .04, cx - s * .36 + bs / 2, cy + s * .16, c, s * .06)
    fline(cx + s * .36 - bs / 2, cy + s * .04, cx + s * .36 - bs / 2, cy + s * .16, c, s * .06)

def ic_server(cx, cy, s, c):
    for yy in [-0.335, -0.02, 0.295]:
        ry = cy + s * yy
        shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx - s * .40, ry, s * .80, s * .24, c, adj=0.25)
        oval(cx - s * .26, ry + s * .12, s * .045, s * .045, '#FFFFFF')
        oval(cx - s * .13, ry + s * .12, s * .045, s * .045, '#FFFFFF')
        fline(cx + s * .08, ry + s * .12, cx + s * .30, ry + s * .12, '#FFFFFF', s * .05)

def ic_presenter(cx, cy, s, c):
    bx, by = cx + s * .06, cy - s * .36
    shape(MSO_SHAPE.ROUNDED_RECTANGLE, bx, by, s * .58, s * .46, None, c, s * .07, adj=0.08)
    shape(MSO_SHAPE.RECTANGLE, bx + s * .08, by + s * .20, s * .07, s * .16, c)
    shape(MSO_SHAPE.RECTANGLE, bx + s * .20, by + s * .12, s * .07, s * .24, c)
    shape(MSO_SHAPE.RECTANGLE, bx + s * .32, by + s * .24, s * .07, s * .12, c)
    oval(cx - s * .26, cy - s * .18, s * .12, s * .12, c)
    shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx - s * .38, cy - s * .02, s * .24, s * .42, c, adj=0.4)
    fline(cx - s * .14, cy + s * .02, bx + s * .02, by + s * .14, c, s * .055)

def ic_dockey(cx, cy, s, c):
    x0, y0 = cx - s * .34, cy - s * .40
    w, h = s * .68, s * .80
    shape(MSO_SHAPE.RECTANGLE, x0, y0, w, h, None, c, s * .10)
    fline(x0 + w * .22, y0 + h * .48, x0 + w * .42, y0 + h * .68, c, s * .10)
    fline(x0 + w * .42, y0 + h * .68, x0 + w * .78, y0 + h * .28, c, s * .10)

def ic_wechat(cx, cy, s, c):
    oval(cx - s * .14, cy - s * .08, s * .30, s * .24, c)
    free([(cx - s * .30, cy + s * .06), (cx - s * .30, cy + s * .26), (cx - s * .12, cy + s * .12)], c)
    oval(cx - s * .22, cy - s * .12, s * .035, s * .035, '#FFFFFF')
    oval(cx - s * .06, cy - s * .12, s * .035, s * .035, '#FFFFFF')
    oval(cx + s * .22, cy + s * .10, s * .24, s * .19, c)
    free([(cx + s * .34, cy + s * .20), (cx + s * .36, cy + s * .34), (cx + s * .20, cy + s * .24)], c)
    oval(cx + s * .16, cy + s * .06, s * .03, s * .03, '#FFFFFF')
    oval(cx + s * .29, cy + s * .06, s * .03, s * .03, '#FFFFFF')

# ---------- 组装（与 HTML 相同顺序） ----------
# 背景 + 外框
shape(MSO_SHAPE.RECTANGLE, 0, 0, W, H, '#FFFFFF')
shape(MSO_SHAPE.ROUNDED_RECTANGLE, 3, 3, W - 6, H - 6, None, '#E4E7EA', 2, adj=0.02)

# 标题
txt(864, 79, '准备度评估的六维证据清单', 66, TITLE_C, True, 'center')

# 表头（顶部圆角矩形）
hdr = shape(MSO_SHAPE.ROUND_2_SAME_RECTANGLE, 12, HEADER_Y, COLS[4] - 12, HEADER_H, NAVY,
            adj=0.20)
try:
    hdr.adjustments[1] = 0.0
except Exception:
    pass
for cx_ in COLS[1:-1]:
    fline(cx_, HEADER_Y + 4, cx_, HEADER_Y + HEADER_H - 4, HSEP, 2)
txt((COLS[0] + COLS[1]) / 2, 148, '维度', 28, '#FFFFFF', True, 'center')
txt((COLS[1] + COLS[2]) / 2, 148, '关键问题', 28, '#FFFFFF', True, 'center')
txt((COLS[2] + COLS[3]) / 2, 148, '证据（示例）', 28, '#FFFFFF', True, 'center')
txt((COLS[3] + COLS[4]) / 2, 148, '负责人', 28, '#FFFFFF', True, 'center')

# 网格线
for i in range(1, 6):
    y = ROWS_Y + ROW_H * i
    fline(12, y, 1716, y, SEP, 2)
for cx_ in COLS[1:-1]:
    fline(cx_, ROWS_Y, cx_, ROWS_Y + ROW_H * 6, SEP, 2)

# 六行
ICONS1 = [ic_target, ic_gear, ic_database, ic_cloud, ic_people, ic_shield_check]
ICONS3 = [ic_doc_chart, ic_flowchart, ic_doc_search, ic_server, ic_presenter, ic_doc_shield]

for i, (name, question, evids, owner) in enumerate(ROWS):
    top = ROWS_Y + ROW_H * i
    cy = top + ROW_H / 2
    acc = ACCENTS[i]
    shape(MSO_SHAPE.ROUNDED_RECTANGLE, 53, top + 8, 78, 78, acc, adj=0.15)
    txt(92, top + 60, str(i + 1), 40, '#FFFFFF', True, 'center')
    ICONS1[i](170, cy - 2, 52, acc)
    txt(234, cy + 10, name, 30, INK, True)
    txt(394, cy + 9, question, 32, INK, False)
    ICONS3[i](895, cy, 64, EICONS[i])
    for j, t in enumerate(evids):
        by = top + (39 if j == 0 else 74)
        oval(958, by - 9, 4.5, 4.5, NAVY)
        txt(975, by, t, 28, INK, False)
    ic_person_fill(1440, cy, 52, '#1C3B52')
    txt(1494, cy + 13, owner, 30, INK, False)

# 评分五档
shape(MSO_SHAPE.ROUNDED_RECTANGLE, 20, 792, 152, 88, NAVY, adj=0.11)
txt(96, 848, '评分五档', 32, '#FFFFFF', True, 'center')
for i, (num, tit, sub) in enumerate(SCORES):
    x0, x1 = CARDS_X[i]
    shape(MSO_SHAPE.ROUNDED_RECTANGLE, x0, SCORE_Y, x1 - x0, SCORE_H, SCORE_BG[i], adj=0.10)
    shape(MSO_SHAPE.ROUNDED_RECTANGLE, x0 + 14, 798, 62, 62, SCORE_ACC[i], adj=0.19)
    txt(x0 + 45, 841, num, 34, '#FFFFFF', True, 'center')
    txt(x0 + 103, 823, tit, 26, INK, True)
    txt(x0 + 103, 860, sub, 19, GRAY, False)

# 页脚 + 水印
shape(MSO_SHAPE.ROUNDED_RECTANGLE, 12, FOOT_Y, 1698, FOOT_H, FOOT_BG, adj=0.12)
ic_dockey(58, FOOT_Y + 25, 30, '#1F3A52')
txt(92, 935, '每项须证据支持，不以访谈印象替代验证。', 25, INK, False)
ic_wechat(1074, 893, 62, WM)
txt(1693, 923, '公众号·解决方案研究所', 54, WM, True, 'end')

out = os.path.join(HERE, '六维证据清单复刻.pptx')
prs.save(out)
print('written:', out)
