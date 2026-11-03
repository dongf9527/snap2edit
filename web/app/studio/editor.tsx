"use client";

// web/app/studio/editor.tsx —— spec 可视化编辑器（PRD F9 → v0.3 studio 页）。
// 三栏布局：元素列表 / SVG 画布（点选·拖拽·方向键微调）/ 属性面板；
// YAML 源码为唯一事实源（双向同步：属性编辑 → 重新序列化；源码编辑 → 画布重渲）。
// 画布渲染与引擎 svgout.py 同语义（web/lib/canvas.ts），正式产物仍由 Python 引擎输出。

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
  elText,
  regenTexts,
  renderSpecSvg,
  syncTextOnEdit,
  translateEl,
  type SpecDoc,
  type SpecEl,
} from "@/lib/canvas";
import { streamApi, type BuildEvent, type RenderReport } from "@/lib/api";

const DRAFT_KEY = "snap2edit.studio.draft";
const HANDOFF_KEY = "snap2edit.studio.spec";

const BOX_TYPES = ["rect", "rrect", "pill", "circle"] as const;
const SEG_TYPES = ["line", "arrow"] as const;

interface Artifacts {
  jobId: string;
  ok: boolean;
  hasPdf: boolean;
}

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
  const [selected, setSelected] = useState<string | null>(null);
  const [hover, setHover] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [showYaml, setShowYaml] = useState(true);
  const [copied, setCopied] = useState(false);
  const [hasDraft, setHasDraft] = useState(false);
  const [dragId, setDragId] = useState<string | null>(null);

  // 构建与预览（复用 /api/build）
  const [buildBusy, setBuildBusy] = useState(false);
  const [buildLog, setBuildLog] = useState<string[]>([]);
  const [report, setReport] = useState<RenderReport | null>(null);
  const [art, setArt] = useState<Artifacts | null>(null);
  const [buildError, setBuildError] = useState<string | null>(null);

  const fileRef = useRef<HTMLInputElement>(null);
  const svgWrapRef = useRef<HTMLDivElement>(null);
  const dragRef = useRef<{ id: string; sx: number; sy: number } | null>(null);
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
      return renderSpecSvg(doc, { selectedId: selected, hoverId: hover });
    } catch {
      return "";
    }
  }, [doc, selected, hover]);

  const canvasW = Number(doc?.canvas?.width ?? 1280);
  const elements = doc?.elements ?? [];
  const selectedEl = elements.find((e) => e.id === selected) ?? null;

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

  const nudge = useCallback(
    (id: string, dx: number, dy: number) => {
      applyEdit((d) => {
        const el = (d.elements ?? []).find((e) => e.id === id);
        if (el) translateEl(el, dx, dy);
      });
    },
    [applyEdit]
  );

  const removeEl = useCallback(
    (id: string) => {
      applyEdit((d) => {
        d.elements = (d.elements ?? []).filter((e) => e.id !== id);
        d.texts = regenTexts(d);
      });
      setSelected(null);
    },
    [applyEdit]
  );

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
      applyEdit((d) => {
        const cw = Number(d.canvas?.width ?? 1280);
        const ch = Number(d.canvas?.height ?? 720);
        const id = nextId(d);
        let el: SpecEl;
        if (type === "text") {
          el = { id, type, x: Math.round(cw * 0.1), y: Math.round(ch * 0.1), size: 20, text: "新文本" };
        } else if ((SEG_TYPES as readonly string[]).includes(type)) {
          el = {
            id, type,
            x1: Math.round(cw * 0.2), y1: Math.round(ch * 0.6),
            x2: Math.round(cw * 0.5), y2: Math.round(ch * 0.6),
          };
        } else {
          el = { id, type, x: Math.round(cw * 0.15), y: Math.round(ch * 0.2), w: 240, h: 120, fill: "#F7F9FC" };
          if (type === "rrect") el.rx = 10;
          if (type === "circle") { el.w = 120; el.h = 120; }
        }
        d.elements = [...(d.elements ?? []), el];
      });
      setNotice(`已新增 ${type} 元素`);
    },
    [applyEdit]
  );

  // —— 画布交互：点选 / 拖拽 ——
  const onSvgPointerDown = useCallback(
    (e: React.PointerEvent) => {
      if (!doc) return;
      const target = (e.target as SVGElement).closest("[id]");
      const raw = target?.getAttribute("id") ?? "";
      if (!raw) {
        setSelected(null);
        return;
      }
      const id = raw.replace(/-(text|head)$/, "");
      setSelected(id);
      const svgRect = svgWrapRef.current?.querySelector("svg")?.getBoundingClientRect();
      if (!svgRect || !(doc.elements ?? []).some((x) => x.id === id)) return;
      const scale = Number(doc.canvas?.width ?? 1280) / svgRect.width;
      dragRef.current = { id, sx: e.clientX * scale, sy: e.clientY * scale };
      setDragId(id);
    },
    [doc]
  );

  const onSvgPointerMove = useCallback(
    (e: React.PointerEvent) => {
      const dr = dragRef.current;
      if (!dr || !doc || !svgWrapRef.current) return;
      const svgRect = svgWrapRef.current.querySelector("svg")?.getBoundingClientRect();
      if (!svgRect) return;
      const scale = Number(doc.canvas?.width ?? 1280) / svgRect.width;
      const dx = Math.round(e.clientX * scale - dr.sx);
      const dy = Math.round(e.clientY * scale - dr.sy);
      // 拖拽中：直接改 DOM transform 做实时预览，松手才提交 YAML（避免高频重解析）
      cancelAnimationFrame(rafRef.current);
      rafRef.current = requestAnimationFrame(() => {
        const svgEl = svgWrapRef.current?.querySelector("svg");
        if (!svgEl) return;
        svgEl.querySelectorAll(`[id="${dr.id}"],[id="${dr.id}-text"],[id="${dr.id}-head"]`).forEach((node) => {
          (node as SVGElement).style.transform = `translate(${dx}px, ${dy}px)`;
        });
      });
    },
    [doc]
  );

  const onSvgPointerUp = useCallback(
    (e: React.PointerEvent) => {
      const dr = dragRef.current;
      dragRef.current = null;
      setDragId(null);
      if (!dr || !doc || !svgWrapRef.current) return;
      const svgRect = svgWrapRef.current.querySelector("svg")?.getBoundingClientRect();
      cancelAnimationFrame(rafRef.current);
      svgWrapRef.current
        .querySelectorAll(`[id="${dr.id}"],[id="${dr.id}-text"],[id="${dr.id}-head"]`)
        .forEach((node) => ((node as SVGElement).style.transform = ""));
      if (!svgRect) return;
      const scale = Number(doc.canvas?.width ?? 1280) / svgRect.width;
      const dx = Math.round(e.clientX * scale - dr.sx);
      const dy = Math.round(e.clientY * scale - dr.sy);
      if (dx || dy) nudge(dr.id, dx, dy);
    },
    [doc, nudge]
  );

  // —— 键盘微调（方向键 1px / Shift 10px；Delete 删除）——
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
      if (!selected) return;
      const step = e.shiftKey ? 10 : 1;
      const moves: Record<string, [number, number]> = {
        ArrowLeft: [-step, 0],
        ArrowRight: [step, 0],
        ArrowUp: [0, -step],
        ArrowDown: [0, step],
      };
      if (moves[e.key]) {
        e.preventDefault();
        nudge(selected, moves[e.key][0], moves[e.key][1]);
      } else if ((e.key === "Delete" || e.key === "Backspace") && !dragId) {
        e.preventDefault();
        removeEl(selected);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [selected, dragId, nudge, removeEl]);

  // —— 工具动作 ——
  const doNew = useCallback(() => {
    setYaml(dumpSpecYaml(blankSpec()));
    setSelected(null);
    setNotice("已新建空白模板");
  }, []);

  const doImportFile = useCallback((f: File | undefined | null) => {
    if (!f) return;
    const fr = new FileReader();
    fr.onload = () => {
      setYaml(String(fr.result));
      setSelected(null);
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
      setSelected(null);
      setNotice("已恢复浏览器草稿");
    }
  }, []);

  // —— 构建（复用 /api/build NDJSON）——
  const buildNow = useCallback(() => {
    if (!yaml.trim() || buildBusy) return;
    setBuildBusy(true);
    setBuildLog([]);
    setReport(null);
    setArt(null);
    setBuildError(null);
    streamApi(
      "/api/build",
      { spec: yaml },
      (ev: BuildEvent) => {
        if (ev.type === "log") setBuildLog((p) => [...p.slice(-5), ev.msg]);
        else if (ev.type === "report") setReport(ev.report);
        else if (ev.type === "done") setArt({ jobId: ev.jobId, ok: ev.ok, hasPdf: ev.hasPdf });
      },
      "构建失败"
    )
      .catch((e) => setBuildError(e instanceof Error ? e.message : String(e)))
      .finally(() => setBuildBusy(false));
  }, [yaml, buildBusy]);

  const listText = (el: SpecEl) => {
    const t = elText(el);
    if (t) return t.length > 16 ? `${t.slice(0, 16)}…` : t;
    if (el.x1 != null) return `(${el.x1},${el.y1})→(${el.x2},${el.y2})`;
    return `(${el.x ?? 0}, ${el.y ?? 0}) ${el.w ?? ""}${el.w ? "×" : ""}${el.h ?? ""}`;
  };

  return (
    <section className="studio" aria-label="spec 可视化编辑器">
      <div className="wb-head">
        <span className="badge">Studio · spec 可视化编辑器（PRD F9 延伸）</span>
        <h2>可视化编辑器：点选 · 拖拽 · 改属性，YAML 实时同步</h2>
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
                className={el.id === selected ? "on" : ""}
                onMouseEnter={() => setHover(el.id)}
                onMouseLeave={() => setHover(null)}
              >
                <button className="li-main" onClick={() => setSelected(el.id)}>
                  <span className="li-type">{el.type}</span>
                  <span className="li-txt">{listText(el) || "—"}</span>
                </button>
                <span className="li-ops">
                  <button title="上移一层" onClick={() => moveEl(el.id, -1)} disabled={i === 0}>↑</button>
                  <button title="下移一层" onClick={() => moveEl(el.id, 1)} disabled={i === elements.length - 1}>↓</button>
                  <button title="删除" className="danger" onClick={() => removeEl(el.id)}>×</button>
                </span>
              </li>
            ))}
          </ul>
        </div>

        {/* 中：画布 */}
        <div className="card studio-canvas-card">
          <h3>画布（点选 · 拖拽 · 方向键微调 · Delete 删除）</h3>
          {parseError ? (
            <p className="alert err" role="alert">YAML 解析失败：{parseError}（修正源码后画布恢复）</p>
          ) : (
            <div
              className="studio-canvas"
              ref={svgWrapRef}
              style={{
                fontFamily: doc
                  ? `'${doc.font?.name ?? "Noto Sans SC"}', '${doc.font?.fallback ?? "Microsoft YaHei"}', sans-serif`
                  : undefined,
              }}
              onPointerDown={onSvgPointerDown}
              onPointerMove={onSvgPointerMove}
              onPointerUp={onSvgPointerUp}
              dangerouslySetInnerHTML={{ __html: svg }}
            />
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
          <h3>属性{selectedEl ? ` · ${selectedEl.id}` : ""}</h3>
          {!selectedEl ? (
            <div className="placeholder slim">
              <p>在画布或左侧列表点选一个元素。</p>
              <small>拖拽移动位置；方向键微调（Shift ×10）；Delete 删除。</small>
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

              {(BOX_TYPES as readonly string[]).includes(selectedEl.type) && (
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
                  {selectedEl.type === "rrect" && (
                    <div className="prop-row">
                      <label>圆角 rx</label>
                      <input
                        type="number"
                        value={Number(selectedEl.rx ?? 0)}
                        onChange={(e) => patchEl(selectedEl.id, { rx: Math.max(0, Number(e.target.value) || 0) })}
                      />
                    </div>
                  )}
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
                <button className="btn ghost mini danger" onClick={() => removeEl(selectedEl.id)}>删除元素</button>
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
        <h3>构建并预览（Python 引擎实测）</h3>
        <p className="build-desc">把当前 spec 交给引擎双渲染与四道校验门；产物在线预览，可下载沉淀。</p>
        <div className="wb-actions">
          <button className="btn primary" onClick={buildNow} disabled={!yaml.trim() || buildBusy} aria-busy={buildBusy}>
            {buildBusy ? (<><span className="spinner" aria-hidden /> 构建中…</>) : "构建并校验"}
          </button>
          <Link className="btn ghost" href="/#workbench">回工作台（图片抽取 / 自动回询迭代）</Link>
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
