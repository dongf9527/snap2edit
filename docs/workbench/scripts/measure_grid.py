#!/usr/bin/env python3
"""精确测量网格边界：扫描行列边界与颜色过渡"""
from PIL import Image
import numpy as np

img = Image.open('/home/z/my-project/upload/002-框架与实施工具.png').convert('RGB')
a = np.array(img)
H, W = a.shape[:2]

# 1) 找主内容区竖直网格线：在 y=200~880 范围扫描 x 上是否有明显的暗线（灰色 #D8.. 左右）
def col_profile(x, y1, y2):
    seg = a[y1:y2, x, :].astype(int)
    return seg.mean(axis=0)

# 网格线通常是浅灰色。扫描每一列在 y 150..900 的"非白色"像素占比
region = a[150:900, :, :].astype(int)
nonwhite = (region.sum(axis=2) < 720).mean(axis=0)  # 每列非白比例
# 打印局部峰值
print("== 竖直方向上非白比例突变的候选列线 ==")
for x in range(1, W-1):
    if nonwhite[x] > 0.5 and nonwhite[x] >= nonwhite[x-1] and nonwhite[x] >= nonwhite[x+1]:
        if x < 400 or (nonwhite[x] - (nonwhite[x-3] if x>3 else 0)) > 0.05:
            pass
# 更直接：打印若干关键x处的颜色
for x in [175, 180, 455, 460, 465, 640, 645, 650, 855, 860, 865, 1035, 1040, 1045, 1215, 1220, 1225, 1395, 1400, 1405, 1410]:
    r,g,b = img.getpixel((x, 250))
    print(f"x={x:4d} y=250 #{r:02X}{g:02X}{b:02X}", end="  ")
    r,g,b = img.getpixel((x, 700))
    print(f"y=700 #{r:02X}{g:02X}{b:02X}")

print()
# 2) 行边界：在 x=300 处扫描 y
print("== 水平方向 x=300 处 y 上的颜色（找行边界）==")
prev = None
for y in range(90, 972, 1):
    r,g,b = img.getpixel((300, y))
    cur = (r,g,b)
    if prev and (abs(cur[0]-prev[0])+abs(cur[1]-prev[1])+abs(cur[2]-prev[2]) > 60):
        print(f"y={y:4d} {prev} -> {cur}")
    prev = cur
