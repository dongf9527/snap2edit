# -*- coding: utf-8 -*-
"""组件库共享底座 —— 颜色演算、复合组件几何、参数化图标（F6）。

组件一律参数化 (id, 位置, 尺寸, 颜色)；几何与配色在此**统一定义**，
svgout / pptxout 两条产线各自把同一份定义渲染为原生可编辑单元：

    cube         立方体（正面 + 顶面 + 侧面三块面片，自动明暗配色）
    matrix-cell  矩阵格子（rows×cols 均分 + gap 间隙 + 逐格文字）
    flow-box     流程框（圆角主体 + 顶部色带标题 + 正文区）
    icon         参数化图标（100×100 归一化多边形，fill/ring/stroke 三种部件）

图标全部由直线段多边形构成，因此 PPTX 侧可用原生 Freeform（任意多边形）
渲染，无需贴图 —— 维持"Picture = 0"的全可编辑承诺。
"""

import math

# ---------------- 颜色演算 ----------------

def _rgb(color):
    h = str(color).lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def shade(color, factor):
    """颜色明暗演算：factor>0 向白色靠近，factor<0 向黑色加深。

    例：shade("#2B6CB0", 0.25) 顶面提亮；shade("#2B6CB0", -0.22) 侧面加深。
    """
    r, g, b = _rgb(color)

    def adj(c):
        return c + (255 - c) * factor if factor >= 0 else c * (1 + factor)

    return "#{:02X}{:02X}{:02X}".format(
        *(max(0, min(255, int(round(adj(c))))) for c in (r, g, b)))


def contrast_text(bg_color):
    """按背景亮度返回可读文字色（深底白字 / 浅底墨字）。"""
    r, g, b = _rgb(bg_color)
    lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
    return "#1F2937" if lum > 0.62 else "#FFFFFF"


# ---------------- cube 立方体 ----------------

def cube_faces(x, y, w, h, depth=None):
    """立方体三块面片（2.5D，全部收在包围盒内）。

    返回 {"depth": d, "top": [4pt], "side": [4pt], "front": (fx, fy, fw, fh)}；
    depth 缺省 = min(w,h)*0.2，并被钳制在 [0, min(w,h)/2]。
    """
    d = float(min(w, h) * 0.2 if depth is None else depth)
    d = max(0.0, min(d, min(w, h) * 0.5))
    return {
        "depth": d,
        "top": [(x, y + d), (x + d, y), (x + w, y), (x + w - d, y + d)],
        "side": [(x + w - d, y + d), (x + w, y), (x + w, y + h - d), (x + w - d, y + h)],
        "front": (x, y + d, w - d, h - d),
    }


# ---------------- matrix-cell 矩阵格子 ----------------

def matrix_cells(x, y, w, h, rows, cols, gap=0.0):
    """rows×cols 均分格子（行优先），返回 [(cx, cy, cw, ch), ...]。

    gap 为格间距(px)，从总宽高中扣除后均分。
    """
    g = max(0.0, float(gap))
    cw = (float(w) - g * (cols - 1)) / cols
    ch = (float(h) - g * (rows - 1)) / rows
    return [(x + c * (cw + g), y + r * (ch + g), cw, ch)
            for r in range(rows) for c in range(cols)]


# ---------------- icon 参数化图标 ----------------
# 部件三元语义：fill=实心多边形 / ring=空心描边闭合多边形 / stroke=开放折线
# 坐标归一化在 100×100（y 向下），渲染时等比 contain 缩放并居中到包围盒。

def _ngon(cx, cy, n, r, rot=0.0):
    """正 n 边形（圆的直线段近似）。"""
    return [(cx + r * math.cos(rot + 2 * math.pi * i / n),
             cy + r * math.sin(rot + 2 * math.pi * i / n)) for i in range(n)]


def _star(cx, cy, n, r_outer, r_inner, rot=0.0):
    """2n 顶点星形（齿轮齿形的直线段近似）。"""
    pts = []
    for i in range(n * 2):
        ang = rot + math.pi * i / n
        r = r_outer if i % 2 == 0 else r_inner
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    return pts


ICONS = {
    "chart": [
        ("fill", [(10, 84), (90, 84), (90, 90), (10, 90)]),
        ("fill", [(16, 52), (28, 52), (28, 84), (16, 84)]),
        ("fill", [(40, 28), (52, 28), (52, 84), (40, 84)]),
        ("fill", [(64, 60), (76, 60), (76, 84), (64, 84)]),
    ],
    "network": [
        ("fill", [(48, 22), (52, 22), (52, 38), (48, 38)]),
        ("fill", [(48, 62), (52, 62), (52, 78), (48, 78)]),
        ("fill", [(22, 48), (38, 48), (38, 52), (22, 52)]),
        ("fill", [(62, 48), (78, 48), (78, 52), (62, 52)]),
        ("fill", [(50, 38), (62, 50), (50, 62), (38, 50)]),
        ("fill", [(50, 4), (59, 13), (50, 22), (41, 13)]),
        ("fill", [(4, 50), (13, 59), (22, 50), (13, 41)]),
        ("fill", [(78, 50), (87, 59), (96, 50), (87, 41)]),
        ("fill", [(41, 87), (50, 96), (59, 87), (50, 78)]),
    ],
    "sparkle": [
        ("fill", [(50, 4), (59, 41), (96, 50), (59, 59),
                  (50, 96), (41, 59), (4, 50), (41, 41)]),
    ],
    "lightning": [
        ("fill", [(58, 4), (26, 52), (44, 52), (38, 96),
                  (74, 40), (52, 40)]),
    ],
    "gear": [
        ("fill", _star(50, 50, 8, 46, 34, rot=-math.pi / 2)),
        ("ring", _ngon(50, 50, 12, 15)),
    ],
    "doc": [
        ("ring", [(24, 6), (62, 6), (76, 20), (76, 94), (24, 94)]),
        ("fill", [(62, 6), (62, 20), (76, 20)]),
        ("fill", [(34, 34), (66, 34), (66, 40), (34, 40)]),
        ("fill", [(34, 50), (66, 50), (66, 56), (34, 56)]),
        ("fill", [(34, 66), (58, 66), (58, 72), (34, 72)]),
    ],
    "user": [
        ("fill", _ngon(50, 30, 8, 17, rot=-math.pi / 2)),
        ("fill", [(18, 94), (20, 72), (34, 61), (66, 61), (80, 72), (82, 94)]),
    ],
    "check": [
        ("fill", [(12, 52), (24, 40), (44, 66), (72, 18), (88, 30), (46, 90)]),
    ],
    "target": [
        ("ring", _ngon(50, 50, 16, 44)),
        ("ring", _ngon(50, 50, 16, 28)),
        ("fill", _ngon(50, 50, 12, 12)),
    ],
    "brain": [
        ("fill", [(20, 72), (12, 58), (14, 42), (22, 30), (34, 22), (48, 18),
                  (62, 20), (74, 28), (82, 40), (84, 54), (78, 66), (66, 74),
                  (50, 76), (34, 74)]),
        ("stroke", [(48, 20), (47, 38), (50, 54), (48, 75)]),
        ("stroke", [(24, 44), (31, 37), (39, 43)]),
        ("stroke", [(25, 60), (33, 54), (41, 60)]),
        ("stroke", [(57, 38), (64, 32), (71, 38)]),
        ("stroke", [(57, 56), (65, 50), (72, 57)]),
    ],
}

ICON_NAMES = tuple(sorted(ICONS))


def icon_parts(name, x, y, w, h):
    """把图标按 contain 缩放 + 居中放进包围盒。

    返回 [(kind, [(px, py), ...]), ...]；未知图标名抛出 KeyError（上层转可读错误）。
    """
    s = min(float(w), float(h)) / 100.0
    dx = x + (w - 100.0 * s) / 2.0
    dy = y + (h - 100.0 * s) / 2.0
    return [(kind, [(dx + px * s, dy + py * s) for px, py in pts])
            for kind, pts in ICONS[name]]
