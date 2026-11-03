#!/usr/bin/env python3
"""来源卡与页脚、场景pills等剩余细节测量"""
from PIL import Image
import numpy as np

img = Image.open('/home/z/my-project/upload/002-框架与实施工具.png').convert('RGB')
a = np.array(img).astype(int)

def vprofile(x, y1, y2, label, th=8):
    print(f"== x={x} {label} ==")
    prev = None
    for y in range(y1, y2):
        r, g, b = a[y, x]
        v = (r+g+b)/3
        if prev is None or abs(v - prev) > th:
            print(f"  y={y}: #{r:02X}{g:02X}{b:02X}")
            prev = v
        else:
            prev = prev*0.85 + v*0.15

# 来源卡背景边界（x=1690 避开封面与文字）
vprofile(1690, 170, 780, "来源卡边界@x=1690")
# 场景pills 精确位置 (r2c4)
vprofile(1180, 320, 460, "客户服务pill上下")
# r2c1 tiles
vprofile(230, 315, 460, "tile上下")
# r2c2 绿pills
vprofile(580, 315, 460, "绿pill上下", 10)
# r4c3 三盒子
vprofile(920, 625, 770, "r4c3盒子边界", 10)
# r3c1 时间线
vprofile(340, 515, 545, "r3c1时间线", 10)
# r3c3 时间轴
vprofile(960, 470, 560, "r3c3时间轴", 10)
# 表格行线精细 (t1 x=300)
vprofile(300, 770, 924, "t1行线@x=300", 8)
# 优先级列颜色 (t2)
vprofile(800, 795, 915, "优先级列@x=800", 8)
