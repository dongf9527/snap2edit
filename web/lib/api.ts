// web/lib/api.ts —— 浏览器侧 API 调用辅助 + 与服务端共享的事件/报告类型。
// 设计要点：绝不直接 res.json()。预览网关在长请求（VLM 30-150s）下可能返回
// HTML/纯文本错误页，直接 json() 会抛出难以理解的
// 「JSON.parse: unexpected character at line 1 column 1」——这里统一转为可读错误；
// 长任务一律走 NDJSON 流式，边跑边有事件，兼顾进度展示与网关保活。

export interface GateItem {
  label: string;
  passed: boolean;
  detail: string;
}

export interface Gate {
  gate: string;
  title: string;
  items: GateItem[];
}

/** 引擎 check --json 的结构化报告（verify.collect_checks） */
export interface RenderReport {
  ok: boolean;
  project: string;
  gates: Gate[];
  failures: string[];
}

export interface ArtifactsDone {
  type: "done";
  jobId: string;
  project: string;
  ok: boolean;
  hasPdf: boolean;
  elapsedMs?: number;
  rounds?: number;
  spec?: string;
  warnings?: string[];
}

export type BuildEvent =
  | { type: "log"; msg: string }
  | { type: "tick"; s: number }
  | { type: "report"; n?: number; report: RenderReport }
  | { type: "round"; n: number; phase: "build" | "check" | "vlm"; note?: string }
  | { type: "spec"; n: number; spec: string }
  | ArtifactsDone
  | { type: "error"; error: string };

/** 读取普通 JSON 响应：非 JSON 一律转成可读错误（根除 JSON.parse 怪报错）。 */
export async function readApiJson<T = unknown>(res: Response): Promise<T> {
  const ct = res.headers.get("content-type") ?? "";
  const text = await res.text().catch(() => "");
  if (!ct.includes("application/json")) {
    const hint = text.trim().slice(0, 160) || "无响应体";
    throw new Error(
      `服务返回了非 JSON 内容（HTTP ${res.status}，Content-Type: ${ct || "缺失"}）：${hint}。` +
        `常见原因：网关超时、服务重启或请求体超限，请重试或换更小的图片。`
    );
  }
  try {
    return JSON.parse(text) as T;
  } catch {
    throw new Error(
      `服务返回的 JSON 无法解析（HTTP ${res.status}）：${text.slice(0, 160) || "空响应体"}`
    );
  }
}

/** POST 并按 NDJSON 逐行消费事件；onEvent 收到 {type:"error"} 或流中断时抛错。 */
export async function streamApi(
  path: string,
  payload: unknown,
  onEvent: (ev: BuildEvent) => void,
  errorEventMessage = "服务端执行失败"
): Promise<void> {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const ct = res.headers.get("content-type") ?? "";
  if (!res.ok || !ct.includes("ndjson")) {
    const text = await res.text().catch(() => "");
    const hint = text.trim().slice(0, 160);
    throw new Error(
      `服务返回异常（HTTP ${res.status}，Content-Type: ${ct || "缺失"}）` +
        `${hint ? "：" + hint : "。常见原因：网关超时或服务重启，请重试。"}`
    );
  }
  const reader = res.body?.getReader();
  if (!reader) throw new Error("浏览器不支持流式读取");
  const dec = new TextDecoder();
  let buf = "";
  let sawError: string | null = null;
  const dispatch = (line: string) => {
    const t = line.trim();
    if (!t) return;
    let ev: BuildEvent | null = null;
    try {
      ev = JSON.parse(t) as BuildEvent;
    } catch {
      return; // 忽略混入的非 JSON 行（代理注入的提示等）
    }
    if (ev.type === "error") sawError = ev.error;
    onEvent(ev);
  };
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    let idx: number;
    while ((idx = buf.indexOf("\n")) >= 0) {
      dispatch(buf.slice(0, idx));
      buf = buf.slice(idx + 1);
    }
  }
  if (buf.trim()) dispatch(buf);
  if (sawError !== null) throw new Error(sawError || errorEventMessage);
}
