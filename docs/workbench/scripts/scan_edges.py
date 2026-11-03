#!/usr/bin/env python3
"""在空白带上扫描边界，避免内容干扰"""
from PIL import Image
import numpy as np

img = Image.open('/home/z/my-project/upload/002-框架与实施工具.png').convert('RGB')
a = np.array(img).astype(int)
H, W = a.shape[:2]

def scan_x(y, x1=0, x2=W, label=""):
    """沿水平方向打印颜色分段（灰度化后找边界）"""
    row = a[y, x1:x2, :].sum(axis=1) / 3
    print(f"--- y={y} {label} ---")
    prev = row[0]; start = x1
    for i in range(1, x2-x1):
        if abs(row[i] - prev) > 12:
            print(f"  x={x1+i:4d}: {int(prev)} -> {int(row[i])}")
            prev = row[i]
        else:
            prev = (prev*0.85 + row[i]*0.15)

def scan_y(x, y1=0, y2=H, label=""):
    col = a[y1:y2, x, :].sum(axis=1) / 3
    print(f"--- x={x} {label} ---")
    prev = col[0]; start = y1
    for i in range(1, y2-y1):
        if abs(col[i] - prev) > 12:
            print(f"  y={y1+i:4d}: {int(prev)} -> {int(col[i])}")
            prev = col[i]
        else:
            prev = (prev*0.85 + col[i]*0.15)

# 行1 cell 顶部空白带
scan_x(165, 150, 1728, "行1 cell上部（图标上方空白）")
# 表格行上方
scan_x(755, 150, 1728, "表格标题带上部")
# 左边缘行边界
scan_y(178, 90, 972, "左侧行标签右缘/content左缘")
# 来源卡右缘
scan_y(1700, 90, 972, "右侧来源卡")
