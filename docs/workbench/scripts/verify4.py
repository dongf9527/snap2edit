#!/usr/bin/env python3
"""来源卡精确边界 + 封面x范围 + r4c1/r1c4 icons"""
from PIL import Image
import numpy as np

img = Image.open('/home/z/my-project/upload/002-框架与实施工具.png').convert('RGB')
a = np.array(img).astype(int)

def hprofile(y, x1, x2, label, th=8):
    print(f"== y={y} {label} ==")
    prev = None
    for x in range(x1, x2):
        r, g, b = a[y, x]
        v = (r+g+b)/3
        if prev is None or abs(v - prev) > th:
            print(f"{x}:#{r:02X}{g:02X}{b:02X} ", end="")
            prev = v
    print()

def vprofile(x, y1, y2, label, th=6):
    print(f"== x={x} {label} ==")
    prev = None
    for y in range(y1, y2):
        r, g, b = a[y, x]
        v = (r+g+b)/3
        if prev is None or abs(v - prev) > th:
            print(f"{y}:#{r:02X}{g:02X}{b:02X} ", end="")
            prev = v
    print()

vprofile(1455, 170, 780, "来源卡fill边界@x=1455", 6)
hprofile(230, 1440, 1720, "来源卡1内容@y=230", 10)
hprofile(385, 1440, 1720, "来源卡2内容@y=385", 10)
hprofile(540, 1440, 1720, "来源卡3内容@y=540", 10)
hprofile(690, 1440, 1720, "来源卡4内容@y=690", 10)
hprofile(700, 189, 503, "r4c1子盒@y=700", 10)
hprofile(645, 189, 503, "r4c1父盒@y=645", 10)
hprofile(240, 1124, 1433, "r1c4图标@y=240", 10)
hprofile(530, 1124, 1433, "r3c4图标@y=530", 10)
vprofile(690, 470, 620, "r3c3圆点@x=690?不对", 10)
hprofile(507, 808, 1121, "r3c3线@y=507", 10)
vprofile(870, 495, 540, "r3c3圆@x=870", 10)
