// web/lib/spec.ts —— Snap2Edit spec.yaml 生成/校验共享逻辑
// 仅含纯 TypeScript 逻辑（无 SDK 依赖）：VLM 提示词、JSON→YAML 转换、结构校验器、骨架兜底。
// 引擎侧同源规则见 src/snap2edit/spec.py（几何字段 / id 唯一 / 占位符黑名单）。
//
// 设计要点：VLM 只负责输出 JSON（转义规则严格、可机器校验），
// YAML 由服务端 yamlDump 确定性序列化 —— 从根上规避「引号未闭合」类输出事故。

import { parse as yamlParse, stringify as yamlDump } from "yaml";

export const ELEMENT_TYPES = ["rect", "rrect", "pill", "circle", "text", "line", "arrow"] as const;
export type ElementType = (typeof ELEMENT_TYPES)[number];

export interface ImageMeta {
  width: number;
  height: number;
  filename?: string;
  /** 客户端 canvas 取样的主色（hex，按占比降序） */
  palette?: string[];
}

export interface SpecValidation {
  ok: boolean;
  errors: string[];
  warnings: string[];
  stats: { elements: number; texts: number };
}

export interface SpecResult {
  ok: boolean;
  mode: "vlm" | "skeleton";
  spec: string;
  validation: SpecValidation;
  model?: string;
  warnings: string[];
  elapsedMs: number;
}

/** base64 dataURL 上限（约 8MB 原始字节） */
export const MAX_IMAGE_CHARS = 11_000_000;

/** 客户端 meta 的服务端规范化（越界字段剔除，类型收紧） */
export function normalizeImageMeta(m: unknown): ImageMeta {
  const o = (m ?? {}) as Record<string, unknown>;
  return {
    width: typeof o.width === "number" && o.width > 0 ? Math.round(o.width) : 0,
    height: typeof o.height === "number" && o.height > 0 ? Math.round(o.height) : 0,
    filename: typeof o.filename === "string" ? o.filename.slice(0, 120) : undefined,
    palette: Array.isArray(o.palette)
      ? o.palette
          .filter((c): c is string => typeof c === "string" && /^#[0-9a-fA-F]{6}$/.test(c))
          .slice(0, 8)
      : undefined,
  };
}

/** 引擎同源占位符黑名单（与 src/snap2edit/spec.py 保持一致） */
const PLACEHOLDER_BLACKLIST = ["XXX", "TODO", "待补充", "【", "undefined", "NaN"];

const GEOM_FIELDS: Record<ElementType, string[]> = {
  rect: ["x", "y", "w", "h"],
  rrect: ["x", "y", "w", "h"],
  pill: ["x", "y", "w", "h"],
  circle: ["x", "y", "w", "h"],
  text: ["x", "y"],
  line: ["x1", "y1", "x2", "y2"],
  arrow: ["x1", "y1", "x2", "y2"],
};

const isNum = (v: unknown): v is number => typeof v === "number" && Number.isFinite(v);

/**
 * 统一序列化：值为双引号风格（避免 PyYAML(YAML 1.1) 把 "16:9" 等无引号标量误读为六十进制整数），
 * key 保持朴素风格（可读性）；lineWidth=0 禁止长文案折行（折行合法但难以阅读且易被误编辑）。
 */
export function dumpSpecYaml(spec: unknown): string {
  return yamlDump(spec, {
    defaultStringType: "QUOTE_DOUBLE",
    defaultKeyType: "PLAIN",
    lineWidth: 0,
  });
}

/**
 * 规范化 VLM 产出的 spec，保证引擎四道门可过：
 * 1) 多行 text 元素拆为单行（y 按行高递增）
 * 2) texts 清单拆行展平；被模型截断的元素文本按清单回填；
 *    渲染中不存在的清单项剔除并备注
 * 3) 全量重编号 id（e1..eN），保证唯一
 */
export function normalizeSpec(spec: Record<string, unknown>): {
  spec: Record<string, unknown>;
  notes: string[];
} {
  const notes: string[] = [];
  const els = Array.isArray(spec.elements)
    ? (spec.elements as Record<string, unknown>[]).slice()
    : [];
  const out: Record<string, unknown>[] = [];

  // 1) 多行 text 元素拆分
  let splitCount = 0;
  for (const el of els) {
    if (el.type === "text" && typeof el.text === "string" && el.text.includes("\n")) {
      const lines = el.text.split("\n").map((s) => s.trim()).filter(Boolean);
      const size = isNum(el.size) ? el.size : 16;
      const lineH = isNum(el.line_h) ? el.line_h : 1.45;
      lines.forEach((ln, i) => {
        out.push({
          ...el,
          y: Math.round((isNum(el.y) ? el.y : 0) + i * size * lineH),
          text: ln,
        });
      });
      splitCount += lines.length - 1;
    } else {
      out.push(el);
    }
  }
  if (splitCount > 0) notes.push(`已将多行文本拆分为独立单行元素（新增 ${splitCount} 行）`);

  // 2) texts 清单对齐
  const rawTexts = Array.isArray(spec.texts)
    ? (spec.texts as unknown[]).filter((t): t is string => typeof t === "string")
    : [];
  const flat: string[] = [];
  for (const t of rawTexts) flat.push(...t.split("\n").map((s) => s.trim()).filter(Boolean));

  let backfilled = 0;
  const finalTexts: string[] = [];
  const dropped: string[] = [];
  for (const t of flat) {
    const all = out.filter((e) => typeof e.text === "string").map((e) => e.text as string);
    if (all.some((e) => e.includes(t))) {
      finalTexts.push(t);
      continue;
    }
    // 前缀回填：元素文本是清单项的前缀（模型写入时截断）
    const cand = out.find(
      (e) =>
        typeof e.text === "string" &&
        (e.text as string).length >= 6 &&
        t.startsWith(e.text as string)
    );
    if (cand) {
      cand.text = t;
      backfilled++;
      finalTexts.push(t);
      continue;
    }
    dropped.push(t);
  }
  if (backfilled > 0) notes.push(`已按 texts 清单回填 ${backfilled} 个被截断的元素文本`);
  if (dropped.length > 0)
    notes.push(`texts 中 ${dropped.length} 条未见于任何元素，已从清单剔除（渲染中本就不存在）`);
  if (finalTexts.length > 0) spec.texts = [...new Set(finalTexts)];

  // 3) 全量重编号
  out.forEach((e, i) => {
    e.id = `e${i + 1}`;
  });
  spec.elements = out;
  return { spec, notes };
}

/* ------------------------------------------------------------------ */
/* 提示词（VLM 输出 JSON，服务端转 YAML）                                */
/* ------------------------------------------------------------------ */

export function buildSystemPrompt(): string {
  return [
    "你是 Snap2Edit 的图表规格抽取引擎。输入是一张图表/信息图/幻灯片截图，",
    "你的任务是输出一份可被 Snap2Edit 引擎双渲染（HTML+SVG 与原生 PPTX）的布局规格。",
    "",
    "输出格式硬性规则：",
    "1. 只输出一个 JSON 对象：不要 markdown 围栏、不要解释、不要注释、不要尾逗号。",
    "2. JSON 必须能被 JSON.parse 直接解析；字符串内的英文双引号必须写成 \\\"。",
    "3. 文字内容如需引号，一律用中文引号「」，避免转义问题。",
    "",
    "字段规则：",
    "- canvas.width/height 必须等于用户消息给出的原图像素尺寸。",
    "- 坐标为整数 px，原点左上角，不得越出画布。",
    "- 颜色一律 #RRGGBB，从图中实际取样，不要臆造。",
    "- 每条可见文字逐字转录进对应 text 元素的 text 字段，禁止改写、缩写、占位。",
    "- texts 数组是全图文字清单，与所有 text 元素的 text 值一一对应（终检文案核对用）。",
    "- elements 按绘制顺序：先背景/大分区，再装饰线，最后文字。",
    "- id 全局唯一，依次 e1、e2、e3……",
    "- 禁止出现：XXX、TODO、待补充、【、undefined、NaN。",
    "- 箭头用 type:arrow（x1,y1 → x2,y2），不要拆成线段+三角形。",
    "",
    "元素几何字段：",
    "- rect / rrect / pill : x,y,w,h（rrect 可加 radius；pill 为胶囊形）",
    "- circle : x,y,w,h（圆形/圆点/椭圆的外接框；圆即 w=h）",
    "- text  : x,y（w 可选），另有 size、color、weight(400/700)、text，可加 align、line_h",
    "- line / arrow : x1,y1,x2,y2；line 另有 stroke、stroke_w，arrow 另有 color、stroke_w",
    "",
    "JSON 结构模板（数值与文字替换为实际内容；不要保留 <> 占位）：",
    `{`,
    `  "project": "图表短名",`,
    `  "canvas": {"width": 1280, "height": 720},`,
    `  "slide": {"preset": "16:9"},`,
    `  "font": {"name": "Noto Sans SC", "fallback": "Microsoft YaHei", "pptx_name": "Microsoft YaHei"},`,
    `  "palette": {"primary": "#1F2937", "accent": "#2B6CB0", "card": "#FFFFFF", "muted": "#8A97A8", "bg": "#FFFFFF"},`,
    `  "texts": ["文字1", "文字2"],`,
    `  "elements": [`,
    `    {"id": "e1", "type": "rect", "x": 0, "y": 0, "w": 1280, "h": 720, "fill": "#FFFFFF"},`,
    `    {"id": "e2", "type": "rrect", "x": 40, "y": 120, "w": 380, "h": 220, "fill": "#F7F9FC", "radius": 10},`,
    `    {"id": "e4", "type": "circle", "x": 60, "y": 60, "w": 36, "h": 36, "fill": "#2B6CB0"},`,
    `    {"id": "e3", "type": "text", "x": 64, "y": 140, "size": 22, "weight": 700, "color": "#1F2937", "text": "卡片标题"}`,
    `  ]`,
    `}`,
    "",
    "复杂度取舍：优先保证 ①全部文字逐字转录完整 ②分区/卡片结构正确 ③主色准确；",
    "个别文字坐标允许 ±8px 误差，后续由四道校验门与人工微调兜底。",
  ].join("\n");
}

export function buildUserPrompt(meta: ImageMeta): string {
  const parts = [
    `原图尺寸：${meta.width} x ${meta.height} px。`,
    meta.filename ? `文件名：${meta.filename}（project 名可据此取短名）。` : "",
    meta.palette?.length
      ? `客户端预取样的主色（按占比降序，供校色参考）：${meta.palette.join("、")}。`
      : "",
    "请分析这张图并输出布局规格 JSON（遵守系统规则，只输出 JSON 本体）。",
  ];
  return parts.filter(Boolean).join("\n");
}

/** 渲染报告自动回询：把引擎校验失败项反馈给 VLM，要求输出修正后的完整 JSON */
export function buildFixPrompt(failures: string[], specYaml: string): string {
  return [
    "你之前给出的布局规格在 Snap2Edit 引擎四道校验门中未全部通过，错误清单如下：",
    ...failures.map((f, i) => `${i + 1}. ${f}`),
    "",
    "请逐条修正这些错误（常见修法：文案缺失→把缺失文字补为对应 text 元素并同步 texts 清单；",
    "文本溢出→缩小该元素 size 或加大 w；占位符→替换为真实文案），",
    "其余正确的部分保持原样。",
    "",
    "当前规格（YAML，仅作参考；你的输出仍必须是 JSON）：",
    "```yaml",
    specYaml.slice(0, 12000),
    "```",
    "",
    "输出要求与最初一致：只输出修正后的完整 JSON 本体，不要围栏、不要解释。",
  ].join("\n");
}

/** 剥离可能的 markdown 围栏 */
export function extractCodeBlock(content: string): string {
  let t = content.trim();
  const fence = t.match(/^```[a-zA-Z]*\s*\n([\s\S]*?)\n?```$/);
  if (fence) t = fence[1];
  return t.trim();
}

/**
 * VLM 输出 → spec 对象。
 * 容错两级：直接 JSON.parse → 清理尾逗号后重试。
 */
export function parseSpecJson(text: string): { ok: true; spec: Record<string, unknown> } | { ok: false; error: string } {
  const t = extractCodeBlock(text);
  try {
    const obj = JSON.parse(t);
    if (!obj || typeof obj !== "object") return { ok: false, error: "JSON 根节点必须是对象" };
    return { ok: true, spec: obj as Record<string, unknown> };
  } catch (e1) {
    const repaired = t.replace(/,\s*([}\]])/g, "$1");
    try {
      const obj = JSON.parse(repaired);
      if (!obj || typeof obj !== "object") return { ok: false, error: "JSON 根节点必须是对象" };
      return { ok: true, spec: obj as Record<string, unknown> };
    } catch {
      return { ok: false, error: `JSON 解析失败：${e1 instanceof Error ? e1.message : String(e1)}` };
    }
  }
}

/* ------------------------------------------------------------------ */
/* 结构校验（引擎门 0 的 TS 同源实现；输入为 YAML 文本）                  */
/* ------------------------------------------------------------------ */

export function validateSpecYaml(raw: string): SpecValidation & { fixedYaml?: string } {
  const errors: string[] = [];
  const warnings: string[] = [];
  const empty: SpecValidation = { ok: false, errors, warnings, stats: { elements: 0, texts: 0 } };

  let doc: unknown;
  try {
    doc = yamlParse(raw);
  } catch (e) {
    errors.push(`YAML 解析失败：${e instanceof Error ? e.message : String(e)}`);
    return { ...empty, errors };
  }
  if (!doc || typeof doc !== "object") {
    errors.push("spec 根节点必须是对象");
    return { ...empty, errors };
  }
  const sp = doc as Record<string, unknown>;

  if (typeof sp.project !== "string" || !sp.project.trim()) errors.push("缺少 project（字符串）");

  const cv = sp.canvas as Record<string, unknown> | undefined;
  if (!cv || !isNum(cv.width) || !isNum(cv.height) || cv.width <= 0 || cv.height <= 0) {
    errors.push("canvas.width/height 缺失或非法（需正数）");
  }
  const W = cv && isNum(cv.width) ? cv.width : 0;
  const H = cv && isNum(cv.height) ? cv.height : 0;

  const els = Array.isArray(sp.elements) ? (sp.elements as Record<string, unknown>[]) : null;
  if (!els || els.length === 0) errors.push("elements 必须是非空数组");

  const seenIds = new Set<string>();
  let textCount = 0;
  const textStrings: string[] = [];

  if (els) {
    els.forEach((el, i) => {
      const label = `elements[${i}]`;
      const id = typeof el.id === "string" ? el.id : "";
      if (!id) errors.push(`${label} 缺少 id`);
      else if (seenIds.has(id)) errors.push(`${label} id 重复：${id}`);
      if (id) seenIds.add(id);

      const type = el.type as ElementType;
      if (!ELEMENT_TYPES.includes(type)) {
        errors.push(`${label} type 非法：${String(el.type)}（允许：${ELEMENT_TYPES.join("/")}）`);
        return;
      }
      for (const f of GEOM_FIELDS[type]) {
        if (!isNum(el[f])) {
          errors.push(`${label}（${type}）缺少数值字段 ${f}`);
        }
      }
      // 边界粗检（仅告警）：x 系字段对照画布宽，y 系字段对照画布高
      if (W > 0 && H > 0) {
        const xs = GEOM_FIELDS[type].filter((f) => f.startsWith("x")).map((f) => el[f]);
        const ys = GEOM_FIELDS[type].filter((f) => f.startsWith("y")).map((f) => el[f]);
        const outX = xs.some((v) => isNum(v) && (v < -2 || v > W + 2));
        const outY = ys.some((v) => isNum(v) && (v < -2 || v > H + 2));
        if (outX || outY) warnings.push(`${label} 坐标可能越出画布`);
      }
      if (type === "text") {
        textCount += 1;
        // 与引擎 spec.py 同源规则：text 元素允许 text 字符串 或 lines 多行数组
        const hasText = typeof el.text === "string" && el.text.trim().length > 0;
        const hasLines =
          Array.isArray(el.lines) &&
          el.lines.length > 0 &&
          el.lines.every((x) => typeof x === "string" && x.trim().length > 0);
        if (!hasText && !hasLines) {
          errors.push(`${label} text 元素缺少文字内容（需要 text 或 lines）`);
        } else if (hasText) {
          textStrings.push(el.text as string);
        } else {
          textStrings.push(...(el.lines as string[]));
        }
        if (!isNum(el.size)) warnings.push(`${label} text 缺少 size，渲染将回退默认字号`);
      }
    });
  }

  // texts 清单：缺失时自动用 text 元素回填
  let fixedYaml: string | undefined;
  const texts = Array.isArray(sp.texts) ? (sp.texts as unknown[]) : null;
  if (!texts || texts.length === 0) {
    if (textStrings.length > 0) {
      sp.texts = textStrings;
      fixedYaml = dumpSpecYaml(sp);
      warnings.push("texts 清单缺失，已自动按 text 元素回填");
    } else {
      errors.push("缺少 texts 文字清单（终检门需要）");
    }
  } else if (texts.some((t) => typeof t !== "string")) {
    errors.push("texts 数组必须全部为字符串");
  }

  // 占位符黑名单扫描（对 YAML 原文与回填后文本都扫）
  for (const bad of PLACEHOLDER_BLACKLIST) {
    if (raw.includes(bad) || (fixedYaml && fixedYaml.includes(bad))) {
      errors.push(`存在占位符/非法字符串：${bad}`);
      break;
    }
  }

  const stats = { elements: els ? els.length : 0, texts: textCount };
  return { ok: errors.length === 0, errors, warnings, stats, fixedYaml };
}

/* ------------------------------------------------------------------ */
/* 骨架兜底（VLM 不可用时给出可编辑起点）                                */
/* ------------------------------------------------------------------ */

export function buildSkeletonYaml(meta: ImageMeta): string {
  const W = meta.width > 0 ? meta.width : 1280;
  const H = meta.height > 0 ? meta.height : 720;
  const pal = meta.palette ?? [];
  const primary = pal.find((c) => !isNearWhite(c)) ?? "#1F2937";
  const accent = pal.find((c) => c !== primary && !isNearWhite(c)) ?? "#2B6CB0";
  const title = (meta.filename ?? "未命名图表").replace(/\.[a-z0-9]+$/i, "").slice(0, 40);

  const spec = {
    project: title || "untitled",
    canvas: { width: W, height: H },
    slide: { preset: "16:9" },
    font: { name: "Noto Sans SC", fallback: "Microsoft YaHei", pptx_name: "Microsoft YaHei" },
    palette: { primary, accent, card: "#FFFFFF", muted: "#8A97A8", bg: "#FFFFFF" },
    texts: [title || "图表标题"],
    elements: [
      { id: "e1", type: "rect", x: 0, y: 0, w: W, h: H, fill: "#FFFFFF" },
      {
        id: "e2",
        type: "text",
        x: 48,
        y: 48,
        size: 30,
        weight: 700,
        color: primary,
        text: title || "图表标题",
      },
    ],
  };
  return dumpSpecYaml(spec);
}

function isNearWhite(hex: string): boolean {
  const m = hex.replace("#", "");
  if (m.length !== 6) return false;
  const r = parseInt(m.slice(0, 2), 16);
  const g = parseInt(m.slice(2, 4), 16);
  const b = parseInt(m.slice(4, 6), 16);
  return r > 235 && g > 235 && b > 235;
}
