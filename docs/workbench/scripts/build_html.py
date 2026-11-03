# -*- coding: utf-8 -*-
"""
高保真重建《AI、ML、DL、GenAI、LLMs、RAG 与 Agentic AI 的区别》信息图
输出：HTML + SVG（1200x1600 基准坐标系，全部真实文本，独立 SVG 最小单元）
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svg_lib import (
    icon_brain, icon_chart, icon_network, icon_sparkle, icon_bubble,
    icon_database, icon_robot, icon_bulb, icon_check, icon_media,
    icon_db_plus, icon_sliders, icon_chat_dots, icon_shield_check,
    icon_headset, icon_excl_solid, icon_excl_ring, icon_spark_deco,
    SMALL_ICONS,
)

W, H = 1200, 1600
FONT = "'Noto Sans SC','PingFang SC','Microsoft YaHei','Hiragino Sans GB',sans-serif"

# ============================ 数据 ============================

CARDS = [
    dict(key='AI', name='人工智能',
         bg='#FDEEF1', border='#F3C3D4', title='#8E1963', icon_c='#C2185B',
         pill_bg='#FBDCE6', dot='#E05C8A',
         desc='使机器具备思考、\n推理和学习的能力，\n让机器能像人一样\n处理问题。',
         icon='brain',
         examples=[('gear', '专家系统'), ('arm', '机器人'), ('car', '自动驾驶')]),
    dict(key='ML', name='机器学习',
         bg='#EDFCF4', border='#AEE3CC', title='#00602F', icon_c='#0FA36B',
         pill_bg='#D9F4E6', dot='#17A96B',
         desc='从数据中学习\n规律和模式，\n让系统具备预测\n和决策能力。',
         icon='chart',
         examples=[('mail', '垃圾邮件检测'), ('doc', '推荐系统'), ('shield', '欺诈检测')]),
    dict(key='DL', name='深度学习',
         bg='#F2EDFE', border='#D5C6F6', title='#5B10A0', icon_c='#7B2FBE',
         pill_bg='#E7DDF9', dot='#7B2FBE',
         desc='基于多层神经网络\n学习复杂特征，\n处理更大规模的\n数据和任务。',
         icon='network',
         examples=[('image', '图像识别'), ('mic', '语音识别'), ('car', '自动驾驶')]),
    dict(key='GenAI', name='生成式 AI',
         bg='#FDF9E4', border='#E9D892', title='#0E2749', icon_c='#1A2C55',
         pill_bg='#F7EDC4', dot='#9AA1B5',
         desc='基于大规模数据\n生成新的内容，\n如文本、图像、\n音频、代码等。',
         icon='sparkle',
         examples=[('bubble', 'ChatGPT'), ('image', 'Midjourney'), ('image', 'DALL·E'),
                   ('image', 'Claude'), ('music', 'Suno'), ('video', 'Runway')]),
    dict(key='LLMs', name='大语言模型',
         bg='#FFF1F5', border='#F3C6D6', title='#941A70', icon_c='#D6246E',
         pill_bg='#FBDDEA', dot='#D6246E',
         desc='以大规模数据为\n基础，具备理解\n和生成自然语言\n的能力。',
         icon='bubble',
         examples=[('doc', 'GPT-4/5'), ('doc', 'Claude 3'), ('doc', 'Gemini 1.5'),
                   ('doc', 'Llama 3'), ('doc', 'Mistral'), ('doc', 'Qwen')]),
    dict(key='RAG', name='检索增强生成',
         bg='#FDF6EA', border='#EDD6A4', title='#B06A00', icon_c='#E08E00',
         pill_bg='#F8E9CB', dot='#E08E00',
         desc='结合外部知识库，\n在生成时进行检索，\n提升回答的准确性\n和时效性。',
         icon='database',
         examples=[('bubble', '企业知识库'), ('person', '公司客服'), ('db', '文档问答')]),
    dict(key='Agentic AI', name='自主智能体',
         bg='#E6FAF6', border='#A5E0D6', title='#00615C', icon_c='#00907F',
         pill_bg='#D2F0EA', dot='#00907F',
         desc='具备自主规划、\n调用工具和执行\n任务的能力，\n能主动完成目标。',
         icon='robot',
         examples=[('gear', 'OpenAI Agents', None), ('monitor', 'Claude', 'Computer Use'),
                   ('fork', 'AutoGPT', None), ('fork', 'LangGraph', 'Agents'), ('doc', 'Manus AI', None)]),
]

# 演进路径
FLOW = [
    ('AI',        '#8E1963', '#FDEFF3', '#F9BCCD', '具备思考和\n智能的能力。'),
    ('ML',        '#00602F', '#F0FBF6', '#BCE9D4', '从数据中学习\n规律。'),
    ('DL',        '#5B10A0', '#F5F0FC', '#D6C2F2', '学习复杂的\n模式和特征。'),
    ('GenAI',     '#6B5900', '#FEFDF2', '#F7E9AC', '生成新的\n内容。'),
    ('LLMs',      '#941A70', '#FEF0F4', '#F9BDD1', '理解并生成\n自然语言。'),
    ('RAG',       '#B06A00', '#FEF8EC', '#F5D8A2', '结合知识库\n增强生成。'),
    ('Agentic AI', '#00615C', '#EFFCFA', '#93E2DA', '能够自主完成\n目标任务。'),
]

# 真实世界的典型应用
APPS = [
    ('AI',         '#5B21B6', '#EFE9FB', '#CDBCF0', '机器人、专家系统、自动驾驶 AI'),
    ('ML',         '#0A7A44', '#E4F7EC', '#A5DFC2', '垃圾邮件检测、推荐系统、欺诈检测'),
    ('DL',         '#5B21B6', '#EFE9FB', '#CDBCF0', '图像识别、语音识别、自动驾驶'),
    ('GenAI',      '#8A6D00', '#FCF5D8', '#EBD896', 'ChatGPT、Midjourney、DALL·E、Claude、Stable Diffusion、Suno'),
    ('LLMs',       '#C2185B', '#FCE4ED', '#F2BBD0', 'GPT-4/5、Claude 3、Gemini 1.5、Llama 3、Mistral、Qwen'),
    ('RAG',        '#B06A00', '#FCEFDA', '#EFD3A0', '企业知识库、公司知识助手、文档问答'),
    ('Agentic AI', '#00726D', '#DCF4F1', '#9FDFD7', '自主智能体、工具使用、工作流自动化'),
]

WHY = [
    '理解它们的层级关系和相互联系。',
    '选择适合你问题的正确方法。',
    '构建更智能的 AI 产品，提升实际价值。',
    '使用 RAG 和 AI Agent 能带来更高的准确性\n和自主性。',
    '保持对技术发展的关注，持续探索和演进。',
]

CONCEPTS = [
    ('多模态 AI', '#0E2749', '#F3EEFC', 'media',   '处理文本、图像、音频、\n视频等多种信息。'),
    ('RAG',       '#0E2749', '#E9F8F0', 'dbplus',  '从外部知识库获取信息，\n提升生成效果。'),
    ('微调训练',   '#6D28D9', '#F3EEFC', 'sliders', '针对特定任务优化\n模型表现。'),
    ('提示工程',   '#2563EB', '#ECEBFB', 'chat',    '设计更好的提示，\n引导模型输出。'),
    ('AI 安全',   '#0E2749', '#E9F8F0', 'shield',  '建立信任与安全机制，\n确保 AI 可控、可靠。'),
    ('AI 智能体', '#0E2749', '#F0EEFB', 'bot2',    '能够感知、思考、行动，\n达成目标。'),
]

SCENES = [
    ('headset', '#4A5568', '客服支持', '(LLM + RAG)', '问答、知识库、个性化服务'),
    ('doc2',    '#0FA36B', '文档处理 (LLM)', None, '摘要、提取、生成、写作'),
    ('image2',  '#2563EB', '图像生成 (GenAI)', None, '图像、设计、内容创作'),
    ('chart2',  '#2563EB', '数据分析 (AI)', None, '分析规律、构建数据集、\n执行任务。'),
    ('shield2', '#0FA36B', '流程自动化 (ML)', None, '检测异常、降低风险、\n提升效率。'),
]

WARNS = [
    dict(icon='solid', ic='#E53946',
         title='重要提醒\nRAG 并非总是 100% 准确。', tc='#D32F3E',
         desc='生成内容可能包含错误，需由可信来源\n进行验证。', dc='#7A5A62'),
    dict(icon='ring', ic='#E53946',
         title='AI 生成内容更需谨慎。', tc='#D32F3E',
         desc='AI 可能会产生不准确的信息，\n务必核实关键信息的来源。', dc='#7A5A62'),
    dict(icon='shield', ic='#3B82F6',
         title='自主智能体需要更多安全保障。', tc='#1D4ED8',
         desc='它的能力更强，也带来更大的风险，\n需要在部署时进行监控、评估和安全机制建设。', dc='#5A6B85'),
]

INK = '#0E274B'      # 深藏蓝
SUB = '#5A6B85'      # 副标题灰蓝
BODY = '#3A4A66'     # 正文
ARROW_C = '#6B7A99'  # 箭头灰蓝


# ============================ 工具函数 ============================

def esc(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def text_el(x, y, s, size, fill, weight=400, anchor='start', spacing=None, opacity=None):
    extra = f' letter-spacing="{spacing}"' if spacing else ''
    op = f' opacity="{opacity}"' if opacity else ''
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
            f'font-weight="{weight}" text-anchor="{anchor}"{extra}{op}>{esc(s)}</text>')


def mtext(cx, y, lines, size, fill, weight=400, lh=None, anchor='middle', spacing=None):
    """多行文本（lines: list[str] 或含 \n 的 str）"""
    if isinstance(lines, str):
        lines = lines.split('\n')
    lh = lh or size * 1.42
    out = []
    for i, ln in enumerate(lines):
        out.append(text_el(cx, y + i * lh, ln, size, fill, weight, anchor, spacing))
    return ''.join(out)


def rrect(x, y, w, h, r, fill, stroke=None, sw=0, opacity=None, extra=''):
    st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ''
    op = f' opacity="{opacity}"' if opacity else ''
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{r}" fill="{fill}"{st}{op}{extra}/>'


# ============================ 七列卡片 ============================

CARD_Y, CARD_H, CARD_W, CARD_X0, CARD_GAP = 271, 497, 152.5, 13.3, 170.2
BIG_ICONS = dict(brain=icon_brain, chart=icon_chart, network=icon_network,
                 sparkle=icon_sparkle, bubble=icon_bubble,
                 database=icon_database, robot=icon_robot)


def card_svg(i, c):
    x = CARD_X0 + i * CARD_GAP
    cx = x + CARD_W / 2
    g = [f'<g id="card-{c["key"].lower().replace(" ", "-")}">']
    # 卡片底
    g.append(rrect(x, CARD_Y, CARD_W, CARD_H, 16, c['bg'], c['border'], 2))
    # 大图标
    ic = BIG_ICONS[c['icon']](f'card-{i + 1}-icon', cx, CARD_Y + 43, 55, c['icon_c'])
    g.append(ic)
    # 标题 / 副标题
    ty = CARD_Y + 100
    size_t = 26 if len(c['key']) <= 4 else 20
    g.append(text_el(cx, ty, c['key'], size_t, c['title'], 900, 'middle'))
    g.append(text_el(cx, ty + 27, c['name'], 16, c['title'], 700, 'middle'))
    # 描述（手工断行，与原图一致）
    g.append(f'<g id="card-{i + 1}-desc">')
    g.append(mtext(cx, CARD_Y + 161, c['desc'].split('\n'), 14, BODY, 400, 24.3))
    g.append('</g>')
    # 典型示例胶囊
    py = CARD_Y + 268
    pw, ph = 108, 30
    g.append(f'<g id="card-{i + 1}-pill">')
    g.append(rrect(cx - pw / 2, py, pw, ph, ph / 2, c['pill_bg']))
    g.append(text_el(cx, py + ph / 2 + 5.5, '典型示例', 14.5, c['title'], 700, 'middle'))
    g.append('</g>')
    # 示例列表
    n = len(c['examples'])
    step = 47 if n <= 3 else (38 if n == 5 else 32.5)
    ly = CARD_Y + 328
    g.append(f'<g id="card-{i + 1}-examples">')
    for k, ex in enumerate(c['examples']):
        ic_name, label = ex[0], ex[1]
        line2 = ex[2] if len(ex) > 2 else None
        yy = ly + k * step
        g.append(SMALL_ICONS[ic_name](f'card-{i + 1}-ex-{k + 1}-icon', x + 22, yy, 16, c['icon_c']))
        fs_ex = 11 if len(label) > 13 else 13.5
        if line2:
            g.append(text_el(x + 35, yy + 1, label, fs_ex, BODY, 500))
            g.append(text_el(x + 35, yy + 14.5, line2, fs_ex, BODY, 500))
        else:
            g.append(text_el(x + 35, yy + 5, label, fs_ex, BODY, 500))
    g.append('</g>')
    g.append('</g>')
    return '\n'.join(g)


def wrap(t, max_chars):
    """中文按字数断行（简单贪心），保留英文单词完整"""
    lines, cur, cur_w = [], '', 0
    for ch in t:
        w = 1 if ord(ch) > 0x2E7F else 0.55
        if cur_w + w > max_chars and cur:
            lines.append(cur); cur, cur_w = ch, w
        else:
            cur += ch; cur_w += w
    if cur:
        lines.append(cur)
    return lines


# ============================ 顶部区域 ============================

def header_svg():
    g = ['<g id="header">']
    # 主标题三段：段1 + 高亮(Agentic AI) + 段3，字号 40
    size = 38
    s1 = 'AI、ML、DL、GenAI、LLMs、RAG 与 '
    s2 = 'Agentic AI'
    s3 = ' 的区别'
    # 估算宽度（Noto Sans SC Bold: CJK=1em, ASCII≈0.58em, 、=1em, space=0.26em）
    def tw(s):
        w = 0
        for ch in s:
            if ord(ch) > 0x2E7F:
                w += 1.0
            elif ch == ' ':
                w += 0.26
            elif ch in '·':
                w += 0.34
            else:
                w += 0.58
        return w * size
    w1, w2, w3 = tw(s1), tw(s2), tw(s3)
    total = w1 + w2 + w3
    x1 = (W - total) / 2
    x2 = x1 + w1
    x3 = x2 + w2
    # 高亮背景
    g.append(rrect(x2 - 8, 22, w2 + 16, 46, 10, '#E0D8F7', extra=' id="title-highlight"'))
    g.append(text_el(x1, 58, s1, size, INK, 900, spacing='-1.5'))
    g.append(text_el(x2, 58, s2, size, INK, 900, spacing='-1.5'))
    g.append(text_el(x3, 58, s3, size, INK, 900, spacing='-1.5'))
    # 右上闪光装饰
    g.append(icon_spark_deco('deco-spark-1', 1156, 26, 26, '#A78BFA'))
    g.append(icon_spark_deco('deco-spark-2', 1180, 50, 13, '#C4B5FD'))
    # 副标题
    g.append(text_el(W / 2, 102, '它们不是同一个概念，但彼此紧密关联 —— 共同构成了技术生态的多层次体系。',
                     19, SUB, 400, 'middle'))
    g.append('</g>')
    return '\n'.join(g)


def core_card_svg():
    x, y, w, h = 15, 119, 360, 152
    g = ['<g id="core-card">']
    g.append(rrect(x, y, w, h, 18, '#FEF3C8'))
    g.append(icon_bulb('core-bulb', x + 42, y + 42, 52, '#B45309', '#FBE9A8'))
    g.append(text_el(x + 82, y + 34, '核心观点', 21, INK, 900))
    g.append(f'<g id="core-body">')
    g.append(mtext(x + 82, y + 67,
                   ['它们不是互相替代，', '而是层层递进的关系，', '共同构成了智能时代', '的技术生态。'],
                   15.5, '#4A4458', 500, 22.5))
    g.append('</g></g>')
    return '\n'.join(g)


# AI 伞形弧
ARC_LX, ARC_RX, ARC_TOP_Y, ARC_FOOT_Y = 460, 1140, 122, 265


def arc_svg():
    cxm = (ARC_LX + ARC_RX) / 2
    g = ['<g id="ai-arc">']
    g.append(f'''<defs><linearGradient id="arcGrad" x1="0" y1="0" x2="0" y2="1">
<stop offset="0" stop-color="#DCD5F6"/><stop offset="1" stop-color="#F5F3FC"/>
</linearGradient></defs>''')
    # 上边缘（脚→顶→脚）+ 下边缘（顶弧回来）
    d = (f'M {ARC_LX},{ARC_FOOT_Y} C {ARC_LX + 70},{ARC_FOOT_Y - 118} {cxm - 200},{ARC_TOP_Y} {cxm},{ARC_TOP_Y} '
         f'C {cxm + 200},{ARC_TOP_Y} {ARC_RX - 70},{ARC_FOOT_Y - 118} {ARC_RX},{ARC_FOOT_Y} '
         f'C {cxm + 80},234 {cxm + 60},254 {cxm},254 '
         f'C {cxm - 60},254 {cxm - 80},234 {ARC_LX},{ARC_FOOT_Y} Z')
    g.append(f'<path d="{d}" fill="url(#arcGrad)" stroke="#B7AEE8" stroke-width="1.6"/>')
    # 内部文字
    g.append(f'<g id="ai-arc-text">')
    g.append(text_el(cxm, 190, 'AI', 46, '#1E2A5E', 900, 'middle'))
    g.append(text_el(cxm, 221, '人工智能', 20, '#1E2A5E', 700, 'middle'))
    g.append(text_el(cxm, 241, '更广泛的概念，包含多种技术方向', 15, '#3A4A6B', 500, 'middle'))
    g.append('</g></g>')
    return '\n'.join(g)


def connectors_svg():
    """弧底到 7 张卡片的连接线 + 圆点"""
    g = ['<g id="connectors" fill="none" stroke-width="2.4">']
    cy_dot = CARD_Y - 4.5  # 圆点圆心 ≈ 266.5
    hy = 261               # 水平延伸线高度
    for i, c in enumerate(CARDS):
        cx = CARD_X0 + i * CARD_GAP + CARD_W / 2
        col = c['dot']
        g.append(f'<g id="connector-{i + 1}" stroke="{col}">')
        if i <= 2:   # 左侧三张：水平延伸到弧脚
            g.append(f'<path d="M {cx:.1f},{hy:.1f} H 486"/>')
        elif i == 3:
            g.append(f'<line x1="{cx:.1f}" y1="252" x2="{cx:.1f}" y2="{hy:.1f}"/>')
        elif i == 4:
            g.append(f'<line x1="{cx:.1f}" y1="248" x2="{cx:.1f}" y2="{hy:.1f}"/>')
        elif i == 5:
            g.append(f'<line x1="{cx:.1f}" y1="250" x2="{cx:.1f}" y2="{hy:.1f}"/>')
        else:
                    g.append(f'<line x1="{cx:.1f}" y1="{hy:.1f}" x2="{cx:.1f}" y2="{cy_dot - 4.6:.1f}"/>')
        g.append(f'<circle cx="{cx:.1f}" cy="{cy_dot:.1f}" r="4.6" fill="{col}" stroke="none"/>')
        g.append('</g>')
    g.append('</g>')
    return '\n'.join(g)


# ============================ 演进路径 ============================

FLOW_Y, FLOW_H = 798, 158
FLOW_PANEL_X, FLOW_PANEL_W = 20, 1160


def flow_svg():
    g = ['<g id="flow-panel">']
    g.append(rrect(FLOW_PANEL_X, FLOW_Y, FLOW_PANEL_W, FLOW_H, 14, '#F7F8FB', '#E3E7F0', 1.5))
    g.append(text_el(W / 2, FLOW_Y + 32, '演进路径（简单流程）', 21, INK, 900, 'middle'))
    g.append('<g id="flow-items">')
    n = len(FLOW)
    pw, ah = 118, 39
    aw = 27
    total = n * pw + (n - 1) * aw
    x = (W - total) / 2
    py = FLOW_Y + 55
    for k, (name, tc, g1, g2, note) in enumerate(FLOW):
        cid = f'flow-{k + 1}-{name.lower().replace(" ", "-")}'
        g.append(f'<g id="{cid}">')
        gid = f'flowGrad{k + 1}'
        g.append(f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="0">'
                 f'<stop offset="0" stop-color="{g1}"/><stop offset="1" stop-color="{g2}"/></linearGradient></defs>')
        g.append(rrect(x, py, pw, ah, ah / 2, f'url(#{gid})'))
        fs = 19 if len(name) <= 5 else 15.5
        g.append(text_el(x + pw / 2, py + ah / 2 + 6.5, name, fs, tc, 900, 'middle'))
        # 说明
        g.append(f'<g id="{cid}-note">')
        g.append(mtext(x + pw / 2, py + ah + 26, note.split('\n'), 14, '#4A5A78', 500, 20))
        g.append('</g></g>')
        if k < n - 1:
            ax = x + pw + aw / 2
            g.append(f'<g id="flow-arrow-{k + 1}">')
            g.append(f'<line x1="{ax - 8:.1f}" y1="{py + ah / 2:.1f}" x2="{ax + 5:.1f}" y2="{py + ah / 2:.1f}" '
                     f'stroke="{ARROW_C}" stroke-width="2.2" stroke-linecap="round"/>')
            g.append(f'<path d="M {ax:.1f},{py + ah / 2 - 4.5:.1f} L {ax + 7:.1f},{py + ah / 2:.1f} '
                     f'L {ax:.1f},{py + ah / 2 + 4.5:.1f}" fill="none" stroke="{ARROW_C}" '
                     f'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>')
            g.append('</g>')
        x += pw + aw
    g.append('</g></g>')
    return '\n'.join(g)


# ============================ 双面板 ============================

PANEL_Y, PANEL_H = 953, 246
LEFT_X, LEFT_W = 20, 687
RIGHT_X, RIGHT_W = 724, 456


def apps_svg():
    g = ['<g id="apps-panel">']
    g.append(rrect(LEFT_X, PANEL_Y, LEFT_W, PANEL_H, 14, '#FEFEFF', '#DBE7F7', 1.5))
    g.append(text_el(LEFT_X + 27, PANEL_Y + 34, '真实世界的典型应用', 21, INK, 900))
    g.append('<g id="apps-rows">')
    ry = PANEL_Y + 56
    rh = 25.5
    for k, (name, tc, bg, bc, desc) in enumerate(APPS):
        y = ry + k * rh
        g.append(f'<g id="app-row-{k + 1}">')
        g.append(rrect(LEFT_X + 27, y, 122, 21.5, 6, bg, bc, 1.4))
        fs = 13.5 if len(name) <= 5 else 11
        g.append(text_el(LEFT_X + 88, y + 15, name, fs, tc, 800, 'middle'))
        # 箭头
        ax = LEFT_X + 162
        g.append(f'<line x1="{ax:.1f}" y1="{y + 10.8:.1f}" x2="{ax + 11:.1f}" y2="{y + 10.8:.1f}" '
                 f'stroke="{tc}" stroke-width="2" stroke-linecap="round"/>')
        g.append(f'<path d="M {ax + 8:.1f},{y + 6.8:.1f} L {ax + 14:.1f},{y + 10.8:.1f} L {ax + 8:.1f},{y + 14.8:.1f}" '
                 f'fill="none" stroke="{tc}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>')
        g.append(text_el(LEFT_X + 190, y + 15.5, desc, 15, BODY, 500))
        g.append('</g>')
    g.append('</g></g>')
    return '\n'.join(g)


def why_svg():
    g = ['<g id="why-panel">']
    g.append(rrect(RIGHT_X, PANEL_Y, RIGHT_W, PANEL_H, 14, '#FEFEFF', '#DBE7F7', 1.5))
    g.append(text_el(RIGHT_X + 27, PANEL_Y + 34, '为什么这很重要', 21, INK, 900))
    g.append('<g id="why-items">')
    ys = [PANEL_Y + 58, PANEL_Y + 97, PANEL_Y + 136, PANEL_Y + 175, PANEL_Y + 226]
    for k, item in enumerate(WHY):
        y = ys[k]
        g.append(f'<g id="why-item-{k + 1}">')
        g.append(icon_check(f'why-check-{k + 1}', RIGHT_X + 44, y + 2, 12.5, '#3D9E63'))
        g.append(mtext(RIGHT_X + 68, y + 7, item.split('\n'), 15.5, BODY, 500, 24, 'start'))
        g.append('</g>')
    g.append('</g></g>')
    return '\n'.join(g)


# ============================ 关键现代概念 ============================

CON_TITLE_Y = 1222
CON_Y, CON_H, CON_W = 1240, 110, 183
CON_GAP = 8.4


def concepts_svg():
    g = ['<g id="concepts">']
    g.append(text_el(W / 2, CON_TITLE_Y, '关键现代概念', 21, INK, 900, 'middle'))
    x = 20
    for k, (name, tc, bg, ic, note) in enumerate(CONCEPTS):
        g.append(f'<g id="concept-{k + 1}">')
        g.append(rrect(x, CON_Y, CON_W, CON_H, 12, bg))
        g.append(text_el(x + CON_W / 2, CON_Y + 28, name, 17.5, tc, 900, 'middle'))
        ccx = x + CON_W / 2
        ccy = CON_Y + 54
        if ic == 'media':
            g.append(icon_media(f'concept-{k + 1}-icon', ccx + 6, ccy, 44, '#7C5CE0', '#7C5CE0', '#8B5CF6'))
        elif ic == 'dbplus':
            g.append(icon_db_plus(f'concept-{k + 1}-icon', ccx, ccy, 44, '#0FA36B', '#0A7A44'))
        elif ic == 'sliders':
            g.append(icon_sliders(f'concept-{k + 1}-icon', ccx, ccy, 40, '#8B5CF6'))
        elif ic == 'chat':
            g.append(icon_chat_dots(f'concept-{k + 1}-icon', ccx, ccy, 40, '#4F6EF0'))
        elif ic == 'shield':
            g.append(icon_shield_check(f'concept-{k + 1}-icon', ccx, ccy, 40, '#0FA36B'))
        else:
            g.append(BIG_ICONS['robot'](f'concept-{k + 1}-icon', ccx, ccy, 40, '#6366F1'))
        g.append(mtext(x + CON_W / 2, CON_Y + 88, note.split('\n'), 13.5, '#4A5568', 400, 19))
        g.append('</g>')
        x += CON_W + CON_GAP
    g.append('</g>')
    return '\n'.join(g)


# ============================ 常见使用场景 ============================

SC_Y, SC_H = 1358, 126


def scenes_svg():
    g = ['<g id="scenes-panel">']
    g.append(rrect(20, SC_Y, 1160, SC_H, 14, '#FEFEFF', '#DBE7F7', 1.5))
    g.append(text_el(47, SC_Y + 30, '常见使用场景', 20, INK, 900))
    g.append('<g id="scene-items">')
    col_w = 1160 / 5
    icons = dict(headset=icon_headset, doc2=lambda *a: SMALL_ICONS['doc'](*a),
                 image2=lambda *a: SMALL_ICONS['image'](*a),
                 shield2=lambda *a: SMALL_ICONS['shield'](*a, check=True))
    iy = SC_Y + 42   # 图标块顶
    for k, (ic, color, t1, t2, note) in enumerate(SCENES):
        x0 = 20 + k * col_w
        g.append(f'<g id="scene-{k + 1}">')
        # 图标（圆角浅底）
        g.append(rrect(x0 + 22, iy, 32, 32, 9, '#F1F4F9'))
        if ic == 'chart2':
            ic_svg = icon_chart(f'scene-{k + 1}-icon', x0 + 38, iy + 16, 22, color)
        else:
            ic_svg = icons[ic](f'scene-{k + 1}-icon', x0 + 38, iy + 16, 22, color)
        g.append(ic_svg)
        # 标题（1~2 行）
        if t2:
            g.append(text_el(x0 + 64, iy + 13, t1, 15, INK, 800))
            g.append(text_el(x0 + 64, iy + 30, t2, 15, INK, 800))
        else:
            g.append(text_el(x0 + 64, iy + 21, t1, 15, INK, 800))
        # 说明
        g.append(f'<g id="scene-{k + 1}-note">')
        g.append(mtext(x0 + 22, iy + 48, note.split('\n'), 13, '#5A6B85', 400, 17.5, 'start'))
        g.append('</g></g>')
    g.append('</g></g>')
    return '\n'.join(g)


# ============================ 重要提醒 ============================

WARN_Y, WARN_H = 1496, 92


def warns_svg():
    g = ['<g id="warn-panel">']
    g.append(rrect(20, WARN_Y, 1160, WARN_H, 14, '#FDF3F5', '#F5D8DE', 1.5))
    cols = [(52, 320), (400, 350), (790, 380)]
    for k, (wd, (x0, cw)) in enumerate(zip(WARNS, cols)):
        g.append(f'<g id="warn-{k + 1}">')
        cyy = WARN_Y + 30
        if wd['icon'] == 'solid':
            g.append(icon_excl_solid(f'warn-{k + 1}-icon', x0 + 17, cyy, 17, wd['ic']))
        elif wd['icon'] == 'ring':
            g.append(icon_excl_ring(f'warn-{k + 1}-icon', x0 + 17, cyy, 16, wd['ic']))
        else:
            g.append(icon_shield_check(f'warn-{k + 1}-icon', x0 + 17, cyy, 34, wd['ic']))
        tl = wd['title'].split('\n')
        ty = WARN_Y + 22
        for j, ln in enumerate(tl):
            g.append(text_el(x0 + 46, ty + j * 19, ln, 15.5, wd['tc'], 900))
        dy = ty + len(tl) * 19 + 4
        g.append(f'<g id="warn-{k + 1}-desc">')
        g.append(mtext(x0 + 46, dy, wd['desc'].split('\n'), 13.5, wd['dc'], 400, 19, 'start'))
        g.append('</g></g>')
    g.append('</g>')
    return '\n'.join(g)


# ============================ 组装 ============================

def build():
    parts = []
    parts.append(header_svg())
    parts.append(arc_svg())
    parts.append(core_card_svg())
    parts.append(connectors_svg())
    for i, c in enumerate(CARDS):
        parts.append(card_svg(i, c))
    parts.append(flow_svg())
    parts.append(apps_svg())
    parts.append(why_svg())
    parts.append(concepts_svg())
    parts.append(scenes_svg())
    parts.append(warns_svg())
    body = '\n'.join(parts)

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI、ML、DL、GenAI、LLMs、RAG 与 Agentic AI 的区别</title>
<style>
  html,body {{ margin:0; padding:0; background:#E8EAF0; }}
  #stage {{ width:1200px; margin:0 auto; background:#FDFDFE; box-shadow:0 4px 30px rgba(30,40,90,.12); }}
  svg {{ display:block; }}
  text {{ font-family:{FONT}; }}
</style>
</head>
<body>
<div id="stage">
<!--
  高保真重建：AI / ML / DL / GenAI / LLMs / RAG / Agentic AI 技术体系对比信息图
  基准坐标系：1200 x 1600（等比对应原图 1086 x 1448）
  所有文字均为真实 <text> 文本；所有图形（箭头/胶囊/卡片/弧形/图标）均为独立 SVG 矢量单元，
  每个可编辑单元都有唯一 id（card-1、flow-2-ml、connector-3、why-item-4 ...），
  可单独选中、移动、修改、复用。
-->
<svg id="infographic" viewBox="0 0 {W} {H}" width="{W}" height="{H}" xmlns="http://www.w3.org/2000/svg">
<rect id="page-bg" x="0" y="0" width="{W}" height="{H}" fill="#FDFDFE"/>
{body}
</svg>
</div>
</body>
</html>'''
    out = '/home/z/my-project/download/AI技术体系对比图.html'
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        f.write(html)
    print('written:', out, len(html), 'bytes')


if __name__ == '__main__':
    build()
