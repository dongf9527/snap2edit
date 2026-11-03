#!/usr/bin/env python3
"""针对性精测:行标签文字、r1 bullet字号、来源卡标题、r2c4 pills、r3c3标签、r4c2卡、r4c3盒"""
from PIL import Image
import numpy as np

a = np.array(Image.open('/home/z/my-project/upload/002-框架与实施工具.png').convert('RGB')).astype(int)

def text_rows(x1, x2, y1, y2, label, th=110):
    """在区域内找文字行(每行暗像素数)"""
    seg = a[y1:y2, x1:x2].sum(axis=2)/3
    dark = (seg < 150).sum(axis=1)
    print(f"== {label} (x{x1}-{x2}) 暗行分布 ==")
    runs = []
    inrun = False
    for i, v in enumerate(dark):
        if v > 2 and not inrun:
            start = i; inrun = True
        elif v <= 2 and inrun:
            runs.append((y1+start, y1+i-1)); inrun = False
    if inrun: runs.append((y1+start, y1+len(dark)-1))
    print("  行:", runs)

def text_cols(y1, y2, x1, x2, label, th=110):
    seg = a[y1:y2, x1:x2].sum(axis=2)/3
    dark = (seg < 150).sum(axis=0)
    runs = []
    inrun = False
    for i, v in enumerate(dark):
        if v > 1 and not inrun:
            start = i; inrun = True
        elif v <= 1 and inrun:
            runs.append((x1+start, x1+i-1)); inrun = False
    if inrun: runs.append((x1+start, x1+len(dark)-1))
    print(f"== {label} (y{y1}-{y2}) 列run: {runs[:8]}")

# 行标签文字行 (x 25-165)
text_rows(25, 165, 177, 315, "行标签1")
text_rows(25, 165, 319, 465, "行标签2")
text_rows(25, 165, 471, 617, "行标签3")
text_rows(25, 165, 623, 769, "行标签4")
text_rows(25, 165, 775, 921, "行标签5")
# r1c1 bullet 行
text_rows(340, 500, 190, 290, "r1c1 bullets")
text_cols(203, 222, 330, 503, "r1c1 bullet1 行业水平与标杆对比")
# r2c4 pills
text_cols(345, 375, 1124, 1433, "r2c4 上排pills")
text_cols(398, 428, 1124, 1433, "r2c4 下排pills")
# r3c3 阶段标签
text_rows(830, 1120, 470, 500, "r3c3 阶段标签")
text_cols(478, 497, 830, 1120, "r3c3 阶段标签列")
# r4c2 卡片
text_rows(515, 800, 620, 720, "r4c2 卡片区域")
# r4c3 盒子
text_rows(850, 990, 630, 770, "r4c3 盒子区域")
# 来源卡1标题
text_rows(1555, 1716, 190, 300, "来源卡1文本")
# 来源卡2标题
text_rows(1555, 1716, 330, 460, "来源卡2文本")
# 主要来源头文字
text_rows(1505, 1716, 105, 165, "主要来源头")
# 标题
text_rows(30, 900, 5, 90, "大标题")
text_cols(10, 80, 30, 900, "大标题列")
# footer 文字
text_rows(60, 800, 928, 962, "footer")
