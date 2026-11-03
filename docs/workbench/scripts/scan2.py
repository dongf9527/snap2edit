#!/usr/bin/env python3
"""精确扫描关键行的边界"""
from PIL import Image
import numpy as np

img = Image.open('/home/z/my-project/upload/002-框架与实施工具.png').convert('RGB')
a = np.array(img).astype(int)
H, W = a.shape[:2]

def seg_scan(fixed, axis, lo, hi, thresh=10):
    """沿某方向扫描，输出灰度分段变化点"""
    if axis == 'x':
        vals = a[fixed, lo:hi, :].sum(axis=1) / 3
    else:
        vals = a[lo:hi, fixed, :].sum(axis=1) / 3
    out = []
    base = vals[0]
    for i in range(1, len(vals)):
        if abs(vals[i] - base) > thresh:
            out.append((lo+i, int(base), int(vals[i])))
            base = vals[i]
        else:
            base = base*0.9 + vals[i]*0.1
    return out

# y=175：行1 cell 上部空白带（cell 背景浅灰 vs 白色间隔）
print("== y=175 ==", seg_scan(175, 'x', 150, 1728))
# y=470：行3 上部
print("== y=470 ==", seg_scan(470, 'x', 150, 1728))
# y=630：行4 上部
print("== y=630 ==", seg_scan(630, 'x', 150, 1728))
# y=790：表格行
print("== y=790 ==", seg_scan(790, 'x', 150, 1728))
# x=200：col1 内部（避开内容，找行边界）— 用 x=490 (col1 右边缘内侧)
print("== x=490 ==", seg_scan(490, 'y', 90, 972))
# x=1430（来源卡左缘）
print("== x=1430 ==", seg_scan(1430, 'y', 90, 972))
# x=80（行标签中部）
print("== x=80 ==", seg_scan(80, 'y', 90, 972))
# y=110（chevron 中部）
print("== y=110 ==", seg_scan(110, 'x', 150, 1728))
