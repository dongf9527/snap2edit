#!/usr/bin/env python3
"""核对 chevron 高度、来源头高度、行标签精确边界、footer 边界"""
from PIL import Image
import numpy as np

img = Image.open('/home/z/my-project/upload/002-框架与实施工具.png').convert('RGB')
a = np.array(img).astype(int)

def vprofile(x, y1, y2, label):
    print(f"== x={x} {label} ==")
    prev = None
    for y in range(y1, y2):
        r, g, b = a[y, x]
        v = (r+g+b)/3
        if prev is None or abs(v - prev) > 15:
            print(f"  y={y}: #{r:02X}{g:02X}{b:02X}")
            prev = v
        else:
            prev = prev*0.8 + v*0.2

def hprofile(y, x1, x2, label):
    print(f"== y={y} {label} ==")
    prev = None
    for x in range(x1, x2):
        r, g, b = a[y, x]
        v = (r+g+b)/3
        if prev is None or abs(v - prev) > 15:
            print(f"  x={x}: #{r:02X}{g:02X}{b:02X}")
            prev = v
        else:
            prev = prev*0.8 + v*0.2

vprofile(300, 90, 180, "chevron1 上下边界")
vprofile(1500, 90, 180, "来源头上下边界")
vprofile(1500, 170, 780, "来源卡1边界")
hprofile(120, 1420, 1728, "来源头左右边界")
vprofile(60, 170, 320, "行标签1上下边界")
hprofile(240, 0, 200, "行标签1左右边界")
vprofile(400, 915, 972, "footer上下边界")
hprofile(945, 0, 600, "footer左右与图标")
vprofile(1590, 770, 924, "来源列底部表格带")
hprofile(840, 1120, 1728, "价值台账左右边界")
