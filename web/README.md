# Snap2Edit Web（Next.js 基础框架）

Snap2Edit 的 Web UI 骨架，对应 PRD F9（v2 路线）。当前为基础程序框架：
Next.js 16（App Router）+ React 19 + TypeScript，无额外 UI 依赖。

## 启动

```bash
cd web
npm install
npm run dev        # http://localhost:3000
npm run build      # 生产构建
```

## 结构

```
web/
├── app/
│   ├── layout.tsx      # 根布局（zh-CN，元信息）
│   ├── page.tsx        # 首页：产品说明 + 流水线 + 案例索引
│   └── globals.css     # 全局样式（无 UI 框架依赖）
├── next.config.ts
├── package.json
└── tsconfig.json
```

## 规划（对接 Python 引擎）

1. `app/api/spec/route.ts` —— 接收/校验 spec.yaml（调用 `snap2edit` CLI 或直接移植校验规则）
2. `app/api/build/route.ts` —— 触发双渲染，返回 HTML 与 PPTX
3. `app/api/check/route.ts` —— 四道校验门结果 JSON 化
4. `app/studio/` —— 规格书在线编辑器 + 双产物预览

> 引擎侧保持单一事实源：Web 只做编排与展示，渲染逻辑一律复用 `src/snap2edit/`。
