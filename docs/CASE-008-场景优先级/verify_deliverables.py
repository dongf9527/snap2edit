#!/usr/bin/env python3
"""Step5/6: 边界校验 + 双交付物终检（N5/N6，全部脚本化断言）—— CASE-008"""
import os, re, sys
from PIL import ImageFont
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

HERE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(HERE, '场景优先级复刻.html')
PPTX = os.path.join(HERE, '场景优先级复刻.pptx')
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

# ================= 文案清单（两条产线共用，与 spec.PHRASES 一致） =================
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
# v2 迭代（2026-11-07）：'公众号' / '解决方案研究所' 随水印移除退出文案清单；
# 并在下方新增两条「无水印」反向断言（终检 15→17 项）。

# ================= HTML 终检 =================
html = open(HTML, encoding='utf-8').read()
check('HTML 存在且非空', os.path.exists(HTML) and len(html) > 15000, f'{len(html)}B')
n_text = len(re.findall(r'<text', html))
check('HTML <text> 数量达标 (>=60)', n_text >= 60, f'{n_text}')
n_id = len(re.findall(r'id="', html))
check('HTML id 数量达标 (>=80)', n_id >= 80, f'{n_id}')
n_img = len(re.findall(r'<image|data:image', html))
check('HTML 无位图 (image/data:image=0)', n_img == 0, f'{n_img}')
check('HTML viewBox 1728x972', 'viewBox="0 0 1728 972"' in html)
missing = [p for p in PHRASES if p not in html]
check('HTML 关键文案逐条 in', not missing, f'缺失:{missing[:5]}')
bad = re.findall(r'XXX|TODO|待补充|【|undefined|NaN', html)
check('HTML 无占位符', not bad, f'{bad[:5]}')
wm_html = ('公众号' in html) or ('解决方案研究所' in html) or ('watermark' in html)
check('HTML 无水印（v2 迭代移除）', not wm_html)

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
EPX = 12192000 / 1728
for sh in s.shapes:
    if sh.has_text_frame and sh.text_frame.text.strip():
        t = sh.text_frame.text
        all_text.append(t)
        r0 = sh.text_frame.paragraphs[0].runs[0]
        size_pt = r0.font.size.pt if r0.font.size else 12
        size_px = size_pt / 0.5556
        weight = 700 if r0.font.bold else 400
        w = tw(t, size_px, weight)
        box_w_px = sh.width / EPX
        if w > box_w_px + 2:
            overflow.append((t[:12], round(w), round(box_w_px)))
check('PPTX 含文本形状 >=40', len(all_text) >= 40, f'{len(all_text)}')
joined = '\n'.join(all_text)
missing_p = [p for p in PHRASES if p not in joined]
check('PPTX 关键文案逐条 in', not missing_p, f'缺失:{missing_p[:5]}')
badp = re.findall(r'XXX|TODO|待补充|【|undefined|NaN', joined)
check('PPTX 无占位符', not badp, f'{badp[:5]}')
wm_pptx = ('公众号' in joined) or ('解决方案研究所' in joined)
check('PPTX 无水印（v2 迭代移除）', not wm_pptx)
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
