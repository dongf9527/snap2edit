"use client";

// web/app/studio/editor.tsx —— spec 可视化编辑器（PRD F9 → v0.4 studio 页）。
// 三栏布局：元素列表 / SVG 画布（点选·框选多选·拖拽吸附·方向键微调）/ 属性面板（含批量对齐/等距）；
// YAML 源码为唯一事实源（双向同步：属性编辑 → 重新序列化；源码编辑 → 画布重渲）。
// 画布渲染与引擎 svgout.py 同语义（web/lib/canvas.ts），正式产物仍由 Python 引擎输出；
// 构建出口双通道：/api/build 单次校验、/api/refine 自动回询迭代（最终 spec 写回编辑器）。

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { parse as yamlParse } from "yaml";
import {
  dumpSpecYaml,
  ELEMENT_TYPES,
  validateSpecYaml,
  type ElementType,
} from "@/lib/spec";
import {
  blankSpec,
  computeSnap,
  elText,
  ICON_NAMES,
  regenTexts,
  renderSpecSvg,
  syncTextOnEdit,
  translateEl,
  elBBox,
  type SnapGuides,
  type SpecDoc,
  type SpecEl,
} from "@/lib/canvas";
import { streamApi, type BuildEvent, type RenderReport } from "@/lib/api";

const DRAFT_KEY = "snap2edit.studio.draft";
const HANDOFF_KEY = "snap2edit.studio.spec";
const SNAP_T_KEY = "snap2edit.studio.snapT";

const BOX_TYPES = ["rect", "rrect", "pill", "circle"] as const;
const SEG_TYPES = ["line", "arrow"] as const;
/** 可旋转类型：复合组件多单元旋转在两产线间易漂移，引擎不支持（与 spec.py 同源） */
const ROTATABLE_TYPES = [...BOX_TYPES, "text"] as const;
const isBoxEl = (el: SpecEl) =>
  ["rect", "rrect", "pill", "circle", "cube", "matrix-cell", "flow-box", "icon"].includes(String(el.type));
const isRotatableEl = (el: SpecEl) =>
  (ROTATABLE_TYPES as readonly string[]).includes(String(el.type));

interface Artifacts {
  jobId: string;
  ok: boolean;
  hasPdf: boolean;
}

interface MarqueeState {
  ax: number;
  ay: number;
  base: string[];
  rect: { x: number; y: number; w: number; h: number };
}

interface RefImage {
  dataUrl: string;
  meta: { width: number; height: number; filename?: string };
}

type HandleKind =
  | `resize-${"n" | "s" | "e" | "w" | "nw" | "ne" | "sw" | "se"}`
  | `scale-${"nw" | "ne" | "sw" | "se"}`
  | "rotate"
  | "pt-1"
  | "pt-2";

interface ResizeCtx {
  ids: string[];
  fx: number;
  fy: number;
  px0: number;
  py0: number;
  axX: boolean;
  axY: boolean;
  snap: Record<string, SpecEl>;
}

interface RotateCtx {
  ids: string[];
  cx: number;
  cy: number;
  a0: number;
  snap: Record<string, SpecEl>;
}

interface BBox {
  x: number;
  y: number;
  w: number;
  h: number;
}

/** 旋转角度读出气泡状态：文案 + 画布坐标（跟随指针） */
interface RotHud {
  text: string;
  px: number;
  py: number;
}

const R1 = (v: number): number => Math.round(v * 10) / 10;

/**
 * 旋转读出气泡文案：
 * 单选盒子/文本 → 归一化终角 ∠（与烘焙结果一致）+ 增量 Δ；
 * 线段（rotate 键不生效）与多选（各元素终角不同）→ 只给增量 Δ；
 * Shift 步进时附提示。
 */
function rotHudText(rr: RotateCtx, delta: number, shift: boolean): string {
  const fmt = (d: number) => `${d > 0 ? "+" : d < 0 ? "-" : "±"}${R1(Math.abs(d))}°`;
  const step = shift ? " · 15°步进" : "";
  if (rr.ids.length === 1) {
    const s = rr.snap[rr.ids[0]];
    if (!isSegEl(s)) {
      const total = R1((((Number(s.rotate ?? 0) + delta) % 360) + 360) % 360);
      return `∠ ${total}°（Δ ${fmt(delta)}）${step}`;
    }
    return `Δ ${fmt(delta)}${step}`;
  }
  return `Δ ${fmt(delta)} · ${rr.ids.length}个${step}`;
}

function unionBBox(bs: BBox[]): BBox {
  const x = Math.min(...bs.map((b) => b.x));
  const y = Math.min(...bs.map((b) => b.y));
  return {
    x,
    y,
    w: Math.max(...bs.map((b) => b.x + b.w)) - x,
    h: Math.max(...bs.map((b) => b.y + b.h)) - y,
  };
}

const isSegEl = (el: SpecEl) => el.type === "line" || el.type === "arrow";

/** 深拷贝（spec 均为 JSON 安全结构） */
function clone<T>(v: T): T {
  return JSON.parse(JSON.stringify(v)) as T;
}

function nextId(doc: SpecDoc): string {
  const ids = new Set((doc.elements ?? []).map((e) => e.id));
  let i = (doc.elements?.length ?? 0) + 1;
  while (ids.has(`e${i}`)) i += 1;
  return `e${i}`;
}

export default function StudioEditor() {
  const [yaml, setYaml] = useState<string>("");
  const [selIds, setSelIds] = useState<string[]>([]);
  const [hover, setHover] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [showYaml, setShowYaml] = useState(true);
  const [copied, setCopied] = useState(false);
  const [hasDraft, setHasDraft] = useState(false);
  const [interacting, setInteracting] = useState(false);
  const [marquee, setMarquee] = useState<MarqueeState["rect"] | null>(null);
  const [guides, setGuides] = useState<SnapGuides>({ v: [], h: [] });
  const [snapT, setSnapT] = useState(8);
  const [rotHud, setRotHud] = useState<RotHud | null>(null);

  // 构建与预览（复用 /api/build 与 /api/refine）
  const [buildBusy, setBuildBusy] = useState(false);
  const [refineBusy, setRefineBusy] = useState(false);
  const busy = buildBusy || refineBusy;
  const [maxRounds, setMaxRounds] = useState(2);
  const [refImg, setRefImg] = useState<RefImage | null>(null);
  const [roundsDone, setRoundsDone] = useState<number | null>(null);
  const [buildLog, setBuildLog] = useState<string[]>([]);
  const [report, setReport] = useState<RenderReport | null>(null);
  const [art, setArt] = useState<Artifacts | null>(null);
  const [buildError, setBuildError] = useState<string | null>(null);

  const fileRef = useRef<HTMLInputElement>(null);
  const imgRef = useRef<HTMLInputElement>(null);
  const svgWrapRef = useRef<HTMLDivElement>(null);
  const dragRef = useRef<{ ids: string[]; sx: number; sy: number } | null>(null);
  const marqueeRef = useRef<MarqueeState | null>(null);
  const snapRef = useRef<{ dx: number; dy: number }>({ dx: 0, dy: 0 });
  const resizeRef = useRef<ResizeCtx | null>(null);
  const resizeScaleRef = useRef<{ sx: number; sy: number }>({ sx: 1, sy: 1 });
  const rotateRef = useRef<RotateCtx | null>(null);
  const rotDeltaRef = useRef(0);
  const ptRef = useRef<{ id: string; which: 1 | 2 } | null>(null);
  const rafRef = useRef(0);

  // —— 启动：工作台带入 / 草稿检测 ——
  useEffect(() => {
    const handed = sessionStorage.getItem(HANDOFF_KEY);
    if (handed) {
      sessionStorage.removeItem(HANDOFF_KEY);
      setYaml(handed);
      setNotice("已从工作台带入 spec，可继续可视化编辑");
      return;
    }
    setYaml(dumpSpecYaml(blankSpec()));
    if (localStorage.getItem(DRAFT_KEY)) setHasDraft(true);
    try {
      const raw = localStorage.getItem(SNAP_T_KEY);
      if (raw != null) {
        const v = Number(raw);
        if (Number.isFinite(v) && v >= 0 && v <= 64) setSnapT(Math.round(v));
      }
    } catch {
      /* 存储异常忽略 */
    }
  }, []);

  // —— 草稿自动保存 ——
  useEffect(() => {
    if (!yaml) return;
    const t = setTimeout(() => {
      try {
        localStorage.setItem(DRAFT_KEY, yaml);
        setHasDraft(true);
      } catch {
        /* 存储异常忽略 */
      }
    }, 800);
    return () => clearTimeout(t);
  }, [yaml]);

  // —— 解析（YAML → 文档）——
  const { doc, parseError } = useMemo(() => {
    if (!yaml.trim()) return { doc: null as SpecDoc | null, parseError: null as string | null };
    try {
      const d = yamlParse(yaml);
      if (!d || typeof d !== "object") return { doc: null, parseError: "spec 根节点必须是对象" };
      return { doc: d as SpecDoc, parseError: null };
    } catch (e) {
      return { doc: null, parseError: e instanceof Error ? e.message : String(e) };
    }
  }, [yaml]);

  const validation = useMemo(() => (yaml.trim() ? validateSpecYaml(yaml) : null), [yaml]);

  const svg = useMemo(() => {
    if (!doc) return "";
    try {
      return renderSpecSvg(doc, { selectedIds: selIds, hoverId: hover });
    } catch {
      return "";
    }
  }, [doc, selIds, hover]);

  const canvasW = Number(doc?.canvas?.width ?? 1280);
  const canvasH = Number(doc?.canvas?.height ?? 720);
  const elements = doc?.elements ?? [];
  const selectedEl = selIds.length === 1 ? (elements.find((e) => e.id === selIds[0]) ?? null) : null;

  /** 统一编辑入口：克隆 → 变更 → 重序列化（YAML 始终是唯一事实源） */
  const applyEdit = useCallback(
    (fn: (d: SpecDoc) => void) => {
      if (!doc) return;
      const d = clone(doc);
      fn(d);
      setYaml(dumpSpecYaml(d));
    },
    [doc]
  );

  const patchEl = useCallback(
    (id: string, patch: Partial<SpecEl>, oldText?: string) => {
      applyEdit((d) => {
        const el = (d.elements ?? []).find((e) => e.id === id);
        if (!el) return;
        Object.assign(el, patch);
        if (patch.text !== undefined && oldText !== undefined && oldText !== patch.text) {
          syncTextOnEdit(d, oldText, patch.text);
        }
      });
    },
    [applyEdit]
  );

  /** 批量平移（拖拽提交 / 方向键微调整组共用，单次 applyEdit 避免闭包陣旧） */
  const nudgeMany = useCallback(
    (ids: string[], dx: number, dy: number) => {
      if (!ids.length || (!dx && !dy)) return;
      applyEdit((d) => {
        for (const id of ids) {
          const el = (d.elements ?? []).find((e) => e.id === id);
          if (el) translateEl(el, dx, dy);
        }
      });
    },
    [applyEdit]
  );

  const removeMany = useCallback(
    (ids: string[]) => {
      if (!ids.length) return;
      const s = new Set(ids);
      applyEdit((d) => {
        d.elements = (d.elements ?? []).filter((e) => !s.has(e.id));
        d.texts = regenTexts(d);
      });
      setSelIds([]);
    },
    [applyEdit]
  );

  const nudge = useCallback((id: string, dx: number, dy: number) => nudgeMany([id], dx, dy), [nudgeMany]);

  const moveEl = useCallback(
    (id: string, dir: -1 | 1) => {
      applyEdit((d) => {
        const arr = d.elements ?? [];
        const i = arr.findIndex((e) => e.id === id);
        const j = i + dir;
        if (i < 0 || j < 0 || j >= arr.length) return;
        [arr[i], arr[j]] = [arr[j], arr[i]];
      });
    },
    [applyEdit]
  );

  const addEl = useCallback(
    (type: ElementType) => {
      if (!doc) return;
      const nid = nextId(doc);
      applyEdit((d) => {
        const cw = Number(d.canvas?.width ?? 1280);
        const ch = Number(d.canvas?.height ?? 720);
        let el: SpecEl;
        if (type === "text") {
          el = { id: nid, type, x: Math.round(cw * 0.1), y: Math.round(ch * 0.1), size: 20, text: "新文本" };
        } else if ((SEG_TYPES as readonly string[]).includes(type)) {
          el = {
            id: nid, type,
            x1: Math.round(cw * 0.2), y1: Math.round(ch * 0.6),
            x2: Math.round(cw * 0.5), y2: Math.round(ch * 0.6),
          };
        } else {
          el = { id: nid, type, x: Math.round(cw * 0.15), y: Math.round(ch * 0.2), w: 240, h: 120, fill: "#F7F9FC" };
          if (type === "rrect") el.rx = 10;
          if (type === "circle") { el.w = 120; el.h = 120; }
          if (type === "cube") {
            el = { id: nid, type, x: el.x, y: el.y, w: 180, h: 150, fill: "#2B6CB0", text: "立方体", size: 15, color: "#FFFFFF" };
          }
          if (type === "matrix-cell") {
            el = {
              id: nid, type, x: el.x, y: el.y, w: 300, h: 160, rows: 2, cols: 3, gap: 8,
              fill: "#2B6CB0", texts: ["格子一", "格子二", "格子三"], size: 14,
            };
          }
          if (type === "flow-box") {
            el = {
              id: nid, type, x: el.x, y: el.y, w: 260, h: 110, fill: "#EFF6FF", stroke: "#2B6CB0",
              band: 0.32, title: "流程标题", text: "流程正文", size: 13,
            };
          }
          if (type === "icon") {
            el = { id: nid, type, x: el.x, y: el.y, w: 80, h: 80, name: "chart", fill: "#2B6CB0" };
          }
        }
        d.elements = [...(d.elements ?? []), el];
      });
      setSelIds([nid]);
      setNotice(`已新增 ${type} 元素`);
    },
    [applyEdit, doc]
  );

  // —— 画布交互：点选 / 框选多选 / 拖拽吸附 / 手柄缩放旋转 ——
  const canvasPoint = useCallback(
    (clientX: number, clientY: number) => {
      const r = svgWrapRef.current?.querySelector("svg")?.getBoundingClientRect();
      const scale = canvasW / (r?.width || 1);
      return { x: (clientX - (r?.left ?? 0)) * scale, y: (clientY - (r?.top ?? 0)) * scale };
    },
    [canvasW]
  );

  const applyTransform = useCallback((ids: string[], dx: number, dy: number) => {
    const svgEl = svgWrapRef.current?.querySelector("svg");
    if (!svgEl) return;
    for (const id of ids) {
      svgEl.querySelectorAll(`[id="${id}"],[id="${id}-text"],[id="${id}-head"]`).forEach((node) => {
        (node as SVGElement).style.transform = dx || dy ? `translate(${dx}px, ${dy}px)` : "";
      });
    }
  }, []);

  /** 逐节点遍历选中元素的 SVG 节点（主形状 + 内嵌文本 + 箭头头） */
  const forEachNode = useCallback((ids: string[], fn: (el: SVGElement) => void) => {
    const svgEl = svgWrapRef.current?.querySelector("svg");
    if (!svgEl) return;
    for (const id of ids) {
      svgEl.querySelectorAll(`[id="${id}"],[id="${id}-text"],[id="${id}-head"]`).forEach((node) => fn(node as SVGElement));
    }
  }, []);

  const clearNodeTransform = useCallback(
    (ids: string[]) => {
      forEachNode(ids, (node) => {
        node.style.transform = "";
        node.style.transformOrigin = "";
      });
    },
    [forEachNode]
  );

  /** 旋转中心：单盒子=自身中心；单文本=锚点；单线段=中点；多选=选区包围盒中心 */
  const rotCenterOf = useCallback((snap: Record<string, SpecEl>, gb: BBox) => {
    const ids = Object.keys(snap);
    if (ids.length === 1) {
      const el = snap[ids[0]];
      if (isBoxEl(el)) return { x: Number(el.x ?? 0) + Number(el.w ?? 0) / 2, y: Number(el.y ?? 0) + Number(el.h ?? 0) / 2 };
      if (isSegEl(el)) return { x: (Number(el.x1 ?? 0) + Number(el.x2 ?? 0)) / 2, y: (Number(el.y1 ?? 0) + Number(el.y2 ?? 0)) / 2 };
      return { x: Number(el.x ?? 0), y: Number(el.y ?? 0) };
    }
    return { x: gb.x + gb.w / 2, y: gb.y + gb.h / 2 };
  }, []);

  /** 手柄按下：初始化缩放/旋转/端点上下文（快照冻结，松手烘焙） */
  const startHandle = useCallback(
    (kind: HandleKind, clientX: number, clientY: number) => {
      if (!doc) return;
      const p = canvasPoint(clientX, clientY);
      const snap: Record<string, SpecEl> = {};
      for (const el of doc.elements ?? []) if (selIds.includes(el.id)) snap[el.id] = clone(el);
      const ids = Object.keys(snap);
      if (!ids.length) return;
      const gb = unionBBox(ids.map((id) => elBBox(snap[id])));
      setInteracting(true);
      if (kind === "rotate") {
        const c = rotCenterOf(snap, gb);
        const rc: RotateCtx = {
          ids,
          cx: c.x,
          cy: c.y,
          a0: (Math.atan2(p.y - c.y, p.x - c.x) * 180) / Math.PI,
          snap,
        };
        rotateRef.current = rc;
        rotDeltaRef.current = 0;
        // 读出气泡随按下立即出现（Δ ±0°）
        setRotHud({ text: rotHudText(rc, 0, false), px: p.x, py: p.y });
      } else if (kind === "pt-1" || kind === "pt-2") {
        ptRef.current = { id: ids[0], which: kind === "pt-1" ? 1 : 2 };
      } else {
        const dir = kind.split("-")[1];
        const anchors: Record<string, [number, number, boolean, boolean]> = {
          nw: [gb.x + gb.w, gb.y + gb.h, true, true],
          ne: [gb.x, gb.y + gb.h, true, true],
          sw: [gb.x + gb.w, gb.y, true, true],
          se: [gb.x, gb.y, true, true],
          n: [gb.x + gb.w / 2, gb.y + gb.h, false, true],
          s: [gb.x + gb.w / 2, gb.y, false, true],
          e: [gb.x, gb.y + gb.h / 2, true, false],
          w: [gb.x + gb.w, gb.y + gb.h / 2, true, false],
        };
        const [fx, fy, axX, axY] = anchors[dir];
        resizeRef.current = { ids, fx, fy, px0: p.x, py0: p.y, axX, axY, snap };
        resizeScaleRef.current = { sx: 1, sy: 1 };
      }
    },
    [doc, selIds, canvasPoint, rotCenterOf]
  );

  /** 缩放烘焙：锚点固定，逐元素按 sx/sy 缩放几何（文本字号随 sy 缩放） */
  const bakeResize = useCallback(
    (rs: ResizeCtx, sx: number, sy: number) => {
      applyEdit((d) => {
        for (const el of d.elements ?? []) {
          const s = rs.snap[el.id];
          if (!s) continue;
          if (isBoxEl(el)) {
            el.x = Math.round(rs.fx + (Number(s.x ?? 0) - rs.fx) * sx);
            el.y = Math.round(rs.fy + (Number(s.y ?? 0) - rs.fy) * sy);
            el.w = Math.max(2, Math.round(Number(s.w ?? 0) * sx));
            el.h = Math.max(2, Math.round(Number(s.h ?? 0) * sy));
          } else if (isSegEl(el)) {
            el.x1 = Math.round(rs.fx + (Number(s.x1 ?? 0) - rs.fx) * sx);
            el.y1 = Math.round(rs.fy + (Number(s.y1 ?? 0) - rs.fy) * sy);
            el.x2 = Math.round(rs.fx + (Number(s.x2 ?? 0) - rs.fx) * sx);
            el.y2 = Math.round(rs.fy + (Number(s.y2 ?? 0) - rs.fy) * sy);
          } else {
            el.x = Math.round(rs.fx + (Number(s.x ?? 0) - rs.fx) * sx);
            el.y = Math.round(rs.fy + (Number(s.y ?? 0) - rs.fy) * sy);
            if (s.size != null) el.size = Math.max(4, Math.round(Number(s.size) * sy));
            if (s.w != null) el.w = Math.max(0, Math.round(Number(s.w) * sx));
          }
        }
      });
    },
    [applyEdit]
  );

  /** 旋转烘焙：单选绕自身中心/锚点/中点；多选各元素中心绕组中心旋转并叠加自身角度 */
  const bakeRotate = useCallback(
    (rr: RotateCtx, delta: number) => {
      applyEdit((d) => {
        const a = (delta * Math.PI) / 180;
        const cos = Math.cos(a);
        const sin = Math.sin(a);
        const setRot = (el: SpecEl, s: SpecEl) => {
          const r = R1(((((Number(s.rotate ?? 0) + delta) % 360) + 360) % 360));
          if (r === 0) delete el.rotate;
          else el.rotate = r;
        };
        for (const el of d.elements ?? []) {
          const s = rr.snap[el.id];
          if (!s) continue;
          if (isBoxEl(el)) {
            const cx0 = Number(s.x ?? 0) + Number(s.w ?? 0) / 2;
            const cy0 = Number(s.y ?? 0) + Number(s.h ?? 0) / 2;
            const ncx = rr.cx + (cx0 - rr.cx) * cos - (cy0 - rr.cy) * sin;
            const ncy = rr.cy + (cx0 - rr.cx) * sin + (cy0 - rr.cy) * cos;
            el.x = Math.round(ncx - Number(s.w ?? 0) / 2);
            el.y = Math.round(ncy - Number(s.h ?? 0) / 2);
            setRot(el, s);
          } else if (isSegEl(el)) {
            for (const [k1, k2] of [["x1", "y1"], ["x2", "y2"]] as const) {
              const px = Number(s[k1] ?? 0) - rr.cx;
              const py = Number(s[k2] ?? 0) - rr.cy;
              el[k1] = Math.round(rr.cx + px * cos - py * sin);
              el[k2] = Math.round(rr.cy + px * sin + py * cos);
            }
          } else {
            const px = Number(s.x ?? 0) - rr.cx;
            const py = Number(s.y ?? 0) - rr.cy;
            el.x = Math.round(rr.cx + px * cos - py * sin);
            el.y = Math.round(rr.cy + px * sin + py * cos);
            setRot(el, s);
          }
        }
      });
    },
    [applyEdit]
  );

  const onCanvasPointerDown = useCallback(
    (e: React.PointerEvent) => {
      if (!doc) return;
      (e.currentTarget as HTMLElement).setPointerCapture?.(e.pointerId);
      // 手柄优先：handle 是 wrap 内覆盖层，不参与画布选中/框选
      const handle = (e.target as HTMLElement).closest?.("[data-handle]") as HTMLElement | null;
      if (handle) {
        startHandle(handle.getAttribute("data-handle") as HandleKind, e.clientX, e.clientY);
        return;
      }
      const p = canvasPoint(e.clientX, e.clientY);
      const target = (e.target as SVGElement).closest("[id]");
      const raw = target?.getAttribute("id") ?? "";
      const hitId = raw ? raw.replace(/-(text|head)$/, "") : "";
      const hitOk = !!hitId && (doc.elements ?? []).some((x) => x.id === hitId);
      if (hitOk) {
        const extend = e.shiftKey || e.ctrlKey || e.metaKey;
        if (extend) {
          // Shift/Ctrl 加减选：只改选区，不启动拖拽
          setSelIds((prev) =>
            prev.includes(hitId) ? prev.filter((s) => s !== hitId) : [...prev, hitId]
          );
          return;
        }
        const ids = selIds.includes(hitId) ? selIds : [hitId];
        if (!selIds.includes(hitId)) setSelIds(ids);
        dragRef.current = { ids, sx: p.x, sy: p.y };
        snapRef.current = { dx: 0, dy: 0 };
        setInteracting(true);
      } else {
        // 空白处按下 → 框选（Shift 从现有选区累加）
        const base = e.shiftKey ? selIds : [];
        const rect = { x: p.x, y: p.y, w: 0, h: 0 };
        marqueeRef.current = { ax: p.x, ay: p.y, base, rect };
        if (!e.shiftKey) setSelIds([]);
        setMarquee(rect);
        setInteracting(true);
      }
    },
    [doc, selIds, canvasPoint, startHandle]
  );

  const onCanvasPointerMove = useCallback(
    (e: React.PointerEvent) => {
      const rs = resizeRef.current;
      const rr = rotateRef.current;
      const pt = ptRef.current;
      const dr = dragRef.current;
      const mr = marqueeRef.current;
      if ((!rs && !rr && !pt && !dr && !mr) || !doc) return;
      const p = canvasPoint(e.clientX, e.clientY);
      if (rs) {
        const dx0 = rs.px0 - rs.fx;
        const dy0 = rs.py0 - rs.fy;
        const sx = rs.axX && Math.abs(dx0) >= 2 ? Math.max(0.05, (p.x - rs.fx) / dx0) : 1;
        const sy = rs.axY && Math.abs(dy0) >= 2 ? Math.max(0.05, (p.y - rs.fy) / dy0) : 1;
        resizeScaleRef.current = { sx, sy };
        cancelAnimationFrame(rafRef.current);
        rafRef.current = requestAnimationFrame(() => {
          forEachNode(rs.ids, (node) => {
            node.style.transformOrigin = `${rs.fx}px ${rs.fy}px`;
            node.style.transform = `scale(${sx}, ${sy})`;
          });
        });
      } else if (rr) {
        const a = (Math.atan2(p.y - rr.cy, p.x - rr.cx) * 180) / Math.PI;
        let delta = a - rr.a0;
        if (e.shiftKey) delta = Math.round(delta / 15) * 15;
        rotDeltaRef.current = delta;
        // 角度实时读出：与烘焙同口径（Shift 量化后），指针动 ≥2px 或文案变化才重渲染
        const text = rotHudText(rr, delta, e.shiftKey);
        setRotHud((prev) =>
          prev && prev.text === text && Math.abs(prev.px - p.x) < 2 && Math.abs(prev.py - p.y) < 2
            ? prev
            : { text, px: p.x, py: p.y }
        );
        cancelAnimationFrame(rafRef.current);
        rafRef.current = requestAnimationFrame(() => {
          forEachNode(rr.ids, (node) => {
            node.style.transformOrigin = `${rr.cx}px ${rr.cy}px`;
            node.style.transform = `rotate(${delta}deg)`;
          });
        });
      } else if (pt) {
        // 线段端点直拖：绝对坐标实时提交（rAF 节流）
        cancelAnimationFrame(rafRef.current);
        rafRef.current = requestAnimationFrame(() => {
          applyEdit((d) => {
            const el = (d.elements ?? []).find((x) => x.id === pt.id);
            if (!el) return;
            if (pt.which === 1) {
              el.x1 = Math.round(p.x);
              el.y1 = Math.round(p.y);
            } else {
              el.x2 = Math.round(p.x);
              el.y2 = Math.round(p.y);
            }
          });
        });
      } else if (dr) {
        const rawDx = Math.round(p.x - dr.sx);
        const rawDy = Math.round(p.y - dr.sy);
        let dx = rawDx;
        let dy = rawDy;
        let g: SnapGuides = { v: [], h: [] };
        if ((rawDx || rawDy) && !e.altKey) {
          const moving = (doc.elements ?? []).filter((x) => dr.ids.includes(x.id));
          const s = computeSnap(moving, dr.ids, doc.elements ?? [], { w: canvasW, h: canvasH }, rawDx, rawDy, snapT);
          dx = s.dx;
          dy = s.dy;
          g = s.guides;
        }
        snapRef.current = { dx, dy };
        setGuides((prev) => (prev.v.join() === g.v.join() && prev.h.join() === g.h.join() ? prev : g));
        // 拖拽中：DOM transform 实时预览（不重渲 SVG），松手才提交 YAML
        cancelAnimationFrame(rafRef.current);
        rafRef.current = requestAnimationFrame(() => applyTransform(dr.ids, dx, dy));
      } else if (mr) {
        const rect = {
          x: Math.min(mr.ax, p.x),
          y: Math.min(mr.ay, p.y),
          w: Math.abs(p.x - mr.ax),
          h: Math.abs(p.y - mr.ay),
        };
        mr.rect = rect;
        setMarquee(rect);
      }
    },
    [doc, canvasPoint, canvasW, canvasH, snapT, applyTransform, applyEdit, forEachNode]
  );

  const onCanvasPointerUp = useCallback(
    () => {
      const rs = resizeRef.current;
      const rr = rotateRef.current;
      const pt = ptRef.current;
      const dr = dragRef.current;
      const mr = marqueeRef.current;
      resizeRef.current = null;
      rotateRef.current = null;
      ptRef.current = null;
      dragRef.current = null;
      marqueeRef.current = null;
      setInteracting(false);
      setGuides({ v: [], h: [] });
      setMarquee(null);
      setRotHud(null);
      cancelAnimationFrame(rafRef.current);
      if (rs) {
        clearNodeTransform(rs.ids);
        const { sx, sy } = resizeScaleRef.current;
        resizeScaleRef.current = { sx: 1, sy: 1 };
        if (sx !== 1 || sy !== 1) bakeResize(rs, sx, sy);
        return;
      }
      if (rr) {
        clearNodeTransform(rr.ids);
        const delta = rotDeltaRef.current;
        rotDeltaRef.current = 0;
        if (delta) bakeRotate(rr, delta);
        return;
      }
      if (pt) return; // 端点直拖已实时提交
      if (dr) {
        applyTransform(dr.ids, 0, 0);
        const { dx, dy } = snapRef.current;
        snapRef.current = { dx: 0, dy: 0 };
        if (dx || dy) nudgeMany(dr.ids, dx, dy);
        return;
      }
      if (mr && doc) {
        // 框选收口：与包围盒相交的元素全部入选；近乎点按（<4px）视为取消
        const tiny = mr.rect.w < 4 && mr.rect.h < 4;
        const hits = tiny
          ? []
          : (doc.elements ?? [])
              .filter((el) => {
                const b = elBBox(el);
                return (
                  b.x < mr.rect.x + mr.rect.w &&
                  b.x + b.w > mr.rect.x &&
                  b.y < mr.rect.y + mr.rect.h &&
                  b.y + b.h > mr.rect.y
                );
              })
              .map((el) => el.id);
        setSelIds([...new Set([...mr.base, ...hits])]);
      }
    },
    [doc, nudgeMany, applyTransform, clearNodeTransform, bakeResize, bakeRotate]
  );

  // —— 键盘微调（方向键 1px / Shift 10px，整组生效；Delete 删除所选）——
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
      if (!selIds.length) return;
      const step = e.shiftKey ? 10 : 1;
      const moves: Record<string, [number, number]> = {
        ArrowLeft: [-step, 0],
        ArrowRight: [step, 0],
        ArrowUp: [0, -step],
        ArrowDown: [0, step],
      };
      if (moves[e.key]) {
        e.preventDefault();
        nudgeMany(selIds, moves[e.key][0], moves[e.key][1]);
      } else if ((e.key === "Delete" || e.key === "Backspace") && !interacting) {
        e.preventDefault();
        removeMany(selIds);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [selIds, interacting, nudgeMany, removeMany]);

  /** 多选对齐：按选区包围盒对齐（left/hcenter/right/top/vcenter/bottom） */
  const alignSel = useCallback(
    (mode: "left" | "hcenter" | "right" | "top" | "vcenter" | "bottom") => {
      if (selIds.length < 2) return;
      applyEdit((d) => {
        const items = (d.elements ?? [])
          .filter((e) => selIds.includes(e.id))
          .map((el) => ({ el, bb: elBBox(el) }));
        if (items.length < 2) return;
        const minX = Math.min(...items.map((i) => i.bb.x));
        const maxX = Math.max(...items.map((i) => i.bb.x + i.bb.w));
        const minY = Math.min(...items.map((i) => i.bb.y));
        const maxY = Math.max(...items.map((i) => i.bb.y + i.bb.h));
        for (const { el, bb } of items) {
          let dx = 0;
          let dy = 0;
          if (mode === "left") dx = minX - bb.x;
          else if (mode === "right") dx = maxX - (bb.x + bb.w);
          else if (mode === "hcenter") dx = (minX + maxX) / 2 - (bb.x + bb.w / 2);
          else if (mode === "top") dy = minY - bb.y;
          else if (mode === "bottom") dy = maxY - (bb.y + bb.h);
          else if (mode === "vcenter") dy = (minY + maxY) / 2 - (bb.y + bb.h / 2);
          if (dx || dy) translateEl(el, Math.round(dx), Math.round(dy));
        }
      });
    },
    [applyEdit, selIds]
  );

  /** 多选等距分布（≥3 个生效）：首尾固定，中间按序均匀展开 */
  const distributeSel = useCallback(
    (axis: "h" | "v") => {
      if (selIds.length < 3) return;
      applyEdit((d) => {
        const items = (d.elements ?? [])
          .filter((e) => selIds.includes(e.id))
          .map((el) => ({ el, bb: elBBox(el) }));
        if (items.length < 3) return;
        const key = axis === "h" ? (i: (typeof items)[number]) => i.bb.x : (i: (typeof items)[number]) => i.bb.y;
        items.sort((a, b) => key(a) - key(b));
        const first = key(items[0]);
        const last = key(items[items.length - 1]);
        const n = items.length;
        for (let i = 1; i < n - 1; i++) {
          const target = first + ((last - first) * i) / (n - 1);
          const delta = Math.round(target - key(items[i]));
          if (delta) translateEl(items[i].el, axis === "h" ? delta : 0, axis === "v" ? delta : 0);
        }
      });
    },
    [applyEdit, selIds]
  );

  // —— 工具动作 ——
  const doNew = useCallback(() => {
    setYaml(dumpSpecYaml(blankSpec()));
    setSelIds([]);
    setNotice("已新建空白模板");
  }, []);

  const doImportFile = useCallback((f: File | undefined | null) => {
    if (!f) return;
    const fr = new FileReader();
    fr.onload = () => {
      setYaml(String(fr.result));
      setSelIds([]);
      setNotice(`已导入 ${f.name}`);
    };
    fr.readAsText(f);
  }, []);

  const doCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(yaml);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      setNotice("复制失败，请在 YAML 源码面板手动全选复制");
    }
  }, [yaml]);

  const doDownload = useCallback(() => {
    const name = String(doc?.project ?? "spec").replace(/[^\w\u4e00-\u9fff-]+/g, "_") || "spec";
    const blob = new Blob([yaml], { type: "text/yaml;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${name}.spec.yaml`;
    a.click();
    URL.revokeObjectURL(url);
  }, [doc, yaml]);

  const restoreDraft = useCallback(() => {
    const d = localStorage.getItem(DRAFT_KEY);
    if (d) {
      setYaml(d);
      setSelIds([]);
      setNotice("已恢复浏览器草稿");
    }
  }, []);

  // —— 构建出口①：/api/build 单次四门校验 ——
  const buildNow = useCallback(() => {
    if (!yaml.trim() || busy) return;
    setBuildBusy(true);
    setBuildLog([]);
    setReport(null);
    setArt(null);
    setBuildError(null);
    setRoundsDone(null);
    streamApi(
      "/api/build",
      { spec: yaml },
      (ev: BuildEvent) => {
        if (ev.type === "log") setBuildLog((p) => [...p.slice(-6), ev.msg]);
        else if (ev.type === "report") setReport(ev.report);
        else if (ev.type === "done") setArt({ jobId: ev.jobId, ok: ev.ok, hasPdf: ev.hasPdf });
      },
      "构建失败"
    )
      .catch((e) => setBuildError(e instanceof Error ? e.message : String(e)))
      .finally(() => setBuildBusy(false));
  }, [yaml, busy]);

  // —— 构建出口②：/api/refine 自动回询迭代（失败项回询 VLM 修正，最终 spec 写回编辑器）——
  const onImgPick = useCallback((f: File | undefined | null) => {
    if (!f) return;
    const fr = new FileReader();
    fr.onload = () => {
      const dataUrl = String(fr.result);
      const im = new Image();
      im.onload = () => {
        setRefImg({ dataUrl, meta: { width: im.naturalWidth, height: im.naturalHeight, filename: f.name } });
        setNotice(`已附加参考原图：${f.name}（${im.naturalWidth}×${im.naturalHeight}），迭代时将做视觉比对`);
      };
      im.onerror = () => setNotice("图片读取失败，请换一张");
      im.src = dataUrl;
    };
    fr.readAsDataURL(f);
  }, []);

  const refineNow = useCallback(() => {
    if (!yaml.trim() || busy) return;
    setRefineBusy(true);
    setBuildLog([]);
    setReport(null);
    setArt(null);
    setBuildError(null);
    setRoundsDone(null);
    const payload: Record<string, unknown> = { spec: yaml, maxRounds };
    if (refImg) {
      payload.image = refImg.dataUrl;
      payload.meta = refImg.meta;
    }
    streamApi(
      "/api/refine",
      payload,
      (ev: BuildEvent) => {
        if (ev.type === "log") setBuildLog((p) => [...p.slice(-8), ev.msg]);
        else if (ev.type === "round")
          setBuildLog((p) => [
            ...p,
            `▸ 第 ${ev.n} 轮 · ${ev.phase === "build" ? "构建校验" : ev.phase === "vlm" ? "AI 修正" : "复检"}${ev.note ? `：${ev.note}` : ""}`,
          ]);
        else if (ev.type === "report") setReport(ev.report);
        else if (ev.type === "spec") setBuildLog((p) => [...p, `▸ 第 ${ev.n} 轮修正 spec 已产出`]);
        else if (ev.type === "done") {
          setArt({ jobId: ev.jobId, ok: ev.ok, hasPdf: ev.hasPdf });
          setRoundsDone(ev.rounds ?? 0);
          if (ev.spec) {
            setYaml(ev.spec);
            setSelIds([]);
          }
          setNotice(
            `自动迭代完成：修正 ${ev.rounds ?? 0} 轮 · ${ev.ok ? "四道门全部通过 ✓" : "仍有未通过项 ✗"}，最终 spec 已写回编辑器`
          );
        }
      },
      "自动迭代失败"
    )
      .catch((e) => setBuildError(e instanceof Error ? e.message : String(e)))
      .finally(() => setRefineBusy(false));
  }, [yaml, busy, maxRounds, refImg]);

  const listText = (el: SpecEl) => {
    const t = elText(el);
    if (t) return t.length > 16 ? `${t.slice(0, 16)}…` : t;
    if (el.x1 != null) return `(${el.x1},${el.y1})→(${el.x2},${el.y2})`;
    return `(${el.x ?? 0}, ${el.y ?? 0}) ${el.w ?? ""}${el.w ? "×" : ""}${el.h ?? ""}`;
  };

  // —— 变换手柄（DOM 覆盖层；画布坐标 → 百分比定位） ——
  const selEls = elements.filter((e) => selIds.includes(e.id));
  const pct = (v: number, total: number) => `${(v / total) * 100}%`;
  let handleEls: React.ReactNode = null;
  if (selEls.length === 1) {
    const el = selEls[0];
    if (isBoxEl(el)) {
      const b = elBBox(el);
      const pts: [number, number, "nw" | "n" | "ne" | "e" | "se" | "s" | "sw" | "w"][] = [
        [b.x, b.y, "nw"], [b.x + b.w / 2, b.y, "n"], [b.x + b.w, b.y, "ne"],
        [b.x + b.w, b.y + b.h / 2, "e"], [b.x + b.w, b.y + b.h, "se"],
        [b.x + b.w / 2, b.y + b.h, "s"], [b.x, b.y + b.h, "sw"], [b.x, b.y + b.h / 2, "w"],
      ];
      handleEls = (
        <>
          {pts.map(([px, py, dir]) => (
            <span
              key={dir}
              data-handle={`resize-${dir}`}
              className={`hd hd-r hd-${dir}`}
              style={{ left: pct(px, canvasW), top: pct(py, canvasH) }}
            />
          ))}
          {isRotatableEl(el) && (
            <span
              data-handle="rotate"
              className="hd hd-rot"
              title="拖拽旋转（Shift 15° 步进）"
              style={{ left: pct(b.x + b.w / 2, canvasW), top: pct(b.y - 28, canvasH) }}
            />
          )}
        </>
      );
    } else if (isSegEl(el)) {
      handleEls = (
        <>
          <span data-handle="pt-1" className="hd hd-pt" title="拖拽起点"
            style={{ left: pct(Number(el.x1 ?? 0), canvasW), top: pct(Number(el.y1 ?? 0), canvasH) }} />
          <span data-handle="pt-2" className="hd hd-pt" title="拖拽终点"
            style={{ left: pct(Number(el.x2 ?? 0), canvasW), top: pct(Number(el.y2 ?? 0), canvasH) }} />
          <span data-handle="rotate" className="hd hd-rot" title="拖拽旋转（端点绕中点转，Shift 15° 步进）"
            style={{
              left: pct((Number(el.x1 ?? 0) + Number(el.x2 ?? 0)) / 2, canvasW),
              top: pct(Math.min(Number(el.y1 ?? 0), Number(el.y2 ?? 0)) - 28, canvasH),
            }} />
        </>
      );
    } else {
      const b = elBBox(el);
      handleEls = (
        <span data-handle="rotate" className="hd hd-rot" title="拖拽旋转（Shift 15° 步进）"
          style={{ left: pct(b.x + b.w / 2, canvasW), top: pct(b.y - 28, canvasH) }} />
      );
    }
  } else if (selEls.length >= 2) {
    const gb = unionBBox(selEls.map(elBBox));
    handleEls = (
      <>
        {(["nw", "ne", "sw", "se"] as const).map((dir) => (
          <span
            key={dir}
            data-handle={`scale-${dir}`}
            className={`hd hd-r hd-${dir}`}
            title="整组缩放（对角固定）"
            style={{
              left: pct(dir.includes("w") ? gb.x : gb.x + gb.w, canvasW),
              top: pct(dir.startsWith("n") ? gb.y : gb.y + gb.h, canvasH),
            }} />
        ))}
        <span data-handle="rotate" className="hd hd-rot" title="整组旋转（各元素绕组中心公转+自转，Shift 15° 步进）"
          style={{ left: pct(gb.x + gb.w / 2, canvasW), top: pct(gb.y - 28, canvasH) }} />
      </>
    );
  }

  return (
    <section className="studio" aria-label="spec 可视化编辑器">
      <div className="wb-head">
        <span className="badge">Studio · spec 可视化编辑器（PRD F9 延伸）</span>
        <h2>可视化编辑器：点选 · 框选多选 · 吸附对齐 · AI 自动迭代</h2>
        <p>
          画布渲染与引擎产线①同语义（<code>web/lib/canvas.ts</code> 镜像 <code>svgout.py</code>），
          YAML 源码是唯一事实源；编辑结果交由 Python 引擎构建校验，
          正式产物仍由 <code>snap2edit build</code> 输出。
          <Link href="/" className="studio-back">← 返回工作台</Link>
        </p>
      </div>

      {/* 工具栏 */}
      <div className="card studio-toolbar">
        <button className="btn ghost" onClick={doNew}>新建</button>
        <button className="btn ghost" onClick={() => fileRef.current?.click()}>导入 .yaml</button>
        <button className="btn ghost" onClick={restoreDraft} disabled={!hasDraft}>恢复草稿</button>
        <button className="btn ghost" onClick={() => void doCopy()}>{copied ? "已复制 ✓" : "复制 YAML"}</button>
        <button className="btn primary" onClick={doDownload}>下载 spec.yaml</button>
        <span className="chip-lite">
          {canvasW} × {Number(doc?.canvas?.height ?? 720)} px · {elements.length} 元素
        </span>
        {notice && <span className="chip-lite studio-notice">{notice}</span>}
        <input
          ref={fileRef}
          type="file"
          accept=".yaml,.yml,text/yaml"
          hidden
          onChange={(e) => doImportFile(e.target.files?.[0])}
        />
      </div>

      {/* 三栏主体 */}
      <div className="studio-grid">
        {/* 左：元素列表 */}
        <div className="card studio-list">
          <h3>元素（{elements.length}）</h3>
          <div className="studio-add">
            {ELEMENT_TYPES.map((t) => (
              <button key={t} className="chip-add" onClick={() => addEl(t)} title={`新增 ${t}`}>
                +{t}
              </button>
            ))}
          </div>
          <ul>
            {elements.map((el, i) => (
              <li
                key={el.id}
                className={selIds.includes(el.id) ? "on" : ""}
                onMouseEnter={() => setHover(el.id)}
                onMouseLeave={() => setHover(null)}
              >
                <button
                  className="li-main"
                  onClick={(ev) => {
                    const ext = ev.shiftKey || ev.ctrlKey || ev.metaKey;
                    setSelIds((prev) =>
                      ext
                        ? prev.includes(el.id)
                          ? prev.filter((s) => s !== el.id)
                          : [...prev, el.id]
                        : [el.id]
                    );
                  }}
                  title="点击选中；Shift/Ctrl 加减选"
                >
                  <span className="li-type">{el.type}</span>
                  <span className="li-txt">{listText(el) || "—"}</span>
                </button>
                <span className="li-ops">
                  <button title="上移一层" onClick={() => moveEl(el.id, -1)} disabled={i === 0}>↑</button>
                  <button title="下移一层" onClick={() => moveEl(el.id, 1)} disabled={i === elements.length - 1}>↓</button>
                  <button title="删除" className="danger" onClick={() => removeMany([el.id])}>×</button>
                </span>
              </li>
            ))}
          </ul>
        </div>

        {/* 中：画布 */}
        <div className="card studio-canvas-card">
          <div className="canvas-head">
            <h3>画布（点选 · 拖拽 · 框选多选 · 缩放/旋转手柄 · 旋转角度实时读出 · Shift 15° 步进）</h3>
            <label className="snap-t" title="拖拽吸附触发距离（画布像素，0 为关闭）">
              吸附阈值
              <input
                type="number"
                min={0}
                max={64}
                value={snapT}
                onChange={(e) => {
                  const v = Math.max(0, Math.min(64, Math.round(Number(e.target.value) || 0)));
                  setSnapT(v);
                  try {
                    localStorage.setItem(SNAP_T_KEY, String(v));
                  } catch {
                    /* 存储异常忽略 */
                  }
                }}
              />
              px
            </label>
          </div>
          {parseError ? (
            <p className="alert err" role="alert">YAML 解析失败：{parseError}（修正源码后画布恢复）</p>
          ) : (
            <div
              className="studio-canvas-wrap"
              onPointerDown={onCanvasPointerDown}
              onPointerMove={onCanvasPointerMove}
              onPointerUp={onCanvasPointerUp}
            >
              <div
                className="studio-canvas"
                ref={svgWrapRef}
                style={{
                  fontFamily: doc
                    ? `'${doc.font?.name ?? "Noto Sans SC"}', '${doc.font?.fallback ?? "Microsoft YaHei"}', sans-serif`
                    : undefined,
                }}
                dangerouslySetInnerHTML={{ __html: svg }}
              />
              {/* 吸附参考线（画布坐标 → 百分比定位，拖拽中实时出现） */}
              {guides.v.map((x, i) => (
                <span key={`v${i}`} className="snap-guide v" style={{ left: `${(x / canvasW) * 100}%` }} />
              ))}
              {guides.h.map((y, i) => (
                <span key={`h${i}`} className="snap-guide h" style={{ top: `${(y / canvasH) * 100}%` }} />
              ))}
              {/* 框选矩形 */}
              {marquee && (
                <span
                  className="marquee-rect"
                  style={{
                    left: `${(marquee.x / canvasW) * 100}%`,
                    top: `${(marquee.y / canvasH) * 100}%`,
                    width: `${(marquee.w / canvasW) * 100}%`,
                    height: `${(marquee.h / canvasH) * 100}%`,
                  }}
                />
              )}
              {/* 旋转角度实时读出气泡（跟随指针，松手消失） */}
              {rotHud && (
                <span
                  className="rot-hud"
                  data-testid="rot-hud"
                  style={{
                    left: `${(rotHud.px / canvasW) * 100}%`,
                    top: `${(rotHud.py / canvasH) * 100}%`,
                  }}
                >
                  {rotHud.text}
                </span>
              )}
              {/* 变换手柄：单选 = 8 向缩放 + 旋转（线段为双端点）；多选 = 4 角等比缩放 + 组旋转 */}
              {!interacting && selEls.length > 0 && handleEls}
            </div>
          )}
          {validation && (validation.errors.length > 0 || validation.warnings.length > 0) ? (
            <div className="studio-validate">
              {validation.errors.slice(0, 4).map((e, i) => (
                <p key={`e${i}`} className="alert err">✗ {e}</p>
              ))}
              {validation.warnings.slice(0, 3).map((w, i) => (
                <p key={`w${i}`} className="alert warn">⚠ {w}</p>
              ))}
            </div>
          ) : (
            !parseError && <p className="studio-okline">结构校验通过 ✓（最终以引擎四道门为准）</p>
          )}
        </div>

        {/* 右：属性面板 */}
        <div className="card studio-props">
          <h3>属性{selectedEl ? ` · ${selectedEl.id}` : selIds.length > 1 ? ` · 已选 ${selIds.length} 个` : ""}</h3>
          {selIds.length > 1 ? (
            <div className="prop-form multi-bar">
              <p className="multi-hint">对齐（按选区包围盒）</p>
              <div className="multi-btns">
                <button onClick={() => alignSel("left")}>⇤ 左对齐</button>
                <button onClick={() => alignSel("hcenter")}>⇔ 水平居中</button>
                <button onClick={() => alignSel("right")}>右对齐 ⇥</button>
                <button onClick={() => alignSel("top")}>⇡ 顶对齐</button>
                <button onClick={() => alignSel("vcenter")}>⇕ 垂直居中</button>
                <button onClick={() => alignSel("bottom")}>底对齐 ⇣</button>
              </div>
              <p className="multi-hint">等距分布（≥3 个生效）</p>
              <div className="multi-btns">
                <button onClick={() => distributeSel("h")}>↔ 水平等距</button>
                <button onClick={() => distributeSel("v")}>↕ 垂直等距</button>
              </div>
              <p className="multi-hint">批量操作</p>
              <div className="multi-btns">
                <button className="danger" onClick={() => removeMany(selIds)}>删除所选（{selIds.length}）</button>
                <button onClick={() => setSelIds([])}>取消选择</button>
              </div>
              <small>拖动任一选中元素可整组移动（带对齐吸附，Alt 拖拽禁用吸附）；方向键微调整组。</small>
            </div>
          ) : !selectedEl ? (
            <div className="placeholder slim">
              <p>在画布或左侧列表点选一个元素；空白处拖动可框选多选。</p>
              <small>拖拽移动（带对齐吸附，Alt 暂时禁用）；Shift/Ctrl 加选；方向键微调（Shift ×10）；Delete 删除。</small>
            </div>
          ) : (
            <div className="prop-form">
              <div className="prop-row">
                <label>类型</label>
                <span className="chip-lite">{selectedEl.type}</span>
                <label className="prop-chk">
                  <input
                    type="checkbox"
                    checked={!!selectedEl.bold}
                    onChange={(e) => patchEl(selectedEl.id, { bold: e.target.checked || undefined })}
                  />
                  粗体
                </label>
              </div>

              {isRotatableEl(selectedEl) && (
                <div className="prop-row">
                  <label>旋转°</label>
                  <input
                    type="number"
                    step={5}
                    value={Number(selectedEl.rotate ?? 0)}
                    onChange={(e) => {
                      const v = R1((((Number(e.target.value) || 0) % 360) + 360) % 360);
                      patchEl(selectedEl.id, { rotate: v === 0 ? undefined : v });
                    }}
                  />
                  <button className="btn ghost mini" onClick={() => patchEl(selectedEl.id, { rotate: undefined })}>
                    复位
                  </button>
                </div>
              )}

              {isBoxEl(selectedEl) && (
                <>
                  <div className="prop-grid4">
                    {(["x", "y", "w", "h"] as const).map((k) => (
                      <label key={k}>
                        {k}
                        <input
                          type="number"
                          value={Number(selectedEl[k] ?? 0)}
                          onChange={(e) => patchEl(selectedEl.id, { [k]: Math.round(Number(e.target.value) || 0) })}
                        />
                      </label>
                    ))}
                  </div>
                  <div className="prop-row">
                    <label>填充</label>
                    <input
                      type="color"
                      value={typeof selectedEl.fill === "string" ? selectedEl.fill : "#FFFFFF"}
                      disabled={selectedEl.fill == null && "fill" in selectedEl}
                      onChange={(e) => patchEl(selectedEl.id, { fill: e.target.value.toUpperCase() })}
                    />
                    <label className="prop-chk">
                      <input
                        type="checkbox"
                        checked={selectedEl.fill == null && "fill" in selectedEl}
                        onChange={(e) => patchEl(selectedEl.id, { fill: e.target.checked ? null : "#FFFFFF" })}
                      />
                      透明
                    </label>
                  </div>
                  <div className="prop-row">
                    <label>描边</label>
                    <input
                      type="color"
                      value={typeof selectedEl.stroke === "string" ? selectedEl.stroke : "#94A3B8"}
                      onChange={(e) => patchEl(selectedEl.id, { stroke: e.target.value.toUpperCase() })}
                    />
                    <button
                      className="btn ghost mini"
                      onClick={() => patchEl(selectedEl.id, { stroke: null, stroke_width: undefined })}
                    >
                      清除描边
                    </button>
                  </div>
                  {(selectedEl.type === "rrect" || selectedEl.type === "matrix-cell" || selectedEl.type === "flow-box") && (
                    <div className="prop-row">
                      <label>圆角 rx</label>
                      <input
                        type="number"
                        value={Number(selectedEl.rx ?? 0)}
                        onChange={(e) => patchEl(selectedEl.id, { rx: Math.max(0, Number(e.target.value) || 0) })}
                      />
                    </div>
                  )}
                  {selectedEl.type === "cube" && (
                    <div className="prop-row">
                      <label>深度 depth</label>
                      <input
                        type="number"
                        value={Number(selectedEl.depth ?? 0)}
                        onChange={(e) => {
                          const v = Math.max(0, Number(e.target.value) || 0);
                          patchEl(selectedEl.id, { depth: v || undefined });
                        }}
                      />
                    </div>
                  )}
                  {selectedEl.type === "icon" && (
                    <div className="prop-row">
                      <label>图标 name</label>
                      <select
                        value={String(selectedEl.name ?? "")}
                        onChange={(e) => patchEl(selectedEl.id, { name: e.target.value })}
                      >
                        {ICON_NAMES.map((nm) => (
                          <option key={nm} value={nm}>{nm}</option>
                        ))}
                      </select>
                    </div>
                  )}
                  {selectedEl.type === "flow-box" && (
                    <>
                      <label className="prop-full">
                        色带标题 title（可空）
                        <input
                          type="text"
                          value={String(selectedEl.title ?? "")}
                          onChange={(e) => patchEl(selectedEl.id, { title: e.target.value || undefined })}
                        />
                      </label>
                      <div className="prop-row">
                        <label>色带高占比 band</label>
                        <input
                          type="number"
                          step={0.05}
                          min={0.05}
                          max={0.9}
                          value={Number(selectedEl.band ?? 0.3)}
                          onChange={(e) => patchEl(selectedEl.id, { band: Math.min(0.9, Math.max(0.05, Number(e.target.value) || 0.3)) })}
                        />
                      </div>
                    </>
                  )}
                  {selectedEl.type === "matrix-cell" && (
                    <>
                      <div className="prop-grid4">
                        <label>
                          rows
                          <input
                            type="number"
                            min={1}
                            value={Number(selectedEl.rows ?? 1)}
                            onChange={(e) => patchEl(selectedEl.id, { rows: Math.max(1, Math.round(Number(e.target.value) || 1)) })}
                          />
                        </label>
                        <label>
                          cols
                          <input
                            type="number"
                            min={1}
                            value={Number(selectedEl.cols ?? 1)}
                            onChange={(e) => patchEl(selectedEl.id, { cols: Math.max(1, Math.round(Number(e.target.value) || 1)) })}
                          />
                        </label>
                        <label>
                          gap
                          <input
                            type="number"
                            min={0}
                            value={Number(selectedEl.gap ?? 0)}
                            onChange={(e) => patchEl(selectedEl.id, { gap: Math.max(0, Number(e.target.value) || 0) })}
                          />
                        </label>
                      </div>
                      <label className="prop-full">
                        格子文字 texts（逗号分隔，行优先；可少于格子数）
                        <input
                          type="text"
                          value={(selectedEl.texts ?? []).join(",")}
                          onChange={(e) => {
                            const arr = e.target.value.split(",").map((s) => s.trim()).filter(Boolean);
                            patchEl(selectedEl.id, { texts: arr.length ? arr : undefined });
                          }}
                        />
                      </label>
                    </>
                  )}
                  {selectedEl.type !== "matrix-cell" && selectedEl.type !== "icon" && (
                    <label className="prop-full">
                      内嵌文本（可空）
                      <textarea
                        rows={2}
                        value={elText(selectedEl)}
                        onChange={(e) => {
                          const oldV = elText(selectedEl);
                          patchEl(selectedEl.id, { text: e.target.value || undefined, lines: undefined }, oldV);
                        }}
                      />
                    </label>
                  )}
                </>
              )}

              {selectedEl.type === "text" && (
                <>
                  <label className="prop-full">
                    文本内容（与 texts 清单自动同步；换行拆为 lines）
                    <textarea
                      rows={3}
                      value={elText(selectedEl)}
                      onChange={(e) => {
                        const oldV = elText(selectedEl);
                        const v = e.target.value;
                        if (v.includes("\n")) {
                          const lines = v.split("\n").map((s) => s.trim()).filter(Boolean);
                          patchEl(selectedEl.id, { text: undefined, lines: lines.length ? lines : undefined }, oldV);
                        } else {
                          patchEl(selectedEl.id, { text: v, lines: undefined }, oldV);
                        }
                      }}
                    />
                  </label>
                  <div className="prop-grid3">
                    <label>
                      x
                      <input type="number" value={Number(selectedEl.x ?? 0)}
                        onChange={(e) => patchEl(selectedEl.id, { x: Math.round(Number(e.target.value) || 0) })} />
                    </label>
                    <label>
                      y
                      <input type="number" value={Number(selectedEl.y ?? 0)}
                        onChange={(e) => patchEl(selectedEl.id, { y: Math.round(Number(e.target.value) || 0) })} />
                    </label>
                    <label>
                      字号
                      <input type="number" value={Number(selectedEl.size ?? 16)}
                        onChange={(e) => patchEl(selectedEl.id, { size: Math.max(4, Number(e.target.value) || 16) })} />
                    </label>
                  </div>
                  <div className="prop-row">
                    <label>颜色</label>
                    <input
                      type="color"
                      value={typeof selectedEl.color === "string" ? selectedEl.color : "#1F2937"}
                      onChange={(e) => patchEl(selectedEl.id, { color: e.target.value.toUpperCase() })}
                    />
                    <label>
                      对齐
                      <select
                        value={selectedEl.align ?? "left"}
                        onChange={(e) => patchEl(selectedEl.id, { align: e.target.value as SpecEl["align"] })}
                      >
                        <option value="left">左</option>
                        <option value="center">中</option>
                        <option value="right">右</option>
                      </select>
                    </label>
                  </div>
                </>
              )}

              {(SEG_TYPES as readonly string[]).includes(selectedEl.type) && (
                <>
                  <div className="prop-grid4">
                    {(["x1", "y1", "x2", "y2"] as const).map((k) => (
                      <label key={k}>
                        {k}
                        <input
                          type="number"
                          value={Number(selectedEl[k] ?? 0)}
                          onChange={(e) => patchEl(selectedEl.id, { [k]: Math.round(Number(e.target.value) || 0) })}
                        />
                      </label>
                    ))}
                  </div>
                  <div className="prop-row">
                    <label>{selectedEl.type === "arrow" ? "颜色" : "描边"}</label>
                    <input
                      type="color"
                      value={typeof selectedEl.stroke === "string" ? selectedEl.stroke : "#2B6CB0"}
                      onChange={(e) => patchEl(selectedEl.id, { stroke: e.target.value.toUpperCase() })}
                    />
                    <label>
                      粗细
                      <input
                        type="number"
                        value={Number(selectedEl.stroke_width ?? 2)}
                        onChange={(e) => patchEl(selectedEl.id, { stroke_width: Math.max(1, Number(e.target.value) || 1) })}
                      />
                    </label>
                  </div>
                </>
              )}

              <div className="prop-actions">
                <button className="btn ghost mini" onClick={() => moveEl(selectedEl.id, -1)}>上移一层</button>
                <button className="btn ghost mini" onClick={() => moveEl(selectedEl.id, 1)}>下移一层</button>
                <button className="btn ghost mini danger" onClick={() => removeMany([selectedEl.id])}>删除元素</button>
              </div>
            </div>
          )}

          {doc && (
            <div className="prop-texts">
              <div className="prop-row">
                <label>texts 清单（{doc.texts?.length ?? 0}）</label>
                <button
                  className="btn ghost mini"
                  onClick={() => applyEdit((d) => { d.texts = regenTexts(d); })}
                  title="按当前元素文案重建，保证门1文案清单一致"
                >
                  从元素重建
                </button>
              </div>
              <small>{(doc.texts ?? []).slice(0, 6).join(" / ") || "（空）"}{(doc.texts?.length ?? 0) > 6 ? " …" : ""}</small>
            </div>
          )}
        </div>
      </div>

      {/* YAML 源码 */}
      <div className="card studio-yaml-card">
        <div className="studio-yaml-head">
          <h3>YAML 源码（唯一事实源，可直接编辑）</h3>
          <button className="btn ghost mini" onClick={() => setShowYaml((v) => !v)}>
            {showYaml ? "收起" : "展开"}
          </button>
        </div>
        {showYaml && (
          <textarea
            className="spec-editor"
            value={yaml}
            spellCheck={false}
            onChange={(e) => setYaml(e.target.value)}
            aria-label="spec.yaml 源码"
          />
        )}
      </div>

      {/* 构建与预览 */}
      <div className="card wb-build" id="studio-build">
        <h3>构建与预览（Python 引擎实测）</h3>
        <p className="build-desc">
          「构建并校验」= 单次双渲染 + 四道校验门；「构建并自动迭代」= 未通过时把失败项回询视觉模型修正 spec
          并重建复检（可附加参考原图做视觉比对），<b>最终 spec 自动写回编辑器</b>。
        </p>
        <div className="wb-actions">
          <button className="btn primary" onClick={buildNow} disabled={!yaml.trim() || busy} aria-busy={buildBusy}>
            {buildBusy ? (<><span className="spinner" aria-hidden /> 构建中…</>) : "构建并校验"}
          </button>
        </div>
        <div className="wb-actions refine-row">
          <label className="refine-rounds">
            迭代轮次
            <select value={maxRounds} onChange={(e) => setMaxRounds(Number(e.target.value))} disabled={busy}>
              <option value={1}>1</option>
              <option value={2}>2</option>
              <option value={3}>3</option>
            </select>
          </label>
          <button className="btn primary" onClick={refineNow} disabled={!yaml.trim() || busy} aria-busy={refineBusy}>
            {refineBusy ? (<><span className="spinner" aria-hidden /> 迭代中…</>) : "构建并自动迭代（refine）"}
          </button>
          <button className="btn ghost" onClick={() => imgRef.current?.click()} disabled={busy}>
            {refImg ? "换一张参考原图" : "附加参考原图（可选）"}
          </button>
          {refImg && (
            <span className="chip-lite">
              🖼 {refImg.meta.filename} · {refImg.meta.width}×{refImg.meta.height}
              <button className="mini-x" title="移除原图" onClick={() => setRefImg(null)}>×</button>
            </span>
          )}
          {roundsDone != null && art && (
            <span className={`badge-mode ${art.ok ? "vlm" : "skeleton"}`}>AI 修正 {roundsDone} 轮</span>
          )}
          <input
            ref={imgRef}
            type="file"
            accept="image/*"
            hidden
            onChange={(e) => onImgPick(e.target.files?.[0])}
          />
        </div>
        <div className="wb-actions">
          <Link className="btn ghost" href="/#workbench">回工作台（图片抽取 → 自动回询迭代）</Link>
        </div>
        {buildLog.length > 0 && (
          <div className="logs" aria-hidden>
            {buildLog.slice(-4).map((l, i) => (<div key={i}>· {l}</div>))}
          </div>
        )}
        {buildError && <p className="alert err" role="alert">{buildError}</p>}
        {report && (
          <div className="gates">
            {report.gates.map((g) => (
              <div className="gate" key={g.gate}>
                <h4>{g.gate}</h4>
                <ul>
                  {g.items.map((it, i) => (
                    <li key={i} className={it.passed ? "pass" : "fail"}>
                      <span aria-hidden>{it.passed ? "✓" : "✗"}</span>
                      <span>{it.label}{it.detail && <small>{it.detail}</small>}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        )}
        {art && (
          <>
            <iframe
              key={art.jobId}
              className="preview-frame"
              src={`/api/artifacts/${art.jobId}/html`}
              title="HTML+SVG 产物预览"
              sandbox="allow-same-origin"
            />
            <div className="dl-row">
              <a className="btn ghost" href={`/api/artifacts/${art.jobId}/html?dl=1`}>下载 HTML</a>
              <a className="btn primary" href={`/api/artifacts/${art.jobId}/pptx`}>下载 PPTX</a>
              <a className="btn ghost" href={`/api/artifacts/${art.jobId}/report.md?dl=1`}>下载校验报告</a>
              <a
                className="btn ghost"
                href={`/api/artifacts/${art.jobId}/report.html`}
                target="_blank"
                rel="noreferrer"
                title="F7 可视化报告：状态灯 / 并排图 / diff 热力图 / 溢出标注"
              >可视化报告</a>
              <span className={`badge-mode ${art.ok ? "vlm" : "skeleton"}`}>
                {art.ok ? "四道门全部通过" : "存在未通过项"}
              </span>
            </div>
          </>
        )}
      </div>
    </section>
  );
}
