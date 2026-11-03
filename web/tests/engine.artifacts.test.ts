// web/tests/engine.artifacts.test.ts —— resolveArtifact 白名单/错位隔离单测（F7 report.html）
// 运行：cd web && node --test tests/engine.artifacts.test.ts
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { randomUUID } from "node:crypto";
import { JOBS_ROOT, resolveArtifact } from "../lib/engine.ts";

function fakeJob(): string {
  const id = randomUUID();
  fs.mkdirSync(path.join(JOBS_ROOT, id, "build"), { recursive: true });
  return id;
}

test("resolveArtifact：kind=html 命中幻灯片本体而非 F7 report.html（错位隔离）", () => {
  const id = fakeJob();
  const build = path.join(JOBS_ROOT, id, "build");
  fs.writeFileSync(path.join(build, "report.html"), "<html>F7</html>");
  fs.writeFileSync(path.join(build, "snap2edit-demo.html"), "<html>deck</html>");
  const deck = resolveArtifact(id, "html");
  assert.ok(deck && deck.endsWith("snap2edit-demo.html"));
  const rep = resolveArtifact(id, "report.html");
  assert.ok(rep && rep.endsWith("report.html"));
});

test("resolveArtifact：report.html 缺席 → null；旧结构（仅幻灯片）不受影响", () => {
  const id = fakeJob();
  const build = path.join(JOBS_ROOT, id, "build");
  fs.writeFileSync(path.join(build, "snap2edit-demo.html"), "<html>deck</html>");
  assert.equal(resolveArtifact(id, "report.html"), null);
  assert.ok(resolveArtifact(id, "html")!.endsWith("snap2edit-demo.html"));
});

test("resolveArtifact：非白名单 kind 与非法 id 一律拒绝", () => {
  const id = fakeJob();
  assert.equal(resolveArtifact(id, "../spec.yaml"), null);
  assert.equal(resolveArtifact(id, "shot"), null);
  assert.equal(resolveArtifact("not-a-uuid", "html"), null);
});

test("resolveArtifact：report.md / shot.png / pptx 语义位不受 F7 影响", () => {
  const id = fakeJob();
  const build = path.join(JOBS_ROOT, id, "build");
  fs.writeFileSync(path.join(build, "report.md"), "# md");
  fs.writeFileSync(path.join(build, "shot.png"), "png");
  fs.writeFileSync(path.join(build, "snap2edit-demo.pptx"), "pptx");
  assert.ok(resolveArtifact(id, "report.md")!.endsWith("report.md"));
  assert.ok(resolveArtifact(id, "shot.png")!.endsWith("shot.png"));
  assert.ok(resolveArtifact(id, "pptx")!.endsWith("snap2edit-demo.pptx"));
});
