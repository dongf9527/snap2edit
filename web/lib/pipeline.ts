// web/lib/pipeline.ts —— 服务端专用：spec → 引擎 build → check --json 的共享管线，
// 以及 NDJSON 流式响应（/api/build 与 /api/refine 共用）。
// NDJSON 的意义：① 长任务逐行推送进度，前端可实时渲染；② 持续有字节流动，
// 避免预览网关因长时间无响应而掐断连接（那正是 JSON.parse 报错的根源）。

import fs from "node:fs";
import path from "node:path";
import type { BuildEvent, RenderReport } from "./api";
import { createJob, pptxToPdf, runEngine } from "./engine";
import { validateSpecYaml } from "./spec";

/** check --json 的完整输出（含服务端 artifacts 绝对路径，不应原样下发给客户端） */
export type FullReport = RenderReport & {
  artifacts?: { html: string; pptx: string; shot: string | null };
  report_md?: string;
  report_html?: string | null; // F7 可视化报告（build/report.html 绝对路径）
};

export function ndjsonHeaders(): HeadersInit {
  return {
    "Content-Type": "application/x-ndjson; charset=utf-8",
    "Cache-Control": "no-store",
    "X-Accel-Buffering": "no",
  };
}

/** 把异步 handler 的产物事件包装为 NDJSON Response；任何异常都转成 {type:"error"} 行。 */
export function streamEvents(
  handler: (send: (ev: BuildEvent) => void) => Promise<void>
): Response {
  const enc = new TextEncoder();
  const stream = new ReadableStream<Uint8Array>({
    async start(controller) {
      let closed = false;
      const send = (ev: BuildEvent) => {
        if (closed) return;
        try {
          controller.enqueue(enc.encode(JSON.stringify(ev) + "\n"));
        } catch {
          closed = true;
        }
      };
      try {
        await handler(send);
      } catch (e) {
        send({ type: "error", error: e instanceof Error ? e.message : String(e) });
      } finally {
        closed = true;
        try {
          controller.close();
        } catch {
          /* already closed */
        }
      }
    },
  });
  return new Response(stream, { headers: ndjsonHeaders() });
}

/** 长静默段（VLM 生成）期间周期发送 tick，维持连接活跃并给前端计时。 */
export function startHeartbeat(send: (ev: BuildEvent) => void, intervalMs = 15_000) {
  const t0 = Date.now();
  const t = setInterval(() => {
    send({ type: "tick", s: Math.round((Date.now() - t0) / 1000) });
  }, intervalMs);
  return () => clearInterval(t);
}

/** TS 侧结构预校验（快速失败，避免把明显非法的 spec 交给引擎） */
export function prevalidate(specYaml: string): { ok: false; errors: string[] } | { ok: true } {
  const v = validateSpecYaml(specYaml);
  return v.ok ? { ok: true } : { ok: false, errors: v.errors };
}

/**
 * 在任务目录写入 spec.yaml → 引擎 build → 引擎 check --json。
 * 抛错 = 环境级失败（引擎缺失/崩溃/超时）；校验未通过不算抛错，看 report.ok / report.failures。
 */
export async function buildAndCheck(
  specYaml: string,
  job: { id: string; dir: string }
): Promise<FullReport> {
  fs.writeFileSync(path.join(job.dir, "spec.yaml"), specYaml, "utf-8");
  const b = await runEngine(["build", job.dir], { timeoutMs: 120_000 });
  if (b.code !== 0) {
    const tail = (b.stderr || b.stdout).trim().split("\n").slice(-3).join(" | ").slice(-400);
    throw new Error(`引擎 build 失败（exit ${b.code}）：${tail}`);
  }
  const c = await runEngine(["check", job.dir, "--json"], { timeoutMs: 180_000 });
  let report: FullReport | null = null;
  try {
    report = JSON.parse(c.stdout.trim()) as FullReport;
  } catch {
    report = null;
  }
  if (!report || typeof report.ok !== "boolean") {
    const tail = (c.stderr || c.stdout).trim().slice(-300);
    throw new Error(`check --json 输出无法解析：${tail}`);
  }
  return report;
}

/** 为一次 refine/build 会话创建任务并转换最终 PDF（尽力而为）。 */
export async function finalizePdf(job: { id: string; dir: string }, report: FullReport | null) {
  const pptx = report?.artifacts?.pptx;
  if (!pptx) return false;
  const pdf = await pptxToPdf(pptx, path.join(job.dir, "build"));
  return !!pdf;
}

export { createJob };
