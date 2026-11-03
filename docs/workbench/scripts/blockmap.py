#!/usr/bin/env python3
"""生成背景分区图：把图分成小块，按主色分类，输出区块地图用于确定布局"""
from PIL import Image
import numpy as np

img = Image.open('/home/z/my-project/upload/002-框架与实施工具.png').convert('RGB')
a = np.array(img).astype(int)
H, W = a.shape[:2]

def classify(r, g, b):
    v = (r+g+b)/3
    if v > 249: return '.'      # 白
    if abs(r-g) < 12 and abs(g-b) < 12 and 225 < v <= 249: return 'g'  # 浅灰块
    if abs(r-g) < 15 and abs(g-b) < 15 and 180 < v <= 225: return 'G'  # 中灰
    if b > r+15 and v < 120: return 'B'  # 深蓝
    if g > r+5 and g > b+5: return 'v'   # 绿
    if r > g+8 and r > b+8 and v < 200: return 'n'  # 棕
    if r > b-5 and b > g+5 and v < 200: return 'p'  # 紫
    if v < 120: return 'D'  # 深色
    return '?'

step = 12
print("    " + "".join(str((x//step)%10) for x in range(0, W, step)))
for y in range(0, H, step):
    row = []
    for x in range(0, W, step):
        block = a[y:y+step, x:x+step].reshape(-1, 3).mean(axis=0)
        row.append(classify(*block))
    print(f"{y:4d}" + "".join(row))
