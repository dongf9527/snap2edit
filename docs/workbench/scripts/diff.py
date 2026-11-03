#!/usr/bin/env python3
"""原图 vs 渲染图 差异热力图(按16px块聚合,输出差异最大的区域)"""
from PIL import Image
import numpy as np

a = np.array(Image.open('/home/z/my-project/upload/002-框架与实施工具.png').convert('RGB')).astype(int)
b = np.array(Image.open('/home/z/my-project/scripts/render_html2.png').convert('RGB')).astype(int)
print("size", a.shape, b.shape)
if a.shape != b.shape:
    from PIL import Image as I
    bi = I.open('/home/z/my-project/scripts/render_html2.png').convert('RGB').resize((a.shape[1], a.shape[0]))
    b = np.array(bi).astype(int)

d = np.abs(a - b).sum(axis=2)
H, W = d.shape
bs = 16
print("差异最大的块 (块坐标=像素/16):")
scores = []
for by in range(0, H-bs, bs):
    for bx in range(0, W-bs, bs):
        s = d[by:by+bs, bx:bx+bs].mean()
        scores.append((s, bx, by))
scores.sort(reverse=True)
for s, bx, by in scores[:40]:
    print(f"  block({bx:4d},{by:4d}) diff={s:6.1f}")
# 保存热力图
hm = (np.clip(d/180, 0, 1) * 255).astype(np.uint8)
Image.fromarray(hm).save('/home/z/my-project/scripts/diff_heat.png')
print("总平均差异:", d.mean())
