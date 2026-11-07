#!/usr/bin/env python3
"""Step3: Playwright 元素级截图（#canvas, deviceScaleFactor=1）同步版"""
from playwright.sync_api import sync_playwright

HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), '能力缺口判断复刻v2.html')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'render_html.png')

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 1728, 'height': 972}, device_scale_factor=1)
    pg.goto(f'file://{HTML}')
    pg.wait_for_timeout(900)
    el = pg.query_selector('#canvas')
    el.screenshot(path=OUT)
    b.close()
print('截图:', OUT)
