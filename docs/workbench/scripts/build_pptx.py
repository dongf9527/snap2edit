# -*- coding: utf-8 -*-
"""
高保真重建《AI、ML、DL、GenAI、LLMs、RAG 与 Agentic AI 的区别》信息图
输出：PPTX（PowerPoint 原生文本框 + 形状，无嵌入图片，全部可单独编辑/拖动）
坐标系：1200x1600 px → 12x16 英寸（1px = 0.01in），字号 pt = px*0.72
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pptx import Presentation
from pptx.util import Inches
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn

from build_html import (CARDS, FLOW, APPS, WHY, CONCEPTS, SCENES, WARNS,
                        INK, SUB, BODY, ARROW_C,
                        CARD_Y, CARD_H, CARD_W, CARD_X0, CARD_GAP)
from pptx_lib import (E, PT, rgb, mix, FONT, text_width, add_text, add_text_baseline, add_mtext,
                      add_shape, add_grad, add_line, add_freeform, bez, qbez,
                      icon_brain, icon_chart, icon_network, icon_sparkle,
                      icon_bubble, icon_database, icon_robot, icon_gear,
                      icon_arm, icon_car, icon_mail, icon_doc, icon_shield,
                      icon_image, icon_mic, icon_music, icon_video, icon_person,
                      icon_monitor, icon_fork, icon_bot_sm, icon_bulb,
                      icon_check, icon_shield_check, icon_media, icon_db_plus,
                      icon_sliders, icon_chat_dots, icon_headset,
                      icon_excl_solid, icon_excl_ring, icon_spark_deco)

W, H = 1200, 1600
ARC_LX, ARC_RX, ARC_TOP_Y, ARC_FOOT_Y = 460, 1140, 122, 265

BIG_ICONS = dict(brain=icon_brain, chart=icon_chart, network=icon_network,
                 sparkle=icon_sparkle, bubble=icon_bubble,
                 database=icon_database, robot=icon_robot)
SMALL = dict(gear=icon_gear, arm=icon_arm, car=icon_car, mail=icon_mail,
             doc=icon_doc, shield=icon_shield, image=icon_image, mic=icon_mic,
             music=icon_music, video=icon_video, person=icon_person,
             monitor=icon_monitor, fork=icon_fork, bot=icon_bot_sm,
             bubble=icon_bubble, db=icon_database)


def new_prs():
    prs = Presentation()
    prs.slide_width = Inches(12)
    prs.slide_height = Inches(16)
    return prs


def build(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
    sh = slide.shapes

    # 页面背景
    add_shape(slide, MSO_SHAPE.RECTANGLE, 0, 0, W, H, '#FDFDFE')

    # ---------- 标题 ----------
    size = 38
    s1 = 'AI、ML、DL、GenAI、LLMs、RAG 与 '
    s2 = 'Agentic AI'
    s3 = ' 的区别'
    w1, w2, w3 = text_width(s1, size), text_width(s2, size), text_width(s3, size)
    x1 = (W - (w1 + w2 + w3)) / 2
    x2 = x1 + w1
    # 高亮背景（置于文字下层）
    add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x2 - 6, 22, w2 + 12, 46,
              '#E0D8F7', adj=0.22)
    # 整行标题一个文本框（三个 run，保证在任何渲染器下句子完整居中）
    tb = slide.shapes.add_textbox(E(40), E(58 - size * 1.10), E(W - 80), E(size * 1.6))
    tf = tb.text_frame
    tf.word_wrap = False
    tf.auto_size = None
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p0 = tf.paragraphs[0]
    p0.alignment = PP_ALIGN.CENTER
    for txt in (s1, s2, s3):
        r = p0.add_run()
        r.text = txt
        f = r.font
        f.size = PT(size); f.bold = True; f.color.rgb = rgb(INK); f.name = FONT
        rPr = r._r.get_or_add_rPr()
        for tag in ('a:ea', 'a:cs'):
            e = rPr.makeelement(qn(tag), {'typeface': FONT})
            rPr.append(e)
    icon_spark_deco(slide, 1156, 26, 26, '#A78BFA')
    icon_spark_deco(slide, 1180, 50, 13, '#C4B5FD')
    add_mtext(slide, W / 2, 102, '它们不是同一个概念，但彼此紧密关联 —— 共同构成了技术生态的多层次体系。',
              19, SUB, align='center')

    # ---------- AI 弧形 ----------
    cxm = (ARC_LX + ARC_RX) / 2
    pts = [(ARC_LX, ARC_FOOT_Y)]
    pts += bez((ARC_LX, ARC_FOOT_Y), (ARC_LX + 70, ARC_FOOT_Y - 118),
               (cxm - 200, ARC_TOP_Y), (cxm, ARC_TOP_Y))
    pts += bez((cxm, ARC_TOP_Y), (cxm + 200, ARC_TOP_Y),
               (ARC_RX - 70, ARC_FOOT_Y - 118), (ARC_RX, ARC_FOOT_Y))
    # 下边缘（中谷，反向采样）
    d1 = bez((ARC_LX, ARC_FOOT_Y), (cxm - 80, 234), (cxm - 60, 254), (cxm, 254))
    d2 = bez((cxm, 254), (cxm + 60, 254), (cxm + 80, 234), (ARC_RX, ARC_FOOT_Y))
    pts += list(reversed(d1 + d2))
    # 渐变近似：整体浅紫填充
    arc = add_freeform(slide, pts, '#E9E5F8', '#B7AEE8', 1.6)
    arc.fill.gradient()
    st = arc.fill.gradient_stops
    st[0].color.rgb = rgb('#DCD5F6'); st[0].position = 0.0
    st[1].color.rgb = rgb('#F5F3FC'); st[1].position = 1.0
    try:
        arc.fill.gradient_angle = 90
    except Exception:
        pass
    add_mtext(slide, cxm, 190, 'AI', 46, '#1E2A5E', True, 'center', weight=900)
    add_mtext(slide, cxm, 221, '人工智能', 20, '#1E2A5E', True, 'center')
    add_mtext(slide, cxm, 241, '更广泛的概念，包含多种技术方向', 15, '#3A4A6B', False, 'center')

    # ---------- 核心观点卡 ----------
    x, y = 15, 119
    add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, 360, 152, '#FEF3C8', adj=0.11)
    icon_bulb(slide, x + 42, y + 42, 52, '#B45309', '#FBE9A8')
    add_text_baseline(slide, x + 82, y + 34, '核心观点', 21, INK, True, weight=900)
    add_mtext(slide, x + 82, y + 67,
              ['它们不是互相替代，', '而是层层递进的关系，', '共同构成了智能时代', '的技术生态。'],
              15.5, '#4A4458', False, 'start', 22.5, weight=500)

    # ---------- 连接线 ----------
    cy_dot = CARD_Y - 4.5
    hy = 261
    for i, c in enumerate(CARDS):
        cx = CARD_X0 + i * CARD_GAP + CARD_W / 2
        col = c['dot']
        if i <= 2:
            add_line(slide, cx, hy, 486, hy, col, 2.4)
        elif i == 3:
            add_line(slide, cx, 252, cx, hy, col, 2.4)
        elif i == 4:
            add_line(slide, cx, 248, cx, hy, col, 2.4)
        elif i == 5:
            add_line(slide, cx, 250, cx, hy, col, 2.4)
        add_line(slide, cx, hy, cx, cy_dot - 4.6, col, 2.4)
        add_shape(slide, MSO_SHAPE.OVAL, cx - 4.6, cy_dot - 4.6, 9.2, 9.2, col)

    # ---------- 七列卡片 ----------
    for i, c in enumerate(CARDS):
        x = CARD_X0 + i * CARD_GAP
        cx = x + CARD_W / 2
        add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, CARD_Y, CARD_W, CARD_H,
                  c['bg'], c['border'], 2, adj=16 / CARD_H)
        if c['icon'] == 'brain':
            icon_brain(slide, cx, CARD_Y + 43, 55, c['icon_c'], c['bg'])
        else:
            BIG_ICONS[c['icon']](slide, cx, CARD_Y + 43, 55, c['icon_c'])
        ty = CARD_Y + 100
        size_t = 26 if len(c['key']) <= 4 else 20
        add_mtext(slide, cx, ty, c['key'], size_t, c['title'], True, 'center', weight=900)
        add_mtext(slide, cx, ty + 27, c['name'], 16, c['title'], True, 'center')
        add_mtext(slide, cx, CARD_Y + 161, c['desc'].split('\n'), 14, BODY,
                  False, 'center', 24.3)
        py = CARD_Y + 268
        add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, cx - 54, py, 108, 30,
                  c['pill_bg'], adj=0.5)
        add_mtext(slide, cx, py + 20.5, '典型示例', 14.5, c['title'], True, 'center')
        n = len(c['examples'])
        step = 47 if n <= 3 else (38 if n == 5 else 32.5)
        ly = CARD_Y + 328
        for k, ex in enumerate(c['examples']):
            ic_name, label = ex[0], ex[1]
            line2 = ex[2] if len(ex) > 2 else None
            yy = ly + k * step
            SMALL[ic_name](slide, x + 22, yy, 16, c['icon_c'])
            fs = 11 if len(label) > 13 else 13.5
            if line2:
                add_mtext(slide, x + 35, yy + 1, [label, line2], fs, BODY, False, 'start', 13.5, weight=500)
            else:
                add_mtext(slide, x + 35, yy + 5, label, fs, BODY, False, 'start', weight=500)

    # ---------- 演进路径 ----------
    FY, FH = 798, 158
    add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, 20, FY, 1160, FH,
              '#F7F8FB', '#E3E7F0', 1.5, adj=14 / FH)
    add_mtext(slide, W / 2, FY + 32, '演进路径（简单流程）', 21, INK, True, 'center', weight=900)
    n = len(FLOW)
    pw, ah, aw = 118, 39, 27
    total = n * pw + (n - 1) * aw
    fx = (W - total) / 2
    py = FY + 55
    for k, (name, tc, g1, g2, note) in enumerate(FLOW):
        add_grad(slide, MSO_SHAPE.ROUNDED_RECTANGLE, fx, py, pw, ah, g1, g2, 0, adj=0.5)
        fs = 19 if len(name) <= 5 else 15.5
        add_mtext(slide, fx + pw / 2, py + ah / 2 + 6.5, name, fs, tc, True, 'center', weight=900)
        add_mtext(slide, fx + pw / 2, py + ah + 26, note.split('\n'), 14, '#4A5A78',
                  False, 'center', 20, weight=500)
        if k < n - 1:
            ax = fx + pw + aw / 2
            ay = py + ah / 2
            add_line(slide, ax - 8, ay, ax + 5, ay, ARROW_C, 2.2)
            add_freeform(slide, [(ax, ay - 4.5), (ax + 7, ay), (ax, ay + 4.5)],
                         None, ARROW_C, 2.2, close=False)
        fx += pw + aw

    # ---------- 双面板 ----------
    PY_, PH_ = 953, 246
    add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, 20, PY_, 687, PH_,
              '#FEFEFF', '#DBE7F7', 1.5, adj=14 / PH_)
    add_text_baseline(slide, 47, PY_ + 34, '真实世界的典型应用', 21, INK, True, weight=900)
    ry = PY_ + 56
    for k, (name, tc, bg, bc, desc) in enumerate(APPS):
        yy = ry + k * 25.5
        add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, 47, yy, 122, 21.5,
                  bg, bc, 1.4, adj=0.28)
        fs = 13.5 if len(name) <= 5 else 11
        add_mtext(slide, 108, yy + 15.5, name, fs, tc, True, 'center')
        ax = 182
        add_line(slide, ax, yy + 10.8, ax + 11, yy + 10.8, tc, 2)
        add_freeform(slide, [(ax + 8, yy + 6.8), (ax + 14, yy + 10.8), (ax + 8, yy + 14.8)],
                     None, tc, 2, close=False)
        add_mtext(slide, 210, yy + 15.5, desc, 15, BODY, False, 'start', weight=500)

    add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, 724, PY_, 456, PH_,
              '#FEFEFF', '#DBE7F7', 1.5, adj=14 / PH_)
    add_text_baseline(slide, 751, PY_ + 34, '为什么这很重要', 21, INK, True, weight=900)
    ys = [PY_ + 58, PY_ + 97, PY_ + 136, PY_ + 175, PY_ + 226]
    for k, item in enumerate(WHY):
        icon_check(slide, 768, ys[k] + 2, 12.5, '#3D9E63')
        add_mtext(slide, 792, ys[k] + 7, item.split('\n'), 15.5, BODY, False, 'start', 24, weight=500)

    # ---------- 关键现代概念 ----------
    add_text_baseline(slide, W / 2 - 100, 1222, '关键现代概念', 21, INK, True, 'center', weight=900)
    x = 20
    for k, (name, tc, bg, ic, note) in enumerate(CONCEPTS):
        add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, 1240, 183, 110, bg, adj=0.11)
        add_mtext(slide, x + 91.5, 1268, name, 17.5, tc, True, 'center', weight=900)
        ccx = x + 91.5
        ccy = 1294
        if ic == 'media':
            icon_media(slide, ccx + 6, ccy, 44, '#7C5CE0')
        elif ic == 'dbplus':
            icon_db_plus(slide, ccx, ccy, 44, '#0FA36B', '#0A7A44')
        elif ic == 'sliders':
            icon_sliders(slide, ccx, ccy, 40, '#8B5CF6')
        elif ic == 'chat':
            icon_chat_dots(slide, ccx, ccy, 40, '#4F6EF0')
        elif ic == 'shield':
            icon_shield_check(slide, ccx, ccy, 40, '#0FA36B')
        else:
            icon_robot(slide, ccx, ccy, 40, '#6366F1')
        add_mtext(slide, x + 91.5, 1328, note.split('\n'), 13.5, '#4A5568', False, 'center', 19)
        x += 183 + 8.4

    # ---------- 常见使用场景 ----------
    SY, SH_ = 1358, 126
    add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, 20, SY, 1160, SH_,
              '#FEFEFF', '#DBE7F7', 1.5, adj=14 / SH_)
    add_text_baseline(slide, 47, SY + 30, '常见使用场景', 20, INK, True, weight=900)
    col_w = 1160 / 5
    iy = SY + 42
    scene_icons = dict(headset=icon_headset, doc2=icon_doc, image2=icon_image,
                       chart2=icon_chart, shield2=icon_shield)
    for k, (ic, color, t1, t2, note) in enumerate(SCENES):
        x0 = 20 + k * col_w
        add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x0 + 22, iy, 32, 32,
                  '#F1F4F9', adj=0.28)
        scene_icons[ic](slide, x0 + 38, iy + 16, 22, color)
        if t2:
            add_mtext(slide, x0 + 64, iy + 13, [t1, t2], 15, INK, True, 'start', 17, weight=800)
        else:
            add_mtext(slide, x0 + 64, iy + 21, t1, 15, INK, True, 'start', weight=800)
        add_mtext(slide, x0 + 22, iy + 48, note.split('\n'), 13, '#5A6B85', False, 'start', 17.5)

    # ---------- 重要提醒 ----------
    WY, WH_ = 1496, 92
    add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, 20, WY, 1160, WH_,
              '#FDF3F5', '#F5D8DE', 1.5, adj=14 / WH_)
    cols = [(52, 320), (400, 350), (790, 380)]
    for k, (wd, (x0, cw)) in enumerate(zip(WARNS, cols)):
        cyy = WY + 30
        if wd['icon'] == 'solid':
            icon_excl_solid(slide, x0 + 17, cyy, 17, wd['ic'])
        elif wd['icon'] == 'ring':
            icon_excl_ring(slide, x0 + 17, cyy, 16, wd['ic'])
        else:
            icon_shield_check(slide, x0 + 17, cyy, 34, wd['ic'])
        tl = wd['title'].split('\n')
        ty = WY + 22
        for j, ln in enumerate(tl):
            add_text_baseline(slide, x0 + 46, ty + j * 19, ln, 15.5, wd['tc'], True, weight=900)
        dy = ty + len(tl) * 19 + 4
        add_mtext(slide, x0 + 46, dy, wd['desc'].split('\n'), 13.5, wd['dc'], False, 'start', 19)

    return slide


def main():
    prs = new_prs()
    build(prs)
    out = '/home/z/my-project/download/AI技术体系对比图.pptx'
    prs.save(out)
    print('written:', out)


if __name__ == '__main__':
    main()
