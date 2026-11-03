// web/app/api/spec/route.ts —— POST /api/spec
// 上传图片（dataURL）→ 视觉模型抽取规格 JSON → 服务端确定性序列化 YAML →
// 结构校验（失败带错误回询重试一次）→ 骨架兜底。
// z-ai-web-dev-sdk 仅在服务端使用；模型可用环境变量 SNAP2EDIT_VISION_MODEL 覆盖。
//
// 健壮性：整个 handler 包裹在 try/catch 内 —— 任何未预期异常一律返回 JSON，
// 杜绝「浏览器收到 HTML/纯文本错误页 → JSON.parse unexpected character」。

import { NextRequest, NextResponse } from "next/server";
import {
  buildSkeletonYaml,
  buildSystemPrompt,
  buildUserPrompt,
  dumpSpecYaml,
  MAX_IMAGE_CHARS,
  normalizeImageMeta,
  normalizeSpec,
  parseSpecJson,
  validateSpecYaml,
  type ImageMeta,
  type SpecResult,
} from "@/lib/spec";
import { getVLM } from "@/lib/vlm";

export const runtime = "nodejs";
export const maxDuration = 300;

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

  const meta: ImageMeta = normalizeImageMeta(body.meta);
  if (!meta.width || !meta.height) {
    return bad(400, "meta.width / meta.height 缺失（客户端需先读取图片像素尺寸）");
  }

  const warnings: string[] = [];
  const sysMsg = { role: "system", content: buildSystemPrompt() };
  const userMsg = {
    role: "user",
    content: [
      { type: "text", text: buildUserPrompt(meta) },
      { type: "image_url", image_url: { url: image } },
    ],
  };

  try {
    const vlm = await getVLM();

    // 第一遍：直接抽取（系统提示词约束 schema，用户消息携带图片与元信息）
    const first = await vlm.callVision([sysMsg, userMsg]);
    const content1: string = vlm.contentOf(first);
    if (!content1.trim()) throw new Error("VLM 返回为空");
    const model = vlm.modelOf(first);
    const finish1: string = vlm.finishOf(first);
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
      const second = await vlm.callVision([
        sysMsg,
        userMsg,
        { role: "assistant", content: content1 },
        { role: "user", content: retryMsg },
      ]);
      const content2: string = vlm.contentOf(second);
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

  // 骨架兜底（含上方 try/catch 内任何未预期异常——绝不返回非 JSON）
  try {
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
  } catch (e2) {
    // 骨架也失败（极端情况）→ 仍然返回 JSON 错误
    return bad(500, `服务端内部错误：${e2 instanceof Error ? e2.message : String(e2)}`);
  }
}
