#!/usr/bin/env python3
"""分别裁剪4个表格 + 行标签 + 页脚 + 顶部来源头"""
from PIL import Image

img = Image.open('/home/z/my-project/upload/002-框架与实施工具.png').convert('RGB')

crops = [
    ("t1_ability",  189, 745, 505, 924, 2.6),
    ("t2_scene",    505, 745, 808, 924, 2.6),
    ("t3_roadmap",  808, 745, 1124, 924, 2.6),
    ("t4_value",    1124, 745, 1716, 924, 2.0),
]
for name, x1, y1, x2, y2, z in crops:
    c = img.crop((x1, y1, x2, y2))
    c = c.resize((int(c.width*z), int(c.height*z)), Image.LANCZOS)
    c.save(f'/home/z/my-project/scripts/{name}.png')
    print(name, c.size)
