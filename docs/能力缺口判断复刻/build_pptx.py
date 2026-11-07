#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
005《准备度评分与能力缺口诊断》— 交付物② 原生 PPTX 生成脚本
坐标系：1728x972 px → 13.333x7.5 英寸（16:9），全原生文本框+形状，Picture=0。
复用 build_html 的数据与共享几何（gear_pts/arc_pts），
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

from build_html import (W, H, TITLE_C, INK, NUM_C, WEIGHT_C, HEADER_NAVY, SEP, VSEP,
                        TOT_BG, TOT_SEP, TRACK, STRIP_BG, PANEL_LINE, PTRACK,
                        BAND_BG, NOTE_C, WM,
                        ROWS, ROW_CY, ROW_SEP, PBARS, PBAR_CY, ACTIONS,
                        TBL_X0, TBL_X1, HDR_Y, HDR_H, COLS,
                        NOW_BAR_X, NOW_BAR_W, TGT_BAR_X, TGT_BAR_W,
                        TOT_Y0, TOT_Y1, TOT_SEPS, STRIP,
                        PBAR_X0, PBAR_W, PVAL_X,
                        gear_pts, arc_pts)

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

def fline(x1, y1, x2, y2, c, w, dash=None):
    return L.add_line(slide, x1, y1, x2, y2, c, w)

def free(pts, fill=None, line=None, lw=1.6, close=True):
    return L.add_freeform(slide, pts, fill, line, lw, close)

def txt(x, y_base, s, size, color, bold=False, align='start', weight=400):
    """LibreOffice 实测：文字整体较基线公式高 ~5px，此处校正"""
    return L.add_text_baseline(slide, x, y_base + 5, s, size, color, bold, align, weight=weight)

def oval(cx, cy, rx, ry, fill=None, line=None, lw=2):
    return shape(MSO_SHAPE.OVAL, cx - rx, cy - ry, rx * 2, ry * 2, fill, line, lw)

# ---------- 图标（白色，绘于彩色圆内） ----------
def ic_target(cx, cy, s, c='#FFFFFF'):
    """战略：靶心 + 飞镖"""
    oval(cx - s * .05, cy + s * .05, s * .29, s * .29, None, c, s * .055)
    oval(cx - s * .05, cy + s * .05, s * .16, s * .16, None, c, s * .05)
    oval(cx - s * .05, cy + s * .05, s * .042, s * .042, c)
    x1, y1 = cx + s * .40, cy - s * .40
    fline(x1, y1, cx + s * .01, cy - s * .01, c, s * .055)
    free([(x1 + s * .085, y1 - s * .025), (x1 - s * .025, y1 + s * .085),
          (x1 - s * .095, y1 - s * .095)], c)

def ic_gear(cx, cy, s, c='#FFFFFF', bg=None):
    """流程：齿轮 + 圆心孔（孔透出圆底色）"""
    b = bg or '#616A4E'
    free(gear_pts(cx, cy, s * .74), c)
    oval(cx, cy, s * .105, s * .105, b)

def ic_database(cx, cy, s, c='#FFFFFF', bg=None):
    """数据：实心圆柱（底色分隔弧线）"""
    b = bg or '#6A594A'
    rx, ry = s * .30, s * .105
    top, bot = cy - s * .30, cy + s * .34
    pts = [(cx - rx, top), (cx + rx, top), (cx + rx, bot)]
    pts += L.bez((cx + rx, bot), (cx + rx, bot + ry), (cx - rx, bot + ry), (cx - rx, bot), n=14)
    free(pts, c)
    oval(cx, top, rx, ry, c)
    for dy in (.22, .44):
        arc = [(cx - rx, 0), (cx + rx, 0)]
        arc = L.bez((cx - rx, top + s * dy), (cx - rx, top + s * dy + ry),
                    (cx + rx, top + s * dy + ry), (cx + rx, top + s * dy), n=14)
        free(arc, None, b, s * .05, close=False)

def ic_laptop(cx, cy, s, c='#FFFFFF'):
    """技术：笔记本"""
    shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx - s * .27, cy - s * .28, s * .54, s * .38,
          None, c, s * .055, adj=0.12)
    fline(cx - s * .38, cy + s * .24, cx + s * .38, cy + s * .24, c, s * .07)

def ic_people(cx, cy, s, c='#FFFFFF'):
    """人才：双人（圆头 + 圆肩钟形身）"""
    def body_pts(px, py, k):
        hw, hh = s * .21 * k, s * .26 * k
        ytop = py - hh * .62
        pts = [(px - hw, py + hh), (px - hw, py - hh * .18)]
        pts += L.qbez((px - hw, ytop), (px - hw, ytop), (px - hw * .45, ytop), n=6)
        pts += L.qbez((px - hw * .45, ytop), (px + hw * .45, ytop), (px + hw * .45, ytop), n=2)
        pts += L.qbez((px + hw * .45, ytop), (px + hw, ytop), (px + hw, py - hh * .18), n=6)
        pts += [(px + hw, py + hh)]
        return pts
    def person(px, py, k):
        oval(px, py - s * .22 * k, s * .125 * k, s * .125 * k, c)
        free(body_pts(px, py + s * .02, k), c)
    person(cx + s * .17, cy + s * .05, 0.80)
    person(cx - s * .12, cy, 1.0)

def ic_shield(cx, cy, s, c='#FFFFFF'):
    """治理：盾牌轮廓"""
    pts = [(cx, cy - s * .34), (cx + s * .27, cy - s * .23), (cx + s * .27, cy + s * .04),
           (cx + s * .145, cy + s * .25), (cx, cy + s * .37), (cx - s * .145, cy + s * .25),
           (cx - s * .27, cy + s * .04), (cx - s * .27, cy - s * .23)]
    free(pts, None, c, s * .055)

def ic_wechat(cx, cy, w, c=WM):
    """微信双气泡（水印）"""
    h = w * 0.79
    oval(cx - w * .155, cy - h * .075, w * .315, h * .27, c)
    free([(cx - w * .30, cy + h * .10), (cx - w * .30, cy + h * .30),
          (cx - w * .125, cy + h * .16)], c)
    oval(cx - w * .225, cy - h * .11, w * .032, w * .032, '#FFFFFF')
    oval(cx - w * .085, cy - h * .11, w * .032, w * .032, '#FFFFFF')
    oval(cx + w * .17, cy + h * .10, w * .25, h * .215, c)
    free([(cx + w * .27, cy + h * .24), (cx + w * .29, cy + h * .42),
          (cx + w * .125, cy + h * .30)], c)
    oval(cx + w * .105, cy + h * .06, w * .027, w * .027, '#FFFFFF')
    oval(cx + w * .225, cy + h * .06, w * .027, w * .027, '#FFFFFF')

# ---------- 组装（与 HTML 相同顺序） ----------
# 主标题
txt(36, 88, '准备度评分与能力缺口诊断', 76, TITLE_C, True)

# 底部灰带
shape(MSO_SHAPE.RECTANGLE, 18, 795, 1694, 43, BAND_BG)

# 表头（顶部圆角）
hdr = shape(MSO_SHAPE.ROUND_2_SAME_RECTANGLE, TBL_X0, HDR_Y, TBL_X1 - TBL_X0, HDR_H,
            HEADER_NAVY, adj=0.14)
try:
    hdr.adjustments[1] = 0.0
except Exception:
    pass
for cx_ in COLS[1:-1]:
    fline(cx_ - 1.5, HDR_Y + 6, cx_ - 1.5, HDR_Y + HDR_H - 6, '#FFFFFF', 3)
txt(126, 180, '维度', 28, '#FFFFFF', True, 'center')
txt(311, 180, '权重', 28, '#FFFFFF', True, 'center')
txt(543, 164, '现状评分', 28, '#FFFFFF', True, 'center')
txt(543, 193, '(满分5)', 21, '#FFFFFF', False, 'center')
txt(865, 164, '目标评分', 28, '#FFFFFF', True, 'center')
txt(865, 193, '(满分5)', 21, '#FFFFFF', False, 'center')

# 网格 + 合计行
for y in ROW_SEP:
    fline(TBL_X0, y, TBL_X1, y, SEP, 2.5)
for cx_ in COLS[1:-1]:
    fline(cx_, HDR_Y + HDR_H, cx_, TOT_Y0, VSEP, 2)
shape(MSO_SHAPE.RECTANGLE, TBL_X0, TOT_Y0, TBL_X1 - TBL_X0, TOT_Y1 - TOT_Y0, TOT_BG)
fline(TBL_X0, 670.5, TBL_X1, 670.5, TOT_SEP, 3)
for cx_ in TOT_SEPS:
    fline(cx_ - 1.5, TOT_Y0, cx_ - 1.5, TOT_Y1, '#FFFFFF', 3)

# 六行
ICONS = [ic_target, ic_gear, ic_database, ic_laptop, ic_people, ic_shield]
for i, (name, wt, now, tgt, iconc, nowc, noww, tgtc, tgtw, stubw) in enumerate(ROWS):
    cy = ROW_CY[i]
    oval(76, cy, 29, 29, iconc)
    ICONS[i](76, cy, 54, '#FFFFFF', iconc) if ICONS[i] in (ic_gear, ic_database) \
        else ICONS[i](76, cy, 54, '#FFFFFF')
    txt(130, cy + 9, name, 27, WEIGHT_C, True)
    txt(311, cy + 7, wt, 26, WEIGHT_C, False, 'center')
    txt(425, cy - 5, now, 26, NUM_C, False)
    shape(MSO_SHAPE.ROUNDED_RECTANGLE, NOW_BAR_X, cy + 2, NOW_BAR_W, 19, TRACK, adj=0.10)
    shape(MSO_SHAPE.ROUNDED_RECTANGLE, NOW_BAR_X, cy + 2, noww, 19, nowc, adj=0.10)
    txt(744, cy - 5, tgt, 26, NUM_C, False)
    shape(MSO_SHAPE.ROUNDED_RECTANGLE, TGT_BAR_X, cy + 2, TGT_BAR_W, 19, TRACK, adj=0.10)
    if stubw:
        shape(MSO_SHAPE.ROUNDED_RECTANGLE, TGT_BAR_X, cy + 2, stubw, 19, '#264059', adj=0.10)
        shape(MSO_SHAPE.ROUNDED_RECTANGLE, TGT_BAR_X + stubw, cy + 2, tgtw - stubw, 19, tgtc, adj=0.10)
    else:
        shape(MSO_SHAPE.ROUNDED_RECTANGLE, TGT_BAR_X, cy + 2, tgtw, 19, tgtc, adj=0.10)

# 合计行
txt(126, 727, '合计', 28, '#0D223E', True, 'center')
txt(311, 725, '100%', 26, '#17324E', False, 'center')
txt(489, 706, '加权现状评分', 22, '#21324C', False, 'center')
txt(487, 748, '2.75', 36, '#0E1F3C', True, 'center')
txt(702, 706, '加权目标评分', 22, '#21324C', False, 'center')
txt(702, 748, '3.95', 36, '#626E4B', True, 'center')
txt(912, 705, '差距', 22, '#21324C', False, 'center')
txt(913, 748, '1.20', 36, '#8F8177', True, 'center')

# 右面板标题条
sx0, sy0, sx1, sy1 = STRIP
strip = shape(MSO_SHAPE.ROUND_2_SAME_RECTANGLE, sx0, sy0, sx1 - sx0, sy1 - sy0,
              STRIP_BG, adj=0.10)
try:
    strip.adjustments[1] = 0.0
except Exception:
    pass
txt(1057, 183, '能力缺口差距排序', 33, '#0E2440', True)
txt(1687, 177, '差距分值', 21, '#22354E', True, 'end')
txt(1687, 197, '(目标-现状)', 17, '#22354E', False, 'end')
fline(1206, 225, 1206, 703, PANEL_LINE, 2)

for i, (rank, name, val, bc, fc, fw) in enumerate(PBARS):
    cy = PBAR_CY[i]
    shape(MSO_SHAPE.ROUNDED_RECTANGLE, 1050, cy - 27, 54, 54, bc, adj=0.22)
    txt(1077, cy + 11, rank, 30, '#FFFFFF', True, 'center')
    txt(1128, cy + 10, name, 28, INK, True)
    shape(MSO_SHAPE.ROUNDED_RECTANGLE, PBAR_X0, cy - 23.5, PBAR_W, 47, PTRACK, adj=0.06)
    shape(MSO_SHAPE.ROUNDED_RECTANGLE, PBAR_X0, cy - 23.5, fw, 47, fc, adj=0.06)
    txt(PVAL_X, cy + 11, val, 31, fc, True, 'end')

# 底部行动区
txt(41, 819, '重点行动与优先事项', 30, '#0E2440', True)
txt(1685, 819, '分值与权重用于项目决策；非行业基准。', 16, NOTE_C, False, 'end')

for i, (icx, icc, bx0, bx1, boxc, bdx, bdc, name, nx, dvx, t, tx, tfs) in enumerate(ACTIONS):
    oval(icx, 882, 37.5, 37.5, icc)
    k = [2, 5, 4][i]
    ICONS[k](icx, 882, 58, '#FFFFFF', icc) if ICONS[k] in (ic_gear, ic_database) \
        else ICONS[k](icx, 882, 58, '#FFFFFF')
    shape(MSO_SHAPE.ROUNDED_RECTANGLE, bx0, 850, bx1 - bx0, 86, boxc, adj=0.14)
    shape(MSO_SHAPE.ROUNDED_RECTANGLE, bdx, 868, 48, 47, bdc, adj=0.20)
    txt(bdx + 24, 901, str(i + 1), 26, '#FFFFFF', True, 'center')
    txt(nx, 902, name, 27, INK, True)
    fline(dvx, 878, dvx, 906, '#A8A9AD', 2.5)
    txt(tx, 902, t, tfs, INK, False)

# 水印
ic_wechat(1088, 901, 66, WM)
txt(1134, 918, '公众号·解决方案研究所', 50, WM, False)

out = os.path.join(HERE, '能力缺口判断复刻.pptx')
prs.save(out)
n_shapes = len(slide.shapes)
n_pics = sum(1 for sh in slide.shapes if sh.shape_type == 13)
print('written:', out, f'| shapes={n_shapes} pictures={n_pics}')
