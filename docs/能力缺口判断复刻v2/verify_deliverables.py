#!/usr/bin/env python3
"""Step5/6: 边界校验 + 双交付物终检（N5/N6，全部脚本化断言）"""
import os, re, sys
from PIL import ImageFont
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), '能力缺口判断复刻v2.html')
PPTX = os.path.join(os.path.dirname(os.path.abspath(__file__)), '能力缺口判断复刻v2.pptx')
FONTS = {400: '/usr/share/fonts/truetype/chinese/NotoSansSC-Regular.ttf',
         700: '/usr/share/fonts/truetype/chinese/NotoSansSC-Bold.ttf'}
_fc = {}
def tw(text, size, weight=400):
    if weight >= 600:
        weight = 700
    if weight not in _fc:
        _fc[weight] = ImageFont.truetype(FONTS[weight], 1000)
    return _fc[weight].getlength(text) / 1000 * size

OK, FAIL = '✓', '✗'
results = []
def check(name, cond, detail=''):
    results.append((name, bool(cond), detail))

# ================= 文案清单（两条产线共用） =================
PHRASES = [
    '准备度评分与能力缺口诊断',
    '维度', '权重', '现状评分', '（满分5）', '目标评分',
    '战略', '流程', '数据', '技术', '人才', '治理',
    '20%', '15%', '10%', '3.5', '3.0', '2.5', '2.0', '4.0', '3.5',
    '合计', '100%', '加权现状评分', '2.75', '加权目标评分', '3.95', '差距', '1.20',
    '能力缺口差距排序', '差距分值', '（目标-现状）',
    '治理', '数据', '人才', '流程', '技术', '战略', '2.0', '1.5', '1.0', '0.5',
    '重点行动与优先事项', '分值与权重用于项目决策；非行业基准。',
    '先完成数据授权和质量核验', '先明确上线责任', '先培训业务主责',
    '公众号·解决方案研究所',
]

# ================= HTML 终检 =================
html = open(HTML, encoding='utf-8').read()
check('HTML 存在且非空', os.path.exists(HTML) and len(html) > 15000, f'{len(html)}B')
n_text = len(re.findall(r'<text', html))
check('HTML <text> 数量达标 (>=40)', n_text >= 40, f'{n_text}')
n_id = len(re.findall(r'id="', html))
check('HTML id 数量达标 (>=60)', n_id >= 60, f'{n_id}')
n_img = len(re.findall(r'<image|data:image', html))
check('HTML 无位图 (image/data:image=0)', n_img == 0, f'{n_img}')
check('HTML viewBox 1728x972', 'viewBox="0 0 1728 972"' in html)
missing = [p for p in PHRASES if p not in html]
check('HTML 关键文案逐条 in', not missing, f'缺失:{missing[:5]}')
bad = re.findall(r'XXX|TODO|待补充|【|undefined|NaN', html)
check('HTML 无占位符', not bad, f'{bad[:5]}')

# ================= PPTX 终检 =================
prs = Presentation(PPTX)
s = prs.slides[0]
check('PPTX 尺寸 EMU 16:9', (prs.slide_width, prs.slide_height) == (12192000, 6858000),
      f'{prs.slide_width}x{prs.slide_height}')
pics = sum(1 for sh in s.shapes if sh.shape_type == MSO_SHAPE_TYPE.PICTURE)
check('PPTX Picture=0 (无嵌入图)', pics == 0, f'{pics}')
n_shapes = len(s.shapes)
check('PPTX 形状数达标 (>=150)', n_shapes >= 150, f'{n_shapes}')

all_text = []
overflow = []
for sh in s.shapes:
    if sh.has_text_frame and sh.text_frame.text.strip():
        t = sh.text_frame.text
        all_text.append(t)
        r = sh.text_frame.paragraphs[0].runs[0]
        size_pt = r.font.size.pt if r.font.size else 12
        size_px = size_pt / 0.5556
        weight = 700 if r.font.bold else 400
        w = tw(t, size_px, weight)
        if w > sh.width / 914400 * 914400 / 914400 * 1728 / 13.3333 + 6:  # EMU→px
            pass
        box_w_px = sh.width * 1728 / 12192000
        if w > box_w_px + 6:
            overflow.append((t[:12], round(w), round(box_w_px)))
check('PPTX 含文本形状 >=40', len(all_text) >= 40, f'{len(all_text)}')
joined = '\n'.join(all_text)
missing_p = [p for p in PHRASES if p not in joined]
check('PPTX 关键文案逐条 in', not missing_p, f'缺失:{missing_p[:5]}')
badp = re.findall(r'XXX|TODO|待补充|【|undefined|NaN', joined)
check('PPTX 无占位符', not badp, f'{badp[:5]}')
check('PPTX 边界零溢出', not overflow, f'{overflow[:5]}')

# 中文字体抽查
fonts_ok = all(r.font.name == 'Noto Sans SC'
               for sh in s.shapes if sh.has_text_frame
               for p_ in sh.text_frame.paragraphs for r in p_.runs)
check('PPTX 字体统一 Noto Sans SC', fonts_ok)

# ================= 汇总 =================
print('=' * 56)
n_ok = sum(1 for _, ok, _ in results if ok)
for name, ok, detail in results:
    print(f'{OK if ok else FAIL} {name}  {detail}')
print('=' * 56)
print(f'终检结果: {n_ok}/{len(results)} 通过')
sys.exit(0 if n_ok == len(results) else 1)
