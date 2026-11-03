# -*- coding: utf-8 -*-
"""对 HTML/SVG 结果截图，用于视觉校验"""
import sys
from playwright.sync_api import sync_playwright

src = sys.argv[1] if len(sys.argv) > 1 else '/home/z/my-project/download/LLM推理全流程_图解.html'
out = sys.argv[2] if len(sys.argv) > 2 else '/tmp/render/svg_shot.png'
scale = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 1240, 'height': 900}, device_scale_factor=scale)
    pg.goto('file://' + src)
    pg.wait_for_timeout(600)
    el = pg.query_selector('svg')
    box = el.bounding_box()
    print('svg bbox:', box)
    pg.set_viewport_size({'width': int(box['width']) + 40, 'height': int(box['height']) + 60})
    pg.wait_for_timeout(300)
    el.screenshot(path=out)
    b.close()
print('saved', out)
