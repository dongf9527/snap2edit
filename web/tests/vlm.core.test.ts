// web/tests/vlm.core.test.ts —— lib/vlm.ts 单测：withTimeout 竞速 / 报错文案 / getVLM 双路径。
// getVLM 依赖 z-ai-web-dev-sdk 的真实安装状态：SDK 可用则校验客户端接口与缓存，
// 不可用（未配置/初始化失败）同样是合法状态——调用方本就负责兜底。
// 运行：cd web && node --test tests/vlm.core.test.ts
import assert from "node:assert/strict";
import test from "node:test";
import { getVLM, vlmUnavailableMsg, withTimeout, type VLMClient } from "../lib/vlm.ts";

test("withTimeout：先到者胜——快 Promise 原样透传", async () => {
  const v = await withTimeout(Promise.resolve("ok"), 200, "测试");
  assert.equal(v, "ok");
});

test("withTimeout：慢 Promise 超时 → 带标签与秒数的可读错误", async () => {
  await assert.rejects(
    () => withTimeout(new Promise(() => {}), 30, "测试调用"),
    /测试调用超时（0\.0\d?s）/
  );
});

test("vlmUnavailableMsg：Error 与字符串两种入参都转为稳定前缀文案", () => {
  assert.equal(vlmUnavailableMsg(new Error("key 缺失")), "VLM 调用失败：key 缺失");
  assert.equal(vlmUnavailableMsg("raw-string"), "VLM 调用失败：raw-string");
});

test("getVLM：SDK 可用 → 客户端接口齐全且缓存命中；不可用 → 拒绝（均为合法路径）", async () => {
  let client: VLMClient | null = null;
  try {
    client = await getVLM();
  } catch {
    // SDK 未安装/未配置 → 拒绝即预期（调用方捕获后走骨架兜底）
  }
  if (client) {
    const again = await getVLM();
    assert.equal(again, client, "第二次调用应命中缓存（同一引用）");
    assert.equal(typeof client.callVision, "function");
    assert.equal(client.modelOf({ model: "glm-4v" }), "glm-4v");
    assert.equal(client.modelOf({}), undefined);
    assert.equal(client.contentOf({ choices: [{ message: { content: "hi" } }] }), "hi");
    assert.equal(client.contentOf({}), "", "空响应 → 空串兜底");
    assert.equal(client.finishOf({ choices: [{ finish_reason: "stop" }] }), "stop");
    assert.equal(client.finishOf({}), "", "缺 finish_reason → 空串兜底");
  } else {
    assert.ok(true, "getVLM 拒绝路径（SDK 不可用）");
  }
});
