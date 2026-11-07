# 原图 vs 渲染图 关键区域墨迹 bbox 对比（定位文字位移/字号差）
from PIL import Image
import numpy as np
import os

HERE = os.path.dirname(os.path.abspath(__file__))
o = np.asarray(Image.open(os.path.join(HERE, '008-场景优先级.png')).convert('RGB')).astype(int)
r = np.asarray(Image.open(os.path.join(HERE, 'render_html.png')).convert('RGB')).astype(int)

def ink_bbox(A, x0, y0, x1, y1, thr=140, dark=True):
    z = A[y0:y1, x0:x1]
    m = (z[:, :, 0] < thr) if dark else (z[:, :, 0] > thr)
    ys, xs = np.where(m)
    if not len(ys):
        return None
    return (xs.min() + x0, ys.min() + y0, xs.max() + x0, ys.max() + y0, int(m.sum()))

ZONES = [
    ('主标题',        20, 5, 700, 95, 140, True),
    ('chip1带字',     60, 172, 290, 208, 200, False),
    ('chip1正文L1',   55, 215, 300, 245, 140, True),
    ('P1表头场景',    90, 358, 200, 405, 200, False),
    ('P1表头加权总分', 770, 360, 900, 405, 200, False),
    ('P1行1名',       95, 415, 260, 460, 140, True),
    ('P1行1分4.00',   780, 415, 890, 460, 140, True),
    ('P2高',          950, 180, 1010, 215, 140, True),
    ('P2徽章TL题',    1120, 178, 1290, 205, 200, False),
    ('P2徽章TL副',    1120, 206, 1290, 232, 200, False),
    ('P2可行性轴',    1300, 595, 1420, 645, 140, True),
    ('P3头带字',      40, 660, 470, 700, 200, False),
    ('P3表头场景',    42, 722, 100, 755, 200, False),
    ('P3行1名',       45, 762, 200, 800, 140, True),
    ('P3行1门槛',     430, 762, 730, 800, 160, True),
    ('P3行1pill字',   745, 762, 905, 800, 160, True),
    ('P4表头决策',    1130, 722, 1230, 755, 200, False),
    ('P4行1策略',     1295, 762, 1690, 800, 160, True),
    # v2 迭代（2026-11-07）：右下角水印已按要求移除，渲染侧两区必为空（MISSING），
    # 与原图对比属预期差异，以下两区仅作历史诊断参考。
    ('水印公众号',    1130, 870, 1290, 935, 210, True),
    ('水印研究所',    1325, 870, 1680, 935, 210, True),
]
print(f'{"区域":<10} {"原图 bbox":<28} {"渲染 bbox":<28} {"dx,dy,尺寸差"}')
for name, x0, y0, x1, y1, thr, dark in ZONES:
    bo = ink_bbox(o, x0, y0, x1, y1, thr, dark)
    br = ink_bbox(r, x0, y0, x1, y1, thr, dark)
    if bo and br:
        dx = br[0] - bo[0]; dy = br[1] - bo[1]
        dw = (br[2] - br[0]) - (bo[2] - bo[0]); dh = (br[3] - br[1]) - (bo[3] - bo[1])
        print(f'{name:<10} {str(bo[:4]):<28} {str(br[:4]):<28} dx={dx} dy={dy} dw={dw} dh={dh}')
    else:
        print(f'{name:<10} {str(bo):<28} {str(br):<28} MISSING')
