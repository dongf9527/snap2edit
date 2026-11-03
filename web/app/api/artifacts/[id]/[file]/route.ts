// web/app/api/artifacts/[id]/[file]/route.ts —— GET 任务产物。
// id 为 UUID 任务号；file ∈ {html, pptx, pdf, shot.png, report.md}（双白名单，无路径穿越面）。
// HTML 以 text/html 直出供 iframe 在线预览；PPTX/PDF 以对应 MIME 提供下载/内嵌预览。

import fs from "node:fs/promises";
import path from "node:path";
import { NextResponse } from "next/server";
import { resolveArtifact } from "@/lib/engine";

export const runtime = "nodejs";

const MIME: Record<string, string> = {
  ".html": "text/html; charset=utf-8",
  ".pptx":
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
  ".pdf": "application/pdf",
  ".png": "image/png",
  ".md": "text/markdown; charset=utf-8",
};

export async function GET(
  req: Request,
  ctx: { params: Promise<{ id: string; file: string }> }
) {
  const { id, file } = await ctx.params;
  const p = resolveArtifact(id, file);
  if (!p) {
    return NextResponse.json(
      { ok: false, error: "产物不存在或任务已过期（任务目录在服务端临时目录，重启后清空）" },
      { status: 404 }
    );
  }
  const type = MIME[path.extname(p).toLowerCase()] ?? "application/octet-stream";
  const data = await fs.readFile(p);
  const wantsDownload = new URL(req.url).searchParams.has("dl");
  const inline = !wantsDownload && (type.startsWith("text/") || type === "application/pdf");
  return new Response(new Uint8Array(data), {
    headers: {
      "Content-Type": type,
      "Cache-Control": "no-store",
      "Content-Disposition": `${inline ? "inline" : "attachment"}; filename*=UTF-8''${encodeURIComponent(path.basename(p))}`,
    },
  });
}
