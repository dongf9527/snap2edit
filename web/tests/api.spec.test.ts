// web/tests/api.spec.test.ts —— lib/api.ts 单元测试（readApiJson 容错 / streamApi NDJSON 流式）
// 运行：cd web && node --test tests/*.test.ts
import assert from "node:assert/strict";
import test from "node:test";
import { readApiJson, streamApi, type BuildEvent } from "../lib/api.ts";

/* ---------- readApiJson ---------- */

test("readApiJson：JSON 正常返回", async () => {
  const res = new Response(JSON.stringify({ ok: true, n: 3 }), {
    headers: { "content-type": "application/json" },
  });
  assert.deepEqual(await readApiJson(res), { ok: true, n: 3 });
});

test("readApiJson：HTML/纯文本错误页 → 可读错误（含状态码与响应体摘要）", async () => {
  const res = new Response("<html>Gateway Timeout</html>", {
    status: 502,
    headers: { "content-type": "text/html" },
  });
  await assert.rejects(
    () => readApiJson(res),
    (e: Error) => e.message.includes("502") && e.message.includes("Gateway Timeout") && e.message.includes("非 JSON")
  );
});

test("readApiJson：content-type 是 JSON 但内容坏 → 解析错误", async () => {
  const res = new Response("{oops", { headers: { "content-type": "application/json" } });
  await assert.rejects(
    () => readApiJson(res),
    (e: Error) => e.message.includes("JSON 无法解析")
  );
});

test("readApiJson：响应体读取失败 → 「无响应体」兜底", async () => {
  const fake = {
    status: 503,
    headers: { get: () => "text/html" },
    text: async () => {
      throw new Error("stream gone");
    },
  } as unknown as Response;
  await assert.rejects(
    () => readApiJson(fake),
    (e: Error) => e.message.includes("无响应体")
  );
});

/* ---------- streamApi（mock fetch） ---------- */

/** 用 ReadableStream 构造 NDJSON 响应；chunks 按原样切分（可拆在行中间，测试缓冲逻辑） */
function ndjsonResponse(chunks: string[], init?: ResponseInit): Response {
  const enc = new TextEncoder();
  const stream = new ReadableStream<Uint8Array>({
    start(c) {
      for (const ch of chunks) c.enqueue(enc.encode(ch));
      c.close();
    },
  });
  return new Response(stream, {
    headers: { "content-type": "application/x-ndjson" },
    ...init,
  });
}

function mockFetchOnce(res: Response): void {
  (globalThis as { fetch: unknown }).fetch = async () => res;
}

test("streamApi：NDJSON 逐行派发（行拆在 chunk 中间也能缓冲拼回）+ 末行无换行符", async () => {
  mockFetchOnce(
    ndjsonResponse([
      '{"type":"log","msg":"第',
      '一步"}\n{"type":"tick","s":1}\n{"type":"log","msg":"第二步"}\n{"type":"done","jobId":"j1","ok":true,"hasPdf":true,"project":"p"}',
    ])
  );
  const events: BuildEvent[] = [];
  await streamApi("/api/build", { spec: "x" }, (ev) => events.push(ev));
  assert.deepEqual(
    events.map((e) => e.type),
    ["log", "tick", "log", "done"]
  );
  const done = events[3] as Extract<BuildEvent, { type: "done" }>;
  assert.equal(done.jobId, "j1");
  assert.equal(done.ok, true);
});

test("streamApi：混入的非 JSON 行被忽略；{type:error} 事件 → 抛出该错误", async () => {
  mockFetchOnce(
    ndjsonResponse(['代理注入的提示行\n{"type":"log","msg":"ok"}\n{"type":"error","error":"构建炸了"}\n'])
  );
  const events: BuildEvent[] = [];
  await assert.rejects(
    () => streamApi("/api/build", {}, (ev) => events.push(ev)),
    (e: Error) => e.message === "构建炸了"
  );
  assert.deepEqual(events.map((e) => e.type), ["log", "error"]);
});

test("streamApi：error 事件消息为空 → 抛默认文案", async () => {
  mockFetchOnce(ndjsonResponse(['{"type":"error","error":""}\n']));
  await assert.rejects(() => streamApi("/api/build", {}, () => {}), /服务端执行失败/);
});

test("streamApi：非 NDJSON / 非 2xx → 可读错误（含状态码与摘要）", async () => {
  mockFetchOnce(new Response("<html>bad gateway</html>", { status: 502, headers: { "content-type": "text/html" } }));
  await assert.rejects(
    () => streamApi("/api/build", {}, () => {}),
    (e: Error) => e.message.includes("502") && e.message.includes("服务返回异常")
  );
});

test("streamApi：res.body 缺失 → 明确报错", async () => {
  const fake = {
    ok: true,
    headers: { get: () => "application/x-ndjson" },
    body: null,
  } as unknown as Response;
  mockFetchOnce(fake);
  await assert.rejects(() => streamApi("/api/build", {}, () => {}), /流式读取/);
});
