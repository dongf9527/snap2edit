# -*- coding: utf-8 -*-
"""对 HTML 执行剩余的精确替换（每项断言必须命中）"""
import io

P = '/home/z/my-project/download/德勤AI落地方法论拆解.html'
s = io.open(P, encoding='utf-8').read()

pairs = [
    # A. 深色顶层基座收窄
    ('<path d="M110 82 260 10 410 82 260 148Z" fill="#5E7189"/>',
     '<path d="M118 82 260 16 402 82 260 148Z" fill="#5E7189"/>'),
    ('<path d="M110 82 260 154 260 188 110 116Z" fill="#3E5068"/>',
     '<path d="M118 82 260 148 260 182 118 116Z" fill="#3E5068"/>'),
    ('<path d="M410 82 260 154 260 188 410 116Z" fill="#4A5C74"/>',
     '<path d="M402 82 260 148 260 182 402 116Z" fill="#4A5C74"/>'),
    # B. 云→立方体、数据层→立方体 连接线改道
    ('<path d="M268 108C230 152 206 176 233 206"/>',
     '<path d="M262 108C225 165 215 220 218 258"/>'),
    ('<path d="M545 206v28c0 20-45 16-118 28"/>',
     '<path d="M545 206v30c0 22-55 18-125 34"/>'),
    # C. 立方体→网格 连接线
    ('<path d="M438 300c42 32 72 72 106 118"/>',
     '<path d="M430 330c48 26 80 56 114 88"/>'),
    # D. 右侧虚线弧
    ('<path d="M475 652A205 148 0 0 0 552 486"/>',
     '<path d="M480 655A200 142 0 0 0 560 472"/>'),
    # E. 节点位置
    ('<circle cx="268" cy="108" r="4"/><circle cx="233" cy="206" r="4.5"/>',
     '<circle cx="262" cy="108" r="4"/><circle cx="218" cy="258" r="4.5"/>'),
    ('<circle cx="427" cy="262" r="4.5"/>', '<circle cx="420" cy="270" r="4.5"/>'),
    # F. 网格+胶片条（缩小并紧贴应用层标签）
    ('''<svg style="left:526px;top:420px" width="90" height="92" viewBox="0 0 90 92" fill="none">
      <rect x="12" y="10" width="30" height="30" rx="7" fill="#7B8CA1"/>
      <rect x="50" y="10" width="30" height="30" rx="7" fill="#56687F"/>
      <rect x="12" y="48" width="30" height="30" rx="7" fill="#56687F"/>
      <rect x="50" y="48" width="30" height="30" rx="7" fill="#8B9CB1"/>
    </svg>
    <svg style="left:490px;top:436px" width="28" height="66" viewBox="0 0 28 66" fill="none">
      <rect x="3" y="3" width="22" height="60" rx="5" stroke="#9AA7B8" stroke-width="2" fill="#F2F5F9"/>
      <rect x="9" y="10" width="10" height="9" rx="2" fill="#B9C4D3"/><rect x="9" y="29" width="10" height="9" rx="2" fill="#B9C4D3"/><rect x="9" y="48" width="10" height="9" rx="2" fill="#B9C4D3"/>
    </svg>''',
     '''<svg style="left:536px;top:424px" width="74" height="76" viewBox="0 0 74 76" fill="none">
      <rect x="8" y="8" width="26" height="26" rx="6" fill="#8496AA"/>
      <rect x="40" y="8" width="26" height="26" rx="6" fill="#5F7288"/>
      <rect x="8" y="42" width="26" height="26" rx="6" fill="#5F7288"/>
      <rect x="40" y="42" width="26" height="26" rx="6" fill="#9AAABB"/>
    </svg>
    <svg style="left:500px;top:440px" width="26" height="62" viewBox="0 0 26 62" fill="none">
      <rect x="3" y="3" width="20" height="56" rx="5" stroke="#9AA7B8" stroke-width="2" fill="#F2F5F9"/>
      <rect x="8" y="9" width="10" height="9" rx="2" fill="#B9C4D3"/><rect x="8" y="27" width="10" height="9" rx="2" fill="#B9C4D3"/><rect x="8" y="45" width="10" height="9" rx="2" fill="#B9C4D3"/>
    </svg>'''),
    # G. 数据库配色加深
    ('<path d="M27 22v40c0 7 12.5 13 28 13s28-6 28-13V22" fill="#E9EEF5" stroke="#C6CFDB" stroke-width="2"/>',
     '<path d="M27 22v40c0 7 12.5 13 28 13s28-6 28-13V22" fill="#D7E0EA" stroke="#C0CBD9" stroke-width="2"/>'),
    ('<ellipse cx="55" cy="22" rx="28" ry="11" fill="#F4F7FB" stroke="#C6CFDB" stroke-width="2"/>',
     '<ellipse cx="55" cy="22" rx="28" ry="11" fill="#EEF3F9" stroke="#C0CBD9" stroke-width="2"/>'),
    ('stroke="#C6CFDB" stroke-width="2" fill="none"/>\n      <ellipse cx="55" cy="22" rx="18" ry="6.5" fill="#DDE6F0"/>',
     'stroke="#B9C5D4" stroke-width="2" fill="none"/>\n      <ellipse cx="55" cy="22" rx="18" ry="6.5" fill="#D5DFEB"/>'),
    # H. 人员图标两侧变浅
    ('<circle cx="30" cy="52" r="9" fill="#7C8DA3"/>\n      <path d="M16 88c0-12 6-19 14-19s14 7 14 19z" fill="#7C8DA3"/>',
     '<circle cx="30" cy="52" r="9" fill="#8C9CB0"/>\n      <path d="M16 88c0-12 6-19 14-19s14 7 14 19z" fill="#8C9CB0"/>'),
    ('<circle cx="88" cy="52" r="9" fill="#8B9CB1"/>\n      <path d="M74 88c0-12 6-19 14-19s14 7 14 19z" fill="#8B9CB1"/>',
     '<circle cx="88" cy="52" r="9" fill="#9AA9BB"/>\n      <path d="M74 88c0-12 6-19 14-19s14 7 14 19z" fill="#9AA9BB"/>'),
    # I. 增长柱变浅
    ('<rect x="14" y="74" width="11" height="18" rx="2" fill="#8B9CB1"/>',
     '<rect x="14" y="74" width="11" height="18" rx="2" fill="#98A8BA"/>'),
    ('<rect x="31" y="62" width="11" height="30" rx="2" fill="#7B8CA1"/>',
     '<rect x="31" y="62" width="11" height="30" rx="2" fill="#8799AD"/>'),
    ('<rect x="48" y="50" width="11" height="42" rx="2" fill="#5D7089"/>',
     '<rect x="48" y="50" width="11" height="42" rx="2" fill="#6C82A0"/>'),
    ('<rect x="65" y="36" width="11" height="56" rx="2" fill="#45596F"/>',
     '<rect x="65" y="36" width="11" height="56" rx="2" fill="#4E647E"/>'),
]

n_ok = 0
for old, new in pairs:
    if s.count(old) != 1:
        print(f'!! 命中 {s.count(old)} 次: {old[:60]}...')
        continue
    s = s.replace(old, new)
    n_ok += 1

io.open(P, 'w', encoding='utf-8').write(s)
print(f'完成 {n_ok}/{len(pairs)} 项替换')
