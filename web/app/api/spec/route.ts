// web/app/api/spec/route.ts —— POST /api/spec
// 上传图片（dataURL）→ 视觉模型抽取规格 JSON → 服务端确定性序列化 YAML →
// 结构校验（失败带错误回询重试一次）→ 骨架兜底。
// z-ai-web-dev-sdk 仅在服务端使用；模型可用环境变量 SNAP2EDIT_VISION_MODEL 覆盖。

import { NextRequest, NextResponse } from "next/server";
import {
  buildSkeletonYaml,
  buildSystemPrompt,
  buildUserPrompt,
  dumpSpecYaml,
  MAX_IMAGE_CHARS,
  normalizeSpec,
  parseSpecJson,
  validateSpecYaml,
  type ImageMeta,
  type SpecResult,
} from "@/lib/spec";

export const runtime = "nodejs";

/** VLM 单次调用上限（自托管无硬性网关限制，取宽裕值） */
const VLM_TIMEOUT_MS = 150_000;

interface CheckedSpec {
  ok: boolean;
  yamlText: string;
  errors: string[];
  warnings: string[];
  stats: { elements: number; texts: number };
}

/** VLM 输出 → JSON 解析 → 规范化 → YAML 序列化 → 结构校验 */
function checkSpec(content: string): CheckedSpec {
  const p = parseSpecJson(content);
  if (!p.ok) {
    return {
      ok: false,
      yamlText: "",
      errors: [p.error],
      warnings: [],
      stats: { elements: 0, texts: 0 },
    };
  }
  const { spec, notes } = normalizeSpec(p.spec);
  const yamlText = dumpSpecYaml(spec);
  const v = validateSpecYaml(yamlText);
  return {
    ok: v.ok,
    yamlText: v.fixedYaml ?? yamlText,
    errors: v.errors,
    warnings: v.warnings,
    stats: v.stats,
  };
}

function withTimeout<T>(p: Promise<T>, ms: number): Promise<T> {
  return Promise.race([
    p,
    new Promise<T>((_, rej) =>
      setTimeout(() => rej(new Error(`VLM 调用超时（${ms / 1000}s）`)), ms)
    ),
  ]);
}

function bad(status: number, error: string) {
  return NextResponse.json({ ok: false, error }, { status });
}

export async function POST(req: NextRequest) {
  const started = Date.now();

  let body: { image?: unknown; meta?: unknown };
  try {
    body = await req.json();
  } catch {
    return bad(400, "请求体必须是 JSON");
  }

  const image = typeof body.image === "string" ? body.image : "";
  if (!image.startsWith("data:image/")) {
    return bad(400, "缺少图片（image 必须是 data:image/ 开头的 dataURL）");
  }
  if (image.length > MAX_IMAGE_CHARS) {
    return bad(413, "图片过大（原始字节 > 8MB），请压缩后重试");
  }

  const m = (body.meta ?? {}) as Record<string, unknown>;
  const meta: ImageMeta = {
    width: typeof m.width === "number" && m.width > 0 ? Math.round(m.width) : 0,
    height: typeof m.height === "number" && m.height > 0 ? Math.round(m.height) : 0,
    filename: typeof m.filename === "string" ? m.filename.slice(0, 120) : undefined,
    palette: Array.isArray(m.palette)
      ? m.palette
          .filter((c): c is string => typeof c === "string" && /^#[0-9a-fA-F]{6}$/.test(c))
          .slice(0, 8)
      : undefined,
  };
  if (!meta.width || !meta.height) {
    return bad(400, "meta.width / meta.height 缺失（客户端需先读取图片像素尺寸）");
  }

  const warnings: string[] = [];
  const userContent = [
    { type: "text", text: buildUserPrompt(meta) },
    { type: "image_url", image_url: { url: image } },
  ] as const;

  try {
    // 按需动态导入：未安装 SDK 时走骨架兜底，应用主体不受影响
    const mod = await import("z-ai-web-dev-sdk");
    const ZAI = mod.default;
    const zai = await ZAI.create();

    const callVision = (messages: unknown) => {
      // 端点对 model 有默认路由（CLI 亦省略该字段）；可用 SNAP2EDIT_VISION_MODEL 覆盖
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const payload: any = { messages, thinking: { type: "disabled" } };
      if (process.env.SNAP2EDIT_VISION_MODEL) payload.model = process.env.SNAP2EDIT_VISION_MODEL;
      return withTimeout(zai.chat.completions.createVision(payload), VLM_TIMEOUT_MS);
    };

    // 第一遍：直接抽取（系统提示词约束 schema，用户消息携带图片与元信息）
    const sysMsg = { role: "system", content: buildSystemPrompt() };
    const userMsg = { role: "user", content: userContent };
    const first = await callVision([sysMsg, userMsg]);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const content1: string = first?.choices?.[0]?.message?.content ?? "";
    if (!content1.trim()) throw new Error("VLM 返回为空");
    const model: string | undefined = first?.model;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const finish1: string = first?.choices?.[0]?.finish_reason ?? "";
    if (finish1 === "length") warnings.push("首次输出因 token 上限被截断，结果可能不完整");

    let cur = checkSpec(content1);

    // 第二遍：带错误回询，纠错重试一次
    if (!cur.ok) {
      warnings.push(`第一遍输出未过校验（${cur.errors.length} 个错误），已带错误反馈重试`);
      const retryMsg = [
        "你上一轮输出的 JSON 未通过校验，错误如下：",
        ...cur.errors.map((e, i) => `${i + 1}. ${e}`),
        "",
        "请修正全部错误后重新输出完整 JSON。仍然只输出 JSON 本体，不要解释、不要围栏。",
      ].join("\n");
      const second = await callVision([
        sysMsg,
        userMsg,
        { role: "assistant", content: content1 },
        { role: "user", content: retryMsg },
      ]);
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const content2: string = second?.choices?.[0]?.message?.content ?? "";
      if (content2.trim()) {
        cur = checkSpec(content2);
      }
    }

    if (cur.ok) {
      warnings.push(...cur.warnings);
      const result: SpecResult = {
        ok: true,
        mode: "vlm",
        spec: cur.yamlText,
        validation: { ok: true, errors: [], warnings: cur.warnings, stats: cur.stats },
        model,
        warnings,
        elapsedMs: Date.now() - started,
      };
      return NextResponse.json(result);
    }

    // VLM 可达但输出始终不合法 → 记录原因，落到骨架
    warnings.push(`VLM 输出未通过结构校验：${cur.errors.slice(0, 4).join("；")}`);
    warnings.push("已回退骨架模式（VLM 抽取失败）");
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    warnings.push(`VLM 调用失败：${msg}`);
    warnings.push("已回退骨架模式。服务端需配置 .z-ai-config（或自建 VLM 适配）后方可使用 AI 生成");
  }

  const skeleton = buildSkeletonYaml(meta);
  const sv = validateSpecYaml(skeleton);
  const result: SpecResult = {
    ok: true,
    mode: "skeleton",
    spec: skeleton,
    validation: { ok: sv.ok, errors: [], warnings: [], stats: sv.stats },
    warnings,
    elapsedMs: Date.now() - started,
  };
  return NextResponse.json(result);
}
