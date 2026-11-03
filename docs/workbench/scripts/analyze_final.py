#!/usr/bin/env python3
"""最终几何确认：治理条、流程卡片、输出卡边界"""
from PIL import Image

img = Image.open('/home/z/my-project/upload/003-企业AI落地.png').convert('RGB')
W, H = img.size
def hexc(px): return '#%02X%02X%02X' % px

print('=== x=700 垂直剖面 y=815..972 (治理条) ===')
prev = None
for y in range(815, 972):
    px = img.getpixel((700, y))
    if prev is None or sum(abs(a-b) for a, b in zip(px, prev)) > 10:
        print(f'  y={y:3d} {hexc(px)}')
    prev = px

print('\n=== x=210 垂直剖面 y=500..680 (栏1 箭头+输出卡) ===')
prev = None
for y in range(500, 680):
    px = img.getpixel((210, y))
    if prev is None or sum(abs(a-b) for a, b in zip(px, prev)) > 10:
        print(f'  y={y:3d} {hexc(px)}')
    prev = px

def runs_in_row(y, min_len=15, thr=18):
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

print('\n=== y=770 流程子弹卡横向 (x=0..1400) ===')
for r in runs_in_row(770)[:40]:
    if r[0] < 1400: print(f'  x={r[0]:4d}-{r[1]:4d} ({r[2]})')

print('\n=== y=890 治理条药丸行 ===')
for r in runs_in_row(890, 12, 10)[:50]:
    print(f'  x={r[0]:4d}-{r[1]:4d} ({r[2]})')

print('\n=== y=925 (治理条下部/来源行) ===')
for r in runs_in_row(925, 12, 8)[:30]:
    print(f'  x={r[0]:4d}-{r[1]:4d} ({r[2]})')

# 圆点圆心精确采样
print('\n=== 数字圆圆心色 (y=690) ===')
for i, x in enumerate([51, 311, 584, 842, 1105], 1):
    print(f'  圆{i} ({x},690): {hexc(img.getpixel((x, 690)))}  ({x},685): {hexc(img.getpixel((x, 685)))}')

# 决策面板行边界 (x=1600 垂直)
print('\n=== x=1600 决策面板垂直剖面 y=660..972 ===')
prev = None
for y in range(660, 972):
    px = img.getpixel((1600, y))
    if prev is None or sum(abs(a-b) for a, b in zip(px, prev)) > 14:
        print(f'  y={y:3d} {hexc(px)}')
    prev = px

# 栏1输出卡横向边界 y=600
print('\n=== y=600 输出卡横向 ===')
for r in runs_in_row(600, 12, 10)[:12]:
    if r[0] < 460: print(f'  x={r[0]:4d}-{r[1]:4d} ({r[2]})')
