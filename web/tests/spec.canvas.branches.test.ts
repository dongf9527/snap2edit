// web/tests/spec.canvas.branches.test.ts —— spec 校验组件分支 + computeSnap 吸附方向分支补全
// 运行：cd web && node --test tests/spec.canvas.branches.test.ts
import assert from "node:assert/strict";
import test from "node:test";
import { validateSpecYaml } from "../lib/spec.ts";
import { computeSnap, type SnapGuides } from "../lib/canvas.ts";
import type { SpecEl } from "../lib/spec.ts";

/* ---------- validateSpecYaml：组件库校验分支 ---------- */

const baseYaml = (elements: string) =>
  [
    "project: 单元测试",
    "canvas: { width: 1280, height: 720 }",
    'palette: { primary: "#1F2937", accent: "#2B6CB0", card: "#FFFFFF", bg: "#FFFFFF" }',
    'texts: ["文案A"]',
    "elements:",
    elements,
  ].join("\n");

test("validateSpecYaml：icon 缺 name → 「缺少 name」分支", () => {
  const v = validateSpecYaml(baseYaml("  - { id: i1, type: icon, x: 0, y: 0, w: 40, h: 40 }"));
  assert.ok(!v.ok && v.errors.some((e) => e.includes("缺少 name")));
});

test("validateSpecYaml：icon 未知 name → 「未知图标」分支", () => {
  const v = validateSpecYaml(baseYaml("  - { id: i1, type: icon, x: 0, y: 0, w: 40, h: 40, name: rocket }"));
  assert.ok(!v.ok && v.errors.some((e) => e.includes("未知图标")));
});

test("validateSpecYaml：flow-box 无 title 也无 text/lines → 「需要 title 或 text/lines」分支", () => {
  const v = validateSpecYaml(baseYaml("  - { id: f1, type: flow-box, x: 0, y: 0, w: 100, h: 50 }"));
  assert.ok(!v.ok && v.errors.some((e) => e.includes("需要 title 或 text/lines")));
});

/* ---------- computeSnap：吸附方向与并列参考线分支 ---------- */

const rect = (id: string, x: number, y: number, w: number, h: number): SpecEl =>
  ({ id, type: "rect", x, y, w, h } as SpecEl);

const CANVAS = { w: 1280, h: 720 };
// 静态元素 s1：x=200..300, y=300..350（目标集：x∈{200,250,300} y∈{300,325,350} + 画布三线）
const S1 = rect("s1", 200, 300, 100, 50);
const M1 = rect("m1", 210, 310, 80, 40);

test("computeSnap：移动盒右缘 → 静态盒左缘（水平边对边）", () => {
  const r = computeSnap([M1], ["m1"], [S1, M1], CANVAS, -88, 0);
  assert.equal(r.dx, -90); // 右缘 202 → 200
  assert.deepEqual(r.guides.v, [200]);
});

test("computeSnap：中心对中心（x 轴精确命中，参考线出中线）", () => {
  const r = computeSnap([M1], ["m1"], [S1, M1], CANVAS, 0, 0);
  assert.equal(r.dx, 0);
  assert.ok(r.guides.v.includes(250));
});

test("computeSnap：y 向最近目标胜出（中心 326 → 325）", () => {
  const r = computeSnap([M1], ["m1"], [S1, M1], CANVAS, 0, -4);
  assert.equal(r.dy, -5);
  assert.deepEqual(r.guides.h, [325]);
});

test("computeSnap：画布上缘吸附（y=-1 → 0）", () => {
  const r = computeSnap([M1], ["m1"], [S1, M1], CANVAS, 0, -311);
  assert.equal(r.dy, -310);
  assert.deepEqual(r.guides.h, [0]);
});

test("computeSnap：等距双目标 → 参考线并列（tie 分支）", () => {
  // s1/s2 用 h=0 的"线状盒"：目标集各自只剩单值 {300} / {400}（h=0 三边重合去重）
  const s1 = rect("s1", 100, 300, 100, 0);
  const s2 = rect("s2", 100, 400, 100, 0);
  // m2 边缘 306/350/394：306↔300 = -6，394↔400 = +6，等距并列；350↔360(画布中线) 距 10 > 阈值
  const m2 = rect("m2", 50, 306, 80, 88);
  const r = computeSnap([m2], ["m2"], [s1, s2, m2], CANVAS, 0, 0);
  const guides = r.guides.h as SnapGuides["h"];
  assert.equal(r.dy, -6);
  assert.ok(guides.includes(300) && guides.includes(400), `应并列 300/400，实际 ${JSON.stringify(guides)}`);
});

test("computeSnap：排除自身后仅剩画布目标集 → 仍可吸附画布中线（dy 7→10）", () => {
  const r = computeSnap([M1], ["m1"], [M1], CANVAS, 5, 7);
  assert.equal(r.dx, 5); // x 向远离画布三线（0/640/1280）→ 不吸附
  assert.equal(r.dy, 10); // 下缘 357 距画布中线 360 仅 3px → 吸附 +3
  assert.deepEqual(r.guides.h, [360]);
  assert.equal(r.guides.v.length, 0);
});
