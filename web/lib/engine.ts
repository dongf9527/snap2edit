// web/lib/engine.ts —— 服务端专用：调用 Python 引擎（snap2edit CLI / python -m）。
// 职责：解析引擎命令、子进程执行（带超时）、任务目录管理、产物路径解析、PPTX→PDF 转换。
import { spawn } from "node:child_process";
import { randomUUID } from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

export const JOBS_ROOT = path.join(os.tmpdir(), "snap2edit-jobs");

export interface EngineResult {
  code: number;
  stdout: string;
  stderr: string;
}

interface EngineCmd {
  cmd: string;
  base: string[];
  env: Record<string, string>;
}

let cachedEngine: EngineCmd | null | undefined;

function which(bin: string): string | null {
  const dirs = (process.env.PATH ?? "").split(path.delimiter).filter(Boolean);
  for (const d of dirs) {
    const p = path.join(d, bin);
    try {
      fs.accessSync(p, fs.constants.X_OK);
      return p;
    } catch {
      /* continue */
    }
  }
  return null;
}

function repoSrcDir(): string | null {
  const cands = [
    path.resolve(process.cwd(), "..", "src"),
    path.resolve(process.cwd(), "src"),
  ];
  return cands.find((p) => fs.existsSync(path.join(p, "snap2edit", "cli.py"))) ?? null;
}

function probe(cmd: string, args: string[], env: Record<string, string>, timeoutMs = 8000): Promise<boolean> {
  return new Promise((res) => {
    let done = false;
    const finish = (ok: boolean) => {
      if (!done) {
        done = true;
        clearTimeout(t);
        res(ok);
      }
    };
    const t = setTimeout(() => {
      try {
        p.kill();
      } catch {
        /* ignore */
      }
      finish(false);
    }, timeoutMs);
    let p: ReturnType<typeof spawn>;
    try {
      p = spawn(cmd, args, { stdio: "ignore", env: { ...process.env, ...env } });
    } catch {
      finish(false);
      return;
    }
    p.on("error", () => finish(false));
    p.on("close", (code) => finish(code === 0));
  });
}

/** 解析可用的引擎调用方式（结果缓存）：优先 snap2edit CLI，其次 venv python，最后系统 python。 */
export async function resolveEngine(): Promise<EngineCmd | null> {
  if (cachedEngine !== undefined) return cachedEngine;
  const srcDir = repoSrcDir();
  const pyEnv: Record<string, string> = srcDir ? { PYTHONPATH: srcDir } : {};

  const cli = which("snap2edit");
  const candidates: { cmd: string; base: string[]; env: Record<string, string> }[] = [];
  if (cli) candidates.push({ cmd: cli, base: [], env: {} });
  for (const py of ["/home/z/.venv/bin/python3", which("python3") ?? ""]) {
    if (py) candidates.push({ cmd: py, base: ["-m", "snap2edit.cli"], env: pyEnv });
  }

  for (const c of candidates) {
    const args = c.base.length ? [...c.base, "--version"] : ["--version"];
    // eslint-disable-next-line no-await-in-loop
    if (await probe(c.cmd, args, c.env)) {
      cachedEngine = c;
      return c;
    }
  }
  cachedEngine = null;
  return null;
}

/** 执行引擎子命令。注意：check 失败时退出码为 2（校验未通过属预期），由调用方解析 stdout。 */
export function runEngine(
  args: string[],
  opts: { timeoutMs?: number } = {}
): Promise<EngineResult> {
  return (async () => {
    const eng = await resolveEngine();
    if (!eng) {
      throw new Error(
        "未找到 Snap2Edit 引擎（snap2edit CLI 或 python3 -m snap2edit.cli）。请先在服务端执行 pip install -e ."
      );
    }
    const timeoutMs = opts.timeoutMs ?? 120_000;
    return new Promise<EngineResult>((resolve, reject) => {
      const p = spawn(eng.cmd, [...eng.base, ...args], {
        env: { ...process.env, ...eng.env },
      });
      let out = "";
      let err = "";
      const t = setTimeout(() => {
        try {
          p.kill("SIGKILL");
        } catch {
          /* ignore */
        }
        reject(new Error(`引擎执行超时（${timeoutMs / 1000}s）`));
      }, timeoutMs);
      p.stdout.on("data", (d) => {
        out += String(d);
      });
      p.stderr.on("data", (d) => {
        err += String(d);
      });
      p.on("error", (e) => {
        clearTimeout(t);
        reject(new Error(`引擎启动失败：${e.message}`));
      });
      p.on("close", (code) => {
        clearTimeout(t);
        resolve({ code: code ?? -1, stdout: out, stderr: err });
      });
    });
  })();
}

export function createJob(): { id: string; dir: string } {
  const id = randomUUID();
  const dir = path.join(JOBS_ROOT, id);
  fs.mkdirSync(dir, { recursive: true });
  return { id, dir };
}

const ARTIFACT_EXT: Record<string, string> = {
  html: ".html",
  pptx: ".pptx",
  pdf: ".pdf",
  "shot.png": ".png",
  "report.md": ".md",
};

/** 按 kind 解析任务产物绝对路径（id / kind 双白名单，杜绝路径穿越）。 */
export function resolveArtifact(jobId: string, kind: string): string | null {
  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(jobId)) return null;
  const ext = ARTIFACT_EXT[kind];
  if (!ext) return null;
  const buildDir = path.join(JOBS_ROOT, jobId, "build");
  const root = path.join(JOBS_ROOT, jobId);
  try {
    const hit = fs.readdirSync(buildDir).filter((f) => f.endsWith(ext)).sort();
    if (!hit.length) return null;
    const p = path.join(buildDir, hit[0]);
    if (!p.startsWith(root + path.sep)) return null;
    return p;
  } catch {
    return null;
  }
}

/** LibreOffice 将 PPTX 转 PDF（在线预览用）。不可用/失败返回 null，不影响主流程。 */
export async function pptxToPdf(pptxPath: string, outDir: string, timeoutMs = 90_000): Promise<string | null> {
  const soffice = which("soffice") ?? which("libreoffice");
  if (!soffice || !fs.existsSync(pptxPath)) return null;
  return new Promise((resolve) => {
    let settled = false;
    const finish = (v: string | null) => {
      if (!settled) {
        settled = true;
        clearTimeout(t);
        resolve(v);
      }
    };
    const t = setTimeout(() => {
      try {
        p.kill("SIGKILL");
      } catch {
        /* ignore */
      }
      finish(null);
    }, timeoutMs);
    const p = spawn(soffice, ["--headless", "--convert-to", "pdf", "--outdir", outDir, pptxPath], {
      stdio: "ignore",
    });
    p.on("error", () => finish(null));
    p.on("close", () => {
      try {
        const pdf = path.join(
          outDir,
          path.basename(pptxPath).replace(/\.pptx$/i, "") + ".pdf"
        );
        finish(fs.existsSync(pdf) ? pdf : null);
      } catch {
        finish(null);
      }
    });
  });
}
