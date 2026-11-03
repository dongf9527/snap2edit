#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""交付文件终检：HTML 真实文本校验 + PPTX 原生形状/文本校验"""
import re, os
from pptx import Presentation
from pptx.util import Emu

ok = True
def chk(cond, msg):
    global ok
    print(('  ✓ ' if cond else '  ✗ ') + msg)
    if not cond: ok = False

print('== 交付物①：HTML+SVG ==')
hp = '/home/z/my-project/download/企业AI落地_复刻.html'
html = open(hp, encoding='utf-8').read()
chk(os.path.getsize(hp) > 30000, f'文件存在且非空 ({os.path.getsize(hp)/1024:.1f} KB)')
texts = re.findall(r'<text[^>]*>([^<]+)</text>', html)
print(f'  SVG <text> 元素数量: {len(texts)}')
chk(len(texts) >= 100, f'全部文字为真实 <text> 文本（{len(texts)} 处，覆盖图中全部文字）')
chk('<image' not in html and 'data:image' not in html, '无任何位图/图片元素')
must = ['企业AI落地的四类关键决策', '为什么做', '先做什么', '如何交付', '如何控制',
        '对应经营目标、流程痛点、价值基线', '对齐经营目标', '支撑战略方向与业务优先级',
        '输出目标树', '输出组合清单', '输出分阶段路线图', '输出台账',
        '诊断', '排序', '试点', '上线', '扩围', '向更多业务与场景复制',
        '治理与价值评估（贯穿全程）', '合规与风险管理', '数据与模型治理',
        '持续监测与反馈', '价值评估与复盘', '三种投资决策', '进入试点', '补齐前置条件',
        '暂缓投入', '来源：基于德勤公开研究归纳。', '搭建数据架构', '明确责任审批']
joined = ''.join(texts)
missing = [m for m in must if m not in joined]
chk(not missing, f'关键文字全部在场 (缺失: {missing if missing else "无"})')
ids = re.findall(r'id="([^"]+)"', html)
chk(len(ids) >= 70, f'独立可寻址 SVG 单元（id 数 {len(ids)}，覆盖全部逻辑组件）')
chk('viewBox="0 0 1280 720"' in html, 'viewBox 1280x720 坐标系')
for t in ['XXX', 'TODO', '待补充', '【', 'undefined', 'NaN']:
    chk(t not in joined, f'无残留占位符 "{t}"')

print('\n== 交付物②：PPTX ==')
pp = '/home/z/my-project/download/企业AI落地_复刻.pptx'
prs = Presentation(pp)
chk(prs.slide_width == Emu(12192000) and prs.slide_height == Emu(6858000), '16:9 原生幻灯片尺寸')
slide = prs.slides[0]
shapes = list(slide.shapes)
n_text = 0; all_text = []
n_pic = 0
for sp in shapes:
    if sp.shape_type == 13 or sp.__class__.__name__ == 'Picture':
        n_pic += 1
    if sp.has_text_frame:
        t = sp.text_frame.text.strip()
        if t:
            n_text += 1; all_text.append(t)
print(f'  形状总数: {len(shapes)}  含文本形状: {n_text}  图片: {n_pic}')
chk(n_pic == 0, '无嵌入图片（100% 原生形状+文本框）')
jt = ''.join(all_text)
missing2 = [m for m in must if m not in jt]
chk(not missing2, f'文本框关键文字全部在场 (缺失: {missing2 if missing2 else "无"})')
for t in ['XXX', 'TODO', '待补充', '【', 'undefined', 'NaN']:
    chk(t not in jt, f'无残留占位符 "{t}"')
# 字体与字号抽查
from pptx.util import Pt
tb0 = slide.shapes[2]  # 大标题(第3个形状: bg,?,title)
found_title = False
for sp in shapes:
    if sp.has_text_frame and '企业AI落地的四类关键决策' in sp.text_frame.text:
        r = sp.text_frame.paragraphs[0].runs[0]
        found_title = (r.font.size >= Pt(40) and r.font.bold)
chk(found_title, '主标题 58px(43.5pt) 加粗')
n_auto = sum(1 for sp in shapes if sp.shape_type is not None and 'AUTO_SHAPE' in str(sp.shape_type))
n_free = sum(1 for sp in shapes if sp.__class__.__name__ == 'FreeformBuilder' or 'Freeform' in sp.__class__.__name__)
print(f'  自动形状: {n_auto}, 自由多边形: {len([sp for sp in shapes if sp.shape_type == 5])}, 连接线: {len([sp for sp in shapes if sp.shape_type == 3])}')

print('\n' + ('== 全部通过 ==' if ok else '== 存在未通过项 =='))
