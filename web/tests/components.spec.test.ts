// web/tests/components.spec.test.ts —— F6 组件库：canvas 镜像渲染 + spec 校验 + texts 回填
// 运行：cd web && node --test tests/*.test.ts
import assert from "node:assert/strict";
import test from "node:test";
import {
  contrastText,
  cubeFaces,
  ICON_NAMES,
  iconParts,
  matrixCells,
  regenTexts,
  renderElementSvg,
  shade,
  type SpecDoc,
  type SpecEl,
} from "../lib/canvas.ts";
import { COMPOSITE_TYPES, validateSpecYaml } from "../lib/spec.ts";

const specOf = (els: SpecEl[]): SpecDoc => ({
  canvas: { width: 1280, height: 720 },
  palette: { primary: "#111111", accent: "#2B6CB0", card: "#FFFFFF", muted: "#8A97A8", bg: "#FFFFFF" },
  elements: els,
});

/* ---------- components 几何/颜色（与 Python 引擎同语义） ---------- */

test("shade/contrastText：明暗演算与对比色阈值", () => {
  assert.equal(shade("#2B6CB0", 0), "#2B6CB0");
  assert.notEqual(shade("#2B6CB0", 0.25), "#2B6CB0");
  assert.equal(shade("#FFFFFF", -0.5), "#808080");
  assert.equal(shade("#000000", 1), "#FFFFFF");
  assert.equal(contrastText("#FFFFFF"), "#1F2937");
  assert.equal(contrastText("#2B6CB0"), "#FFFFFF");
});

test("cubeFaces：缺省深度、钳制与三面几何", () => {
  const f = cubeFaces(10, 20, 100, 80, 16);
  assert.equal(f.depth, 16);
  assert.deepEqual(f.front, [10, 36, 84, 64]);
  assert.equal(cubeFaces(0, 0, 100, 100).depth, 20);
  assert.equal(cubeFaces(0, 0, 40, 40, 99).depth, 20);
  assert.equal(cubeFaces(0, 0, 40, 40, -5).depth, 0);
});

test("matrixCells：均分与 gap", () => {
  const cells = matrixCells(0, 0, 210, 100, 2, 3, 10);
  assert.equal(cells.length, 6);
  assert.deepEqual(cells[0], [0, 0, (210 - 20) / 3, (100 - 10) / 2]);
  assert.equal(cells[3][1], (100 - 10) / 2 + 10);
});

test("iconParts/ICON_NAMES：contain 缩放居中与未知图标容错", () => {
  assert.ok(ICON_NAMES.includes("brain") && ICON_NAMES.includes("target"));
  const parts = iconParts("chart", 0, 0, 50, 100);
  const xs = parts.flatMap(([, pts]) => pts.map(([x]) => x));
  const ys = parts.flatMap(([, pts]) => pts.map(([, y]) => y));
  assert.ok(Math.min(...xs) >= -1e-6 && Math.max(...xs) <= 50 + 1e-6);
  assert.ok(Math.min(...ys) >= 25 - 1e-6 && Math.max(...ys) <= 75 + 1e-6);
  assert.deepEqual(iconParts("no-such", 0, 0, 10, 10), []);
});

/* ---------- canvas 渲染镜像 ---------- */

test("renderElementSvg：cube 三面 + 正面文字", () => {
  const html = renderElementSvg(specOf([]), {
    id: "c", type: "cube", x: 0, y: 0, w: 80, h: 70, fill: "#2B6CB0", depth: 12,
    text: "立", size: 12, color: "#FFFFFF",
  });
  assert.ok(html.includes('<polygon id="c-top"'));
  assert.ok(html.includes('<polygon id="c-side"'));
  assert.ok(html.includes('<rect id="c"'));
  assert.ok(html.includes('<text id="c-text"'));
});

test("renderElementSvg：matrix-cell 逐格 id + 逐格文字 + 对比色", () => {
  const html = renderElementSvg(specOf([]), {
    id: "m", type: "matrix-cell", x: 0, y: 0, w: 90, h: 60, rows: 2, cols: 3,
    gap: 4, fill: "#2B6CB0", texts: ["一", "二", "三"], size: 10,
  });
  assert.ok(html.includes('<rect id="m-r1c1"'));
  assert.ok(html.includes('<rect id="m-r2c3"'));
  assert.ok(html.includes('<text id="m-r1c1-text"'));
  assert.ok(html.includes('fill="#FFFFFF"'));               // 深底自动白字
});

test("renderElementSvg：flow-box 色带路径 + 标题/正文", () => {
  const html = renderElementSvg(specOf([]), {
    id: "f", type: "flow-box", x: 0, y: 0, w: 120, h: 70, fill: "#EFF6FF",
    title: "标题", text: "正文", size: 10, band: 0.3,
  });
  assert.ok(html.includes('<path id="f-band"'));
  assert.ok(html.includes('<text id="f-title"'));
  assert.ok(html.includes('<text id="f-text"'));
});

test("renderElementSvg：icon 三种部件（fill/ring/stroke）", () => {
  const gear = renderElementSvg(specOf([]), { id: "g", type: "icon", x: 0, y: 0, w: 60, h: 60, name: "gear", fill: "#2F855A" });
  assert.ok(gear.includes('<polygon id="g-0"'));
  assert.ok(gear.includes('fill="none" stroke='));
  const brain = renderElementSvg(specOf([]), { id: "b", type: "icon", x: 0, y: 0, w: 60, h: 60, name: "brain", fill: "#2B6CB0" });
  assert.ok(brain.includes("<polyline"));
});

/* ---------- regenTexts / spec 校验 ---------- */

test("regenTexts：含组件库文字且标题先于正文", () => {
  const texts = regenTexts({
    canvas: { width: 100, height: 100 },
    elements: [
      { id: "m", type: "matrix-cell", x: 0, y: 0, w: 60, h: 30, rows: 1, cols: 2, texts: ["甲", "乙"] },
      { id: "f", type: "flow-box", x: 0, y: 40, w: 60, h: 30, title: "流程", text: "正文" },
      { id: "t", type: "text", x: 0, y: 80, text: "自由文本" },
    ],
  });
  assert.deepEqual(texts, ["甲", "乙", "流程", "正文", "自由文本"]);
});

test("validateSpecYaml：组件类型通过校验且 texts 回填含组件文字", () => {
  const yaml = [
    "project: 组件测试",
    "canvas: {width: 400, height: 300}",
    "elements:",
    "  - {id: c, type: cube, x: 0, y: 0, w: 80, h: 70, fill: '#2B6CB0'}",
    "  - {id: m, type: matrix-cell, x: 100, y: 0, w: 90, h: 60, rows: 2, cols: 3, texts: ['一', '二', '三'], size: 10}",
    "  - {id: f, type: flow-box, x: 210, y: 0, w: 120, h: 70, title: 标题, text: 正文, size: 10}",
    "  - {id: i, type: icon, x: 350, y: 0, w: 40, h: 40, name: gear}",
  ].join("\n");
  const v = validateSpecYaml(yaml);
  assert.equal(v.ok, true, v.errors.join("; "));
  assert.ok(v.fixedYaml && v.fixedYaml.includes("一"));      // texts 自动回填含矩阵文字
});

test("validateSpecYaml：组件非法参数报错 + 复合组件 rotate 告警", () => {
  const base = "project: 组件测试\ncanvas: {width: 400, height: 300}\ntexts: [x]\nelements:\n";
  const v1 = validateSpecYaml(base + "  - {id: m, type: matrix-cell, x: 0, y: 0, w: 90, h: 60, rows: 1, cols: 1, texts: ['一', '二'], size: 10}\n");
  assert.ok(v1.errors.some((e) => e.includes("超出格子数")));
  const v2 = validateSpecYaml(base + "  - {id: i, type: icon, x: 0, y: 0, w: 40, h: 40, name: rocket}\n");
  assert.ok(v2.errors.some((e) => e.includes("未知图标")));
  const v3 = validateSpecYaml(base + "  - {id: f, type: flow-box, x: 0, y: 0, w: 80, h: 60}\n");
  assert.ok(v3.errors.some((e) => e.includes("需要 title")));
  const v4 = validateSpecYaml(base + "  - {id: c, type: cube, x: 0, y: 0, w: 80, h: 70, rotate: 30}\n");
  assert.ok(v4.warnings.some((w) => w.includes("不支持 rotate")));
});

test("COMPOSITE_TYPES 与引擎 _COMPOSITE_TYPES 同源", () => {
  assert.deepEqual([...COMPOSITE_TYPES].sort(), ["cube", "flow-box", "icon", "matrix-cell"]);
});
