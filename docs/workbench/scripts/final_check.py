#!/usr/bin/env python3
"""最终核对:交付物完整性、原生性、文本真实性"""
import os, re, zipfile

print("=" * 60)
# 1) HTML 检查
html_path = '/home/z/my-project/download/框架与实施工具.html'
html = open(html_path, encoding='utf-8').read()
n_g = len(re.findall(r'<g id="', html))
n_text = len(re.findall(r'<text', html))
n_img = len(re.findall(r'<img|<image', html))
print(f"[HTML] {os.path.getsize(html_path)} bytes")
print(f"  独立SVG单元 <g> 数量: {n_g}")
print(f"  真实文本 <text> 数量: {n_text}")
print(f"  位图元素 <img>/<image>: {n_img}  (应为0)")
texts = re.findall(r'<text[^>]*>([^<]*)</text>', html)
full = ''.join(texts)
keys = ['公开框架与实施工具的对应关系', '公开研究 / 能力评估', '可信 AI', '董事会治理', '规模化实践',
        '主要来源（公开资料）', '本报告拆解 /', '现状证据', '场景组合', '分阶段交付', '责任与控制', '企业应用',
        '公平性', '隐私保护', '探索期', '规模化期', '评估', '监控', '阶段1', '能力评估表', '战略与组织',
        '场景清单', '智能客服', '营销内容生成', '优先级', '路线图与上线关卡', '价值台账', '效率提升', '客服部',
        'AI capability', 'assessment', 'Trustworthy AI', 'AI Governance', 'Roadmap', 'State of AI 2026',
        '数字渠道能力评估', '可信特征', '董事会监督', '规模化议题', '评分权重、预算和排期']
miss = [k for k in keys if k not in full]
print(f"  关键文字核对: {len(keys)-len(miss)}/{len(keys)} 通过" + (f"  缺失:{miss}" if miss else ""))

# 2) PPTX 检查
pptx_path = '/home/z/my-project/download/框架与实施工具.pptx'
z = zipfile.ZipFile(pptx_path)
media = [n for n in z.namelist() if n.startswith('ppt/media/')]
print(f"[PPTX] {os.path.getsize(pptx_path)} bytes")
print(f"  嵌入媒体文件: {len(media)}  (应为0) {media if media else ''}")

from pptx import Presentation
from pptx.util import Emu
prs = Presentation(pptx_path)
print(f"  画布: {prs.slide_width/914400:.3f}in x {prs.slide_height/914400:.3f}in "
      f"({prs.slide_width}x{prs.slide_height} EMU)")
slide = prs.slides[0]
kinds = {}
n_tb = 0
for sh in slide.shapes:
    t = str(sh.shape_type)
    kinds[t] = kinds.get(t, 0) + 1
    if sh.has_text_frame and sh.text_frame.text.strip():
        n_tb += 1
print(f"  形状总数: {len(slide.shapes)}, 含文本的形状: {n_tb}")
for t, c in sorted(kinds.items(), key=lambda kv: -kv[1]):
    print(f"    {t}: {c}")
all_text = ' '.join(sh.text_frame.text for sh in slide.shapes if sh.has_text_frame)
miss2 = [k for k in keys if k not in all_text]
print(f"  关键文字核对: {len(keys)-len(miss2)}/{len(keys)} 通过" + (f"  缺失:{miss2}" if miss2 else ""))
