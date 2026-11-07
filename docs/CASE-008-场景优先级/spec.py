#!/usr/bin/env python3
"""布局规格书 —— CASE-008 · 008-场景优先级.png (1728x972)
《场景优先级与组合决策》四面板版式。
一份规格喂两条产线：build_html.py 与 build_pptx.py 均从本文件取数。
坐标系：与原图像素 1:1；所有颜色/坐标为实测值（scripts/case008_measure*.py）。
"""

W, H = 1728, 972

# ---------- 色板（实测） ----------
C = {
    'bg':          '#FDFDFD',  # 页面底
    'white':       '#FFFFFF',
    'card_border': '#E4E8ED',  # 面板卡描边
    'navy':        '#1B3A52',  # 面板头带/表头带
    'title_navy':  '#0A2440',  # 大标题
    'axis':        '#081630',  # 矩阵轴线（近黑藏青）
    'axis_label':  '#3A485F',
    'chip_olive':  '#80866F',
    'chip_brown':  '#968478',
    'chip_purple': '#787692',
    'chip_body':   '#EDEFF1',
    'chip_text':   '#33415A',
    'stripe_l':    '#F5F6F8',  # P1 奇数行
    'stripe_d':    '#E5EBF1',  # P1 偶数行
    'score_tint':  '#EAEFF4',  # P1 总分列奇数行
    'score_light': '#F7F8FA',  # P1 总分列偶数行
    'hdr_sep_under': '#DFE6EB',  # P1 表头下沿细线
    'badge1': '#7D856C', 'badge2': '#968478', 'badge3': '#797692', 'badge4': '#868383',
    'name_navy':   '#1D253C',   # P1 场景名核心色
    'name_navy2':  '#212C42',   # P3/P4 场景名核心色
    'num_navy':    '#27314C',
    'score_navy':  '#111932',
    'q_tl': '#E9F2E9', 'q_tr': '#E1EFFA', 'q_bl': '#EDEBE9', 'q_br': '#EBE8F3',
    'badge_tl': '#849179', 'badge_tr': '#7F9DBC', 'badge_bl': '#9B887C', 'badge_br': '#817D94',
    'row_stripe':  '#F4F6F8',  # P3/P4 偶数行
    'row_sep':     '#E2E6EC',
    'cell_g1': '#DCE6D1',  # P3r1 可进入试点
    'cell_g2': '#DCE6D2',  # P3r2 / P4r1
    'cell_g3': '#DDE6D3',  # P4r2
    'cell_p':  '#D2D0DF',  # 需补充条件/补充条件
    'cell_x':  '#DAD6D4',  # 暂缓推进/隔离验证
    'pill_green_t':  '#33414E',
    'pill_purple_t': '#575767',
    'pill_gray_t':   '#6B6763',
    'body_text':   '#3D4860',
    # v2 迭代（2026-11-07）：wm_gray/wm_dot 两色随水印移除一并废弃
}
FONT = 'Noto Sans SC'

# ---------- 大标题 ----------
# 墨迹 [21,77]x[33,626]；size 60；字距实测校准 -0.6（Chromium 渲染对齐后）
TITLE = dict(text='场景优先级与组合决策', x=31, y=72, size=60, weight=800,
             color=C['title_navy'], spacing=0)

# ---------- 四张面板卡 ----------
# (x, y, w, h, 头带高, 头带文字, 文字x, 基线, 后缀)
P1_CARD = dict(x=22, y=106, w=909, h=539, band_h=49)
P2_CARD = dict(x=943, y=106, w=763, h=537, band_h=49)
P3_CARD = dict(x=22, y=654, w=901, h=288, band_h=47)
P4_CARD = dict(x=936, y=654, w=771, h=288, band_h=47)

BAND_TITLES = [
    dict(x=24, y=108, w=905, h=49, text='场景优先级排序模型', tx=46, ty=142, size=26, weight=700, spacing=0.6),
    dict(x=945, y=108, w=759, h=49, text='场景价值与可行性矩阵', tx=971, ty=142, size=26, weight=700, spacing=0.7),
    dict(x=24, y=656, w=897, h=47, text='风险门槛与关键要求', tx=46, ty=690, size=26, weight=700, spacing=0,
         suffix='（独立于排序得分）', suffix_x=281, suffix_size=21.5, suffix_weight=700,
         suffix_color='#ECF0F2'),
    dict(x=938, y=656, w=766, h=47, text='投资组合与推进策略', tx=959, ty=690, size=26, weight=700, spacing=-0.2),
]

# ---------- P1 芯片区（三张独立卡片：色带+浅灰体） ----------
# 标签拆双元素：CJK 名(size 21) + 括号百分比(size 22)，各自按实测中心锚定
CHIPS = [
    dict(x=44, y=169, w=257, band_h=41, body_h=128, band=C['chip_olive'],
         label='价值', label_c=144, pct='(40%)', pct_c=208.5,
         lines=['对业务目标的贡献程度', '如效率提升、成本节约、', '收入增长、体验改善', '1 – 5 分']),
    dict(x=350, y=169, w=257, band_h=41, body_h=128, band=C['chip_brown'],
         label='可行性', label_c=444, pct='(35%)', pct_c=518,
         lines=['技术成熟度、数据可获得性', '实施复杂度、资源投入', None, '1 – 5 分']),
    dict(x=655, y=169, w=256, band_h=41, body_h=128, band=C['chip_purple'],
         label='可控性', label_c=749, pct='(25%)', pct_c=823.5,
         lines=['风险可控程度', '可控性越高、风险越易控制', None, '1 – 5 分']),
]
CHIP_BASELINES = [239, 267, 294, 322]     # 正文四行基线
CHIP_TEXT_X_INSET = 17                    # 正文左缘 = chip.x + 17 (61/367/672)
CHIP_TEXT_SIZE = 19                       # 芯片正文字号
CHIP_TEXT_WEIGHT = 500                    # 芯片正文字重（核心色密度实测）
CHIP_LABEL_BASELINE = 198                 # 色带白字基线
CHIP_LABEL_SIZE = 21                      # CJK 名字号
CHIP_PCT_SIZE = 22                        # 括号百分比字号

# ---------- P1 评分表 ----------
T1 = dict(
    x=37, y=352, w=880, header_h=59,       # 表头带 [352,411]
    hdr_under_line=dict(y=411.5, h=1.5, color=C['hdr_sep_under']),
    col_seps=[256, 414.5, 587.5, 749.5],   # 表头白分隔线
    sep_y0=364, sep_y1=399,
    score_x0=749,                          # 总分列左界（条纹反相）
    hdr_text=[                             # (text, cx, baseline, size, weight, color)
        ('场景',     123, 390, 19, 700, C['white']),
        ('价值',     334, 376, 19, 700, C['white']),
        ('(40%)',    334, 400, 20, 700, C['white']),
        ('可行性',   500, 376, 19, 700, C['white']),
        ('(35%)',    500, 400, 20, 700, C['white']),
        ('可控性',   668, 376, 19, 700, C['white']),
        ('(25%)',    668, 400, 20, 700, C['white']),
        ('加权总分', 832, 390, 19, 700, C['white']),
    ],
    rows=[                                  # 行界 [top, bottom]
        (413, 460.5), (461.5, 512), (513, 563.5), (564.5, 614),
    ],
    row_cy=[436.5, 486.5, 538, 589],
    stripe_even=C['stripe_d'], stripe_odd=C['stripe_l'],
    score_odd=C['score_tint'], score_even=C['score_light'],
    badge_cx=71, badge_r=17.5, badge_num_size=18,
    name_x=104, name_size=20, name_weight=600,
    num_cx=[334, 500, 668], num_size=19, num_weight=400,
    score_cx=833.5, score_size=20, score_weight=700,
    text_baseline=[447, 497, 549, 600],    # = row_cy + 10.8
    num_baseline=[446, 496, 548, 599],     # = row_cy + 9.9
    score_baseline=[446, 496, 547.5, 598.5],  # = row_cy + 9.5
    data=[  # (场景, 价值, 可行性, 可控性, 总分, 徽章色)
        ('知识助手',       '4', '4', '4', '4.00', C['badge1']),
        ('工单分流',       '4', '3', '4', '3.65', C['badge2']),
        ('合同审查辅助',   '4', '3', '2', '3.15', C['badge3']),
        ('自动付款 Agent', '5', '2', '1', '2.95', C['badge4']),
    ],
)

# ---------- P2 价值-可行性矩阵 ----------
MATRIX = dict(
    quads=[  # (x, y, w, h, fill)
        (1043, 169, 314, 208, C['q_tl']),
        (1363, 169, 327, 208, C['q_tr']),
        (1043, 383, 314, 178, C['q_bl']),
        (1363, 383, 327, 178, C['q_br']),
    ],
    y_axis=dict(x=1039.5, y0=188, y1=564, arrow_tip=173, arrow_half=5.5),
    x_axis=dict(y=565.5, x0=1040, x1=1682, arrow_tip=1692, arrow_half=5.5),
    labels=[  # (text, x, baseline, size, anchor)
        ('高', 986, 207, 20, 'middle'),
        ('价', 975, 367, 20, 'middle'),
        ('值', 975, 394, 20, 'middle'),
        ('低', 980, 576, 20, 'middle'),
        ('可行性', 1358, 625, 22.5, 'middle'),
        ('高', 1674, 604, 20, 'middle'),
    ],
    label_weight=700,
    badges=[  # (x, y, w, h, fill, title, sub, 标题基线, 副题基线)
        (1113, 174, 177, 60, C['badge_tl'], '先补能力', '(高价值·低可行性)', 201, 225),
        (1436, 173, 177, 60, C['badge_tr'], '优先试点', '(高价值·高可行性)', 200, 224),
        (1114, 484, 176, 59, C['badge_bl'], '暂缓', '(低价值·低可行性)', 511, 535),
        (1436, 484, 176, 59, C['badge_br'], '小额验证', '(低价值·高可行性)', 511, 535),
    ],
    badge_title_size=21, badge_sub_size=15,
)

# ---------- P3 风险门槛表 ----------
T3 = dict(
    x=37, y=717, w=871, header_h=41,       # 表头 [717,758]，表右缘 908
    col_seps=[191.5, 420.5, 738.5], sep_y0=723, sep_y1=752,
    hdr_text=[('场景', 49), ('主要风险', 207), ('风险门槛与要求', 434), ('结论', 756)],
    hdr_baseline=746, hdr_size=18,
    rows=[(760, 800), (803, 840), (843, 882), (885, 925)],
    row_cy=[780, 821.5, 862.5, 905],
    sep_ys=[801.5, 841.5, 883.5, 926.5],   # 行分隔线（最后一条=表底线）
    stripe=C['row_stripe'],
    name_x=50, body_x1=210, body_x2=437,
    cell_x=739, cell_w=169,                # 结论列整列色块 [739,908]
    text_size=18.5, name_size=19, name_weight=700,
    name_baseline=[786, 827, 868, 910],
    body_baseline=[786, 827, 868, 910],
    pill_baseline=[787, 828, 869, 911], pill_size=18.5,
    data=[  # (场景, 主要风险, 风险门槛与要求, 结论, cell色, 文字色)
        ('知识助手',     '内容准确性、数据安全', '符合数据安全与内容治理要求', '可进入试点', C['cell_g1'], C['pill_green_t']),
        ('工单分流',     '分类准确率、业务中断', '满足准确率与灰度运行要求',   '可进入试点', C['cell_g2'], C['pill_green_t']),
        ('合同审查辅助', '法律合规、责任界定',   '须法务复核，满足合规要求',   '需补充条件', C['cell_p'],  C['pill_purple_t']),
        ('自动付款 Agent', '资金安全、合规风险', '涉及资金支付，风险门槛高',   '暂缓推进',   C['cell_x'],  C['pill_gray_t']),
    ],
)

# ---------- P4 投资组合表 ----------
T4 = dict(
    x=951, y=717, w=740, header_h=41,      # 表头 [717,758]，表右缘 1691
    col_seps=[1119.5, 1275.5], sep_y0=723, sep_y1=752,
    hdr_text=[('场景', 963), ('优先级决策', 1134), ('推进策略', 1296)],
    hdr_baseline=746, hdr_size=18,
    rows=[(760, 800), (803, 840), (843, 882), (885, 925)],
    row_cy=[780, 821.5, 862.5, 905],
    sep_ys=[801.5, 841.5, 883.5, 926.5],
    stripe=C['row_stripe'],
    name_x=964, body_x1=1298,
    cell_x=1120, cell_w=155,               # 决策列整列色块 [1120,1275]
    text_size=18.5, name_size=19, name_weight=700,
    name_baseline=[788, 829, 871, 913],    # 原图 P4 行文字比 P3 低 2px
    body_baseline=[788, 829, 871, 913],
    pill_baseline=[789, 830, 871, 913], pill_size=18.5,
    data=[  # (场景, 决策, 推进策略, cell色, 文字色)
        ('知识助手',       '先试点', '优先投入，快速试点，验证价值并迭代优化', C['cell_g2'], C['pill_green_t']),
        ('工单分流',       '先试点', '选择典型业务线，分阶段扩展应用范围',     C['cell_g3'], C['pill_green_t']),
        ('合同审查辅助',   '补充条件', '完善合规与法务复核机制，满足条件后推进', C['cell_p'],  C['pill_purple_t']),
        ('自动付款 Agent', '隔离验证', '在隔离环境中小额验证，评估风险并完善管控', C['cell_x'], C['pill_gray_t']),
    ],
)

# ---------- 水印 ----------
# v2 迭代（2026-11-07）：应用户要求移除页面右下角水印（微信 logo + 公众号 + 解决方案研究所），
# 双交付物均不再包含该元素；原图中仍存在，diff 校验时右下角为预期差异区。

# ---------- 文案清单（终检共用） ----------
PHRASES = [
    '场景优先级与组合决策',
    '场景优先级排序模型', '价值', '可行性', '可控性', '(40%)', '(35%)', '(25%)',
    '对业务目标的贡献程度', '如效率提升、成本节约、', '收入增长、体验改善',
    '技术成熟度、数据可获得性', '实施复杂度、资源投入',
    '风险可控程度', '可控性越高、风险越易控制', '1 – 5 分',
    '场景', '加权总分',
    '知识助手', '工单分流', '合同审查辅助', '自动付款 Agent',
    '4', '3', '2', '1', '5', '4.00', '3.65', '3.15', '2.95',
    '场景价值与可行性矩阵', '先补能力', '(高价值·低可行性)', '优先试点', '(高价值·高可行性)',
    '暂缓', '(低价值·低可行性)', '小额验证', '(低价值·高可行性)',
    '风险门槛与关键要求', '（独立于排序得分）', '主要风险', '风险门槛与要求', '结论',
    '内容准确性、数据安全', '符合数据安全与内容治理要求', '可进入试点',
    '分类准确率、业务中断', '满足准确率与灰度运行要求',
    '法律合规、责任界定', '须法务复核，满足合规要求', '需补充条件',
    '资金安全、合规风险', '涉及资金支付，风险门槛高', '暂缓推进',
    '投资组合与推进策略', '优先级决策', '推进策略',
    '先试点', '补充条件', '隔离验证',
    '优先投入，快速试点，验证价值并迭代优化', '选择典型业务线，分阶段扩展应用范围',
    '完善合规与法务复核机制，满足条件后推进', '在隔离环境中小额验证，评估风险并完善管控',
]
