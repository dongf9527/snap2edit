#!/usr/bin/env python3
"""裁剪关键小块（高倍放大）"""
from PIL import Image

img = Image.open('/home/z/my-project/upload/002-框架与实施工具.png').convert('RGB')

crops = [
    ("z_r3c1_phases", 189, 466, 503, 560, 3.0),   # 行3col1 阶段chevron
    ("z_r3c2_phases", 505, 466, 806, 560, 3.0),   # 行3col2 评估/加固/监控
    ("z_r2c1_icons",  189, 313, 503, 466, 2.5),   # 行2col1 图标tile
    ("z_r2c2_pills",  505, 313, 806, 466, 2.5),   # 行2col2 绿pill
    ("z_r2c3_org",    808, 313, 1121, 466, 2.5),  # 行2col3 组织架构
    ("z_r2c4_pills",  1124, 313, 1433, 466, 2.5), # 行2col4 场景pill
    ("z_r5_tables",   189, 745, 1716, 924, 1.5),  # 底部表格
    ("z_footer",      20, 920, 900, 972, 2.0),    # 底部注释
    ("z_r1c1",        189, 169, 503, 313, 2.5),   # 行1col1
    ("z_r4c2",        505, 620, 806, 771, 2.5),   # 行4col2 三卡
    ("z_r4c3",        808, 620, 1121, 771, 2.5),  # 行4col3
    ("z_r1_head",     186, 96, 1728, 170, 1.4),   # 顶部chevron完整
]
for name, x1, y1, x2, y2, z in crops:
    c = img.crop((x1, y1, x2, y2))
    c = c.resize((int(c.width*z), int(c.height*z)), Image.LANCZOS)
    c.save(f'/home/z/my-project/scripts/{name}.png')
    print(name, c.size)
