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
  // 组件库（F6，与 src/snap2edit/components.py 同语义）
  name?: string;          // icon 图标名
  rows?: number;          // matrix-cell
  cols?: number;
  gap?: number;
  texts?: string[];
  depth?: number;         // cube
  title?: string;         // flow-box
  band?: number;
  band_fill?: string | null;
  title_color?: string | null;
  title_size?: number;
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

/** 元素旋转角（度、顺时针；与引擎 svgout._rot 同语义） */
function rotOf(el: SpecEl): number {
  const r = el.rotate;
  return typeof r === "number" && Number.isFinite(r) ? ((r % 360) + 360) % 360 : 0;
}

function rotAttr(deg: number, cx: number, cy: number): string {
  return deg ? ` transform="rotate(${n(deg)} ${n(cx)} ${n(cy)})"` : "";
}

function esc(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
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
  centered: boolean,
  rotC?: { deg: number; cx: number; cy: number }
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
  const ra = rotC ? rotAttr(rotC.deg, rotC.cx, rotC.cy) : "";
  return (
    `<text id="${esc(tid)}" font-size="${n(size)}" fill="${esc(color)}" ` +
    `font-weight="${weight}" text-anchor="${anchor}"${ra}>${tspans}</text>`
  );
}

function boxSvg(spec: SpecDoc, el: SpecEl): string {
  const pal = spec.palette ?? {};
  const { x = 0, y = 0, w = 0, h = 0 } = el;
  const rot = rotOf(el);
  const ra = rotAttr(rot, x + w / 2, y + h / 2);
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
      `rx="${n(w / 2)}" ry="${n(h / 2)}" fill="${esc(fill)}"${sAttr}${ra}/>`;
  } else {
    const rxV = el.type === "pill" ? h / 2 : (el.rx ?? Math.min(w, h) * 0.1);
    const rx = el.type === "rect" ? "" : ` rx="${n(rxV)}"`;
    out =
      `<rect id="${esc(el.id)}" x="${n(x)}" y="${n(y)}" ` +
      `width="${n(w)}" height="${n(h)}"${rx} fill="${esc(fill)}"${sAttr}${ra}/>`;
  }
  if (el.text)
    out += textSvg(spec, el, `${el.id}-text`, x + w / 2, y + h / 2, true,
      rot ? { deg: rot, cx: x + w / 2, cy: y + h / 2 } : undefined);
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

/* ---------------- 组件库（F6）：与 src/snap2edit/components.py 同源移植 ---------------- */

type Poly = [number, number][];

function hexRgb(color: string): [number, number, number] {
  const h = String(color).replace("#", "");
  return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
}

/** 颜色明暗演算：factor>0 向白色靠近，<0 向黑色加深（与 components.shade 同语义） */
export function shade(color: string, factor: number): string {
  const [r, g, b] = hexRgb(color);
  const adj = (c: number) => (factor >= 0 ? c + (255 - c) * factor : c * (1 + factor));
  const f = (c: number) => Math.max(0, Math.min(255, Math.round(adj(c))));
  return "#" + [f(r), f(g), f(b)].map((c) => c.toString(16).padStart(2, "0").toUpperCase()).join("");
}

/** 按背景亮度返回可读文字色（与 components.contrast_text 同语义） */
export function contrastText(bg: string): string {
  const [r, g, b] = hexRgb(bg);
  const lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return lum > 0.62 ? "#1F2937" : "#FFFFFF";
}

/** 立方体三块面片（与 components.cube_faces 同语义，全部收在包围盒内） */
export function cubeFaces(
  x: number, y: number, w: number, h: number, depth?: number
): { depth: number; top: Poly; side: Poly; front: [number, number, number, number] } {
  const d = Math.max(0, Math.min(depth ?? Math.min(w, h) * 0.2, Math.min(w, h) * 0.5));
  return {
    depth: d,
    top: [[x, y + d], [x + d, y], [x + w, y], [x + w - d, y + d]],
    side: [[x + w - d, y + d], [x + w, y], [x + w, y + h - d], [x + w - d, y + h]],
    front: [x, y + d, w - d, h - d],
  };
}

/** rows×cols 均分格子（行优先；与 components.matrix_cells 同语义） */
export function matrixCells(
  x: number, y: number, w: number, h: number, rows: number, cols: number, gap = 0
): [number, number, number, number][] {
  const g = Math.max(0, gap);
  const cw = (w - g * (cols - 1)) / cols;
  const ch = (h - g * (rows - 1)) / rows;
  const out: [number, number, number, number][] = [];
  for (let r = 0; r < rows; r++)
    for (let c = 0; c < cols; c++) out.push([x + c * (cw + g), y + r * (ch + g), cw, ch]);
  return out;
}

const ngon = (cx: number, cy: number, n: number, r: number, rot = 0): Poly =>
  Array.from({ length: n }, (_, i) => [
    cx + r * Math.cos(rot + (2 * Math.PI * i) / n),
    cy + r * Math.sin(rot + (2 * Math.PI * i) / n),
  ] as [number, number]);

const star = (cx: number, cy: number, n: number, ro: number, ri: number, rot = 0): Poly => {
  const pts: Poly = [];
  for (let i = 0; i < n * 2; i++) {
    const ang = rot + (Math.PI * i) / n;
    const r = i % 2 === 0 ? ro : ri;
    pts.push([cx + r * Math.cos(ang), cy + r * Math.sin(ang)]);
  }
  return pts;
};

/** 参数化图标库（与 components.ICONS 同源数据；fill=实心 / ring=空心描边 / stroke=开放折线） */
export const ICONS: Record<string, [string, Poly][]> = {
  chart: [
    ["fill", [[10, 84], [90, 84], [90, 90], [10, 90]]],
    ["fill", [[16, 52], [28, 52], [28, 84], [16, 84]]],
    ["fill", [[40, 28], [52, 28], [52, 84], [40, 84]]],
    ["fill", [[64, 60], [76, 60], [76, 84], [64, 84]]],
  ],
  network: [
    ["fill", [[48, 22], [52, 22], [52, 38], [48, 38]]],
    ["fill", [[48, 62], [52, 62], [52, 78], [48, 78]]],
    ["fill", [[22, 48], [38, 48], [38, 52], [22, 52]]],
    ["fill", [[62, 48], [78, 48], [78, 52], [62, 52]]],
    ["fill", [[50, 38], [62, 50], [50, 62], [38, 50]]],
    ["fill", [[50, 4], [59, 13], [50, 22], [41, 13]]],
    ["fill", [[4, 50], [13, 59], [22, 50], [13, 41]]],
    ["fill", [[78, 50], [87, 59], [96, 50], [87, 41]]],
    ["fill", [[41, 87], [50, 96], [59, 87], [50, 78]]],
  ],
  sparkle: [
    ["fill", [[50, 4], [59, 41], [96, 50], [59, 59], [50, 96], [41, 59], [4, 50], [41, 41]]],
  ],
  lightning: [
    ["fill", [[58, 4], [26, 52], [44, 52], [38, 96], [74, 40], [52, 40]]],
  ],
  gear: [
    ["fill", star(50, 50, 8, 46, 34, -Math.PI / 2)],
    ["ring", ngon(50, 50, 12, 15)],
  ],
  doc: [
    ["ring", [[24, 6], [62, 6], [76, 20], [76, 94], [24, 94]]],
    ["fill", [[62, 6], [62, 20], [76, 20]]],
    ["fill", [[34, 34], [66, 34], [66, 40], [34, 40]]],
    ["fill", [[34, 50], [66, 50], [66, 56], [34, 56]]],
    ["fill", [[34, 66], [58, 66], [58, 72], [34, 72]]],
  ],
  user: [
    ["fill", ngon(50, 30, 8, 17, -Math.PI / 2)],
    ["fill", [[18, 94], [20, 72], [34, 61], [66, 61], [80, 72], [82, 94]]],
  ],
  check: [
    ["fill", [[12, 52], [24, 40], [44, 66], [72, 18], [88, 30], [46, 90]]],
  ],
  target: [
    ["ring", ngon(50, 50, 16, 44)],
    ["ring", ngon(50, 50, 16, 28)],
    ["fill", ngon(50, 50, 12, 12)],
  ],
  brain: [
    ["fill", [[20, 72], [12, 58], [14, 42], [22, 30], [34, 22], [48, 18],
              [62, 20], [74, 28], [82, 40], [84, 54], [78, 66], [66, 74],
              [50, 76], [34, 74]]],
    ["stroke", [[48, 20], [47, 38], [50, 54], [48, 75]]],
    ["stroke", [[24, 44], [31, 37], [39, 43]]],
    ["stroke", [[25, 60], [33, 54], [41, 60]]],
    ["stroke", [[57, 38], [64, 32], [71, 38]]],
    ["stroke", [[57, 56], [65, 50], [72, 57]]],
  ],
};

export const ICON_NAMES: string[] = Object.keys(ICONS).sort();

/** 图标 contain 缩放 + 居中（与 components.icon_parts 同语义） */
export function iconParts(name: string, x: number, y: number, w: number, h: number): [string, Poly][] {
  const parts = ICONS[name] ?? [];
  const s = Math.min(w, h) / 100;
  const dx = x + (w - 100 * s) / 2;
  const dy = y + (h - 100 * s) / 2;
  return parts.map(([kind, pts]) => [kind, pts.map(([px, py]) => [dx + px * s, dy + py * s] as [number, number])]);
}

const ptsAttr = (pts: Poly): string => pts.map(([px, py]) => `${n(px)},${n(py)}`).join(" ");

function cubeSvg(spec: SpecDoc, el: SpecEl): string {
  const x = Number(el.x ?? 0), y = Number(el.y ?? 0), w = Number(el.w ?? 0), h = Number(el.h ?? 0);
  const faces = cubeFaces(x, y, w, h, el.depth);
  const base = el.fill || spec.palette?.accent || "#2B6CB0";
  const sAttr = el.stroke ? ` stroke="${esc(el.stroke)}" stroke-width="${n(Number(el.stroke_width ?? 1))}"` : "";
  const [fx, fy, fw, fh] = faces.front;
  let out =
    `<polygon id="${esc(el.id)}-top" points="${ptsAttr(faces.top)}" fill="${esc(shade(base, 0.25))}"${sAttr}/>` +
    `<polygon id="${esc(el.id)}-side" points="${ptsAttr(faces.side)}" fill="${esc(shade(base, -0.22))}"${sAttr}/>` +
    `<rect id="${esc(el.id)}" x="${n(fx)}" y="${n(fy)}" width="${n(fw)}" height="${n(fh)}" fill="${esc(base)}"${sAttr}/>`;
  if (el.text)
    out += textSvg(spec, el, `${el.id}-text`, fx + fw / 2, fy + fh / 2, true);
  return out;
}

function matrixSvg(spec: SpecDoc, el: SpecEl): string {
  const pal = spec.palette ?? {};
  const x = Number(el.x ?? 0), y = Number(el.y ?? 0), w = Number(el.w ?? 0), h = Number(el.h ?? 0);
  const rows = Math.max(1, Math.round(Number(el.rows ?? 1)));
  const cols = Math.max(1, Math.round(Number(el.cols ?? 1)));
  const cells = matrixCells(x, y, w, h, rows, cols, Number(el.gap ?? 0));
  let fill: string;
  if (el.fill == null) fill = "fill" in el ? "none" : pal.card || "#FFFFFF";
  else fill = el.fill;
  const sAttr = el.stroke ? ` stroke="${esc(el.stroke)}" stroke-width="${n(Number(el.stroke_width ?? 1))}"` : "";
  const out: string[] = [];
  cells.forEach(([cx, cy, cw, ch], k) => {
    const r = Math.floor(k / cols) + 1;
    const c = (k % cols) + 1;
    const rxV = el.rx ?? Math.min(cw, ch) * 0.12;
    out.push(`<rect id="${esc(el.id)}-r${r}c${c}" x="${n(cx)}" y="${n(cy)}" width="${n(cw)}" height="${n(ch)}" rx="${n(rxV)}" fill="${esc(fill)}"${sAttr}/>`);
  });
  (el.texts ?? []).forEach((txt, k) => {
    if (k >= cells.length) return;
    const [cx, cy, cw, ch] = cells[k];
    const r = Math.floor(k / cols) + 1;
    const c = (k % cols) + 1;
    const tcolor = el.color || (fill !== "none" ? contrastText(fill) : null) || pal.primary || "#1F2937";
    const cellEl: SpecEl = { ...el, text: String(txt), color: tcolor };
    out.push(textSvg(spec, cellEl, `${el.id}-r${r}c${c}-text`, cx + cw / 2, cy + ch / 2, true));
  });
  return out.join("");
}

function flowboxSvg(spec: SpecDoc, el: SpecEl): string {
  const pal = spec.palette ?? {};
  const x = Number(el.x ?? 0), y = Number(el.y ?? 0), w = Number(el.w ?? 0), h = Number(el.h ?? 0);
  let base: string;
  if (el.fill == null) base = "fill" in el ? "none" : pal.card || "#FFFFFF";
  else base = el.fill;
  const sAttr = el.stroke ? ` stroke="${esc(el.stroke)}" stroke-width="${n(Number(el.stroke_width ?? 1))}"` : "";
  const rxV = el.rx ?? Math.min(w, h) * 0.1;
  let out = `<rect id="${esc(el.id)}" x="${n(x)}" y="${n(y)}" width="${n(w)}" height="${n(h)}" rx="${n(rxV)}" fill="${esc(base)}"${sAttr}/>`;
  const bh = el.title ? h * Number(el.band ?? 0.3) : 0;
  if (bh) {
    const bandFill = el.band_fill || shade(base !== "none" ? base : "#94A3B8", -0.18);
    const r = Math.min(rxV, bh);
    const band =
      `M ${n(x + r)} ${n(y)} L ${n(x + w - r)} ${n(y)} ` +
      `Q ${n(x + w)} ${n(y)} ${n(x + w)} ${n(y + r)} ` +
      `L ${n(x + w)} ${n(y + bh)} L ${n(x)} ${n(y + bh)} ` +
      `L ${n(x)} ${n(y + r)} Q ${n(x)} ${n(y)} ${n(x + r)} ${n(y)} Z`;
    out += `<path id="${esc(el.id)}-band" d="${band}" fill="${esc(bandFill)}"/>`;
    const titleEl: SpecEl = {
      id: `${el.id}-title`, type: "text",
      size: el.title_size ?? el.size ?? 16, text: String(el.title),
      color: el.title_color || contrastText(bandFill), bold: true,
    };
    out += textSvg(spec, titleEl, `${el.id}-title`, x + w / 2, y + bh / 2, true);
  }
  if (el.text || (el.lines && el.lines.length)) {
    out += textSvg(spec, el, `${el.id}-text`, x + w / 2, y + bh + (h - bh) / 2, true);
  }
  return out;
}

function iconSvg(spec: SpecDoc, el: SpecEl): string {
  const pal = spec.palette ?? {};
  const color = el.fill || pal.accent || "#2B6CB0";
  const w = Number(el.w ?? 0), h = Number(el.h ?? 0);
  const scale = Math.min(w, h) / 100;
  const sw = el.stroke_width || Math.max(1, 4 * scale);
  const out: string[] = [];
  iconParts(String(el.name ?? ""), Number(el.x ?? 0), Number(el.y ?? 0), w, h).forEach(([kind, pts], i) => {
    const pid = `${el.id}-${i}`;
    const p = ptsAttr(pts);
    if (kind === "fill") out.push(`<polygon id="${esc(pid)}" points="${p}" fill="${esc(color)}"/>`);
    else if (kind === "ring")
      out.push(`<polygon id="${esc(pid)}" points="${p}" fill="none" stroke="${esc(color)}" stroke-width="${n(sw)}"/>`);
    else
      out.push(`<polyline id="${esc(pid)}" points="${p}" fill="none" stroke="${esc(color)}" stroke-width="${n(sw)}" stroke-linecap="round" stroke-linejoin="round"/>`);
  });
  return out.join("");
}

/** 单元素 → SVG 片段（与 svgout.render_element 同语义） */
export function renderElementSvg(spec: SpecDoc, el: SpecEl): string {
  switch (el.type) {
    case "rect":
    case "rrect":
    case "pill":
    case "circle":
      return boxSvg(spec, el);
    case "text": {
      const rot = rotOf(el);
      return textSvg(spec, el, el.id, Number(el.x ?? 0), Number(el.y ?? 0), false,
        rot ? { deg: rot, cx: Number(el.x ?? 0), cy: Number(el.y ?? 0) } : undefined);
    }
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
    case "cube":
      return cubeSvg(spec, el);
    case "matrix-cell":
      return matrixSvg(spec, el);
    case "flow-box":
      return flowboxSvg(spec, el);
    case "icon":
      return iconSvg(spec, el);
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

/** 从元素重建 texts 清单（与元素文案严格一致，保证门1可过；含组件库文字） */
export function regenTexts(spec: SpecDoc): string[] {
  const out: string[] = [];
  const push = (t: unknown) => {
    const s = typeof t === "string" ? t : "";
    if (s && !out.includes(s)) out.push(s);
  };
  for (const el of spec.elements ?? []) {
    if (el.type === "flow-box" && el.title) push(el.title); // 标题先于正文（与引擎 texts_of 同序）
    for (const t of [elText(el)]) push(t);
    if (el.type === "matrix-cell" && Array.isArray(el.texts)) {
      for (const t of el.texts) push(t);
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
