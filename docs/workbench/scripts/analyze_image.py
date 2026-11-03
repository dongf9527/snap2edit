#!/usr/bin/env python3
"""分析原图 003-企业AI落地.png：尺寸、配色采样、结构网格定位"""
from PIL import Image

img = Image.open('/home/z/my-project/upload/003-企业AI落地.png').convert('RGB')
W, H = img.size
print(f'尺寸: {W}x{H}  比例: {W/H:.4f}')

def hexc(px):
    return '#%02X%02X%02X' % px

def sample(name, x, y):
    px = img.getpixel((x, y))
    print(f'{name:38s} ({x:4d},{y:4d}) -> {hexc(px)}')

# ---- 头部四栏色块（标题栏，y约170） ----
print('\n=== 四栏标题栏底色 (y=170) ===')
for i, x in enumerate([85, 660, 1230, 1650], 1):
    sample(f'栏{i}标题栏', x, 170)

print('\n=== 四栏标题栏底色 (y=120 中心附近) ===')
for i, x in enumerate([85, 660, 1230, 1650], 1):
    sample(f'栏{i}标题栏中心', x, 120)

# ---- 背景色 ----
print('\n=== 背景 ===')
sample('页面背景(顶部)', 900, 15)
sample('页面背景(中部间隙)', 945, 500)
sample('页面背景(底部)', 900, 950)

# ---- 内容卡片 ----
print('\n=== 内容卡片 ===')
sample('卡片白底', 85, 260)
sample('卡片边框(上边缘y=207)', 85, 208)
sample('输出卡片底色(浅灰, y=585)', 85, 585)

# ---- 箭头 ----
print('\n=== 箭头三角 (栏1 下方, y≈520) ===')
for y in [505, 515, 525]:
    sample(f'箭头y={y}', 210, y)

# ---- 底部流程条 ----
print('\n=== 底部五步流程条 (y≈690) ===')
sample('步骤1箭头块', 150, 690)
sample('步骤2箭头块', 400, 690)
sample('数字圆1', 42, 662)
sample('数字圆3', 573, 662)

print('\n=== 流程条下方列表底色 (y≈770) ===')
sample('列表区域', 150, 770)

# ---- 三种投资决策 ----
print('\n=== 右侧投资决策 (y≈655 标题栏 / y≈705) ===')
sample('投资决策标题栏', 1500, 655)
sample('投资决策标题栏2', 1560, 652)
sample('决策行1图标圆', 1385, 713)
sample('决策行1底色', 1600, 713)

# ---- 底部治理条 ----
print('\n=== 底部治理条 (y≈855 主条 / y≈885 子条) ===')
sample('治理条背景', 300, 855)
sample('治理条中心图标区', 640, 855)
sample('子条1', 200, 888)

# ---- 来源行 ----
print('\n=== 来源行 ===')
sample('来源文字', 60, 950)

# ---- 扫描四栏边界：沿 y=400 找竖直分界 ----
print('\n=== 沿 y=400 水平扫描颜色变化（定位栏边界） ===')
prev = None
for x in range(0, W, 2):
    px = img.getpixel((x, 400))
    # 只关注明显变化
    if prev is None or (abs(px[0]-prev[0])+abs(px[1]-prev[1])+abs(px[2]-prev[2]) > 60):
        print(f'  x={x:4d} -> {hexc(px)}')
    prev = px
