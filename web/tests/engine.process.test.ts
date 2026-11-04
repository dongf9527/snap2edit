// web/tests/engine.process.test.ts —— lib/engine.ts 子进程/任务目录/PDF 转换单测
// 密闭策略：单一生成 bin 目录注入 PATH，脚本一律 #!/bin/sh + POSIX 语法
// （env 在 PATH 受限时找不到 bash，#!/usr/bin/env bash 会 127）。
// 运行：cd web && node --test tests/engine.process.test.ts
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { randomUUID } from "node:crypto";
import { createJob, JOBS_ROOT, pptxToPdf, resolveArtifact, resolveEngine, runEngine } from "../lib/engine.ts";

const REAL_PATH = process.env.PATH ?? "";

/** 单一 bin 目录：所有假可执行文件集中于此，PATH 只指向它也能跑。 */
function sh(dir: string, name: string, body: string): string {
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, name), `#!/bin/sh\n${body}\n`, { mode: 0o755 });
  return path.join(dir, name);
}

const BIN = path.join(os.tmpdir(), `s2e-bin-${randomUUID()}`);
fs.mkdirSync(BIN, { recursive: true });
// 前置而非替换：假 CLI 仍处查找序首位，同时保留 basename/sleep 等外置命令可用
const FAKE_PATH = `${BIN}${path.delimiter}${REAL_PATH}`;
process.env.PATH = FAKE_PATH;

// 假引擎 CLI：--version 立即回显（探测用）；sleep 参数睡 5s（超时用）
sh(BIN, "snap2edit",
  'echo "warn-line" >&2\n' +
  'if [ "$1" = "sleep" ]; then sleep 5; fi\n' +
  'echo "snap2edit fake $1"\nexit 0');

test.after(() => {
  process.env.PATH = REAL_PATH;
});

/* ---------- resolveEngine / runEngine ---------- */

test("resolveEngine：PATH 中的假 snap2edit CLI 被探测命中并缓存", async () => {
  const eng = await resolveEngine();
  assert.ok(eng, "应解析到假 CLI");
  assert.ok(eng.cmd.endsWith("snap2edit"), `实际 ${eng.cmd}`);
  assert.deepEqual(eng.base, []);
});

test("runEngine：子进程 code/stdout/stderr 全量回传", async () => {
  const r = await runEngine(["--version"]);
  assert.equal(r.code, 0);
  assert.match(r.stdout, /snap2edit fake/);
  assert.match(r.stderr, /warn-line/);
});

test("runEngine：超时 → SIGKILL 并 reject 可读超时错误", async () => {
  await assert.rejects(() => runEngine(["sleep"], { timeoutMs: 300 }), /引擎执行超时/);
});

/* ---------- createJob / resolveArtifact ---------- */

test("createJob：UUID 目录创建于 JOBS_ROOT 下", () => {
  const job = createJob();
  assert.match(job.id, /^[0-9a-f-]{36}$/);
  assert.ok(fs.existsSync(job.dir));
  fs.rmSync(job.dir, { recursive: true, force: true });
});

test("resolveArtifact：build 目录不存在 → catch 分支返回 null（不抛错）", () => {
  assert.equal(resolveArtifact(randomUUID(), "html"), null);
});

test("resolveArtifact：目录存在但无该 kind 文件 → null（hit 为空分支）", () => {
  const id = randomUUID();
  fs.mkdirSync(path.join(JOBS_ROOT, id, "build"), { recursive: true });
  fs.writeFileSync(path.join(JOBS_ROOT, id, "build", "readme.txt"), "x");
  assert.equal(resolveArtifact(id, "pdf"), null);
  fs.rmSync(path.join(JOBS_ROOT, id), { recursive: true, force: true });
});

/* ---------- pptxToPdf（假 soffice，S2E_SOFFICE_MODE 切换行为） ---------- */

const SOFFICE = sh(BIN, "soffice",
  'mode="${S2E_SOFFICE_MODE:-make}"\n' +
  'outdir=""; prev=""; last=""\n' +
  'for a in "$@"; do if [ "$prev" = "--outdir" ]; then outdir="$a"; fi; last="$a"; prev="$a"; done\n' +
  'base="$(basename "$last" .pptx)"\n' +
  'if [ "$mode" = "make" ]; then printf "%%PDF-fake" > "$outdir/$base.pdf"; fi\n' +
  'if [ "$mode" = "sleep" ]; then sleep 5; fi\n' +
  "exit 0");

function fakePptx(): string {
  const p = path.join(os.tmpdir(), `s2e-${randomUUID()}.pptx`);
  fs.writeFileSync(p, "PK-fake");
  return p;
}

test("pptxToPdf：soffice 缺失（PATH 为空）→ null 短路", async () => {
  process.env.PATH = "";
  try {
    assert.equal(await pptxToPdf(fakePptx(), os.tmpdir()), null);
  } finally {
    process.env.PATH = FAKE_PATH;
  }
});

test("pptxToPdf：pptx 文件不存在 → null（存在性短路分支）", async () => {
  assert.equal(await pptxToPdf(path.join(os.tmpdir(), "no-such.pptx"), os.tmpdir()), null);
});

test("pptxToPdf：转换成功 → 返回 outdir 下的 pdf 绝对路径", async () => {
  const pptx = fakePptx();
  const outDir = fs.mkdtempSync(path.join(os.tmpdir(), "s2e-pdf-"));
  const pdf = await pptxToPdf(pptx, outDir);
  assert.ok(pdf && fs.existsSync(pdf), `应产出 pdf，实际 ${pdf}`);
  assert.equal(path.basename(pdf!), path.basename(pptx, ".pptx") + ".pdf");
  fs.rmSync(outDir, { recursive: true, force: true });
  fs.rmSync(pptx, { force: true });
});

test("pptxToPdf：soffice 退出但未产出 pdf → null（close 后存在性判定分支）", async () => {
  process.env.S2E_SOFFICE_MODE = "noop";
  try {
    const outDir = fs.mkdtempSync(path.join(os.tmpdir(), "s2e-pdf-"));
    assert.equal(await pptxToPdf(fakePptx(), outDir), null);
    fs.rmSync(outDir, { recursive: true, force: true });
  } finally {
    process.env.S2E_SOFFICE_MODE = "make";
  }
});

test("pptxToPdf：转换超时 → kill + null（超时分支）", async () => {
  process.env.S2E_SOFFICE_MODE = "sleep";
  try {
    const outDir = fs.mkdtempSync(path.join(os.tmpdir(), "s2e-pdf-"));
    assert.equal(await pptxToPdf(fakePptx(), outDir, 300), null);
    fs.rmSync(outDir, { recursive: true, force: true });
  } finally {
    process.env.S2E_SOFFICE_MODE = "make";
  }
});

// SOFFICE 变量保留引用，避免 lint 误报未使用（供排查定位 bin 路径）
void SOFFICE;
