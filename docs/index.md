---
title: 首页
description: 一份布局规格，同步产出全可编辑的 HTML+SVG 与原生 PPTX，四道校验门自动把关。
hide:
  - navigation
  - toc
---

# Snap2Edit · 截图复刻引擎

<div class="grid cards" markdown>

-   :material-file-restore:{ .lg .middle } **截图复刻，双产物同源**

    ---

    把一张静态信息图 / 流程图 / 方法论图，还原为两份**完全可编辑**的交付物：
    全真实文本的 HTML+SVG 与 100% 原生形状（Picture = 0）的 PPTX。

    [:octicons-arrow-right-24: 六步标准流程](WORKFLOW.md)

-   :material-file-document-edit:{ .lg .middle } **规格书驱动**

    ---

    一份 YAML spec（坐标 + 色板 + 文案 + 元素）是两条产线的**唯一事实源**，
    改一处、双端同步，从根上消除"双产物漂移"。

    [:octicons-arrow-right-24: 架构文档](ARCHITECTURE.md)

-   :material-check-all:{ .lg .middle } **四道校验门**

    ---

    文案覆盖 / 无位图 / 无嵌入图片 / 文本边界实测防溢出 / 截图非空白，
    全绿才允许交付；`check` 退出码语义化，CI 可直接断言。

    [:octicons-arrow-right-24: 可视化报告](PRD.md#f7-p1)

-   :material-robot:{ .lg .middle } **AI 友好**

    ---

    `check --json` / `loop --json` 输出结构化结果，可嵌入 LLM Agent
    与自动化流水线；`/api/spec` 支持视觉模型直接从原图抽取 spec 草稿。

    [:octicons-arrow-right-24: AI 规格书模型](AI_SPEC_MODEL.md)

</div>

## 五分钟上手

```bash
# 安装（Playwright 为可选依赖：仅第四道"截图门"需要）
pip install snap2edit            # PyPI 发布后
pip install -e ".[verify]"       # 或源码安装 + 截图门

# 四步完成首个产物
snap2edit new my-chart           # 1. 生成规格书模板
vim my-chart/spec.yaml           # 2. 对照原图编写 spec
snap2edit build my-chart         # 3. 一键双渲染 → build/*.html + *.pptx
snap2edit check my-chart         # 4. 四道门校验 → build/report.md + report.html
```

报告全绿即可交付两份文件；任一项失败，退出码非 0，CI 可直接断言。
可选 `--original 原图.png` 启用 16px 块差异热力图比对（收敛辅助）。

## 文档地图

| 文档 | 内容 |
|---|---|
| [PRD · 产品需求文档](PRD.md) | F1–F10 特性清单、D1–D6 设计决策、里程碑与风险 |
| [架构文档（4+1 视图）](ARCHITECTURE.md) | 逻辑 / 过程 / 部署 / 开发视图 + ADR 决策记录 |
| [六步标准流程](WORKFLOW.md) | 原图分析 → HTML → PPTX → 双校验 → 终检的方法论全解 |
| [AI 规格书模型](AI_SPEC_MODEL.md) | 规格书的 AI 可写性设计：约束、示例与提示词策略 |
| [Web 全链路](WEB_PIPELINE.md) | 上传 → 预览 → studio 编辑 → refine 闭环 → 下载 |
| [旋转元素支持](ROTATE.md) | rotate 字段端到端：双产线渲染 + 变换手柄 + VLM 抽取 |
| [协作规则](COLLABORATION.md) | 分支、提交、评审与发布协作约定 |
| [案例库（GitHub）](https://github.com/dongf9527/snap2edit/tree/main/docs) | 七个复刻案例：源图 + 交付物三件套归档（仓库内 `docs/`） |

## 项目状态

| | |
|---|---|
| 当前版本 | **v1.0.0**（PyPI / GitHub Releases） |
| 测试覆盖 | 引擎 100%（分支级），Web 100% |
| 协议 | MIT |
| 里程碑 | v0.1 骨架 ✅ → v0.5 全特性 ✅ → **v1.0 打包发布 ✅** → v2.0 AI 旗舰（规划） |
