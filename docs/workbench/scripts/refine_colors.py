# -*- coding: utf-8 -*-
"""补充采样：徽章圆色、橄榄绿头部、背景渐变、文字灰度"""
from PIL import Image

im = Image.open('/home/z/my-project/upload/001-AI方法论.png').convert('RGB')
W, H = im.size

def px(x, y):
    return '#%02X%02X%02X' % im.getpixel((x, y))

print('--- 背景四角与中部 ---')
for x, y in [(10, 10), (864, 10), (1718, 10), (10, 500), (1718, 500), (10, 962), (1718, 962), (864, 250)]:
    print(f'  ({x:4d},{y:3d})', px(x, y))

print('--- 列头主色 ---')
for name, x, y in [('col1头', 150, 296), ('col1的01块', 60, 296), ('col2头', 550, 296), ('col2的02块', 420, 296),
                   ('col3头', 950, 296), ('col3的03块', 800, 296)]:
    print(f'  {name:10s}', px(x, y))

print('--- 数字徽章（区域中暗色像素中位）---')
def badge(x0, x1, y0, y1):
    rs, gs, bs = [], [], []
    for x in range(x0, x1):
        for y in range(y0, y1):
            r, g, b = im.getpixel((x, y))
            if (r + g + b) / 3 < 140:
                rs.append(r); gs.append(g); bs.append(b)
    if not rs:
        return 'N/A'
    rs.sort(); gs.sort(); bs.sort()
    m = len(rs) // 2
    return '#%02X%02X%02X  (n=%d)' % (rs[m], gs[m], bs[m], m)

print('  col1徽章:', badge(56, 94, 396, 438))
print('  col2徽章:', badge(436, 474, 396, 438))
print('  col3徽章:', badge(823, 861, 396, 438))

print('--- 文字色（区域内最暗像素）---')
def darkest(x0, y0, x1, y1):
    best, bc = 999, None
    for x in range(x0, x1):
        for y in range(y0, y1):
            r, g, b = im.getpixel((x, y))
            l = (r + g + b) / 3
            if l < best:
                best, bc = l, (r, g, b)
    return '#%02X%02X%02X' % bc

print('  副标题:', darkest(40, 350, 460, 372))
print('  卡片描述:', darkest(148, 430, 340, 462))
print('  卡片标题:', darkest(148, 400, 340, 424))
print('  页脚:', darkest(30, 928, 380, 956))
print('  插图标签:', darkest(1180, 320, 1420, 345))

print('--- 插图平台/立方体 ---')
for x, y in [(1250, 470), (1300, 520), (1400, 485), (1300, 330), (1360, 350), (1240, 545), (1440, 540), (1330, 240)]:
    print(f'  ({x:4d},{y:3d})', px(x, y))
