# -*- coding: utf-8 -*-
"""第二轮插图微调：基座抬升、光晕柔化、立方体青光增强、云/柱状图标优化"""
import io

P = '/home/z/my-project/download/德勤AI落地方法论拆解.html'
s = io.open(P, encoding='utf-8').read()

pairs = [
    # 1. 四层基座整体抬升 16px
    ('<svg style="left:40px;top:502px" width="520" height="272"', '<svg style="left:40px;top:486px" width="520" height="272"'),
    ('<svg style="left:40px;top:477px" width="520" height="234"', '<svg style="left:40px;top:461px" width="520" height="234"'),
    ('<svg style="left:40px;top:461px" width="520" height="198"', '<svg style="left:40px;top:445px" width="520" height="198"'),
    ('<svg style="left:40px;top:448px" width="520" height="166"', '<svg style="left:40px;top:432px" width="520" height="166"'),
    # 2. 立方体下方光斑柔化
    ('<ellipse cx="150" cy="322" rx="118" ry="22" fill="#A9D2EC" opacity=".45"/>',
     '<ellipse cx="150" cy="306" rx="128" ry="20" fill="#B7D8EE" opacity=".38"/>'),
    # 3. 立方体顶面青光增强
    ('<ellipse cx="125" cy="75" rx="58" ry="25" fill="#8FD0EA" opacity=".32"/>',
     '<ellipse cx="125" cy="75" rx="58" ry="25" fill="#8FD0EA" opacity=".45"/>'),
    ('<ellipse cx="125" cy="75" rx="26" ry="11" fill="#A8DFF4" opacity=".55"/>',
     '<ellipse cx="125" cy="75" rx="26" ry="11" fill="#A8DFF4" opacity=".7"/>'),
    # 4. 云图标：云形更饱满、芯片更精致
    ('''<path d="M34 66a17 17 0 0 1-2-33 22 22 0 0 1 42-6 16 16 0 0 1 12 30 14 14 0 0 1-10 9z" fill="#F1F4F9" stroke="#C6CFDB" stroke-width="2"/>
      <path d="M34 66h42a14 14 0 0 0 10-9 15.5 15.5 0 0 0 2-12l-54 12z" fill="#DDE4EE"/>
      <rect x="46" y="34" width="24" height="18" rx="3" fill="#3E4E63"/>
      <rect x="52" y="40" width="12" height="7" rx="1.5" fill="#8FD4F0"/>
      <path d="M50 30v4M58 30v4M66 30v4M50 52v4M58 52v4M66 52v4M42 40h4M42 46h4M70 40h4M70 46h4" stroke="#3E4E63" stroke-width="2"/>''',
     '''<path d="M32 64a16 16 0 0 1-1-31 21 21 0 0 1 40-7 15 15 0 0 1 14 26 13 13 0 0 1-9 12z" fill="#F2F5FA" stroke="#C9D2DE" stroke-width="2"/>
      <path d="M32 64h44a13 13 0 0 0 9-12 15 15 0 0 0 3-13l-56 13z" fill="#DEE5EF"/>
      <rect x="47" y="36" width="22" height="16" rx="3" fill="#4A5A70"/>
      <rect x="52" y="41" width="12" height="6" rx="1.5" fill="#9BD8F2"/>
      <path d="M51 32v4M58 32v4M65 32v4M51 56v4M58 56v4M65 56v4M43 40h4M43 48h4M69 40h4M69 48h4" stroke="#4A5A70" stroke-width="1.8"/>'''),
    # 5. 柱状图标变浅
    ('<path d="M40 34 52 28v54l-12 6Z" fill="#5F7288"/><path d="M52 28l10 5v54l-10-5Z" fill="#8FA0B4"/>',
     '<path d="M40 34 52 28v54l-12 6Z" fill="#6C8098"/><path d="M52 28l10 5v54l-10-5Z" fill="#9FAFBF"/>'),
    ('<path d="M62 48 74 42v34l-12 6Z" fill="#5F7288"/><path d="M74 42l10 5v34l-10-5Z" fill="#8FA0B4"/>',
     '<path d="M62 48 74 42v34l-12 6Z" fill="#6C8098"/><path d="M74 42l10 5v34l-10-5Z" fill="#9FAFBF"/>'),
    ('<path d="M40 34 50 39v54l-10-5Z" fill="#4C5D71"/>', '<path d="M40 34 50 39v54l-10-5Z" fill="#586A80"/>'),
    ('<path d="M62 48 72 53v34l-10-5Z" fill="#4C5D71"/>', '<path d="M62 48 72 53v34l-10-5Z" fill="#586A80"/>'),
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
