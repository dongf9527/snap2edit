#!/usr/bin/env python3
"""精细采样各元素颜色"""
from PIL import Image
import numpy as np
from collections import Counter

img = Image.open('/home/z/my-project/upload/002-框架与实施工具.png').convert('RGB')
a = np.array(img)

def region_colors(x1, y1, x2, y2, name, top=6):
    c = Counter()
    for y in range(y1, y2):
        for x in range(x1, x2):
            c[tuple(int(v) for v in a[y, x])] += 1
    total = (y2-y1)*(x2-x1)
    print(f"{name} ({x1},{y1})-({x2},{y2}):")
    for color, n in c.most_common(top):
        r, g, b = int(color[0]), int(color[1]), int(color[2])
        print(f"   #{r:02X}{g:02X}{b:02X} rgb({r},{g},{b}) {100*n/total:.1f}%")

# 网格线与cell内部
region_colors(496, 200, 510, 290, "col1/col2分界竖线区域", 4)
region_colors(250, 305, 400, 318, "row1/row2分界横线区域", 4)
region_colors(420, 180, 490, 200, "row1 col1 内部空白", 3)
region_colors(830, 175, 880, 185, "row1 col3 顶部", 3)
# chevron 主色
region_colors(250, 105, 450, 160, "chevron1", 3)
region_colors(560, 105, 760, 160, "chevron2", 3)
region_colors(870, 105, 1070, 160, "chevron3", 3)
region_colors(1180, 105, 1380, 160, "chevron4", 3)
region_colors(1450, 100, 1700, 160, "主要来源头", 3)
# 行标签
region_colors(20, 320, 160, 350, "行标签2", 3)
region_colors(30, 190, 58, 215, "数字圈1", 3)
# row2 图标tile
region_colors(210, 320, 250, 355, "row2 col1 tile1", 3)
# row2 绿pills
region_colors(530, 330, 660, 352, "pill公平性", 3)
region_colors(530, 362, 660, 382, "pill安全性", 3)
# row2 场景pills
region_colors(1150, 340, 1215, 372, "pill客户服务", 3)
region_colors(1225, 340, 1290, 372, "pill营销增长", 3)
region_colors(1150, 385, 1215, 418, "pill运营提效", 3)
region_colors(1225, 385, 1290, 418, "pill产品创新", 3)
# row3 阶段chevron
region_colors(210, 475, 260, 495, "探索期", 3)
region_colors(295, 475, 350, 495, "试点期", 3)
region_colors(390, 475, 450, 495, "规模化期", 3)
region_colors(530, 475, 580, 495, "评估", 3)
region_colors(620, 475, 665, 495, "加固", 3)
region_colors(705, 475, 750, 495, "监控", 3)
# 来源卡
region_colors(1440, 180, 1700, 200, "来源卡1上部", 3)
region_colors(1465, 195, 1545, 265, "封面1", 5)
region_colors(1465, 350, 1545, 420, "封面2", 5)
region_colors(1465, 505, 1545, 575, "封面3", 5)
region_colors(1465, 655, 1545, 725, "封面4", 5)
