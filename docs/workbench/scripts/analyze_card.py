#!/usr/bin/env python3
"""卡片边框细节：3x 放大 + 像素剖面"""
from PIL import Image

img = Image.open('/home/z/my-project/upload/003-企业AI落地.png').convert('RGB')
def hexc(px): return '#%02X%02X%02X' % px

# 卡1区域放大3x
c = img.crop((15, 210, 445, 350)).resize((430*3, 140*3), Image.LANCZOS)
c.save('/home/z/my-project/scripts/crop_card1.png')

# 垂直剖面 x=420（避开图标和文字），y 210-620 打印每行颜色
print('=== x=420 垂直剖面 (y=210..620, 仅打印变化) ===')
prev = None
for y in range(210, 621):
    px = img.getpixel((420, y))
    if prev is None or sum(abs(a-b) for a, b in zip(px, prev)) > 12:
        print(f'  y={y:3d} {hexc(px)}')
    prev = px

print('\n=== 水平剖面 y=300 (x=15..445, 仅打印变化) ===')
prev = None
for x in range(15, 446):
    px = img.getpixel((x, 300))
    if prev is None or sum(abs(a-b) for a, b in zip(px, prev)) > 12:
        print(f'  x={x:3d} {hexc(px)}')
    prev = px
