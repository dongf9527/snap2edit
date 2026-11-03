#!/usr/bin/env python3
"""第三阶段：底部区域精确几何 + 圆点颜色"""
from PIL import Image

img = Image.open('/home/z/my-project/upload/003-企业AI落地.png').convert('RGB')
W, H = img.size
def hexc(px): return '#%02X%02X%02X' % px

def runs_in_row(y, min_len=20, thr=28):
    runs, start = [], 0
    prev = img.getpixel((0, y))
    for x in range(1, W):
        px = img.getpixel((x, y))
        if abs(px[0]-prev[0])+abs(px[1]-prev[1])+abs(px[2]-prev[2]) > thr:
            if x - start >= min_len:
                runs.append((start, x, hexc(img.getpixel(((start+x)//2, y)))))
            start = x
        prev = px
    if W - start >= min_len:
        runs.append((start, W, hexc(img.getpixel(((start+W)//2, y)))))
    return runs

for y in [662, 690, 700, 712, 850, 860, 888, 940]:
    print(f'--- y={y} ---')
    for r in runs_in_row(y):
        print(f'  x={r[0]:4d}-{r[1]:4d} ({r[2]})')

# 数字圆心颜色采样（步骤1-5 圆点）
print('\n=== 五个数字圆颜色 ===')
# 从 crop 估计：圆1 x≈42,y≈660; 圆2 x≈289; 圆3 x≈573; 圆4 x≈838; 圆5 x≈1104 (原图坐标)
for i, (x, y) in enumerate([(42,661),(289,661),(573,661),(838,661),(1104,661)], 1):
    print(f'  圆{i} ({x},{y}): {hexc(img.getpixel((x,y)))}')

# 决策面板行底色、图标圆颜色
print('\n=== 决策面板 ===')
for name,(x,y) in {
    '标题栏底':(1500,648), '标题栏左边缘扫':(1360,648),
    '行1底':(1600,690), '行1圆心':(1390,712),
    '行2底':(1600,782), '行2圆心':(1390,804),
    '行3底':(1600,878), '行3圆心':(1390,898),
    '面板外背景':(1330,700),
}.items():
    print(f'  {name}: {hexc(img.getpixel((x,y)))}')

# 栏1卡片精确y边界（x=400 纵向）
print('\n=== x=400 栏1纵向（卡片边界） ===')
prev = img.getpixel((400, 80)); start = 80
for y in range(81, 620):
    px = img.getpixel((400, y))
    if abs(px[0]-prev[0])+abs(px[1]-prev[1])+abs(px[2]-prev[2]) > 20:
        if y-start >= 12:
            print(f'  y={start:4d}-{y:4d} ({hexc(img.getpixel((400,(start+y)//2)))})')
        start = y
    prev = px
print(f'  y={start}-620 ({hexc(img.getpixel((400,600)))})')

# 栏1横向卡片边界（y=260）
print('\n=== y=260 栏1横向（卡片x边界） ===')
for r in runs_in_row(260, 25):
    if r[0] < 460:
        print(f'  x={r[0]:4d}-{r[1]:4d} ({r[2]})')
