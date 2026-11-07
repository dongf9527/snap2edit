#!/usr/bin/env python3
"""v2 迭代（2026-11-07 水印移除）校验证据生成：
  compare_html.png            原图 vs HTML 渲染（上下堆叠）
  compare_pptx.png            原图 vs PPTX 渲染（上下堆叠）
  水印移除_右下角三联对比.png   右下角 [1000,840,1728,972]：原图 / HTML / PPTX
"""
from PIL import Image
import os

HERE = os.path.dirname(os.path.abspath(__file__))
EV = os.path.join(HERE, '校验证据')

orig = Image.open(os.path.join(HERE, '008-场景优先级.png')).convert('RGB')
html = Image.open(os.path.join(HERE, 'render_html.png')).convert('RGB')
pptx = Image.open('/tmp/render_wm_pp/pptx_1728.png').convert('RGB')

def stack(a, b, out):
    W, H = a.size
    cv = Image.new('RGB', (W, H * 2 + 8), '#333333')
    cv.paste(a, (0, 0)); cv.paste(b, (0, H + 8))
    cv.save(out)
    print('并排对比:', out, cv.size)

stack(orig, html, os.path.join(EV, 'compare_html.png'))
stack(orig, pptx, os.path.join(EV, 'compare_pptx.png'))

box = (1000, 840, 1728, 972)
crops = [im.crop(box) for im in (orig, html, pptx)]
W, H = crops[0].size
cv = Image.new('RGB', (W, H * 3 + 20), '#FFFFFF')
cv.paste(crops[0], (0, 0)); cv.paste(crops[1], (0, H + 10)); cv.paste(crops[2], (0, 2 * H + 20))
out = os.path.join(EV, '水印移除_右下角三联对比.png')
cv.save(out)
print('水印移除专证:', out, cv.size, '（上=原图含水印 / 中=HTML v2 / 下=PPTX v2）')
