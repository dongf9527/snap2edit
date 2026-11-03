# workbench · 历史过程存档

> Snap2Edit 引擎化之前，六步标准流程以一次性脚本方式执行。本目录按原貌存档这些脚本，
> 是 `src/snap2edit/` 的"考古地层"：引擎中的组件库、坐标公式、校验断言均源于此。

## contents

| 路径 | 说明 |
|---|---|
| `scripts/` | 全部过程脚本（37 个，.py / .js） |
| `diff_heat.png` | 差异热力图样例（16px 块聚合，Step 3 校验方法） |
| `compare_html.png` | 原图 vs 渲染图并排对比样例（Step 3 校验方法） |

## scripts 里的脚本怎么读

| 前缀/文件 | 对应流程步骤 |
|---|---|
| `analyze_*` / `sample*` / `measure_*` / `scan*` / `find_lines` / `blockmap` | Step 1 原图分析（尺寸/取色/布局测量） |
| `crop_*` | Step 1 区域裁剪放大，逐字转录文案 |
| `svg_lib` / `gen_svg_html` / `build_html` / `patch_html*` | Step 2 HTML+SVG 生成与迭代 |
| `shot_html.js` / `render_html` | Step 3 Playwright 截图与并排对比 |
| `diff` / `compare_*` | Step 3 差异热力图 |
| `pptx_lib` / `gen_pptx` / `build_pptx` | Step 4 原生 PPTX 生成 |
| `verify*` / `final_check` | Step 5–6 校验与终检（`verify_deliverables.py` 已演进为引擎的 `verify.py`） |

> 注：执行过程中的几十张裁剪/调试 PNG 未入库（体积大、仅一次性价值），
> 保留的 `diff_heat.png` 与 `compare_html.png` 是校验方法的代表性证据。
> 这些脚本仅供追溯，**不要再在新项目中使用**——请使用 `src/snap2edit/` 引擎。
