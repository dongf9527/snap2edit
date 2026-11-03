#!/usr/bin/env python3
"""渲染 HTML 截图 + 与原图并排对比图"""
import asyncio, sys
from playwright.async_api import async_playwright
from PIL import Image

async def shot(html_path, out_png, width=1280, height=720, scale=1):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width': width, 'height': height},
                                      device_scale_factor=scale)
        await page.goto(f'file://{html_path}')
        await page.wait_for_timeout(600)
        el = await page.query_selector('#stage')
        await el.screenshot(path=out_png)
        await browser.close()

if __name__ == '__main__':
    html = '/home/z/my-project/download/企业AI落地_复刻.html'
    out = '/home/z/my-project/scripts/render_html.png'
    asyncio.run(shot(html, out))
    print('shot ->', out)

    # 并排对比：上=原图(缩放到1280x720)，下=复刻
    orig = Image.open('/home/z/my-project/upload/003-企业AI落地.png').convert('RGB').resize((1280, 720), Image.LANCZOS)
    mine = Image.open(out).convert('RGB')
    if mine.size != (1280, 720):
        mine = mine.resize((1280, 720), Image.LANCZOS)
    comp = Image.new('RGB', (1280, 720*2+8), '#FF0000')
    comp.paste(orig, (0, 0)); comp.paste(mine, (0, 728))
    comp.save('/home/z/my-project/scripts/compare_html.png')
    print('compare -> /home/z/my-project/scripts/compare_html.png')
