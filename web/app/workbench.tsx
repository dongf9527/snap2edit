"use client";

// web/app/workbench.tsx —— 「上传图片 → 生成 spec」交互工作台（PRD F9 第一块）
// 纯客户端：负责图片预处理（限尺、取色）；AI 抽取在 /api/spec 服务端完成。

import { useCallback, useRef, useState } from "react";
import type { SpecResult } from "@/lib/spec";

type Phase = "idle" | "ready" | "generating" | "done" | "error";

interface LocalMeta {
  width: number;
  height: number;
  filename: string;
  palette: string[];
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
      const data = await res.json();
      if (!res.ok || !data.ok) {
        throw new Error(data?.error ?? `服务返回 ${res.status}`);
      }
      setResult(data as SpecResult);
      setSpecText((data as SpecResult).spec);
      setPhase("done");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setPhase("error");
    }
  }, [preview, meta]);

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

  const busy = phase === "generating";

  return (
    <section className="wb" id="workbench" aria-label="上传图片生成 spec 工作台">
      <div className="wb-head">
        <span className="badge">Step 0 · 上传图片 → 生成 spec（PRD F9）</span>
        <h2>工作台：从截图到规格书</h2>
        <p>
          上传图表截图，视觉模型将布局、坐标、色板与全部文字抽取为
          <code> spec.yaml</code>；下载后交给引擎双渲染：
          <code> snap2edit build</code>。
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
            <button className="btn ghost" onClick={() => inputRef.current?.click()} disabled={busy}>
              {preview ? "重新选择" : "选择图片"}
            </button>
            <button className="btn primary" onClick={() => void generate()} disabled={!preview || busy} aria-busy={busy}>
              {busy ? (
                <>
                  <span className="spinner" aria-hidden /> 生成中…
                </>
              ) : result ? (
                "重新生成"
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
          <h3>2 · spec.yaml</h3>

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
              <small>复杂图表约需 30–90 秒</small>
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
                <button className="btn primary" onClick={downloadSpec}>
                  下载 spec.yaml
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      <p className="wb-note">
        下一步：把下载的 <code>spec.yaml</code> 放入目录后执行 <code>snap2edit build &lt;目录&gt;</code>{" "}
        与 <code>snap2edit check &lt;目录&gt;</code>，即可得到 HTML+SVG 与原生 PPTX 双产物并通过四道校验门。
        模型接入说明见 <code>web/README.md</code>。
      </p>
    </section>
  );
}
