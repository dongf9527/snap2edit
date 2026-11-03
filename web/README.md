# Snap2Edit Web（Next.js 基础框架）

Snap2Edit 的 Web UI，对应 PRD F9（v2 路线）。当前已实现首个交互功能
**「上传图片 → 生成 spec」**：上传图表截图，视觉模型抽取布局/坐标/色板/全部文字，
产出可编辑的 `spec.yaml`，下载后交由 Python 引擎双渲染。
技术栈：Next.js 16（App Router）+ React 19 + TypeScript，无额外 UI 框架依赖。

## 启动

```bash
cd web
npm install
npm run dev        # http://localhost:3000
npm run build && npm start   # 生产模式
```

## 「上传图片 → 生成 spec」工作台

```
浏览器上传图片（限尺 ≤2000px / canvas 取色）
  → POST /api/spec（dataURL + meta）
    → 视觉模型抽取规格 JSON（系统提示词约束 schema）
    → normalizeSpec：多行拆分 / 截断回填 / texts 对齐 / id 重编号
    → dumpSpecYaml：双引号风格序列化（规避 PyYAML 1.1 六十进制陷阱）
    → validateSpecYaml：结构校验（失败带错误回询重试一次）
    → 兜底：VLM 不可用时返回骨架模板（mode: skeleton）
  → 页面展示可编辑 YAML，支持复制 / 下载 spec.yaml
```

实测（1280×720 复杂信息图）：一遍通过结构校验，129 元素 / 92 条文字，
spec 直接通过 `snap2edit build` + `snap2edit check` 四道门全绿。

## 模型接入

- 服务端通过 [`z-ai-web-dev-sdk`](https://www.npmjs.com/package/z-ai-web-dev-sdk)
  调用视觉模型（仅限后端）。SDK 从 `.z-ai-config`（项目根 / `~` / `/etc`）读取配置。
- 可用环境变量 `SNAP2EDIT_VISION_MODEL` 覆盖默认视觉模型。
- 未配置 SDK/模型时功能不中断：自动回退骨架模板模式。
- 模型规格选型分析见 [`docs/AI_SPEC_MODEL.md`](../docs/AI_SPEC_MODEL.md)。

## 结构

```
web/
├── app/
│   ├── layout.tsx        # 根布局（zh-CN，元信息）
│   ├── page.tsx          # 首页：工作台 + 流水线 + 案例索引
│   ├── workbench.tsx     # 「上传图片 → 生成 spec」客户端组件
│   ├── globals.css       # 全局样式（无 UI 框架依赖）
│   └── api/spec/route.ts # POST /api/spec：VLM 抽取 → 规范化 → 校验 → 兜底
├── lib/
│   └── spec.ts           # 提示词 / JSON→YAML / 校验器 / 规范化 / 骨架（与引擎同源规则）
├── next.config.ts
├── package.json
└── tsconfig.json
```

## 规划（对接 Python 引擎）

1. `app/api/build/route.ts` —— 触发双渲染，返回 HTML 与 PPTX
2. `app/api/check/route.ts` —— 四道校验门结果 JSON 化
3. `app/studio/` —— 规格书在线编辑器 + 双产物预览

> 引擎侧保持单一事实源：Web 只做编排与展示，渲染逻辑一律复用 `src/snap2edit/`。
