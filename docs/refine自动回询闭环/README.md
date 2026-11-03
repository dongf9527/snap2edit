# refine 自动回询闭环 · 端到端实测案例

本案例归档 Snap2Edit 在线管线「渲染报告自动回询迭代」的一次**完整实测证据**：
初始 spec 注入一处缺陷 → 引擎四道门第 1 轮拦截 → 报告 failures 自动回询视觉模型修正 →
第 2 轮重建全绿。对应 `POST /api/refine`（NDJSON 流式），架构见
[`WEB_PIPELINE.md`](../WEB_PIPELINE.md)。

## 实测信息

| 项 | 值 |
|---|---|
| 日期 | 2026-11-03 |
| 源图 | `源图_900px.jpg`（德勤AI落地方法论，900×506，视觉模型实际所见） |
| 视觉模型 | glm-5.3-flash（`z-ai-web-dev-sdk`，SNAP2EDIT_VISION_MODEL 可覆盖） |
| 初始 spec | `spec_v1_含缺陷.yaml`（AI 抽取版 + 人为注入 1 条缺陷） |
| 缺陷注入 | texts 清单追加文案「这条文案在渲染中不存在，必须新增一个text元素」 |
| 迭代轮次 | maxRounds=2（实际用 1 轮修正即通过） |
| 总耗时 | 43.9s（含 2 次构建 + 1 次 VLM 修正） |

## 闭环过程

```
第 1 次构建（spec_v1_含缺陷.yaml）
  门1 文案清单 ✗（渲染中不存在该文案）→ 详情见 校验报告_第1轮_未通过.md
    ↓ failures 自动回询 VLM（附原图 + 当前 spec + 错误清单）
第 1 轮修正完成（spec_v2_修正后.yaml，14788 字符）
    ↓
第 2 次构建 → 四道门全部通过 ✓（校验报告_第2轮_通过.md）
    ↓
PPTX → PDF 转换 → done（rounds=1, hasPdf=True）
```

## 文件清单

| 文件 | 说明 |
|---|---|
| `源图_900px.jpg` | 视觉模型实际看到的源图 |
| `spec_v1_含缺陷.yaml` | 初始 spec（texts 含 1 条渲染中不存在的文案） |
| `校验报告_第1轮_未通过.md` | 第 1 轮四道门报告：门1/门2 文案清单拦截 |
| `spec_v2_修正后.yaml` | VLM 回询修正后的 spec（新增对应 text 元素并同步 texts） |
| `校验报告_第2轮_通过.md` | 第 2 轮四道门报告：全部通过 |
| `德勤AI落地方法论.html` | 交付物①：全真实文本 HTML+SVG |
| `德勤AI落地方法论.pptx` | 交付物②：原生形状 PPTX（Picture = 0） |
| `预览_PPT转PDF.pdf` | PPTX 的 PDF 预览件（LibreOffice 转换） |
| `shot.png` | 门4 Playwright 渲染截图 |
| `事件时间线.txt` | NDJSON 事件流逐条记录（round/report/log/done） |

## 结论

- 修复行为符合预期：VLM 未简单删除清单项，而是**新增了对应 text 元素并同步 texts 清单**，
  使门1文案清单与渲染内容重新一致——这正是回询修正希望模型学到的方式。
- 四道门作为「事实源裁判」的角色成立：任何 spec 与渲染结果的不一致都会被拦截，
  并以结构化 failures 的形式驱动下一轮修正。
