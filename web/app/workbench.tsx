"use client";

// web/app/workbench.tsx —— 「上传图片 → 生成 spec → 构建预览 → 自动回询迭代」工作台
// 纯客户端：图片预处理（限尺、取色）与 UI；AI 抽取在 /api/spec，构建校验在 /api/build，
// 自动迭代在 /api/refine（NDJSON 流式）。所有 fetch 均经 readApiJson/streamApi ——
// 预览网关返回 HTML 错误页时给出可读提示，绝不出现裸的 JSON.parse 报错。

import { useCallback, useRef, useState } from "react";
import { readApiJson, streamApi, type BuildEvent, type RenderReport } from "@/lib/api";
import type { SpecResult } from "@/lib/spec";

type Phase = "idle" | "ready" | "generating" | "done" | "error";

interface LocalMeta {
  width: number;
  height: number;
  filename: string;
  palette: string[];
}

interface Artifacts {
  jobId: string;
  project: string;
  ok: boolean;
  hasPdf: boolean;
}

const MAX_SIDE = 2000;

/** canvas 取样主色：4bit/通道 量化分桶，返回按占比降序的 hex 列表 */
function extractPalette(img: HTMLImageElement): string[] {
  const N = 64;
  const cv = document.createElement("canvas");
  cv.width = N;
  cv.height = N;
  const ctx = cv.getContext("2d");
  if (!ctx) return [];
  ctx.drawImage(img, 0, 0, N, N);
  const data = ctx.getImageData(0, 0, N, N).data;
  const buckets = new Map<number, number>();
  for (let i = 0; i < data.length; i += 4) {
    const a = data[i + 3];
    if (a < 128) continue;
    const r = data[i],
      g = data[i + 1],
      b = data[i + 2];
    const key = ((r >> 4) << 8) | ((g >> 4) << 4) | (b >> 4);
    buckets.set(key, (buckets.get(key) ?? 0) + 1);
  }
  return [...buckets.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6)
    .map(([key]) => {
      const r = ((key >> 8) & 0xf) * 17;
      const g = ((key >> 4) & 0xf) * 17;
      const b = (key & 0xf) * 17;
      return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, "0")}`;
    });
}

/** 读取文件 → dataURL（超限时等比缩小并转 JPEG）+ 像素尺寸 + 主色 */
async function prepareImage(file: File): Promise<{ dataUrl: string; meta: LocalMeta }> {
  const dataUrl = await new Promise<string>((res, rej) => {
    const fr = new FileReader();
    fr.onload = () => res(String(fr.result));
    fr.onerror = () => rej(new Error("读取文件失败"));
    fr.readAsDataURL(file);
  });
  const img = await new Promise<HTMLImageElement>((res, rej) => {
    const im = new Image();
    im.onload = () => res(im);
    im.onerror = () => rej(new Error("图片解码失败"));
    im.src = dataUrl;
  });

  const meta: LocalMeta = {
    width: img.naturalWidth,
    height: img.naturalHeight,
    filename: file.name,
    palette: extractPalette(img),
  };

  const maxSide = Math.max(img.naturalWidth, img.naturalHeight);
  if (maxSide <= MAX_SIDE && dataUrl.length <= 6_000_000) {
    return { dataUrl, meta };
  }
  const scale = Math.min(1, MAX_SIDE / maxSide);
  const cv = document.createElement("canvas");
  cv.width = Math.round(img.naturalWidth * scale);
  cv.height = Math.round(img.naturalHeight * scale);
  const ctx = cv.getContext("2d");
  if (!ctx) return { dataUrl, meta };
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, cv.width, cv.height);
  ctx.drawImage(img, 0, 0, cv.width, cv.height);
  return { dataUrl: cv.toDataURL("image/jpeg", 0.85), meta };
}

export default function Workbench() {
  const [phase, setPhase] = useState<Phase>("idle");
  const [preview, setPreview] = useState<string | null>(null);
  const [meta, setMeta] = useState<LocalMeta | null>(null);
  const [result, setResult] = useState<SpecResult | null>(null);
  const [specText, setSpecText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // —— 3 · 构建与预览 / 自动回询迭代 ——
  const [buildBusy, setBuildBusy] = useState(false);
  const [refineBusy, setRefineBusy] = useState(false);
  const [rounds, setRounds] = useState(2);
  const [logs, setLogs] = useState<string[]>([]);
  const [steps, setSteps] = useState<string[]>([]);
  const [report, setReport] = useState<RenderReport | null>(null);
  const [art, setArt] = useState<Artifacts | null>(null);
  const [buildError, setBuildError] = useState<string | null>(null);
  const [buildWarn, setBuildWarn] = useState<string[]>([]);
  const [tab, setTab] = useState<"html" | "pdf">("html");
  const [tick, setTick] = useState<number | null>(null);

  const pushLog = useCallback((msg: string) => {
    setLogs((prev) => [...prev.slice(-40), msg]);
  }, []);

  const acceptFile = useCallback(async (file: File | undefined | null) => {
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      setError("请选择图片文件（PNG / JPG / WebP）");
      setPhase("error");
      return;
    }
    setError(null);
    try {
      const { dataUrl, meta: m } = await prepareImage(file);
      setPreview(dataUrl);
      setMeta(m);
      setResult(null);
      setSpecText("");
      setPhase("ready");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setPhase("error");
    }
  }, []);

  const generate = useCallback(async () => {
    if (!preview || !meta) return;
    setPhase("generating");
    setError(null);
    setResult(null);
    try {
      const res = await fetch("/api/spec", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image: preview, meta }),
      });
      // 健壮读取：网关返回 HTML/纯文本错误页时转为可读提示（而非裸 JSON.parse 报错）
      const data = await readApiJson<SpecResult & { error?: string }>(res);
      if (!res.ok || !data.ok) {
        throw new Error((data as { error?: string }).error ?? `服务返回 ${res.status}`);
      }
      setResult(data);
      setSpecText(data.spec);
      setPhase("done");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setPhase("error");
    }
  }, [preview, meta]);

  /** 统一消费 build/refine 的 NDJSON 事件流 */
  const consume = useCallback(
    async (path: string, payload: unknown, busy: (v: boolean) => void) => {
      busy(true);
      setLogs([]);
      setSteps([]);
      setReport(null);
      setArt(null);
      setBuildError(null);
      setBuildWarn([]);
      setTick(null);
      try {
        await streamApi(
          path,
          payload,
          (ev: BuildEvent) => {
            if (ev.type === "log") {
              pushLog(ev.msg);
            } else if (ev.type === "tick") {
              setTick(ev.s);
            } else if (ev.type === "round") {
              const label =
                ev.phase === "vlm"
                  ? `第${ev.n}轮 · 视觉模型修正${ev.note ? `（${ev.note}）` : ""}`
                  : `第${ev.n}次构建${ev.note ? `（${ev.note}）` : ""}`;
              setSteps((prev) => [...prev, label]);
            } else if (ev.type === "report") {
              setReport(ev.report);
              setSteps((prev) => [
                ...prev,
                ev.report.ok
                  ? `校验 ✓ 四道门全部通过`
                  : `校验 ✗ ${ev.report.failures.length} 项未通过`,
              ]);
            } else if (ev.type === "spec") {
              setSpecText(ev.spec);
            } else if (ev.type === "done") {
              setArt({
                jobId: ev.jobId,
                project: ev.project,
                ok: ev.ok,
                hasPdf: ev.hasPdf,
              });
              if (ev.spec) setSpecText(ev.spec);
              if (ev.warnings?.length) setBuildWarn(ev.warnings);
              setTab("html");
            }
          },
          "服务端执行失败"
        );
      } catch (e) {
        setBuildError(e instanceof Error ? e.message : String(e));
      } finally {
        setTick(null);
        busy(false);
      }
    },
    [pushLog]
  );

  const buildNow = useCallback(() => {
    if (!specText.trim()) return;
    return consume("/api/build", { spec: specText }, setBuildBusy);
  }, [consume, specText]);

  const refineNow = useCallback(() => {
    if (!specText.trim() || !preview || !meta) return;
    return consume(
      "/api/refine",
      { image: preview, meta, spec: specText, maxRounds: rounds },
      setRefineBusy
    );
  }, [consume, meta, preview, rounds, specText]);

  const copySpec = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(specText);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      setError("复制失败，请手动全选复制");
    }
  }, [specText]);

  const downloadSpec = useCallback(() => {
    const base = (meta?.filename ?? "spec").replace(/\.[a-z0-9]+$/i, "");
    const blob = new Blob([specText], { type: "text/yaml;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${base}.spec.yaml`;
    a.click();
    URL.revokeObjectURL(url);
  }, [meta, specText]);

  /** 带着当前 spec 跳转可视化编辑器（sessionStorage 交接） */
  const openInStudio = useCallback(() => {
    if (!specText.trim()) return;
    sessionStorage.setItem("snap2edit.studio.spec", specText);
    window.location.href = "/studio";
  }, [specText]);

  const busy = phase === "generating";
  const pipelineBusy = buildBusy || refineBusy;

  return (
    <section className="wb" id="workbench" aria-label="上传图片生成 spec 工作台">
      <div className="wb-head">
        <span className="badge">Step 0 · 上传图片 → 生成 spec → 构建预览 → 自动迭代</span>
        <h2>工作台：从截图到可编辑双产物</h2>
        <p>
          上传图表截图，视觉模型将布局、坐标、色板与全部文字抽取为
          <code> spec.yaml</code>；随后一键调用 Python 引擎双渲染，在线预览
          HTML+SVG 与 PPTX（PDF 形态）；校验未通过时自动把渲染报告回询视觉模型迭代修正。
        </p>
      </div>

      <div className="wb-grid">
        {/* 左：上传与预览 */}
        <div className="card wb-col">
          <h3>1 · 选择图片</h3>
          <div
            className={`dropzone${dragOver ? " over" : ""}${preview ? " has" : ""}`}
            onClick={() => inputRef.current?.click()}
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragOver(false);
              void acceptFile(e.dataTransfer.files?.[0]);
            }}
            role="button"
            tabIndex={0}
            aria-label="上传或拖入图片"
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
            }}
          >
            {preview ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={preview} alt="待复刻的截图预览" />
            ) : (
              <div className="dz-hint">
                <span aria-hidden>🖼️</span>
                <p>点击选择 或 拖拽图片到此处</p>
                <small>PNG / JPG / WebP，建议 ≤ 8MB（超限自动压缩）</small>
              </div>
            )}
          </div>
          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            hidden
            onChange={(e) => void acceptFile(e.target.files?.[0])}
          />

          {meta && (
            <div className="meta-chips" aria-live="polite">
              <span className="chip-lite">
                {meta.width} × {meta.height} px
              </span>
              <span className="chip-lite" title={meta.filename}>
                {meta.filename.slice(0, 24)}
              </span>
              <span className="swatches" aria-label="取样主色">
                {meta.palette.map((c) => (
                  <i key={c} style={{ background: c }} title={c} />
                ))}
              </span>
            </div>
          )}

          <div className="wb-actions">
            <button className="btn ghost" onClick={() => inputRef.current?.click()} disabled={busy || pipelineBusy}>
              {preview ? "重新选择" : "选择图片"}
            </button>
            <button className="btn primary" onClick={() => void generate()} disabled={!preview || busy || pipelineBusy} aria-busy={busy}>
              {busy ? (
                <>
                  <span className="spinner" aria-hidden /> 生成中…
                </>
              ) : result ? (
                "重新生成 spec"
              ) : (
                "生成 spec.yaml"
              )}
            </button>
          </div>

          {phase === "error" && error && (
            <p className="alert err" role="alert">
              {error}
            </p>
          )}
        </div>

        {/* 右：生成结果 */}
        <div className="card wb-col">
          <h3>2 · spec.yaml（可编辑）</h3>

          {!result && !busy && (
            <div className="placeholder">
              <p>生成结果将显示在这里。</p>
              <small>
                流程：图片 → 视觉模型抽取 → 结构校验（失败自动带错误重试一次）→ 可编辑 YAML。
                服务端未配置模型时返回骨架模板。
              </small>
            </div>
          )}

          {busy && (
            <div className="placeholder" aria-live="polite">
              <span className="spinner big" aria-hidden />
              <p>正在分析图片并抽取布局规格…</p>
              <small>复杂图表约需 30–90 秒；若网关超时请重试（长任务已做流式保活）</small>
            </div>
          )}

          {result && (
            <>
              <div className="result-meta">
                <span className={`badge-mode ${result.mode}`}>
                  {result.mode === "vlm" ? `AI 抽取 · ${result.model ?? "vision"}` : "骨架模板（未接模型）"}
                </span>
                <span className="chip-lite">{(result.elapsedMs / 1000).toFixed(1)}s</span>
                <span className="chip-lite">
                  {result.validation.stats.elements} 元素 · {result.validation.stats.texts} 文本
                </span>
              </div>

              {result.warnings.length > 0 && (
                <ul className="alert warn">
                  {result.warnings.slice(0, 6).map((w, i) => (
                    <li key={i}>{w}</li>
                  ))}
                </ul>
              )}

              <textarea
                className="spec-editor"
                value={specText}
                onChange={(e) => setSpecText(e.target.value)}
                spellCheck={false}
                aria-label="spec.yaml 内容（可编辑）"
              />

              <div className="wb-actions">
                <button className="btn ghost" onClick={() => void copySpec()}>
                  {copied ? "已复制 ✓" : "复制"}
                </button>
                <button className="btn ghost" onClick={downloadSpec}>
                  下载 spec.yaml
                </button>
                <button className="btn primary" onClick={openInStudio}>
                  在可视化编辑器中打开 →
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {/* 3 · 构建与双产物预览 / 自动回询迭代 */}
      <div className="card wb-build" id="build-preview">
        <h3>3 · 构建与双产物预览（Python 引擎实测）</h3>
        <p className="build-desc">
          把上方 spec 交给引擎 <code>snap2edit build</code> 与{" "}
          <code>snap2edit check</code>：双渲染 HTML+SVG 与原生 PPTX，四道校验门逐项出报告；
          「自动回询迭代」会在未通过时把报告错误反馈给视觉模型修正 spec 并重建（需保留原图）。
        </p>

        <div className="wb-actions">
          <button
            className="btn primary"
            onClick={() => void buildNow()}
            disabled={!specText.trim() || pipelineBusy}
            aria-busy={buildBusy}
          >
            {buildBusy ? (
              <>
                <span className="spinner" aria-hidden /> 构建中…
              </>
            ) : (
              "构建并校验"
            )}
          </button>
          <button
            className="btn ghost"
            onClick={() => void refineNow()}
            disabled={!specText.trim() || !preview || pipelineBusy}
            aria-busy={refineBusy}
            title={!preview ? "需要先上传原图（供视觉模型比对修正）" : undefined}
          >
            {refineBusy ? (
              <>
                <span className="spinner" aria-hidden /> 迭代中…
              </>
            ) : (
              "自动回询迭代"
            )}
          </button>
          <label className="rounds-sel">
            修正轮次
            <select
              value={rounds}
              onChange={(e) => setRounds(Number(e.target.value))}
              disabled={pipelineBusy}
            >
              <option value={1}>1</option>
              <option value={2}>2</option>
              <option value={3}>3</option>
            </select>
          </label>
          {tick !== null && (
            <span className="chip-lite" aria-live="polite">
              模型生成中… {tick}s（长静默属正常）
            </span>
          )}
        </div>

        {steps.length > 0 && (
          <div className="steps" aria-live="polite">
            {steps.map((s, i) => (
              <span
                key={i}
                className={`step-chip${s.includes("✓") ? " ok" : s.includes("✗") ? " bad" : ""}`}
              >
                {s}
              </span>
            ))}
          </div>
        )}

        {logs.length > 0 && (
          <div className="logs" aria-hidden>
            {logs.slice(-6).map((l, i) => (
              <div key={i}>· {l}</div>
            ))}
          </div>
        )}

        {buildError && (
          <p className="alert err" role="alert">
            {buildError}
          </p>
        )}
        {buildWarn.length > 0 && (
          <ul className="alert warn">
            {buildWarn.slice(0, 6).map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        )}

        {report && (
          <div className="gates">
            {report.gates.map((g) => (
              <div className="gate" key={g.gate}>
                <h4>{g.gate}</h4>
                <ul>
                  {g.items.map((it, i) => (
                    <li key={i} className={it.passed ? "pass" : "fail"}>
                      <span aria-hidden>{it.passed ? "✓" : "✗"}</span>
                      <span>
                        {it.label}
                        {it.detail && <small>{it.detail}</small>}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        )}

        {art && (
          <>
            <div className="tabs" role="tablist" aria-label="产物预览切换">
              <button
                role="tab"
                aria-selected={tab === "html"}
                className={`tab${tab === "html" ? " on" : ""}`}
                onClick={() => setTab("html")}
              >
                产线① HTML+SVG
              </button>
              <button
                role="tab"
                aria-selected={tab === "pdf"}
                className={`tab${tab === "pdf" ? " on" : ""}`}
                onClick={() => setTab("pdf")}
                disabled={!art.hasPdf}
                title={!art.hasPdf ? "PDF 预览不可用（LibreOffice 未就绪），可下载 PPTX 查看" : undefined}
              >
                产线② PPTX（PDF 形态）
              </button>
              <span className={`badge-mode ${art.ok ? "vlm" : "skeleton"}`}>
                {art.ok ? "四道门全部通过" : "存在未通过项（可自动迭代或手工修正）"}
              </span>
            </div>

            <iframe
              key={`${art.jobId}-${tab}`}
              className="preview-frame"
              src={`/api/artifacts/${art.jobId}/${tab === "html" ? "html" : "pdf"}`}
              title={tab === "html" ? "HTML+SVG 产物预览" : "PPTX 的 PDF 形态预览"}
              {...(tab === "html" ? { sandbox: "allow-same-origin" } : {})}
            />

            <div className="dl-row">
              <a className="btn ghost" href={`/api/artifacts/${art.jobId}/html?dl=1`}>
                下载 HTML
              </a>
              <a className="btn primary" href={`/api/artifacts/${art.jobId}/pptx`}>
                下载 PPTX
              </a>
              <a className="btn ghost" href={`/api/artifacts/${art.jobId}/report.md?dl=1`}>
                下载校验报告
              </a>
              <a
                className="btn ghost"
                href={`/api/artifacts/${art.jobId}/report.html`}
                target="_blank"
                rel="noreferrer"
                title="F7 可视化报告：状态灯 / 并排图 / diff 热力图 / 溢出标注"
              >
                可视化报告
              </a>
              <span className="chip-lite" title={art.project}>
                任务 {art.jobId.slice(0, 8)} · {art.project}
              </span>
            </div>
          </>
        )}

        {!art && !report && !buildError && !pipelineBusy && (
          <div className="placeholder slim">
            <p>构建结果与在线预览将显示在这里。</p>
            <small>
              产物为临时会话（服务端 /tmp），重启后失效；正式沉淀请下载后放入仓库 docs 案例。
            </small>
          </div>
        )}
      </div>

      <p className="wb-note">
        引擎本地命令：<code>snap2edit build &lt;目录&gt;</code> 与{" "}
        <code>snap2edit check &lt;目录&gt; [--json]</code>。API 一览：
        <code>POST /api/spec</code>（抽取）、<code>POST /api/build</code>（构建校验，NDJSON）、
        <code>POST /api/refine</code>（自动回询迭代，NDJSON）、
        <code>GET /api/artifacts/&lt;id&gt;/&lt;html|pptx|pdf&gt;</code>。详见 <code>web/README.md</code>。
      </p>
    </section>
  );
}
