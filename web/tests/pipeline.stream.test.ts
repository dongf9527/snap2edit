// web/tests/pipeline.stream.test.ts —— lib/pipeline.ts 单测：NDJSON 流 / 心跳 / 预校验 /
// buildAndCheck（假引擎 CLI 密闭）/ finalizePdf。
// 脚本一律 #!/bin/sh + POSIX（PATH 受限时 #!/usr/bin/env bash 会 127）。
// 运行：cd web && node --test tests/pipeline.stream.test.ts
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { randomUUID } from "node:crypto";
import {
  buildAndCheck,
  finalizePdf,
  ndjsonHeaders,
  prevalidate,
  startHeartbeat,
  streamEvents,
  type FullReport,
} from "../lib/pipeline.ts";
import { createJob } from "../lib/engine.ts";
import type { BuildEvent } from "../lib/api.ts";

const REAL_PATH = process.env.PATH ?? "";

const OK_REPORT = JSON.stringify({ ok: true, project: "假项目", gates: [], failures: [] });

/** 假引擎 CLI：build 按 S2E_BUILD_EXIT 退出；check 输出 S2E_CHECK_OUT（默认合法报告）。 */
const BIN = path.join(os.tmpdir(), `s2e-bin-${randomUUID()}`);
fs.mkdirSync(BIN, { recursive: true });
fs.writeFileSync(
  path.join(BIN, "snap2edit"),
  "#!/bin/sh\n" +
    'if [ "$1" = "build" ]; then echo "build-err" >&2; exit "${S2E_BUILD_EXIT:-0}"; fi\n' +
    'if [ "$1" = "check" ]; then printf "%s" "$S2E_CHECK_OUT"; exit 0; fi\n' +
    'echo "snap2edit fake"; exit 0\n',
  { mode: 0o755 }
);
process.env.PATH = `${BIN}${path.delimiter}${REAL_PATH}`;
process.env.S2E_CHECK_OUT = OK_REPORT;

test.after(() => {
  process.env.PATH = REAL_PATH;
  delete process.env.S2E_BUILD_EXIT;
  delete process.env.S2E_CHECK_OUT;
});

const GOOD_YAML = [
  "project: 单元测试",
  "canvas: { width: 1280, height: 720 }",
  'palette: { primary: "#1F2937", accent: "#2B6CB0", card: "#FFFFFF", bg: "#FFFFFF" }',
  'texts: ["文案A"]',
  "elements:",
  "  - { id: e1, type: rect, x: 0, y: 0, w: 10, h: 10 }",
].join("\n");

/* ---------- ndjsonHeaders / streamEvents ---------- */

test("ndjsonHeaders：NDJSON + no-store + 网关禁缓冲三件套", () => {
  const h = ndjsonHeaders() as Record<string, string>;
  assert.match(h["Content-Type"], /x-ndjson/);
  assert.equal(h["Cache-Control"], "no-store");
  assert.equal(h["X-Accel-Buffering"], "no");
});

test("streamEvents：handler 正常推送 → 逐行 NDJSON 可解析还原", async () => {
  const res = streamEvents(async (send) => {
    send({ type: "log", msg: "第 1 步" });
    send({ type: "log", msg: "第 2 步" });
  });
  const lines = (await res.text()).trim().split("\n").map((l) => JSON.parse(l) as BuildEvent);
  assert.equal(lines.length, 2);
  assert.equal(lines[0].type, "log");
});

test("streamEvents：handler 抛错 → 转为 {type:error} 行（不 5xx）", async () => {
  const res = streamEvents(async () => {
    throw new Error("boom-xyz");
  });
  const last = (await res.text()).trim().split("\n").pop()!;
  const ev = JSON.parse(last) as BuildEvent;
  assert.equal(ev.type, "error");
  assert.match((ev as { error: string }).error, /boom-xyz/);
});

test("streamEvents：消费端提前 cancel → 后续 send 静默丢弃（closed 分支）", async () => {
  const res = streamEvents(async (send) => {
    send({ type: "log", msg: "before" });
    await new Promise((r) => setTimeout(r, 30));
    send({ type: "log", msg: "after-cancel" }); // 流已取消 → enqueue 抛错 → closed
    await new Promise((r) => setTimeout(r, 20));
    send({ type: "log", msg: "after-closed" }); // closed=true → 直接 return
  });
  const reader = res.body!.getReader();
  const first = await reader.read();
  assert.ok(first.value && new TextDecoder().decode(first.value).includes("before"));
  await reader.cancel();
  await new Promise((r) => setTimeout(r, 90)); // 两个 late-send 窗口，不应抛未处理异常
  assert.ok(true);
});

/* ---------- startHeartbeat ---------- */

test("startHeartbeat：按周期发 tick（s 为秒数），stop 后停止", async () => {
  const evs: BuildEvent[] = [];
  const stop = startHeartbeat((e) => evs.push(e), 20);
  await new Promise((r) => setTimeout(r, 90));
  stop();
  const n = evs.length;
  assert.ok(n >= 2, `90ms 内至少 2 个 tick，实际 ${n}`);
  const first = evs[0] as { type: "tick"; s: number };
  assert.equal(first.type, "tick");
  assert.ok(first.s >= 0);
  await new Promise((r) => setTimeout(r, 80));
  assert.equal(evs.length, n, "stop 后不应再有 tick");
});

/* ---------- prevalidate ---------- */

test("prevalidate：合法 spec → {ok:true}；非法 → {ok:false, errors 继承}", () => {
  assert.deepEqual(prevalidate(GOOD_YAML), { ok: true });
  const bad = prevalidate("a: [1, 2");
  assert.ok(!bad.ok && bad.errors.length >= 1);
});

/* ---------- buildAndCheck（假引擎 CLI）---------- */

test("buildAndCheck：build+check 双成功 → 解析出结构化报告；spec.yaml 已落盘", async () => {
  const job = createJob();
  const report = await buildAndCheck(GOOD_YAML, job);
  assert.equal(report.ok, true);
  assert.equal(report.project, "假项目");
  assert.ok(fs.existsSync(path.join(job.dir, "spec.yaml")));
  fs.rmSync(job.dir, { recursive: true, force: true });
});

test("buildAndCheck：build 失败（exit≠0）→ 抛错并带 stderr 尾部摘要", async () => {
  process.env.S2E_BUILD_EXIT = "3";
  try {
    const job = createJob();
    await assert.rejects(
      () => buildAndCheck(GOOD_YAML, job),
      /引擎 build 失败（exit 3）.*build-err/s
    );
    fs.rmSync(job.dir, { recursive: true, force: true });
  } finally {
    delete process.env.S2E_BUILD_EXIT;
  }
});

test("buildAndCheck：check 输出非 JSON → 抛「无法解析」", async () => {
  process.env.S2E_CHECK_OUT = "definitely-not-json";
  try {
    const job = createJob();
    await assert.rejects(() => buildAndCheck(GOOD_YAML, job), /check --json 输出无法解析/);
    fs.rmSync(job.dir, { recursive: true, force: true });
  } finally {
    process.env.S2E_CHECK_OUT = OK_REPORT;
  }
});

test("buildAndCheck：JSON 合法但缺 ok 字段 → 同样判为无法解析（结构守卫分支）", async () => {
  process.env.S2E_CHECK_OUT = '{"x":1}';
  try {
    const job = createJob();
    await assert.rejects(() => buildAndCheck(GOOD_YAML, job), /无法解析/);
    fs.rmSync(job.dir, { recursive: true, force: true });
  } finally {
    process.env.S2E_CHECK_OUT = OK_REPORT;
  }
});

/* ---------- finalizePdf ---------- */

test("finalizePdf：无报告 / 无 pptx 产物 → false（短路分支）", async () => {
  const job = createJob();
  assert.equal(await finalizePdf(job, null), false);
  assert.equal(await finalizePdf(job, { ok: true, project: "t", gates: [], failures: [] }), false);
  fs.rmSync(job.dir, { recursive: true, force: true });
});

test("finalizePdf：有 pptx 产物且 soffice 转换成功 → true（!!pdf 分支）", async () => {
  fs.writeFileSync(path.join(BIN, "soffice"),
    "#!/bin/sh\n" +
    'outdir=""; prev=""; last=""\n' +
    'for a in "$@"; do if [ "$prev" = "--outdir" ]; then outdir="$a"; fi; last="$a"; prev="$a"; done\n' +
    'base="$(basename "$last" .pptx)"\n' +
    'printf "%%PDF-fake" > "$outdir/$base.pdf"\n' +
    "exit 0\n", { mode: 0o755 });
  try {
    const job = createJob();
    const pptx = path.join(job.dir, "build", "t.pptx");
    fs.mkdirSync(path.dirname(pptx), { recursive: true });
    fs.writeFileSync(pptx, "PK-fake");
    const ok = await finalizePdf(job, {
      ok: true, project: "t", gates: [], failures: [],
      artifacts: { html: "", pptx, shot: null },
    });
    assert.equal(ok, true);
    fs.rmSync(job.dir, { recursive: true, force: true });
  } finally {
    fs.rmSync(path.join(BIN, "soffice"), { force: true });
  }
});
