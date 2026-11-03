#!/usr/bin/env python3
"""裁剪关键区域放大保存，供视觉核对"""
from PIL import Image

img = Image.open('/home/z/my-project/upload/003-企业AI落地.png').convert('RGB')

crops = {
    'crop_flow.png':      (0, 620, 1290, 972),    # 底部五步流程 + 治理条
    'crop_right.png':     (1230, 590, 1728, 972), # 三种投资决策
    'crop_col1.png':      (0, 80, 460, 620),      # 栏1完整
    'crop_title.png':     (0, 0, 900, 90),        # 大标题
}
for name, box in crops.items():
    c = img.crop(box)
    w, h = c.size
    c = c.resize((int(w*1.6), int(h*1.6)), Image.LANCZOS)
    c.save(f'/home/z/my-project/scripts/{name}')
    print(name, c.size)
