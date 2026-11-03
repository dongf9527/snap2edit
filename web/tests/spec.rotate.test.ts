// web/tests/spec.rotate.test.ts —— lib/spec.ts rotate 链路单元测试
// 运行：cd web && node --test tests/   （Node 24 原生跑 TS，无需编译）
// 覆盖：VLM 提示词 rotate 规则 / normalizeSpec 归一化同源 / validateSpecYaml 分级判定
import assert from "node:assert/strict";
import test from "node:test";
import { buildSystemPrompt, normalizeSpec, validateSpecYaml } from "../lib/spec.ts";

test("系统提示词包含 rotate 抽取规则（顺时针 / [0,360) / 线段排除）", () => {
  const p = buildSystemPrompt();
  assert.match(p, /rotate/);
  assert.match(p, /顺时针/);
  assert.match(p, /\[0,360\)/);
  assert.match(p, /不要写 rotate/); // 水平/垂直元素与线段/箭头两处
  assert.match(p, /倾斜由端点坐标表达/);
  assert.match(p, /±5°/); // 复杂度取舍里的角度容差
});

test("normalizeSpec：线段/箭头 rotate 键剔除并备注", () => {
  const { spec, notes } = normalizeSpec({
    elements: [
      { id: "a", type: "line", x1: 0, y1: 0, x2: 100, y2: 50, rotate: 15 },
      { id: "b", type: "arrow", x1: 0, y1: 0, x2: 100, y2: 50, rotate: 30 },
    ],
  });
  for (const el of spec.elements) assert.ok(!("rotate" in el));
  assert.ok(notes.some((n) => n.includes("rotate 键")));
});

test("normalizeSpec：rotate 归一化 [0,360)（370→10、-10→350、0 删键、一位小数）", () => {
  const { spec, notes } = normalizeSpec({
    elements: [
      { id: "a", type: "rect", x: 0, y: 0, w: 10, h: 10, rotate: 370 },
      { id: "b", type: "rect", x: 0, y: 0, w: 10, h: 10, rotate: -10 },
      { id: "c", type: "rect", x: 0, y: 0, w: 10, h: 10, rotate: 0 },
      { id: "d", type: "text", x: 0, y: 0, text: "T", rotate: 12.34 },
    ],
  });
  const [a, b, c, d] = spec.elements;
  assert.equal(a.rotate, 10);
  assert.equal(b.rotate, 350);
  assert.ok(!("rotate" in c));
  assert.equal(d.rotate, 12.3);
  assert.ok(notes.some((n) => n.includes("归一化")));
});

test("normalizeSpec：非法 rotate 保留交校验器报错（回询链路）", () => {
  const { spec } = normalizeSpec({
    elements: [{ id: "a", type: "rect", x: 0, y: 0, w: 10, h: 10, rotate: "abc" }],
  });
  assert.equal(spec.elements[0].rotate, "abc");
});

test("validateSpecYaml：rotate 非数字报错 / 越界与线段仅告警 / 合法值零噪音", () => {
  const base = (elYaml: string) =>
    [
      "project: t",
      "canvas: { width: 1280, height: 720 }",
      'palette: { primary: "#1F2937", accent: "#2B6CB0", card: "#FFFFFF", bg: "#FFFFFF" }',
      'texts: ["文案A"]',
      "elements:",
      elYaml,
    ].join("\n");

  const v1 = validateSpecYaml(
    base('  - { id: e1, type: rect, x: 0, y: 0, w: 10, h: 10, rotate: "abc" }')
  );
  assert.ok(!v1.ok);
  assert.ok(v1.errors.some((e) => e.includes("rotate 必须是数字")));

  const v2 = validateSpecYaml(
    base("  - { id: e1, type: rect, x: 0, y: 0, w: 10, h: 10, rotate: 400 }")
  );
  assert.ok(v2.ok);
  assert.ok(v2.warnings.some((w) => w.includes("归一化")));

  const v3 = validateSpecYaml(
    base("  - { id: e1, type: line, x1: 0, y1: 0, x2: 10, y2: 10, rotate: 30 }")
  );
  assert.ok(v3.ok);
  assert.ok(v3.warnings.some((w) => w.includes("不支持 rotate")));

  const v4 = validateSpecYaml(
    base("  - { id: e1, type: rect, x: 0, y: 0, w: 10, h: 10, rotate: 45 }")
  );
  assert.ok(v4.ok);
  assert.equal(v4.warnings.length, 0);
});
