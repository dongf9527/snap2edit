# Snap2Edit Web（Next.js）

Snap2Edit 的 Web UI，对应 PRD F9（v2 路线）。已实现从截图到可编辑双产物的**全链路在线工作台**：
上传图片 → 视觉模型生成 `spec.yaml` → 一键调用 Python 引擎双渲染 → 在线预览 HTML+SVG 与
PPTX（PDF 形态）→ 校验未通过时自动把渲染报告回询视觉模型迭代修正；
另附 **spec 可视化编辑器（/studio）**：画布点选/拖拽/改属性，YAML 实时双向同步。
技术栈：Next.js 16（App Router）+ React 19 + TypeScript，无额外 UI 框架依赖。

## 启动

```bash
cd web
npm install
npm run dev                  # http://localhost:3000
npm run build && npm start   # 生产模式
```

前置：引擎需可被服务端解析（优先 `snap2edit` CLI，其次 `python3 -m snap2edit.cli`，
仓库根执行 `pip install -e .` 即可）；PPTX→PDF 预览依赖 `soffice`（LibreOffice），
缺失时 PDF 页签自动禁用，不影响下载 PPTX。

## 全链路工作台

```
浏览器上传图片（限尺 ≤2000px / canvas 取色）
  → POST /api/spec（dataURL + meta）
      视觉模型抽取规格 JSON → normalizeSpec → dumpSpecYaml → validateSpecYaml
      （失败带错误回询重试一次；VLM 不可用回退骨架模板 mode:skeleton）
  → 页面展示可编辑 YAML，支持复制 / 下载
  → POST /api/build { spec }                       （NDJSON 流式）
      写任务目录 → snap2edit build → snap2edit check --json → PPTX 转 PDF
  → GET /api/artifacts/<jobId>/<html|pptx|pdf|shot.png|report.md>
      HTML iframe 在线预览 / PDF 预览 / 下载
  → POST /api/refine { image, meta, spec, maxRounds }   （NDJSON 流式）
      build → check → 未通过则把报告 failures 回询 VLM 修正 spec → 重建复检
      循环 maxRounds 轮，全程推送 round/report/spec/tick 事件
```

## spec 可视化编辑器（/studio）

```
入口：首页「打开可视化编辑器」/ 工作台「在可视化编辑器中打开 →」（sessionStorage 交接 spec）
布局：元素列表（选中/增删/上下移）｜SVG 画布（点选·拖拽·方向键微调·Delete 删除）｜属性面板
同步：YAML 源码是唯一事实源 —— 属性编辑 → 重新序列化；源码编辑 → 画布重渲
画布：web/lib/canvas.ts 与引擎 svgout.py 同语义（坐标/圆角/基线/箭头三角），预览 ≈ 产物
安全网：结构校验实时提示；texts 清单自动同步 + 一键从元素重建（保证门1可过）
出口：构建并预览（复用 /api/build，四道门 + iframe + 下载）/ 复制 / 下载 spec.yaml / 浏览器草稿
```

> 正式产物永远由 Python 引擎输出（单一事实源）；studio 只做编辑与预览，不做第二套渲染逻辑。

## API 一览

| 路由 | 方法 | 输入 | 输出 | 说明 |
|---|---|---|---|---|
| `/api/spec` | POST | `{ image: dataURL, meta }` | JSON `SpecResult` | 视觉模型抽取规格（失败骨架兜底） |
| `/api/build` | POST | `{ spec: YAML }` | NDJSON 事件流 | 双渲染 + 四道门 + PPTX→PDF |
| `/api/refine` | POST | `{ image, meta, spec, maxRounds? }` | NDJSON 事件流 | 自动回询迭代闭环 |
| `/api/artifacts/<id>/<file>` | GET | UUID + `html/pptx/pdf/shot.png/report.md` | 文件（MIME 正确） | 产物服务；`?dl=1` 强制下载 |

NDJSON 事件类型：`log`（过程日志）/ `tick`（长静默保活心跳）/ `round`（迭代轮次与阶段）/
`report`（引擎 `check --json` 结构化四道门报告）/ `spec`（修正后的 spec 文本）/
`done`（jobId、ok、hasPdf、rounds、spec、warnings、elapsedMs）/ `error`（任何异常）。
**约定：所有路由的所有分支（含 400/404/413/500）只返回 JSON，绝不返回 HTML/纯文本错误页。**

## 健壮性设计（JSON.parse 报错的根治）

预览网关在长请求（VLM 30–150s）下可能掐断连接并返回 HTML 错误页；旧版前端直接
`res.json()`，HTML 首字符 `<` 即抛出难以理解的
`JSON.parse: unexpected character at line 1 column 1 of the JSON data`。三层根治：

1. **服务端**：每个 handler 全量 try/catch，任何未预期异常都转 `NextResponse.json()`；
   引擎缺失/崩溃/超时给出中文可读错误。
2. **协议**：长任务一律 NDJSON 流式（`application/x-ndjson`），边跑边有字节流动，
   期间周期发送 `tick` 心跳，避免网关因静默掐断连接。
3. **客户端**：`readApiJson()` 先查 Content-Type 再解析，非 JSON 一律转为可读错误；
   `streamApi()` 逐行解析事件，混入的非 JSON 行（代理注入提示等）直接忽略。

## 结构

```
web/
├── app/
│   ├── layout.tsx              # 根布局（zh-CN，元信息）
│   ├── page.tsx                # 首页：工作台 + 流水线 + 案例索引
│   ├── workbench.tsx           # 全链路工作台客户端组件
│   ├── globals.css             # 全局样式（无 UI 框架依赖）
│   ├── studio/
│   │   ├── page.tsx            # /studio 可视化编辑器路由
│   │   └── editor.tsx          # 编辑器客户端组件（列表/画布/属性/YAML/构建）
│   └── api/
│       ├── spec/route.ts       # POST /api/spec：VLM 抽取 → 校验 → 兜底
│       ├── build/route.ts      # POST /api/build：双渲染 + 四道门（NDJSON）
│       ├── refine/route.ts     # POST /api/refine：自动回询迭代（NDJSON）
│       └── artifacts/[id]/[file]/route.ts  # GET 产物服务（双白名单防穿越）
├── lib/
│   ├── spec.ts                 # 提示词 / JSON→YAML / 校验器 / 骨架（与引擎同源规则）
│   ├── canvas.ts               # 客户端 SVG 画布渲染（svgout.py 的 TS 镜像）
│   ├── api.ts                  # 浏览器侧 fetch 辅助 + 事件/报告类型
│   ├── engine.ts               # 服务端：引擎子进程 / 任务目录 / 产物解析 / PPTX→PDF
│   ├── pipeline.ts             # 服务端：build+check 管线 / NDJSON 流式包装
│   └── vlm.ts                  # 服务端：视觉模型客户端（按需动态导入）
├── next.config.ts
├── package.json
└── tsconfig.json
```

> 引擎侧保持单一事实源：Web 只做编排与展示，渲染与校验逻辑一律复用 `src/snap2edit/`；
> 四道门结构化报告由引擎 `snap2edit check <dir> --json`（`verify.collect_checks`）输出。
> 架构细节与端到端实测记录见 [`docs/WEB_PIPELINE.md`](../docs/WEB_PIPELINE.md)。
