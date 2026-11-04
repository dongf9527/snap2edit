// web/tests/engine.fallback.test.ts —— lib/engine.ts 引擎解析回退链单测（独立进程：缓存隔离）。
// 场景：PATH 里的 snap2edit 候选探测失败（exit 1）→ 依次尝试硬编码 venv python 与 PATH python3。
// 沙箱（venv 装有引擎）命中 python 候选；CI（web-test 不装 Python 引擎）→ 全部失败返回 null，
// runEngine 抛出可读错误。两条路径均为合法结果，断言按实际环境分叉。
// 运行：cd web && node --test tests/engine.fallback.test.ts
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { randomUUID } from "node:crypto";
import { resolveEngine, runEngine } from "../lib/engine.ts";

const REAL_PATH = process.env.PATH ?? "";
const REAL_CWD = process.cwd();

test("resolveEngine：CLI 候选失效 → 回退 python 候选或整体判 null（runEngine 抛可读错误）", async (t) => {
  const bin = path.join(os.tmpdir(), `s2e-bin-${randomUUID()}`);
  fs.mkdirSync(bin, { recursive: true });
  // 假 CLI 探测必败：--version 退出码 1
  fs.writeFileSync(path.join(bin, "snap2edit"), "#!/bin/sh\nexit 1\n", { mode: 0o755 });
  // 换到无 src 的临时 cwd：repoSrcDir 返回 null → python 候选不注入 PYTHONPATH
  const bare = fs.mkdtempSync(path.join(os.tmpdir(), "s2e-bare-"));
  process.chdir(bare);
  process.env.PATH = `${bin}${path.delimiter}${REAL_PATH}`;

  try {
    const eng = await resolveEngine();
    if (eng) {
      // 沙箱路径：venv python 装有引擎（editable）→ 回退命中
      assert.ok(eng.base.includes("-m"), `应回退 python -m，实际 ${eng.cmd} ${eng.base}`);
      assert.equal(eng.env.PYTHONPATH, undefined, "src 缺失时不应注入 PYTHONPATH");
      const r = await runEngine(["--version"]);
      assert.equal(r.code, 0);
    } else {
      // CI 路径：无任何引擎 → null，runEngine 报「未找到」
      await assert.rejects(() => runEngine(["--version"]), /未找到 Snap2Edit 引擎/);
    }
  } finally {
    process.env.PATH = REAL_PATH;
    process.chdir(REAL_CWD);
    fs.rmSync(bare, { recursive: true, force: true });
  }
});
