// web/lib/vlm.ts —— 服务端专用：视觉模型客户端（z-ai-web-dev-sdk 按需动态导入）。
// 未安装/未配置 SDK 时 getVLM() 抛错，由调用方决定兜底行为（骨架 / 骨架+告警）。

export const VLM_TIMEOUT_MS = 150_000;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnyObj = any;

export interface VLMClient {
  /** messages: OpenAI 风格消息数组；返回原始响应 */
  callVision: (messages: unknown[]) => Promise<AnyObj>;
  /** 响应中的 model 字段（可能缺省） */
  modelOf: (resp: AnyObj) => string | undefined;
  /** 取 choices[0].message.content，空串兜底 */
  contentOf: (resp: AnyObj) => string;
  finishOf: (resp: AnyObj) => string;
}

export function withTimeout<T>(p: Promise<T>, ms: number, label = "VLM 调用"): Promise<T> {
  return Promise.race([
    p,
    new Promise<T>((_, rej) =>
      setTimeout(() => rej(new Error(`${label}超时（${ms / 1000}s）`)), ms)
    ),
  ]);
}

let cached: VLMClient | undefined;

/** 创建 VLM 客户端；SDK 缺失/初始化失败时抛出原始错误（调用方捕获后兜底）。 */
export async function getVLM(): Promise<VLMClient> {
  if (cached !== undefined) return cached;
  const mod = await import("z-ai-web-dev-sdk");
  const ZAI = mod.default;
  const zai = await ZAI.create();
  cached = {
    callVision: (messages: unknown[]) => {
      // 端点对 model 有默认路由（CLI 亦省略该字段）；可用 SNAP2EDIT_VISION_MODEL 覆盖
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const payload: any = { messages, thinking: { type: "disabled" } };
      if (process.env.SNAP2EDIT_VISION_MODEL) payload.model = process.env.SNAP2EDIT_VISION_MODEL;
      return withTimeout(zai.chat.completions.createVision(payload), VLM_TIMEOUT_MS);
    },
    modelOf: (r) => r?.model,
    contentOf: (r) => r?.choices?.[0]?.message?.content ?? "",
    finishOf: (r) => r?.choices?.[0]?.finish_reason ?? "",
  };
  return cached;
}

/** VLM 永不可用时的稳定报错文案（避免向用户泄漏内部细节） */
export function vlmUnavailableMsg(e: unknown): string {
  const msg = e instanceof Error ? e.message : String(e);
  return `VLM 调用失败：${msg}`;
}
