#!/usr/bin/env python3
"""第二阶段：精确定位结构边界 + 关键区域配色"""
from PIL import Image

img = Image.open('/home/z/my-project/upload/003-企业AI落地.png').convert('RGB')
W, H = img.size
S = 1280 / W  # 到 1280x720 坐标系的缩放因子

def hexc(px): return '#%02X%02X%02X' % px

def runs_in_row(y, min_len=30):
    """扫描一行，输出连续同色区段（长度>=min_len）"""
    runs = []
    start = 0
    prev = img.getpixel((0, y))
    for x in range(1, W):
        px = img.getpixel((x, y))
        if abs(px[0]-prev[0])+abs(px[1]-prev[1])+abs(px[2]-prev[2]) > 30:
            if x - start >= min_len:
                runs.append((start, x, hexc(img.getpixel(((start+x)//2, y)))))
            start = x
        prev = px
    if W - start >= min_len:
        runs.append((start, W, hexc(img.getpixel(((start+W)//2, y)))))
    return runs

print('=== y=120 标题栏行区段（四栏精确x边界） ===')
for r in runs_in_row(120):
    print(f'  x={r[0]:4d}-{r[1]:4d} (中点色 {r[2]})  → 1280系: {r[0]*S:.0f}-{r[1]*S:.0f}')

print('\n=== y=40 标题区（看标题文字色带） ===')
for r in runs_in_row(40, 50):
    print(f'  x={r[0]:4d}-{r[1]:4d} ({r[2]})')

def runs_in_col(x, y0, y1, min_len=15):
    """扫描一列"""
    runs = []
    start = y0
    prev = img.getpixel((x, y0))
    for y in range(y0+1, y1):
        px = img.getpixel((x, y))
        if abs(px[0]-prev[0])+abs(px[1]-prev[1])+abs(px[2]-prev[2]) > 25:
            if y - start >= min_len:
                runs.append((start, y, hexc(img.getpixel((x, (start+y)//2)))))
            start = y
        prev = px
    if y1 - start >= min_len:
        runs.append((start, y1, hexc(img.getpixel((x, (start+y1)//2)))))
    return runs

print('\n=== x=85 栏1纵向扫描（卡片y边界） ===')
for r in runs_in_col(85, 0, H):
    print(f'  y={r[0]:4d}-{r[1]:4d} ({r[2]})  → 720系: {r[0]*S*W/W*(H/W)*W/H*972/972*0.0:.0f}'.replace('  → 720系: nan',''))

print('\n=== x=1500 右侧投资决策纵向扫描 ===')
for r in runs_in_col(1500, 600, H):
    print(f'  y={r[0]:4d}-{r[1]:4d} ({r[2]})')

print('\n=== x=300 底部流程区纵向扫描 ===')
for r in runs_in_col(300, 620, H):
    print(f'  y={r[0]:4d}-{r[1]:4d} ({r[2]})')

# 关键纯色采样
print('\n=== 关键纯色点采样 ===')
pts = {
    '标题文字(企业AI)': (45, 55),
    '栏1数字01': (60, 120),
    '栏1图标圆(靶心)': (72, 253),
    '栏1卡片底': (400, 260),
    '栏1输出卡片底': (400, 585),
    '栏2输出卡片底': (970, 585),
    '栏3输出卡片底': (1540, 585),
    '流程箭头块1': (150, 690),
    '流程箭头块3': (700, 690),
    '数字圆1底': (44, 660),
    '数字圆1边': (44, 648),
    '投资决策标题栏': (1560, 652),
    '投资决策框底': (1560, 760),
    '投资决策行1底': (1600, 700),
    '投资决策行2底': (1600, 795),
    '投资决策行3底': (1600, 890),
    '决策图标1(绿)': (1386, 712),
    '决策图标2(棕)': (1386, 800),
    '决策图标3(紫)': (1386, 893),
    '治理条底': (300, 852),
    '治理子条底': (200, 888),
    '双筒镜图标区': (640, 850),
}
for name, (x, y) in pts.items():
    try:
        print(f'  {name:24s} ({x:4d},{y:4d}) -> {hexc(img.getpixel((x,y)))}')
    except IndexError:
        print(f'  {name:24s} 越界')
