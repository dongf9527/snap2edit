#!/usr/bin/env python3
"""最后一批水平方向测量"""
from PIL import Image
import numpy as np

img = Image.open('/home/z/my-project/upload/002-框架与实施工具.png').convert('RGB')
a = np.array(img).astype(int)

def hprofile(y, x1, x2, label, th=10):
    print(f"== y={y} {label} ==")
    prev = None
    for x in range(x1, x2):
        r, g, b = a[y, x]
        v = (r+g+b)/3
        if prev is None or abs(v - prev) > th:
            print(f"  x={x}: #{r:02X}{g:02X}{b:02X}", end="")
            prev = v
        else:
            prev = prev*0.85 + v*0.15
    print()

hprofile(360, 1124, 1433, "r2c4上排pills左右", 12)
hprofile(415, 1124, 1433, "r2c4下排pills左右", 12)
hprofile(355, 189, 503, "r2c1 tiles左右", 12)
hprofile(345, 505, 806, "r2c2绿pill左右", 12)
hprofile(500, 189, 503, "r3c1三阶段左右", 12)
hprofile(500, 505, 806, "r3c2三阶段左右", 12)
hprofile(510, 808, 1121, "r3c3时间轴线", 12)
hprofile(655, 808, 1121, "r4c3盒子左右", 12)
hprofile(250, 189, 503, "r1c1图标左右", 12)
hprofile(945, 1550, 1728, "footer右边界", 12)
hprofile(650, 1124, 1433, "r4c4图标", 12)
hprofile(230, 1440, 1716, "来源卡1封面与文字", 12)
# r3c3 阶段标签
hprofile(487, 808, 1121, "r3c3阶段标签", 12)
