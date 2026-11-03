# -*- coding: utf-8 -*-
"""生成《LLM 推理全流程》图解的 HTML + SVG 版本（全部真实文本，独立 SVG 最小单元）"""
import html as H

W, Hh = 1200, 1620
INK = '#1F1F1F'
BLUE = '#2E6FE0'
PILL_TX = '#1D5BC6'
PILL_BG = '#D3E5FA'
Y_F, Y_S = '#FBE3B6', '#C9963F'          # 黄色小盒
C_BLUE, C_GREEN, C_ORNG, C_PURP = '#85B5E6', '#A6CD8B', '#F2B279', '#BC8FD9'
POS_PAL = ['#F2B279', '#A6CD8B', '#F7D57E']

E = []  # svg elements


def esc(s):
    return H.escape(str(s), quote=True)


def T(x, y, s, px=15, w=400, f=INK, a='middle', it=False, sp=None):
    st = f' letter-spacing="{sp}"' if sp else ''
    its = ' font-style="italic"' if it else ''
    E.append(f'<text x="{x}" y="{y}" font-size="{px}" font-weight="{w}" fill="{f}" '
             f'text-anchor="{a}" dominant-baseline="central"{its}{st}>{esc(s)}</text>')


def TR(x, y, runs, a='middle', f=INK):
    """runs: list of (text, opts) ; opts: px,w,it,f,sub"""
    out, cur = [], 0
    for run in runs:
        t, o = run[0], (run[1] if len(run) > 1 else {})
        if not isinstance(o, dict):
            o = {'px': o}
        px = o.get('px', 15)
        dy = ''
        if o.get('sub') and cur == 0:
            cur = px * 0.22
            dy = f' dy="{cur:.1f}"'
        elif not o.get('sub') and cur != 0:
            dy = f' dy="{-(cur):.1f}"'
            cur = 0
        its = ' font-style="italic"' if o.get('it') else ''
        wt = o.get('w', 400)
        fc = o.get('f', f)
        cls = f' font-size="{px}" font-weight="{wt}" fill="{fc}"{its}{dy}'
        out.append(f'<tspan{cls}>{esc(t)}</tspan>')
    E.append(f'<text x="{x}" y="{y}" text-anchor="{a}" dominant-baseline="central">{"".join(out)}</text>')


def RR(x, y, w, h, rx=0, fill='none', stroke='none', sw=0, dash=None, op=None):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    o = f' opacity="{op}"' if op else ''
    fs = fill if fill else 'none'
    E.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fs}" '
             f'stroke="{stroke}" stroke-width="{sw}"{d}{o}/>')


def LN(x1, y1, x2, y2, stroke='#222222', sw=1.5, dash=None, marker=None, cap='butt', op=None):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    m = f' marker-end="url(#{marker})"' if marker else ''
    o = f' opacity="{op}"' if op else ''
    E.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" '
             f'stroke-width="{sw}" stroke-linecap="{cap}"{d}{m}{o}/>')


def PTH(d, stroke='#222222', sw=1.5, dash=None, marker=None, fill='none'):
    dd = f' stroke-dasharray="{dash}"' if dash else ''
    m = f' marker-end="url(#{marker})"' if marker else ''
    E.append(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" '
             f'stroke-linecap="round"{dd}{m}/>')


def POLY(pts, fill='none', stroke='none', sw=0, dash=None):
    p = ' '.join(f'{a},{b}' for a, b in pts)
    d = f' stroke-dasharray="{dash}"' if dash else ''
    E.append(f'<polygon points="{p}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')


def CIRC(cx, cy, r, fill='none', stroke='none', sw=0):
    E.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')


def PLUS(cx, cy, r, sw=1.6, stroke='#333333', fill='#FFFFFF'):
    CIRC(cx, cy, r, fill=fill, stroke=stroke, sw=sw)
    LN(cx - r * 0.55, cy, cx + r * 0.55, cy, stroke=stroke, sw=sw, cap='round')
    LN(cx, cy - r * 0.55, cx, cy + r * 0.55, stroke=stroke, sw=sw, cap='round')


def MAT(x, y, rows, cols, cw, ch, gx=1, gy=1, fill=C_BLUE, stroke='#FFFFFF', sw=1, outer=None, fillfn=None):
    for r in range(rows):
        for c in range(cols):
            f = fillfn(r, c) if fillfn else fill
            RR(x + c * (cw + gx), y + r * (ch + gy), cw, ch, 0, f, stroke, sw)
    if outer:
        RR(x - 1, y - 1, cols * (cw + gx) - gx + 2, rows * (ch + gy) - gy + 2, 0, 'none', outer, 1.4)


def CUBE(fx, fy, fw, fh, dx, dy, front, top, side, stroke, cols=3, rows=4):
    """fx,fy: front face 左上角; dx,dy: 顶面偏移"""
    POLY([(fx, fy), (fx + dx, fy - dy), (fx + fw + dx, fy - dy), (fx + fw, fy)], fill=top, stroke=stroke, sw=1.2)
    POLY([(fx + fw, fy), (fx + fw + dx, fy - dy), (fx + fw + dx, fy + fh - dy), (fx + fw, fy + fh)], fill=side,
         stroke=stroke, sw=1.2)
    RR(fx, fy, fw, fh, 0, front, stroke, 1.2)
    for i in range(1, cols):
        LN(fx + fw * i / cols, fy, fx + fw * i / cols, fy + fh, stroke='#FFFFFF', sw=1, op=0.7)
    for j in range(1, rows):
        LN(fx, fy + fh * j / rows, fx + fw, fy + fh * j / rows, stroke='#FFFFFF', sw=1, op=0.7)


def header(n, cx, cy, label, pw, px=19):
    CIRC(cx, cy, 16, fill=BLUE)
    T(cx, cy + 0.5, str(n), px=17, w=800, f='#FFFFFF')
    RR(cx + 16, cy - 16, pw, 32, 16, fill=PILL_BG)
    T(cx + 16 + pw / 2, cy + 0.5, label, px=px, w=800, f=PILL_TX)


def arrow(pts, color='#222222', sw=1.6, dash=None, mk='mb'):
    """折线箭头：pts 顺序连接，末端带箭头"""
    d = 'M ' + ' L '.join(f'{a} {b}' for a, b in pts)
    PTH(d, stroke=color, sw=sw, dash=dash, marker=mk)


# ============================================================ 标题
T(600, 60, 'LLM 推理全流程', 54, 900)
T(600, 114, '从 Prompt 到第一个 Token', 30, 800)

# ============================================================ 步骤 1 输入提示词
header(1, 48, 165, '输入提示词', 120)
T(122, 208, '(Prompt)', 16, 500)
# 纸张
POLY([(48, 228), (158, 228), (178, 248), (178, 348), (48, 348)], fill='#FFFFFF', stroke='#3A3A3A', sw=1.8)
POLY([(158, 228), (158, 248), (178, 248)], fill='#DCE3EA', stroke='#3A3A3A', sw=1.4)
LN(60, 246, 148, 246, stroke='#BFC7CF', sw=2)
LN(60, 261, 148, 261, stroke='#BFC7CF', sw=2)
LN(60, 276, 130, 276, stroke='#BFC7CF', sw=2)
T(113, 310, '今天的天气', 17, 600)
T(113, 334, '真不错，', 17, 600)
T(113, 380, 'Prompt', 15, 600)
T(113, 402, '（原始文本）', 15)

# ============================================================ 步骤 2 分词
header(2, 280, 165, '分词 (Tokenization)', 196)
T(300, 206, '将文本切分为若干词元', 15, 500, a='start')
T(300, 228, '(Token)', 15, 500, a='start')
toks = ['今天', '的', '天气', '真', '不错', '，']
ids = ['3200', '2819', '1543', '820', '945', '100']
bx = [250 + i * 74 for i in range(6)]
for i in range(6):
    RR(bx[i], 248, 70, 44, 6, '#FFFFFF', '#3A3A3A', 1.6)
    T(bx[i] + 35, 270, toks[i], 18, 600)
    LN(bx[i] + 35, 296, bx[i] + 35, 336, marker='mb')
    RR(bx[i], 342, 70, 44, 6, Y_F, Y_S, 1.6)
    T(bx[i] + 35, 364, ids[i], 16, 600)
T(470, 414, 'Token IDs（数字编码）', 15)
TR(470, 440, [('输入序列长度 ', 15), ('N', 15, {'w': 800, 'it': True}), (' = 6', 15)])

# ============================================================ 步骤 3 词嵌入
header(3, 718, 165, '词嵌入 (Embedding)', 200)
T(700, 206, '将 Token ID 映射为高维向量，', 15, 500, a='start')
T(700, 228, '并加上位置编码（位置信息）', 15, 500, a='start')
T(848, 254, '词向量', 15, 700)
T(950, 254, '位置向量', 15, 700)
T(1072, 242, '输入表示', 15, 700)
T(1072, 262, '(embedding)', 13)
for i in range(6):
    ytop = 272 + i * 32
    RR(730, ytop, 60, 26, 5, Y_F, Y_S, 1.4)
    T(760, ytop + 13, ids[i], 14, 600)
    LN(792, ytop + 13, 808, ytop + 13, marker='mb')
    # 词向量（蓝）
    for c in range(4):
        RR(814 + c * 18, ytop + 4, 17, 18, 0, C_BLUE, '#FFFFFF', 1)
    # 位置向量（暖色混合）
    for c in range(4):
        RR(914 + c * 18, ytop + 4, 17, 18, 0, POS_PAL[(i + c) % 3], '#FFFFFF', 1)
    LN(984, ytop + 13, 1000, ytop + 13, marker='mb')
PLUS(897, 362, 12)
emb_special = {(0, 4): C_ORNG, (1, 1): C_GREEN, (2, 3): C_ORNG, (3, 0): C_GREEN, (4, 2): C_ORNG, (5, 4): C_GREEN,
               (2, 0): '#F7D57E'}
MAT(1006, 272, 6, 5, 26, 28, 1, 1, outer='#555555',
    fillfn=lambda r, c: emb_special.get((r, c), C_BLUE))
T(872, 474, '词嵌入 + 位置编码', 17, 700)
TR(1072, 472, [('N', 16, {'w': 800, 'it': True}), (' × ', 16), ('d', 16, {'it': True}),
               ('model', 10, {'sub': True, 'it': True})])

# 大箭头 1→2 / 2→3
POLY([(192, 302), (210, 302), (210, 292), (240, 312), (210, 332), (210, 322), (192, 322)],
     fill='#B9CFEA', stroke='#6C8FBF', sw=1.5)
POLY([(700, 302), (716, 302), (716, 292), (742, 312), (716, 332), (716, 322), (700, 322)],
     fill='#B9CFEA', stroke='#6C8FBF', sw=1.5)

# 弯箭头 3→4
PTH('M 592 470 C 618 496, 604 516, 568 526', stroke='#222222', sw=2, marker='mb')

# ============================================================ 步骤 4 Transformer 层堆叠
header(4, 38, 512, 'Transformer 层堆叠', 214)
# 层叠副本
for i in range(5, 0, -1):
    RR(250 + 9 * i, 540 - 8 * i, 585, 585, 14, '#FFFFFF', '#9AA4AE', 1.2)
RR(250, 540, 585, 585, 14, '#FFFFFF', '#3A3A3A', 2)
T(62, 554, '重复 L 层，每层包含多头注意力', 13.5, 500, a='start')
T(62, 576, '和前馈网络（FFN/MLP 或 MoE）', 13.5, 500, a='start')
TR(172, 668, [('第 ', 15), ('l', 15, {'it': True}), (' 层（示意）', 15)])

# 残差连接 + 顶层 LayerNorm
LN(272, 598, 404, 598, marker='mb')
T(312, 586, '残差连接', 13, 500, f='#333333', a='start')
RR(408, 580, 226, 36, 18, Y_F, Y_S, 1.6)
T(521, 598, 'LayerNorm', 16, 700)
LN(272, 598, 272, 872, sw=1.6)
LN(521, 616, 521, 626, marker='mb')

# ---------- 多头注意力
RR(292, 630, 458, 218, 12, '#EAF3FC', '#7FA8D9', 1.6)
T(521, 654, '多头注意力 (Attention)', 19, 800)
T(322, 706, 'Q', 21, 800)
T(472, 706, 'K', 21, 800)
T(622, 706, 'V', 21, 800)
MAT(340, 682, 4, 5, 17, 12, 1, 1, fill=C_BLUE)
MAT(490, 682, 4, 5, 17, 12, 1, 1, fill=C_GREEN)
MAT(640, 682, 4, 5, 17, 12, 1, 1, fill=C_ORNG)
# 因果掩码
RR(300, 758, 168, 82, 10, '#FBE4EC', '#E8A8BE', 1.5)
T(360, 788, '因果掩码', 15.5, 700)
T(360, 808, '(Causal Mask)', 12.5)
for r in range(5):
    for c in range(5):
        if c <= r:
            RR(398 + c * 14, 770 + r * 14, 13, 13, 0, C_PURP, '#FFFFFF', 1)
LN(470, 806, 482, 806, marker='mb')
# 注意力计算
RR(486, 780, 112, 54, 8, '#FFFFFF', '#3A3A3A', 1.5)
T(542, 800, '注意力计算', 14.5, 700)
T(542, 820, '(多头并行)', 12)
LN(538, 737, 538, 776, marker='mb')
# 注意力输出
RR(612, 768, 130, 74, 8, '#FFFFFF', '#3A3A3A', 1.4, dash='5,4')
T(677, 786, '注意力输出', 14, 700)
MAT(640, 794, 2, 6, 15, 15, 1, 1, fill=C_BLUE)
LN(598, 806, 608, 806, marker='mb')
LN(684, 737, 684, 764, marker='mb')
# 左侧输入
T(118, 742, '来自上一层的', 14.5)
T(118, 764, '隐状态', 14.5)
TR(118, 794, [('H', 17, {'w': 800, 'it': True}), ('l-1', 11, {'sub': True, 'it': True})])
TR(118, 820, [('(N × ', 14), ('d', 14, {'it': True}), ('model', 9.5, {'sub': True, 'it': True}), (')', 14)])
LN(205, 780, 288, 780, marker='mb')

# ⊕1 与第二个 LayerNorm
PLUS(521, 872, 13)
PTH('M 677 842 L 677 872 L 539 872', marker='mb')
LN(272, 872, 504, 872, marker='mb')
LN(521, 885, 521, 894)
RR(408, 894, 226, 36, 18, Y_F, Y_S, 1.6)
T(521, 912, 'LayerNorm', 16, 700)
LN(521, 930, 521, 936, marker='mb')

# 残差2（右侧绕行）
arrow([(521, 885), (762, 885), (762, 1050), (539, 1050)])

# ---------- 前馈网络
RR(292, 940, 458, 90, 12, '#EDF6E7', '#9CC08C', 1.6)
T(521, 964, '前馈网络（FFN / MLP 或 MoE）', 17.5, 800)
RR(304, 978, 92, 44, 8, '#FFFFFF', '#3A3A3A', 1.4)
T(350, 996, '线性变换', 13.5, 700)
TR(350, 1014, [('(', 13), ('W', 13, {'it': True, 'w': 700}), ('1', 9, {'sub': True}), (')', 13)])
LN(398, 1000, 410, 1000, marker='mb')
RR(414, 978, 132, 44, 8, '#FFFFFF', '#3A3A3A', 1.4)
PTH('M 424 1012 C 438 1012, 434 986, 450 986', stroke='#E87BA4', sw=2.5)
T(492, 996, '激活函数', 13.5, 700)
T(492, 1014, '(SiLU 等)', 12)
LN(548, 1000, 560, 1000, marker='mb')
RR(564, 978, 92, 44, 8, '#FFFFFF', '#3A3A3A', 1.4)
T(610, 996, '线性变换', 13.5, 700)
TR(610, 1014, [('(', 13), ('W', 13, {'it': True, 'w': 700}), ('2', 9, {'sub': True}), (')', 13)])
LN(658, 1000, 670, 1000, marker='mb')
MAT(674, 978, 3, 4, 15, 15, 1, 1, fill=C_BLUE)
# ⊕2 与底部 LayerNorm
PLUS(521, 1050, 13)
LN(521, 1030, 521, 1037)
LN(521, 1063, 521, 1068, marker='mb')
RR(408, 1072, 226, 36, 18, Y_F, Y_S, 1.6)
T(521, 1090, 'LayerNorm', 16, 700)
LN(521, 1108, 521, 1128, marker='mb')
TR(864, 1082, [('× ', 26, {'it': True, 'w': 800}), ('L', 26, {'it': True, 'w': 800})])

# ============================================================ 步骤 5 KV Cache
header(5, 913, 512, 'KV Cache（键值缓存）', 224)
T(913, 556, '在推理过程中缓存每层的 K、V', 14.5, 500, a='start')
T(913, 578, '（便于后续自回归生成时复用）', 14.5, 500, a='start')
RR(950, 604, 235, 392, 12, 'none', '#7A7A7A', 1.5, dash='7,5')
TR(1067, 632, [('第 ', 16.5, {'w': 800}), ('l', 16.5, {'w': 800, 'it': True}), (' 层的 KV Cache', 16.5, {'w': 800})])
T(966, 670, 'K Cache', 15.5, 800, a='start')
T(966, 690, '（已缓存的键）', 13, 500, a='start')
T(1004, 716, '已缓存', 13.5, a='start')
TR(1004, 736, [('(≤ N × ', 13), ('d', 13, {'it': True}), ('k', 9.5, {'sub': True, 'it': True}), (')', 13)], a='start')
CUBE(1080, 664, 66, 72, 16, 14, '#7FB0E8', '#A9CBF0', '#5E93CC', '#4A7BB8', 3, 4)
T(966, 828, 'V Cache', 15.5, 800, a='start')
T(966, 848, '（已缓存的值）', 13, 500, a='start')
T(1004, 874, '已缓存', 13.5, a='start')
TR(1004, 894, [('(≤ N × ', 13), ('d', 13, {'it': True}), ('v', 9.5, {'sub': True, 'it': True}), (')', 13)], a='start')
CUBE(1078, 822, 72, 76, 18, 16, '#BC8FD9', '#D6B4EA', '#9A6BBF', '#8A55B0', 3, 4)
# 写入 / 读取 箭头
LN(752, 748, 944, 748, stroke=BLUE, sw=2.6, marker='mbl')
T(852, 686, '写入 K、V', 14.5, 700, f=BLUE)
T(852, 708, '到缓存', 14.5, 700, f=BLUE)
T(852, 730, '(在 Prefill 阶段)', 12.5, 500, f=BLUE)
LN(946, 800, 756, 800, stroke=BLUE, sw=2.2, dash='7,5', marker='mbl')
T(852, 846, '在 Decode 阶段', 14, 700, f=BLUE)
T(852, 868, '读取历史 KV', 14, 700, f=BLUE)
T(852, 890, '加速计算', 14, 700, f=BLUE)

# ============================================================ Prefill 阶段面板
RR(20, 1136, 486, 334, 14, '#E8F2FC', '#C4DCF2', 1.2)
T(40, 1170, 'Prefill 阶段：处理整个提示词', 21, 800, a='start')
T(40, 1198, '一次性计算所有输入位置的隐藏状态，并将每层的 K、V 写入缓存', 13.5, 500, f='#333333', a='start')
RR(40, 1214, 446, 250, 10, 'none', '#777777', 1.3, dash='6,5')
T(263, 1236, '最后一层输出隐藏状态', 15, 700)
TR(263, 1258, [('H', 15, {'w': 800, 'it': True}), ('L', 10, {'sub': True, 'it': True}),
               (' (N × ', 14), ('d', 14, {'it': True}), ('model', 10, {'sub': True, 'it': True}), (')', 14)])
pref_rows = ['今天', '的', '天气', '真', '不错', '，']
for i in range(6):
    ytop = 1262 + i * 28
    T(72, ytop + 9.5, pref_rows[i], 14.5)
    T(104, ytop + 9.5, '—', 13, f='#888888')
    for c in range(13):
        f = C_PURP if i == 5 else C_BLUE
        RR(118 + c * 24, ytop, 22, 19, 0, f, '#FFFFFF', 1)
LN(116, 1427, 430, 1427, stroke='#D489C7', sw=2, dash='5,4')
TR(263, 1440, [('最后一个位置的向量 ', 15, {'w': 800}), ('h', 15, {'w': 800, 'it': True}),
               ('last', 10, {'sub': True, 'it': True})])
TR(263, 1456, [('(1 × ', 12.5), ('d', 12.5, {'it': True}), ('model', 9, {'sub': True, 'it': True}), (')', 12.5)])
PTH('M 486 1332 C 504 1332, 510 1322, 518 1314', marker='mb')

# ============================================================ 步骤 6 取最后位置
RR(508, 1136, 214, 282, 14, '#FDF0F4', '#F0C8D8', 1.2)
header(6, 532, 1164, '取最后位置', 116, px=16.5)
T(615, 1202, '(Last Position)', 15.5, 800)
T(615, 1234, '提取序列中最后一个', 14)
T(615, 1256, '位置的隐藏状态', 14)
for c in range(7):
    RR(522 + c * 27, 1298, 24, 20, 0, C_PURP, '#FFFFFF', 1)
TR(615, 1350, [('h', 17, {'w': 800, 'it': True}), ('last', 11, {'sub': True, 'it': True})])
TR(615, 1372, [('(1 × ', 14), ('d', 14, {'it': True}), ('model', 10, {'sub': True, 'it': True}), (')', 14)])
POLY([(712, 1302), (730, 1302), (730, 1295), (748, 1308), (730, 1321), (730, 1314), (712, 1314)],
     fill='#B989D6')

# ============================================================ 步骤 7 最终归一化
RR(725, 1136, 180, 282, 14, '#FDF6DE', '#EAD9A8', 1.2)
header(7, 749, 1164, '最终归一化', 108, px=16.5)
T(815, 1202, '(Final Norm)', 15.5, 800)
RR(745, 1224, 140, 48, 10, Y_F, Y_S, 1.5)
T(815, 1244, 'RMSNorm /', 14.5, 700)
T(815, 1262, 'LayerNorm', 14.5, 700)
LN(815, 1272, 815, 1292, marker='mb')
for c in range(7):
    RR(732 + c * 24, 1306, 22, 20, 0, C_PURP, '#FFFFFF', 1)
T(815, 1356, 'ĥ', 18, 800, it=True)
TR(815, 1378, [('(1 × ', 14), ('d', 14, {'it': True}), ('model', 10, {'sub': True, 'it': True}), (')', 14)])
POLY([(900, 1302), (916, 1302), (916, 1295), (934, 1308), (916, 1321), (916, 1314), (900, 1314)],
     fill='#B989D6')

# ============================================================ 步骤 8 语言模型头
RR(912, 1136, 272, 282, 14, '#EDF6E9', '#C4DFBA', 1.2)
header(8, 936, 1164, '语言模型头', 118, px=16.5)
T(1048, 1202, '(LM Head)', 15.5, 800)
T(1048, 1234, '线性变换到词表大小', 14.5)
RR(926, 1284, 96, 52, 10, Y_F, Y_S, 1.5)
TR(974, 1310, [('W', 20, {'w': 800, 'it': True}), ('vocab', 12, {'sub': True, 'it': True})])
LN(1024, 1310, 1046, 1310, marker='mb')
T(1092, 1272, 'Logits', 15.5, 800)
TR(1092, 1292, [('(1 × |V|)', 12)])
LN(1056, 1300, 1056, 1352, stroke='#444444', sw=1.4)
LN(1056, 1352, 1140, 1352, stroke='#444444', sw=1.4)
for i, hgt in enumerate([38, 28, 32, 19, 14, 10]):
    RR(1062 + i * 13, 1352 - hgt, 9, hgt, 0, C_BLUE, '#FFFFFF', 0.5)
LN(1092, 1360, 1092, 1424, marker='mb')

# ============================================================ 步骤 9 解码采样
RR(648, 1432, 536, 156, 14, '#E7F1FB', '#BFD9F2', 1.2)
header(9, 672, 1462, '解码采样 (Decoding)', 224, px=16.5)
T(700, 1494, '将 logits 转换为下一个 Token', 14, 500, a='start')
# 贪心解码
RR(662, 1508, 126, 66, 8, 'none', '#888888', 1.2, dash='5,4')
T(725, 1524, '贪心解码', 14, 700)
T(725, 1542, '(Greedy)', 12)
RR(670, 1550, 62, 18, 4, '#FFFFFF', '#555555', 1)
T(701, 1559, 'argmax', 10.5, 600)
for i, hgt in enumerate([26, 10, 6]):
    RR(744 + i * 10, 1568 - hgt, 7, hgt, 0, '#85B5E6' if i == 0 else '#C9C9C9', '#FFFFFF', 0.5)
# 随机采样
RR(798, 1508, 128, 66, 8, 'none', '#888888', 1.2, dash='5,4')
T(856, 1524, '随机采样', 14, 700)
T(856, 1542, '(Sampling)', 12)
for i, hgt in enumerate([24, 32, 14, 20, 9]):
    RR(806 + i * 12, 1568 - hgt, 8, hgt, 0, C_BLUE, '#FFFFFF', 0.5)
RR(890, 1540, 26, 26, 6, '#FFFFFF', '#555555', 1.3)
for dx, dy in [(896, 1546), (910, 1546), (903, 1553), (896, 1560), (910, 1560)]:
    CIRC(dx, dy, 2.2, fill='#444444')
# 核采样
RR(936, 1508, 128, 66, 8, 'none', '#888888', 1.2, dash='5,4')
T(1000, 1524, '核采样', 14, 700)
T(1000, 1542, '(Top-p)', 12)
for i, hgt in enumerate([24, 32, 14, 20, 9]):
    RR(948 + i * 12, 1568 - hgt, 8, hgt, 0, C_BLUE, '#FFFFFF', 0.5)
PTH('M 948 1568 C 970 1556, 990 1548, 1012 1528', stroke='#A66BCF', sw=2.2)
T(1080, 1546, '…', 22, 800)

# ============================================================ 步骤 10 第一个 Token
header(10, 188, 1496, '第一个 Token（输出）', 202, px=17)
T(305, 1532, '得到生成的第一个 Token 及其文本形式', 14)
LN(644, 1556, 476, 1556, sw=2, marker='mb')
RR(196, 1548, 92, 44, 8, '#F9D7E8', '#D883B4', 1.6)
T(242, 1570, '2987', 20, 800)
LN(292, 1570, 358, 1570, marker='mb')
RR(364, 1548, 92, 44, 8, Y_F, Y_S, 1.6)
T(410, 1570, '晴天', 19, 800)
T(242, 1612, 'Token ID', 13.5)
T(410, 1612, '解码为文本', 13.5)

# ============================================================ 组装 HTML
svg = f'''<svg viewBox="0 0 {W} {Hh}" xmlns="http://www.w3.org/2000/svg" font-family="'PingFang SC','Microsoft YaHei','Noto Sans SC','Source Han Sans SC',sans-serif">
<defs>
<marker id="mb" markerWidth="10" markerHeight="9" refX="8" refY="4.5" orient="auto-start-reverse">
<path d="M1,1 L9,4.5 L1,8 Z" fill="#222222"/></marker>
<marker id="mbl" markerWidth="10" markerHeight="9" refX="8" refY="4.5" orient="auto-start-reverse">
<path d="M1,1 L9,4.5 L1,8 Z" fill="#2E6FE0"/></marker>
</defs>
<rect x="0" y="0" width="{W}" height="{Hh}" fill="#FFFFFF"/>
''' + '\n'.join(E) + '\n</svg>'

page = '''<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LLM 推理全流程 —— 从 Prompt 到第一个 Token</title>
<style>
  body { margin:0; background:#EEF0F4; display:flex; justify-content:center; padding:28px 16px; }
  .poster { background:#fff; width:min(960px,100%); border-radius:14px;
            box-shadow:0 6px 30px rgba(30,40,60,.12); overflow:hidden; }
  svg { display:block; width:100%; height:auto; }
</style>
</head>
<body>
<div class="poster">''' + svg + '''</div>
</body>
</html>'''

out = '/home/z/my-project/download/LLM推理全流程_图解.html'
with open(out, 'w', encoding='utf-8') as fp:
    fp.write(page)
print('written', out, len(page), 'chars,', len(E), 'svg elements')
