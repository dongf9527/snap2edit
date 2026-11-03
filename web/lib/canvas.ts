// web/lib/canvas.ts —— 客户端 SVG 画布渲染：与引擎 svgout.py 同语义的 TS 镜像实现。
// 用途：studio 可视化编辑器。坐标/圆角/文字基线/箭头三角算法均与产线①一致，
// 保证「编辑器里看到的样子 ≈ 引擎 build 出的 HTML+SVG」。
// 注意：这是预览渲染；正式产物永远由 Python 引擎输出（单一事实源）。

import type { ElementType } from "./spec";

export interface SpecEl {
  id: string;
  type: ElementType | string;
  // 形状
  x?: number;
  y?: number;
  w?: number;
  h?: number;
  rx?: number;
  fill?: string | null;
  stroke?: string | null;
  stroke_width?: number;
  // 线/箭头
  x1?: number;
  y1?: number;
  x2?: number;
  y2?: number;
  // 文本
  text?: string;
  lines?: string[];
  size?: number;
  color?: string | null;
  bold?: boolean;
  align?: "left" | "center" | "right";
  line_height?: number;
  // 兜底：VLM 可能产出的其他字段原样保留
  [k: string]: unknown;
}

export interface SpecDoc {
  project?: string;
  canvas?: { width?: number; height?: number };
  font?: { name?: string; fallback?: string; pptx_name?: string };
  palette?: Record<string, string | null>;
  texts?: string[];
  elements?: SpecEl[];
  [k: string]: unknown;
}

const ANCHOR: Record<string, string> = { left: "start", center: "middle", right: "end" };

function n(v: number): string {
  const s = (Math.round(v * 10) / 10).toFixed(1);
  return s.endsWith(".0") ? s.slice(0, -2) : s;
}

function esc(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function family(spec: SpecDoc): string {
  const f = spec.font ?? {};
  return `'${f.name ?? "Noto Sans SC"}', '${f.fallback ?? "Microsoft YaHei"}', sans-serif`;
}

/** 元素主文本（lines 优先）；供列表/属性面板展示 */
export function elText(el: SpecEl): string {
  if (Array.isArray(el.lines) && el.lines.length) return el.lines.join("\n");
  return typeof el.text === "string" ? el.text : "";
}

function textSvg(
  spec: SpecDoc,
  el: SpecEl,
  tid: string,
  cx: number,
  cy: number,
  centered: boolean
): string {
  const pal = spec.palette ?? {};
  const size = Number(el.size ?? 16);
  const lines = el.lines ?? [elText(el)];
  const color = el.color || pal.primary || "#1F2937";
  const weight = el.bold ? "bold" : "normal";
  const lh = Number(el.line_height ?? 1.45) * size;
  const anchor = centered ? "middle" : (ANCHOR[el.align ?? "left"] ?? "start");
  const first = centered ? cy - ((lines.length - 1) * lh) / 2 + size * 0.34 : cy + size * 0.82;
  const tspans = lines
    .map((ln, k) => `<tspan x="${n(cx)}" y="${n(first + k * lh)}">${esc(String(ln))}</tspan>`)
    .join("");
  return (
    `<text id="${esc(tid)}" font-size="${n(size)}" fill="${esc(color)}" ` +
    `font-weight="${weight}" text-anchor="${anchor}">${tspans}</text>`
  );
}

function boxSvg(spec: SpecDoc, el: SpecEl): string {
  const pal = spec.palette ?? {};
  const { x = 0, y = 0, w = 0, h = 0 } = el;
  // 与 svgout 一致：fill 键存在且为 null/none → 透明；键缺失 → palette.card
  let fill: string;
  if (el.fill == null) fill = "fill" in el ? "none" : pal.card || "#FFFFFF";
  else fill = el.fill;
  const sAttr = el.stroke
    ? ` stroke="${esc(el.stroke)}" stroke-width="${n(Number(el.stroke_width ?? 1))}"`
    : "";
  let out: string;
  if (el.type === "circle") {
    out =
      `<ellipse id="${esc(el.id)}" cx="${n(x + w / 2)}" cy="${n(y + h / 2)}" ` +
      `rx="${n(w / 2)}" ry="${n(h / 2)}" fill="${esc(fill)}"${sAttr}/>`;
  } else {
    const rxV = el.type === "pill" ? h / 2 : (el.rx ?? Math.min(w, h) * 0.1);
    const rx = el.type === "rect" ? "" : ` rx="${n(rxV)}"`;
    out =
      `<rect id="${esc(el.id)}" x="${n(x)}" y="${n(y)}" ` +
      `width="${n(w)}" height="${n(h)}"${rx} fill="${esc(fill)}"${sAttr}/>`;
  }
  if (el.text) out += textSvg(spec, el, `${el.id}-text`, x + w / 2, y + h / 2, true);
  return out;
}

function arrowSvg(spec: SpecDoc, el: SpecEl): string {
  const pal = spec.palette ?? {};
  const { x1 = 0, y1 = 0, x2 = 0, y2 = 0 } = el;
  const color = el.stroke || pal.accent || "#2B6CB0";
  const sw = Number(el.stroke_width ?? 2);
  const hs = Number(el.head ?? 9);
  const ang = Math.atan2(y2 - y1, x2 - x1);
  const bx = x2 - hs * Math.cos(ang);
  const by = y2 - hs * Math.sin(ang);
  const lx = -hs * Math.sin(ang);
  const ly = hs * Math.cos(ang);
  const tri = `${n(x2)},${n(y2)} ${n(bx + lx)},${n(by + ly)} ${n(bx - lx)},${n(by - ly)}`;
  const ex = x2 - hs * 0.6 * Math.cos(ang);
  const ey = y2 - hs * 0.6 * Math.sin(ang);
  return (
    `<line id="${esc(el.id)}" x1="${n(x1)}" y1="${n(y1)}" x2="${n(ex)}" y2="${n(ey)}" ` +
    `stroke="${esc(color)}" stroke-width="${sw}" stroke-linecap="round"/>` +
    `<polygon id="${esc(el.id)}-head" points="${tri}" fill="${esc(color)}"/>`
  );
}

/** 单元素 → SVG 片段（与 svgout.render_element 同语义） */
export function renderElementSvg(spec: SpecDoc, el: SpecEl): string {
  switch (el.type) {
    case "rect":
    case "rrect":
    case "pill":
    case "circle":
      return boxSvg(spec, el);
    case "text":
      return textSvg(spec, el, el.id, Number(el.x ?? 0), Number(el.y ?? 0), false);
    case "line": {
      const pal = spec.palette ?? {};
      return (
        `<line id="${esc(el.id)}" x1="${n(Number(el.x1 ?? 0))}" y1="${n(Number(el.y1 ?? 0))}" ` +
        `x2="${n(Number(el.x2 ?? 0))}" y2="${n(Number(el.y2 ?? 0))}" ` +
        `stroke="${esc(el.stroke || pal.muted || "#94A3B8")}" ` +
        `stroke-width="${n(Number(el.stroke_width ?? 1))}"/>`
      );
    }
    case "arrow":
      return arrowSvg(spec, el);
    default:
      return "";
  }
}

export interface CanvasOpts {
  /** 选中高亮的元素 id 列表（编辑器内部态，不影响导出；支持多选） */
  selectedIds?: string[] | null;
  /** 鼠标悬停 id */
  hoverId?: string | null;
}

/**
 * 整画布 SVG 字符串（viewBox 1:1 px）。选中/悬停以独立覆盖层表达，
 * 不改动元素本身，因此该字符串亦可直接用于「所见即所得」检查。
 */
export function renderSpecSvg(spec: SpecDoc, opts: CanvasOpts = {}): string {
  const cw = Number(spec.canvas?.width ?? 1280);
  const ch = Number(spec.canvas?.height ?? 720);
  const bg = spec.palette?.bg;
  const body = (spec.elements ?? []).map((el) => renderElementSvg(spec, el)).join("\n");
  // 覆盖层：多选/悬停描边框（不参与导出语义；用 elBBox 统一处理线段/文本）
  const overlay: string[] = [];
  const els = spec.elements ?? [];
  const selSet = new Set(opts.selectedIds ?? []);
  for (const el of els) {
    if (!selSet.has(el.id)) continue;
    const b = elBBox(el);
    const pad = 3;
    overlay.push(
      `<rect class="ov-sel" x="${n(b.x - pad)}" y="${n(b.y - pad)}" width="${n(Math.max(b.w + pad * 2, 8))}" ` +
        `height="${n(Math.max(b.h + pad * 2, 8))}" fill="none"/>`
    );
  }
  const hov = els.find((e) => e.id === opts.hoverId);
  if (hov && !selSet.has(hov.id)) {
    const b = elBBox(hov);
    overlay.push(
      `<rect class="ov-hov" x="${n(b.x - 2)}" y="${n(b.y - 2)}" width="${n(Math.max(b.w + 4, 8))}" ` +
        `height="${n(Math.max(b.h + 4, 8))}" fill="none"/>`
    );
  }
  return (
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${cw} ${ch}" ` +
    `width="${cw}" height="${ch}" data-canvas="${cw}x${ch}">` +
    (bg ? `<rect x="0" y="0" width="${cw}" height="${ch}" fill="${esc(bg)}"/>` : "") +
    body +
    overlay.join("") +
    `</svg>`
  );
}

/** 从元素重建 texts 清单（与元素文案严格一致，保证门1可过） */
export function regenTexts(spec: SpecDoc): string[] {
  const out: string[] = [];
  for (const el of spec.elements ?? []) {
    for (const t of [elText(el)]) {
      if (t && !out.includes(t)) out.push(t);
    }
  }
  return out;
}

/** 元素文本变化后同步 texts 清单中的旧值 */
export function syncTextOnEdit(spec: SpecDoc, oldVal: string, newVal: string): void {
  if (!Array.isArray(spec.texts)) return;
  const i = spec.texts.indexOf(oldVal);
  if (i >= 0) {
    if (newVal) spec.texts[i] = newVal;
    else spec.texts.splice(i, 1);
  } else if (newVal && !spec.texts.includes(newVal)) {
    spec.texts.push(newVal);
  }
}

/** 空白起步模板 */
export function blankSpec(w = 1280, h = 720): SpecDoc {
  return {
    project: "未命名图表",
    canvas: { width: w, height: h },
    slide: { preset: "16:9" },
    font: { name: "Noto Sans SC", fallback: "Microsoft YaHei", pptx_name: "Microsoft YaHei" },
    palette: {
      primary: "#1F2937",
      accent: "#2B6CB0",
      card: "#FFFFFF",
      muted: "#8A97A8",
      bg: "#FFFFFF",
    },
    texts: ["标题文本"],
    elements: [
      { id: "e1", type: "rect", x: 0, y: 0, w, h, fill: "#FFFFFF" },
      { id: "e2", type: "text", x: 48, y: 48, size: 30, weight: 700, text: "标题文本" },
    ],
  };
}

/** 元素几何边界（拖拽/框选命中/吸附/对齐共用；文本宽度按字号估算） */
export function elBBox(el: SpecEl): { x: number; y: number; w: number; h: number } {
  if (el.type === "text") {
    const size = Number(el.size ?? 16);
    const lines = el.lines ?? [elText(el) || " "];
    const lh = Number(el.line_height ?? 1.45) * size;
    const maxLen = Math.max(1, ...lines.map((l) => String(l).length));
    return {
      x: Number(el.x ?? 0),
      y: Number(el.y ?? 0),
      w: Math.round(maxLen * size * 0.62),
      h: lines.length * lh,
    };
  }
  if (el.type === "line" || el.type === "arrow") {
    const x = Math.min(Number(el.x1 ?? 0), Number(el.x2 ?? 0));
    const y = Math.min(Number(el.y1 ?? 0), Number(el.y2 ?? 0));
    return { x, y, w: Math.abs(Number(el.x2 ?? 0) - Number(el.x1 ?? 0)), h: Math.abs(Number(el.y2 ?? 0) - Number(el.y1 ?? 0)) };
  }
  return { x: Number(el.x ?? 0), y: Number(el.y ?? 0), w: Number(el.w ?? 0), h: Number(el.h ?? 0) };
}

export interface SnapGuides {
  v: number[];
  h: number[];
}

/** 吸附触发距离（画布 px） */
export const SNAP_THRESHOLD = 8;

/**
 * 拖拽吸附：移动元素的左/中/右（上/中/下）边缘，对齐静态元素边缘/中线与画布边缘/中线。
 * 返回修正后的位移与需要渲染的吸附线位置（画布坐标）。
 */
export function computeSnap(
  moving: SpecEl[],
  movingIds: string[],
  all: SpecEl[],
  canvas: { w: number; h: number },
  dx: number,
  dy: number,
  threshold = SNAP_THRESHOLD
): { dx: number; dy: number; guides: SnapGuides } {
  const ids = new Set(movingIds);
  const mv = moving.map((el) => {
    const b = elBBox(el);
    return { x: b.x + dx, y: b.y + dy, w: b.w, h: b.h };
  });
  const st = all.filter((e) => !ids.has(e.id)).map(elBBox);

  const vx = new Set<number>([0, Math.round(canvas.w / 2), canvas.w]);
  const hy = new Set<number>([0, Math.round(canvas.h / 2), canvas.h]);
  for (const b of st) {
    vx.add(b.x);
    vx.add(Math.round(b.x + b.w / 2));
    vx.add(b.x + b.w);
    hy.add(b.y);
    hy.add(Math.round(b.y + b.h / 2));
    hy.add(b.y + b.h);
  }
  const edgesOf = (boxes: { x: number; y: number; w: number; h: number }[], axis: "x" | "y") => {
    const s = new Set<number>();
    for (const b of boxes) {
      if (axis === "x") {
        s.add(b.x);
        s.add(b.x + b.w / 2);
        s.add(b.x + b.w);
      } else {
        s.add(b.y);
        s.add(b.y + b.h / 2);
        s.add(b.y + b.h);
      }
    }
    return s;
  };

  const best = (edges: Set<number>, targets: Set<number>) => {
    let adj = 0;
    let guides: number[] = [];
    let found = false;
    for (const m of edges) {
      for (const t of targets) {
        const a = t - m;
        if (Math.abs(a) > threshold) continue;
        if (!found || Math.abs(a) < Math.abs(adj)) {
          found = true;
          adj = a;
          guides = [t];
        } else if (found && Math.abs(a) === Math.abs(adj) && !guides.includes(t)) {
          guides.push(t);
        }
      }
    }
    return { adj: found ? adj : 0, guides };
  };

  const bx = best(edgesOf(mv, "x"), vx);
  const by = best(edgesOf(mv, "y"), hy);
  return {
    dx: dx + bx.adj,
    dy: dy + by.adj,
    guides: { v: bx.guides, h: by.guides },
  };
}

/** 平移元素（拖拽/方向键微调共用） */
export function translateEl(el: SpecEl, dx: number, dy: number): void {
  if (el.type === "line" || el.type === "arrow") {
    el.x1 = Math.round(Number(el.x1 ?? 0) + dx);
    el.y1 = Math.round(Number(el.y1 ?? 0) + dy);
    el.x2 = Math.round(Number(el.x2 ?? 0) + dx);
    el.y2 = Math.round(Number(el.y2 ?? 0) + dy);
    return;
  }
  el.x = Math.round(Number(el.x ?? 0) + dx);
  el.y = Math.round(Number(el.y ?? 0) + dy);
}
