#!/usr/bin/env python3
"""布局规格书 —— 005-能力缺口判断.png (1728x972)
一份规格喂两条产线：build_html.py 与 build_pptx.py 均从本文件取数。
坐标系：与原图像素 1:1。所有颜色为实测 hex。
"""

W, H = 1728, 972
CANVAS_W, CANVAS_H = W, H

# ---------- 色板 ----------
C = {
    'bg':        '#FEFEFE',
    'navy':      '#253E56',   # 表头/标题/主文字
    'navy_deep': '#1C3250',   # 标题实测略深
    'steel':     '#435D78',   # 战略条/钢蓝
    'steel_dk':  '#2A445C',   # 战略目标条深段
    'navy_dk':   '#2B4660',   # 人才目标条
    'olive':     '#848C6E',   # 流程/治理条
    'brown':     '#998879',   # 数据条
    'purple':    '#8A879F',   # 技术条
    'tal_navy':  '#49627E',   # 人才现状条
    'track':     '#E4E7EB',   # 左表条轨道
    'track_b':   '#DFE4E9',   # 目标条轨道(略蓝)
    'stripe':    '#FAFBFC',   # 行条纹
    'sep_line':  '#EAECF1',   # 行分隔线
    'panel_gray':'#EEF0F3',   # 右面板标题带/合计行
    'rborder':   '#E8EBEF',   # 右面板描边
    'sum_bg':    '#EDF0F3',   # 合计行
    'bot_bg':    '#F2F4F7',   # 底部面板
    'card1':     '#F0EAE6',   # 卡1 暖棕调
    'card2':     '#EBEDE8',   # 卡2 橄榄调
    'card3':     '#F1EFF4',   # 卡3 紫调
    'olive_dk':  '#60694B',   # 徽章/值 深橄榄
    'brown_dk':  '#7C6A58',
    'purple_dk': '#7D7893',
    'navy_badge':'#2A3F57',
    'olive_md':  '#7C8465',
    'brown_md':  '#968677',
    'purple_md': '#86839C',
    'tan_md':    '#968677',
    'gap_olive': '#5E6749',
    'gap_brown': '#817161',
    'gap_purple':'#6F6A8B',
    'gap_navy':  '#314E6D',
    'gap_olive2':'#66704F',
    'gap_tan':   '#786655',
    'sum_olive': '#677052',   # 3.95
    'sum_brown': '#7E6B58',   # (备用)
    'sum_tan':   '#978778',
    'val_navy':  '#12264A',
    'gray_note': '#8A919C',
    'wm_gray':   '#A9A7AA',
    'white':     '#FFFFFF',
}

FONT = 'Noto Sans SC'

# ---------- 大标题 ----------
TITLE = dict(text='准备度评分与能力缺口诊断', x=37, y=90, size=78, weight=800, color=C['navy'], anchor='start')

# ---------- 左表 ----------
TBL = dict(x=17, y=127, w=998, h=663, r=14)         # 容器 [17,127]-[1015,790]
HDR = dict(y=127, h=81, bg=C['navy'])                # 表头带 [127,208]
# 表头分隔线（白 2px）
HDR_SEPS = [233, 389, 842]
HDR_TEXT = [
    dict(t='维度', cx=125, cy=181, size=28, weight=700, color=C['white']),
    dict(t='权重', cx=310, cy=181, size=28, weight=700, color=C['white']),
    dict(t='现状评分', cx=545, cy=163, size=28, weight=700, color=C['white']),
    dict(t='（满分5）', cx=546, cy=193, size=20, weight=400, color=C['white']),
    dict(t='目标评分', cx=865, cy=163, size=28, weight=700, color=C['white']),
    dict(t='（满分5）', cx=864, cy=193, size=20, weight=400, color=C['white']),
]
# 6 行：cy 中心 / 名称 / 权重 / 现状分 / 目标分 / 现状条宽 / 目标条宽 / 行配色
ROWS = [
    dict(name='战略', w='20%', cur='3.5', tgt='4.0', fw=189, tw=205, icon=C['navy'],
         cur_c=C['steel'],    tgt_c=C['steel'],    two_tone=False),
    dict(name='流程', w='20%', cur='3.0', tgt='4.0', fw=162, tw=205, icon='#6E7852',
         cur_c=C['olive'],    tgt_c=C['olive'],    two_tone=False),
    dict(name='数据', w='20%', cur='2.5', tgt='4.0', fw=133, tw=205, icon='#7A6853',
         cur_c=C['brown'],    tgt_c=C['brown'],    two_tone=False),
    dict(name='技术', w='15%', cur='3.0', tgt='4.0', fw=161, tw=205, icon='#7D7A96',
         cur_c=C['purple'],   tgt_c=C['purple'],   two_tone=False),
    dict(name='人才', w='10%', cur='2.0', tgt='3.5', fw=102, tw=174, icon='#2A3F57',
         cur_c=C['tal_navy'], tgt_c=C['navy_dk'],  two_tone=False),
    dict(name='治理', w='15%', cur='2.0', tgt='4.0', fw=101, tw=205, icon='#5E6849',
         cur_c=C['olive'],    tgt_c=C['olive'],    two_tone=False),
]
ROW_TOPS = [213, 289, 365, 441, 517, 593]            # 行带顶（行高 76，末行至 669）
ROW_CY   = [251, 323, 398, 476, 553, 631]
BAR_Y    = lambda cy: (cy + 3, cy + 20)              # 条 y=[cy+3, cy+20] h=17
CUR_X0, CUR_TRK = 423, 672                            # 现状条轨道 [423,672]
TGT_X0, TGT_TRK = 743, 990                            # 目标条轨道 [743,990]
STRATEGY_TGT_SPLIT = 795                              # 战略目标条深段 [743,795]

# 合计行 [669,790]
SUM = dict(y=669, h=121, bg=C['sum_bg'],
           items=[
               dict(t='合计', kind='label', cx=128, cy=730, size=28, weight=700, color=C['navy']),
               dict(t='100%', kind='label', cx=311, cy=728, size=24, weight=600, color=C['navy']),
               dict(t='加权现状评分', kind='label', cx=489, cy=700, size=22, weight=400, color=C['navy']),
               dict(t='2.75', kind='value', cx=487, cy=748, size=40, weight=800, color=C['val_navy']),
               dict(t='加权目标评分', kind='label', cx=702, cy=700, size=22, weight=400, color=C['navy']),
               dict(t='3.95', kind='value', cx=702, cy=748, size=40, weight=800, color=C['sum_olive']),
               dict(t='差距', kind='label', cx=912, cy=700, size=21, weight=400, color=C['navy']),
               dict(t='1.20', kind='value', cx=913, cy=748, size=40, weight=800, color=C['sum_tan']),
           ])

# ---------- 右面板 ----------
RPANEL = dict(x=1032, y=127, w=680, h=640, r=14, band_h=83, bg_band=C['panel_gray'],
              title='能力缺口差距排序', title_x=1058, title_cy=181, title_size=33,
              note1='差距分值', note1_x=1687, note1_cy=176, note1_size=23,
              note2='（目标-现状）', note2_x=1687, note2_cy=196, note2_size=19)
GAPS = [   # cy, 名称, 徽章/条/值 色, 条宽, 值
    dict(cy=260, name='治理', badge=C['olive_dk'],  bar=C['olive_md'],  val='2.0', vw=319, vc=C['gap_olive']),
    dict(cy=338, name='数据', badge=C['brown_dk'],  bar=C['brown_md'],  val='1.5', vw=239, vc=C['gap_brown']),
    dict(cy=419, name='人才', badge=C['purple_dk'], bar=C['purple_md'], val='1.5', vw=240, vc=C['gap_purple']),
    dict(cy=500, name='流程', badge=C['navy_badge'],bar=C['steel'],     val='1.0', vw=169, vc=C['gap_navy']),
    dict(cy=582, name='技术', badge='#626B4D',      bar=C['olive_md'],  val='1.0', vw=169, vc=C['gap_olive2']),
    dict(cy=663, name='战略', badge=C['brown_dk'],  bar=C['tan_md'],    val='0.5', vw=85,  vc=C['gap_tan']),
]
GAP_BAR_X0, GAP_BAR_END = 1207, 1605
GAP_BAR_H = 46
BADGE = dict(x=1051, w=52, h=52, r=10)

# ---------- 底部 ----------
BOT = dict(x=17, y=777, w=1694, h=160, r=14, bg=C['bot_bg'],
           title='重点行动与优先事项', title_x=41, title_cy=820, title_size=30,
           note='分值与权重用于项目决策；非行业基准。', note_x1=1424, note_x2=1676, note_cy=817, note_size=15)
CARDS = [
    dict(x=143, y=847, w=425, h=90, r=14, bg=C['card1'],
         icon_cx=93, icon_cy=889, icon_bg='#705E4D', icon='db',
         badge='1', badge_bg='#6E5B4A', label='数据',
         text='先完成数据授权和质量核验', text_x=294),
    dict(x=714, y=847, w=418, h=90, r=14, bg=C['card2'],
         icon_cx=653, icon_cy=884, icon_bg='#6C785A', icon='shield',
         badge='2', badge_bg='#66714F', label='治理',
         text='先明确上线责任', text_x=883),
    dict(x=1276, y=847, w=409, h=90, r=14, bg=C['card3'],
         icon_cx=1207, icon_cy=885, icon_bg='#4A5568', icon='people',
         badge='3', badge_bg='#7D7893', label='人才',
         text='先培训业务主责', text_x=1439),
]
BADGE_S = dict(w=48, h=48, r=10, size=26)            # 卡内小徽章
WATERMARK = dict(text='公众号·解决方案研究所', x2=1689, cy=905, size=50, color=C['wm_gray'], opacity=0.75,
                 wx=1079, wy=899, wr=31)
