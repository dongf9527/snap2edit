#!/usr/bin/env python3
"""Step3: 原图 vs 截图 diff —— 总均差 + 16px 块 TOP40 + 热力图"""
from PIL import Image
import numpy as np
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(HERE, '008-场景优先级.png')
B = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'render_html.png')
OUT = os.path.join(HERE, 'diff_heat.png')

img1 = Image.open(A).convert('RGB')
img2 = Image.open(B).convert('RGB')
if img2.size != img1.size:
    img2 = img2.resize(img1.size, Image.LANCZOS)
a = np.asarray(img1).astype(int)
b = np.asarray(img2).astype(int)
d = np.abs(a - b).sum(axis=2)
print(f'总平均差异: {d.mean():.2f} / 765   (目标 < 30)')
BS = 16
H, W = d.shape
hb, wb = H // BS, W // BS
blocks = d[:hb*BS, :wb*BS].reshape(hb, BS, wb, BS).mean(axis=(1, 3))
flat = [(float(blocks[i, j]), i, j) for i in range(hb) for j in range(wb)]
flat.sort(reverse=True)
print('TOP30 差异块 (block_y,block_x -> 原图坐标):')
for v, i, j in flat[:30]:
    if v < 55:
        break
    print(f'  ({i:3d},{j:3d}) -> ({j*BS:4d},{i*BS:4d})  diff={v:.0f}')
heat = np.clip(blocks * 3, 0, 255).astype(np.uint8)
Image.fromarray(np.stack([heat, heat // 3, heat // 3], axis=2)).resize((wb*8, hb*8), Image.NEAREST).save(OUT)
print('热力图:', OUT)
