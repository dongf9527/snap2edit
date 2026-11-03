#!/usr/bin/env python3
"""找表格的竖直边框线与水平边框线"""
from PIL import Image
import numpy as np

img = Image.open('/home/z/my-project/upload/002-框架与实施工具.png').convert('RGB')
a = np.array(img).astype(int)
H, W = a.shape[:2]

# 表格区域 y 745-924：对每个 x 统计"灰线"像素数（值<240 且连续性高）
gray = (a[:, :, :].sum(axis=2) / 3) < 242
colcnt = gray[748:920, :].sum(axis=0)
cands = [x for x in range(150, W) if colcnt[x] > 100]
# 聚合相邻
groups = []
for x in cands:
    if groups and x - groups[-1][-1] <= 2:
        groups[-1].append(x)
    else:
        groups.append([x])
print("表格竖线 x:", [ (g[0]+g[-1])//2 for g in groups ])

rowcnt = gray[:, 200:1700].sum(axis=1)
cands = [y for y in range(740, 930) if rowcnt[y] > 700]
groups = []
for y in cands:
    if groups and y - groups[-1][-1] <= 2:
        groups[-1].append(y)
    else:
        groups.append([y])
print("表格横线 y:", [ (g[0]+g[-1])//2 for g in groups ])

# 网格其他区域横线（行分界）
cands = [y for y in range(150, 760) if rowcnt[y] > 700]
groups = []
for y in cands:
    if groups and y - groups[-1][-1] <= 2:
        groups[-1].append(y)
    else:
        groups.append([y])
print("主网格横线 y:", [ (g[0]+g[-1])//2 for g in groups ])

# 主网格竖线（y 175-760）
colcnt2 = gray[175:760, :].sum(axis=0)
cands = [x for x in range(150, W) if colcnt2[x] > 400]
groups = []
for x in cands:
    if groups and x - groups[-1][-1] <= 2:
        groups[-1].append(x)
    else:
        groups.append([x])
print("主网格竖线 x:", [ (g[0]+g[-1])//2 for g in groups ])
