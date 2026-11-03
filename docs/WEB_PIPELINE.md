# WEB_PIPELINE · 在线管线：双产物预览与自动回询迭代

本文档记录 v0.3.0 在线管线的架构设计、JSON.parse 报错的根因分析与修复、
以及端到端实测证据（2026-11-03，沙箱实测）。

## 1 · 在线管线总览

```
浏览器                                      Next.js 服务端                     Python 引擎
──────                                      ────────────                     ───────────
上传图片 ──────────────▶ POST /api/spec ───▶ 视觉模型抽取 ──────────────────▶ （无需引擎）
                            │                  normalizeSpec/dumpYaml/校验
        可编辑 spec.yaml ◀──┘
                            │
「构建并校验」──────▶ POST /api/build ─────▶ 写任务目录 ───────────────────▶ snap2edit build
                            │                snap2edit check --json ◀──── 四道门结构化报告
                            │                PPTX → PDF（soffice）
        NDJSON 事件流 ◀─────┘（log/report/done）
                            │
「自动回询迭代」────▶ POST /api/refine ────▶ 循环 maxRounds 轮：
                            │                  build → check → ok? 终止
                            │                  └ 否：failures 回询 VLM 修正 spec
        NDJSON 事件流 ◀─────┘                  → 重建复检
                            │
预览/下载 ──────────▶ GET /api/artifacts/<jobId>/<file>
                            HTML（iframe 预览）/ PDF（PPTX 转换件）/ PPTX（下载）
                            shot.png / report.md
```

任务目录：`/tmp/snap2edit-jobs/<uuid>/`（spec.yaml + build/ 产物），重启即清空，
正式沉淀仍走仓库 `docs/<案例>/` 归档（协作规则：以仓库为准）。

## 2 · JSON.parse 报错：根因与三层根治

**现象**：沙箱中生成 spec.yaml 时浏览器抛
`JSON.parse: unexpected character at line 1 column 1 of the JSON data`。

**根因**：旧版前端 `workbench.tsx` 直接 `await res.json()`。预览网关在长请求
（视觉模型 30–150s）下可能返回 HTML/纯文本错误页（502/504 页面、重启提示等），
响应首字符是 `<` 或空体，`JSON.parse` 在第 1 列即失败——报错信息完全掩盖了真实原因。

**三层根治**：

| 层 | 措施 | 位置 |
|---|---|---|
| 服务端 | handler 全量 try/catch；所有分支（400/404/413/500）只回 `NextResponse.json()`；引擎缺失/崩溃/超时给中文可读错误 | `app/api/*/route.ts` |
| 协议 | 长任务一律 NDJSON 流式（`application/x-ndjson`），字节持续流动 + 15s `tick` 心跳，网关无静默期可掐 | `lib/pipeline.ts` |
| 客户端 | `readApiJson()` 先查 Content-Type 再 parse，非 JSON 转可读错误；`streamApi()` 逐行解析，混入的非 JSON 行忽略 | `lib/api.ts` |

**错误注入实测**（修复后）：

```
POST /api/spec  body=not-json           → 400 {"ok":false,"error":"请求体必须是 JSON"}
POST /api/build body={"spec":""}        → 400 {"ok":false,"error":"缺少 spec（YAML 文本）"}
POST /api/build 非法 spec（elements:[]） → 400 {"ok":false,"error":"spec 未通过结构预校验：…"}
GET  /api/artifacts/../etc/html         → 404（路径穿越拦截）
GET  /api/artifacts/00000000-…/html     → 404（{"ok":false,"error":"产物不存在…"}）
```

## 3 · 引擎配套改造（单一事实源）

- `verify.collect_checks()`：四道门结构化报告
  `{ok, project, gates[{gate,title,items[{label,passed,detail}]}], failures[], artifacts, report_md}`
  —— CLI 文本报告与 web API 同源；`run_checks()` 变为薄包装。
- `snap2edit check <dir> --json`：stdout 输出上述 JSON（退出码 0/2）。
- `spec.safe_project()`：项目名消毒（空格/斜杠/特殊字符 → `_`，保留中文，≤60 字符），
  杜绝 VLM 产出的 project 名炸出非法文件路径。
- `spec.norm_color()`：颜色规范化（`#RGB/#RRGGBB/#RRGGBBAA` 统一、缺 `#` 补全、
  `none/transparent` → 透明），非法值报**可读 SpecError**——该错误会进入 refine 的
  failures 回询给视觉模型，形成自动修正信号。
- 新增 `circle` 元素类型（HTML 椭圆 / PPTX OVAL 双渲染）；fill=`none` 双产线一致的透明语义。

## 4 · 端到端实测记录（2026-11-03）

环境：沙箱生产构建（`next build` + `next start -p 3210`），真实图片
`upload/001-AI方法论.png`（缩至 900px / JPEG 156KB）。

| # | 场景 | 结果 |
|---|---|---|
| 1 | `POST /api/spec` 真图抽取 | ✓ mode=vlm（glm-5.3-flash），48.8s，118 元素 / 78 文本，零告警 |
| 2 | `POST /api/build`（demo spec） | ✓ NDJSON 四门全绿，PPTX→PDF 成功，3.8s |
| 3 | `POST /api/refine`（好 spec） | ✓ 快路径：首过即终，rounds=0，3.9s |
| 4 | `POST /api/refine`（注入缺陷 spec：texts 多一条渲染中不存在的文案） | ✓ 完整闭环：第 1 次构建门1 挂（文案缺失）→ VLM 回询修正（60s，tick 心跳保活）→ 第 2 次构建全绿 → done rounds=1，总 67.5s |
| 5 | 产物服务 5 种产物 | ✓ html/pptx/pdf/shot.png/report.md 全 200，MIME 正确，`?dl=1` 下载形态生效 |
| 6 | 安全与容错 | ✓ 穿越/假 id/未知 kind 均 404 JSON；API 错误路径全部 JSON |
| 7 | UI 渲染 | ✓ 工作台三区块（上传/spec 编辑/构建预览+迭代）+ 修正轮次选择器渲染正常 |

## 5 · 已知边界

- 任务产物在服务端临时目录，服务重启后 404（前端有可读提示），属预期设计。
- LibreOffice 缺失时 PDF 页签禁用（PDX 下载 PPTX 不受影响）；门4 截图依赖
  Playwright，缺失时该项跳过不阻断其余三门。
- refine 的 VLM 修正为「整图重抽取 + 错误清单反馈」而非增量 patch：修正质量依赖
  模型能力，最多 maxRounds 轮，超限保留当前最优 spec 并附 warnings。
