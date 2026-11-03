// web/app/api/refine/route.ts —— POST /api/refine
// 渲染报告自动回询迭代（PRD 四道校验门的闭环化）：
//   build → check --json → 未通过？→ 把报告 failures 回询 VLM 修正 spec → 重建重检
//   循环 maxRounds 轮（默认 2），全程 NDJSON 流式推送 round/report/spec/tick 事件。
// 输入 { image?(dataURL), meta?, spec(YAML), maxRounds? }：
//   - 附原图（工作台/studio 均可）：失败项 + 原图视觉比对修正；
//   - 无原图（studio 可视化编辑入口）：仅按报告失败项纯文本修正。

import { NextRequest, NextResponse } from "next/server";
import { parse as yamlParse } from "yaml";
import {
  buildFixPrompt,
  buildSystemPrompt,
  buildUserPrompt,
  dumpSpecYaml,
  MAX_IMAGE_CHARS,
  normalizeImageMeta,
  normalizeSpec,
  parseSpecJson,
  validateSpecYaml,
} from "@/lib/spec";
import {
  buildAndCheck,
  createJob,
  finalizePdf,
  prevalidate,
  startHeartbeat,
  streamEvents,
  type FullReport,
} from "@/lib/pipeline";
import { getVLM } from "@/lib/vlm";

export const runtime = "nodejs";
export const maxDuration = 600;

export async function POST(req: NextRequest) {
  let body: { image?: unknown; meta?: unknown; spec?: unknown; maxRounds?: unknown };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ ok: false, error: "请求体必须是 JSON" }, { status: 400 });
  }

  const image = typeof body.image === "string" ? body.image : "";
  if (image && !image.startsWith("data:image/")) {
    return NextResponse.json(
      { ok: false, error: "image 必须是 data:image/ 开头的 dataURL；无原图时可省略该字段（按报告纯文本修正）" },
      { status: 400 }
    );
  }
  if (image.length > MAX_IMAGE_CHARS) {
    return NextResponse.json({ ok: false, error: "图片过大（原始字节 > 8MB）" }, { status: 413 });
  }
  const meta = normalizeImageMeta(body.meta);
  if (image && (!meta.width || !meta.height)) {
    return NextResponse.json({ ok: false, error: "附原图时 meta.width / meta.height 缺失" }, { status: 400 });
  }
  const spec0 = typeof body.spec === "string" ? body.spec : "";
  if (!spec0.trim()) {
    return NextResponse.json({ ok: false, error: "缺少 spec（YAML 文本）" }, { status: 400 });
  }
  const pv = prevalidate(spec0);
  if (!pv.ok) {
    return NextResponse.json(
      { ok: false, error: `spec 未通过结构预校验：${pv.errors.slice(0, 4).join("；")}` },
      { status: 400 }
    );
  }
  const maxRounds = Math.min(3, Math.max(1, Number(body.maxRounds) || 2));

  const started = Date.now();
  return streamEvents(async (send) => {
    const warnings: string[] = [];
    const job = createJob();
    let curYaml = spec0;
    let lastReport: FullReport | null = null;
    let fixedRounds = 0;

    for (let attempt = 0; attempt <= maxRounds; attempt++) {
      const n = attempt + 1;
      send({
        type: "round",
        n,
        phase: "build",
        note: attempt === 0 ? "构建当前 spec" : "构建修正后的 spec",
      });
      send({ type: "log", msg: `第 ${n} 次构建：引擎 build + 四道校验门…` });

      let failures: string[];
      let okNow = false;
      try {
        lastReport = await buildAndCheck(curYaml, job);
        failures = lastReport.failures;
        okNow = lastReport.ok;
        send({ type: "report", n, report: lastReport });
        send({
          type: "log",
          msg: `第 ${n} 次构建校验：${okNow ? "✓ 全部通过" : `✗ ${failures.length} 项未通过`}`,
        });
      } catch (e) {
        // 环境级失败（引擎报错）：把错误也交给 VLM 修正
        failures = [`引擎构建失败：${e instanceof Error ? e.message : String(e)}`];
        okNow = false;
        send({ type: "log", msg: `第 ${n} 次构建失败：${failures[0]}` });
      }

      if (okNow) break;
      if (attempt === maxRounds) break; // 轮次用尽

      // —— VLM 回询修正 ——
      send({ type: "round", n, phase: "vlm", note: `${failures.length} 项错误回询修正` });
      let vlm;
      try {
        vlm = await getVLM();
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        warnings.push(`VLM 不可用，无法自动修正：${msg}`);
        send({ type: "log", msg: `VLM 不可用，终止迭代（保留当前最优 spec）：${msg}` });
        break;
      }

      const stopBeat = startHeartbeat(send);
      try {
        // 当前 spec 转 JSON 作为模型上下文
        const curJson = yamlToJson(curYaml);
        // 附原图：四段式（系统 + 原图抽取 + 已产 spec + 失败项修正）；
        // 无原图（studio 可视化编辑入口）：三段式纯文本修正
        const messages = image
          ? [
              { role: "system", content: buildSystemPrompt() },
              {
                role: "user",
                content: [
                  { type: "text", text: buildUserPrompt(meta) },
                  { type: "image_url", image_url: { url: image } },
                ],
              },
              { role: "assistant", content: JSON.stringify(curJson) },
              { role: "user", content: buildFixPrompt(failures, curYaml) },
            ]
          : [
              { role: "system", content: buildSystemPrompt() },
              {
                role: "user",
                content: `我在可视化编辑器中维护以下 spec JSON（未经图片抽取）：\n${JSON.stringify(curJson)}`,
              },
              { role: "user", content: buildFixPrompt(failures, curYaml) },
            ];
        const resp = await vlm.callVision(messages);
        const content = vlm.contentOf(resp);
        if (!content.trim()) throw new Error("VLM 返回为空");
        if (vlm.finishOf(resp) === "length") {
          warnings.push(`第 ${n} 轮修正输出因 token 上限被截断`);
        }
        const p = parseSpecJson(content);
        if (!p.ok) throw new Error(p.error);
        const { spec: norm } = normalizeSpec(p.spec);
        const yamlText = dumpSpecYaml(norm);
        const v = validateSpecYaml(yamlText);
        if (!v.ok) {
          throw new Error(`修正结果未通过结构校验：${v.errors.slice(0, 3).join("；")}`);
        }
        curYaml = v.fixedYaml ?? yamlText;
        fixedRounds += 1;
        send({ type: "spec", n, spec: curYaml });
        send({ type: "log", msg: `第 ${n} 轮修正完成，开始重建验证…` });
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        warnings.push(`第 ${n} 轮自动修正失败：${msg}（保留上一版 spec 继续）`);
        send({ type: "log", msg: `第 ${n} 轮修正失败：${msg}（保留上一版继续）` });
      } finally {
        stopBeat();
      }
    }

    // 最终产物转 PDF（预览用）
    send({ type: "log", msg: "转换最终 PPTX → PDF（在线预览用）…" });
    const hasPdf = await finalizePdf(job, lastReport);

    send({
      type: "done",
      jobId: job.id,
      project: lastReport?.project ?? "output",
      ok: !!lastReport?.ok,
      hasPdf,
      rounds: fixedRounds,
      spec: curYaml,
      warnings,
      elapsedMs: Date.now() - started,
    });
  });
}

/** YAML 文本 → JSON 对象（给 VLM 的上下文）；解析失败抛错由上层兜底 */
function yamlToJson(yamlText: string): unknown {
  return yamlParse(yamlText);
}
