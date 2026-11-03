# 图片高保真还原为 HTML+SVG 与 PPTX —— 标准流程文档

> **适用场景**：将一张信息图 / 方法论图 / 流程图 / 对比图，还原为两种**完全可编辑**的交付物：
>
> - **交付物① HTML+SVG 版**：全部文字为真实 `<text>` 文本（可选中、复制、修改），箭头、矩阵格子、立方体、流程框等每个元素都是**带 `id` 的独立 SVG 最小单元**，可单独取用组装；**全文件禁止出现任何位图**（`<image>`、`data:image`、背景图一律不允许）。
> - **交付物② PPTX 版**：由 python-pptx 生成的 **PowerPoint 原生文本框 + 形状**（不含任何嵌入图片，`Picture` 数量必须为 0），每个单元可在 PPT 里单独拖动、改字、改色。
>
> **核心方法论**：一份规格书、两条产线、双重校验闭环、数值化验收。

---

## 一、总体思路与流程图

```
                     ┌─────────────────────────────┐
      原图 upload/ ──▶│ Step 1  图像分析             │
                     │ 尺寸·取色·布局测量·文字转录    │
                     └──────────────┬──────────────┘
                                    ▼
                          「布局规格书」（三张表）
                    坐标尺寸表 / 配色板 / 文案逐字表
                     │                            │
          ┌──────────▼──────────┐      ┌──────────▼──────────┐
          │ Step 2  HTML+SVG 产线│      │ Step 4  PPTX 产线    │
          │ svg_lib.py 组件库    │      │ pptx_lib.py 助手库   │
          │ gen_svg_html.py 组装 │      │ gen_pptx.py 原生形状 │
          └──────────┬──────────┘      └──────────┬──────────┘
                     ▼                            ▼
          Step 3  Playwright 截图        Step 5  soffice→PDF→PNG
          并排对比 + diff 差异热力图      并排对比 + 边界溢出校验
                     │ 达标                        │ 达标
                     ▼                            ▼
               交付物① HTML ✓               交付物② PPTX ✓
                     └────────────┬───────────────┘
                                  ▼
                    Step 6  verify_deliverables.py 终检
                       （文字清单/无位图/无占位符/尺寸）
                                  ▼
                            download/ 交付
```

四条原则：

1. **一份规格书喂两条产线**——坐标、颜色、文字只分析一次，HTML 与 PPTX 依据同一份数据落位，保证两版内容天然一致。
2. **组件化建模**——不写"一坨 SVG"，而是把箭头、格子、立方体、图标等做成独立函数，每个函数输出带 `id` 的最小单元，HTML 和 PPTX 复用同一套组件定义。
3. **双重校验闭环**——HTML 用"截图 vs 原图 diff"收敛，PPTX 用"渲染图 vs 原图并排 + 数值边界校验"收敛，不凭感觉说"差不多了"。
4. **数值化验收**——终检用脚本断言（文字齐全、无位图、无占位符、形状数、幻灯片尺寸），全部 ✓ 才交付。

---

## 二、环境设置

### 2.1 系统依赖

| 组件 | 要求 | 用途 |
|---|---|---|
| Linux 沙箱 / 任意 Unix | — | 运行环境（Windows 需自配 WSL 或等价工具链） |
| Python | 3.9+ | 全部分析与生成脚本 |
| Node.js | 16+ | Playwright 截图脚本（亦可用纯 Python 版，二选一即可） |
| LibreOffice（`soffice`） | 系统包 | PPTX → PDF 无头渲染（PPTX 视觉校验的唯一通道） |
| poppler-utils（`pdftoppm`） | 系统包 | PDF → PNG，供版式比对 |
| 中文字体 | Noto Sans SC / Noto Sans CJK | 渲染截图不糊、字体量宽与 PowerPoint 度量一致 |

```bash
# 系统包（如缺失）
sudo apt-get install -y libreoffice poppler-utils fonts-noto-cjk

# Python 依赖
pip install python-pptx pillow numpy playwright
python -m playwright install chromium          # Python 版浏览器

# Node 版 Playwright（可选，与 Python 版二选一）
npm init -y && npm i playwright && npx playwright install chromium
```

### 2.2 目录约定

```
/home/z/my-project/
├── upload/     # 原图（只读输入，绝不原地修改）
├── scripts/    # 全部脚本 + 中间对比图（保留下来，过程可追溯）
├── analysis/   # 区域裁剪放大图（文字逐字核对用）
└── download/   # 最终交付物（HTML / PPTX / 预览图）
```

> 纪律：脚本一律落盘到 `scripts/` 再执行（长脚本不跑 `python -c` 内联）；原图只读；中间产物与最终交付物分目录。

---

## 三、主要依赖清单

| 依赖 | 使用环节 | 关键作用 | 备注 / 坑 |
|---|---|---|---|
| **Pillow** | Step 1 / 3 / 5 | 读尺寸、按坐标取色、区域裁剪放大、并排拼图、字体实测宽度 | `ImageFont.getlength()` 的度量与 PowerPoint 基本一致，是防溢出的核心 |
| **numpy** | Step 3 | 原图 vs 截图的逐像素差异矩阵、按 16px 块聚合、输出热力图 | 块聚合能直接告诉你"改哪里"，比逐像素人眼扫快一个量级 |
| **playwright + chromium** | Step 3 | HTML → PNG **元素级截图**（只截 `#stage`/`#canvas` 容器） | `device_scale_factor=1` 保证与原图 1:1 像素对齐，否则 diff 全是假差异 |
| **python-pptx** | Step 4 / 6 | 原生矩形/圆角/箭头/连接线/渐变/文本框；终检时读回形状树断言 | 唯一的 PPTX 写入依赖；不引入任何"截图贴进 PPT"的捷径 |
| **LibreOffice** | Step 5 | `soffice --headless --convert-to pdf` 渲染 PPTX | 与真实 PowerPoint 有细微渲染差异，所以还要配数值边界校验兜底 |
| **poppler-utils** | Step 5 | `pdftoppm` 把校验 PDF 转 PNG | 低分辨率（-r 60~90）即可，够看版式 |
| **中文字体** | 全程 | 量宽、渲染一致 | 缺字体会导致中文豆腐块 + 量宽失准 + PPT 里回退宋体 |

---

## 四、Step by Step 执行流程

### Step 1　原图分析 —— 产出「布局规格书」

**目的**：把一张"给人看的图"翻译成一份"给程序用的规格书"。

**动作与脚本**（均为本次实际使用的脚本）：

1. **尺寸与坐标系**：`analyze_image.py` 用 PIL 读取原图精确像素尺寸，确立坐标基准。原则：**SVG `viewBox` 与原图像素 1:1**（如 `viewBox="0 0 1280 720"`、`1728×972`），PPTX 按公式映射到幻灯片（见 Step 4 公式）。
2. **配色采样**：`sample_colors.py` / `sample2.py` / `refine_colors.py` 按坐标取色。要点：
   - 背景、格子填充、格子边框、箭头、正文、标题**分开放置采样点**，不要只采一处；
   - 同一色区**多点采样取众数**，避开文字与抗锯齿边缘的污染；
   - 输出一张去重后的色板表（hex），后续两条产线共用。
3. **布局测量**：`scan_edges.py` / `find_lines.py` / `measure_grid.py` / `blockmap.py` 扫描横竖分割线、格子边界与色块范围，得到每个矩形的 `(x, y, w, h)`；`measure_text.py` 量标题/正文的字高与基线位置。
4. **文字逐字核对**：`crop_regions.py` / `crop_detail.py` 把图切成若干区域（表头、每行每列、卡片、页脚……）输出放大裁剪图到 `analysis/`，**逐区域人工转录**，特别是小字号脚注、来源行、标签里的字。

**产出**：布局规格书 = ① 坐标尺寸表（每个元素的位置）＋ ② 色板表 ＋ ③ 文案逐字表。

> ✅ **结点 N1**：三张表齐全；放大裁剪图中每个区域文字都已转录、无"猜字"；主色 hex 与原图肉眼一致。不达标 → 回到裁剪图重转录，禁止带着模糊内容进入下一步。

---

### Step 2　编写生成脚本，产出 HTML+SVG 版

**目的**：把规格书变成全真实文本、组件化的 HTML 文件。

**动作与脚本**：

1. **先建组件库 `svg_lib.py`**：每个逻辑组件一个函数，参数化为 `(id, cx, cy, 尺寸, 颜色)`，返回带 `id` 的 `<g>` 片段。本次实现过：`icon_brain`（大脑）、`icon_chart`（柱状图）、`icon_network`（神经网络）、`icon_sparkle`（闪光星）等图标，以及箭头、矩阵格子、立方体、流程框系列。**组件内部用相对坐标计算、外部只暴露中心点和尺寸**，这样换个位置换个颜色即可复用。
2. **再写组装器 `gen_svg_html.py` / `build_html.py`**：按规格书逐元素调用组件，落到统一 `viewBox` 坐标系；所有文字一律 `<text>`（`text-anchor` 控制对齐，`tspan` 处理多行），**全文件不允许出现 `<image>` 与 `data:image`**。
3. **文字宽度预检**：生成时用 PIL `ImageFont.getlength()` 按"字号 × 1000 缩放"实测每段文字宽度，据此选择字号、行宽或截行，避免渲染后溢出格子。
4. 小步修补走独立 `patch_html.py` / `patch_html2.py` / `patch_html3.py`，定点替换，保留修改轨迹。

**产出**：`download/<名称>.html`。

> ✅ **结点 N2**：文件生成；正则统计 `<text>` 数量 ≥ 规格书文案条数；`<image`/`data:image` 零命中；`id` 数 ≥ 组件清单数（本次实例：text ≥ 100、id ≥ 70）。

---

### Step 3　渲染 HTML 截图，与原图对比校验（第一闭环）

**目的**：让"代码里对的"变成"渲染出来也对的"，用差异定位代替肉眼找茬。

**动作与脚本**：

1. **元素级截图** `shot_html.js`（Node 版）或 `render_html.py`（Python async 版）：

   ```js
   const { chromium } = require('playwright');
   const b = await chromium.launch();
   const p = await b.newPage({ viewport: { width: 1776, height: 1020 }, deviceScaleFactor: 1 });
   await p.goto('file:///…/xxx.html');
   await p.waitForTimeout(900);          // 等字体加载完
   await (await p.$('#canvas')).screenshot({ path: '/tmp/render_html.png' });
   ```

   关键点：只截画布容器元素（`#stage` / `#canvas`）、`deviceScaleFactor=1`、等待字体加载。
2. **并排对比图** `render_html.py`：原图与截图缩放到同尺寸，上下拼接（中间红分隔线）输出 `compare_html.png`，一张图看全局。
3. **差异热力图** `diff.py`：numpy 求逐像素差值绝对值之和，按 **16px 块聚合**，输出差异最大的 TOP 40 块坐标（`block(x,y) diff=…`）和热力图 `diff_heat.png`——直接给出"哪里最不像"。
4. **迭代**：按差异块坐标回到生成器/patch 脚本修正 → 重渲染 → 再 diff，循环直至差异收敛（经验阈值：总平均差异 < 10/255，且热力图无成片高亮）。

**产出**：`compare_html.png`（并排）、`diff_heat.png`（热力图）、收敛后的最终 HTML。

> ✅ **结点 N3**：并排图肉眼基本无差；diff 总平均差异收敛、无成片高亮块。不达标 → 按 TOP 差异块定位修正，**禁止未收敛就进入 PPTX 产线**（规格书没对齐，PPTX 会跟着错）。

---

### Step 4　编写 python-pptx 脚本，产出原生 PPTX

**目的**：同一份规格书，落到 PowerPoint 原生对象上，保证每个单元可拖动、可改字。

**动作与脚本**：

1. **坐标换算（两条公式定全场）**：

   ```text
   EMU/px = 幻灯片宽 EMU ÷ 画布 px 宽        # E(px) = Emu(round(px × EMU_PX))
   pt/px  = 幻灯片高 pt ÷ 画布 px 高          # FS(px) = Pt(px × PT_PX)
   ```

   实测两例：16:9 幻灯片（12192000×6858000 EMU）配 1728×972 画布 → `EMU_PX = 12192000/1728 ≈ 7055.6`、`PT_PX = 540/972 ≈ 0.5556`；自定义画布 1px=0.01in → `EMU_PX = 9144`、`PT_PX = 0.72`。
2. **助手库 `pptx_lib.py`**（Step 2 组件思想的 PPT 版）：
   - `E()` 长度换算、`PT()` 字号换算、`rgb()` 颜色、`mix()` 颜色插值（渐变端色）；
   - `text_width()` 用 PIL 按目标字体实测文本宽度，**写框之前先知道放不放得下**；
   - 文本框统一：`word_wrap=False`、四边 `margin=0`、按规格书设 `line_spacing`；
   - **中文字体双保险**：除 `font.name` 外，必须给 `rPr` 追加 `a:ea`（东亚字体）与 `a:cs`，否则中文在 PowerPoint 里回退宋体；`weight ≥ 800` 时同时置 `bold`；
   - 所有形状 `shadow.inherit = False`，避免 LibreOffice/PowerPoint 默认阴影污染。
3. **形状选型**：矩形/圆角矩形/椭圆用 `MSO_SHAPE`，箭头与连接线用 `MSO_CONNECTOR`（`MSO_LINE_DASH_STYLE` 控制虚线），渐变用 `mix()` 算端色后线性填充——与 SVG 版一一对应。
4. **组装器 `gen_pptx.py` / `build_pptx.py`**：用空白版式（`slide_layouts[6]`），按与 SVG 完全相同的规格书逐元素落位；文字条目与 `<text>` 清单一一对账。

**产出**：`download/<名称>.pptx`。

> ✅ **结点 N4**：PPTX 生成；读回形状树确认 `Picture` 数量 = 0；含文本形状数 ≥ 规格书文案条数；幻灯片尺寸 EMU 正确（如 12192000×6858000）。

---

### Step 5　渲染 PPTX 为图片校验版式（第二闭环）

**目的**：验证"PowerPoint 打开后的真实观感"，而不是 python-pptx 代码的自嗨。

**动作**：

```bash
cd /home/z/my-project/download
soffice --headless --convert-to pdf "xxx.pptx"          # PPTX → PDF
rm -rf /tmp/render && mkdir -p /tmp/render
pdftoppm -r 60 -jpeg -jpegopt quality=60 "xxx.pdf" /tmp/render/page   # PDF → PNG
```

1. **并排对比**：渲染图与原图拼接成 `compare_pptx.png` / `cmp_pptx_bottom.png`，检查整体版式、配色、层级。
2. **数值边界校验** `verify_bounds.py`：用 `text_width()` 实测每个文本框的文字宽度 vs 框宽/格宽，输出所有溢出项——LibreOffice 渲染与 PowerPoint 有细微差别，数值校验是兜底。
3. **迭代**：问题项回到 `gen_pptx.py` 修字号/框位/换行 → 重跑 → 重渲染，直至通过。

> ✅ **结点 N5**：渲染版式与原图一致（格子对齐、箭头指向正确、无文字溢出/截断）；边界校验零溢出。

---

### Step 6　最终核对交付文件

**目的**：用脚本断言代替"感觉没问题"，两条硬约束一次验收。

**动作**：`verify_deliverables.py` / `final_check.py` 统一终检：

**交付物① HTML 检查项**：
- 文件存在且非空（> 30 KB 量级）；
- `<text>` 元素数量达标（实例 ≥ 100）——全部文字为真实文本；
- `<image` / `data:image` 零命中——无任何位图；
- **关键文案清单逐条 in 检查**（标题、每个模块标题、脚注、来源行……）；
- 独立 `id` 数达标（实例 ≥ 70）——组件皆可单独寻址；
- `viewBox` 坐标系正确；
- 无残留占位符：`XXX`、`TODO`、`待补充`、`【`、`undefined`、`NaN`。

**交付物② PPTX 检查项**：
- 幻灯片尺寸 EMU 正确（实例 12192000×6858000，16:9）；
- 形状总数 / 含文本形状数达标；
- **`Picture` 形状数量 = 0**——无嵌入图片，100% 原生形状+文本框；
- 文本框关键文案逐条 in 检查（与 HTML 同一份清单）；
- 字体、字号抽查；
- 同一份占位符黑名单零命中。

**收尾**：清点 `download/` 交付清单、写 README、必要时输出预览图。

> ✅ **结点 N6（终验）**：终检脚本全部 ✓。任何一项 ✗ 都不算完成。

---

## 五、重要结点汇总表

| 结点 | 里程碑 | 验收标准（可执行） | 不达标时的动作 |
|---|---|---|---|
| **N1** | 布局规格书定稿 | 坐标表/色板/文案表齐全；放大裁剪逐字核对完成 | 回裁剪图重转录，禁止"猜字" |
| **N2** | HTML+SVG 生成 | 无 `<image>`；`<text>` 数 ≥ 文案数；`id` 数 ≥ 组件数 | 补组件/补文字 |
| **N3** | HTML 校验收敛 | 并排图一致；diff 总平均差异 < 10/255 且无成片高亮 | 按 TOP 差异块 patch → 重渲染 |
| **N4** | PPTX 生成 | `Picture` = 0；文本形状数 ≥ 文案数；尺寸 EMU 正确 | 补形状/查换算公式 |
| **N5** | PPTX 校验通过 | 渲染版式一致；`verify_bounds` 零溢出 | 调字号/框位重跑 |
| **N6** | 终检交付 | 终检脚本全 ✓（文字清单、无位图、无占位符、字体抽查） | 修复后整脚本重跑 |

**两条产线的顺序纪律**：N3 必须先于 Step 4——规格书未对齐就开 PPTX 产线，等于把错误复制一份。

---

## 六、关键公式与速查

```text
# 坐标换算
EMU/px = 幻灯片宽 EMU ÷ 画布 px 宽
pt/px  = 幻灯片高 pt ÷ 画布 px 高      # 16:9 → 540pt ÷ 画布高

# 常用组合
16:9 幻灯片 12192000×6858000 EMU + 1728×972 画布 → 7055.6 EMU/px, 0.5556 pt/px
1px = 0.01in 画布                                → 9144   EMU/px, 0.72   pt/px

# 字体量宽（防溢出）
ImageFont.truetype('NotoSansSC-Bold.ttf', 1000).getlength(t) / 1000 × 字号 = 实际宽度 px

# diff 收敛判据
总平均差异（0~255/通道和）< 10，且 16px 块热力图无成片高亮
```

---

## 七、经验与坑（实战清单）

1. **规格书先行**：所有坐标、颜色、文字先落表再写代码，改一处两条产线同步改，不会 HTML 一套、PPTX 一套。
2. **取色要避让**：文字与边框抗锯齿会污染采样，同色区多点采样取众数；边框色和填充色分开采。
3. **截图必须元素级、1:1**：只截 `#stage`/`#canvas` 且 `deviceScaleFactor=1`，并等待字体加载（~900ms），否则 diff 热力图全是无意义差异。
4. **diff 用块聚合**：16px 块聚合 + TOP N 排序，输出直接就是"修改任务清单"，比人眼扫快得多。
5. **文字宽度靠实测不靠估**：PIL `getlength()` 与 PowerPoint 度量一致；SVG 和 PPTX 写字前都先量，溢出消灭在生成阶段。
6. **中文字体要设 `a:ea`**：只设 `font.name` 时，PowerPoint 会把中文回退成宋体；`a:ea` + `a:cs` 双设置才稳。
7. **形状统一关阴影**：`shadow.inherit = False`，否则 LibreOffice 渲染校验时会出现原图没有的阴影。
8. **渲染校验用低分辨率即可**：`pdftoppm -r 60~90` 足够看版式；数值边界校验负责兜底精度。
9. **修补走独立 patch 脚本**：小修定点替换、保留轨迹；结构性改动才回生成器重跑。
10. **终检必须脚本化**：`Picture == 0`、无 `<image>`、文案清单 in、占位符黑名单，全部做成断言——"看着挺像"不构成验收依据。

---

## 八、本次实际产出清单

| 原图（upload/） | 交付物 HTML | 交付物 PPTX |
|---|---|---|
| 001-AI方法论.png | 德勤AI落地方法论拆解.html | 德勤AI落地方法论拆解.pptx |
| 002-框架与实施工具.png | 框架与实施工具.html | 框架与实施工具.pptx |
| 003-企业AI落地.png | 企业AI落地_复刻.html | 企业AI落地_复刻.pptx |
| — | AI技术体系对比图.html | AI技术体系对比图.pptx |
| — | LLM推理全流程_图解.html | LLM推理全流程_图解.pptx |

> 全部脚本保留在 `scripts/`（分析、SVG 组件库、组装、patch、PPTX 助手库、生成、校验共 20+ 个），区域放大核对图在 `analysis/`，可完整复盘每一步。
