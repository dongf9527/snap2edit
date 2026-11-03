# -*- coding: utf-8 -*-
"""第三轮：基座顶面中心与立方体底面对齐（消除悬浮感）"""
import io

P = '/home/z/my-project/download/德勤AI落地方法论拆解.html'
s = io.open(P, encoding='utf-8').read()

# 立方体底面中心 local y=425；暗层顶面中心 438（完全包含立方体底面，斜率同为0.5无缝衔接）
# 各层中心：暗 438 / 中 474 / 浅 511 / 白 550 → 反推各 svg top（local cy 分别为 82/98/114/125）
pairs = [
    ('<svg style="left:40px;top:432px" width="520" height="166"', '<svg style="left:40px;top:356px" width="520" height="166"'),   # 暗
    ('<svg style="left:40px;top:445px" width="520" height="198"', '<svg style="left:40px;top:376px" width="520" height="198"'),   # 中
    ('<svg style="left:40px;top:461px" width="520" height="234"', '<svg style="left:40px;top:397px" width="520" height="234"'),   # 浅
    ('<svg style="left:40px;top:486px" width="520" height="272"', '<svg style="left:40px;top:425px" width="520" height="272"'),   # 白
]

n_ok = 0
for old, new in pairs:
    c = s.count(old)
    if c != 1:
        print(f'!! 命中 {c} 次: {old[:56]}...')
        continue
    s = s.replace(old, new)
    n_ok += 1

io.open(P, 'w', encoding='utf-8').write(s)
print(f'完成 {n_ok}/{len(pairs)}')
