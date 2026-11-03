// web/tests/canvas.spec.test.ts —— lib/canvas.ts 单元测试（渲染镜像 / 几何 / 吸附 / 文本同步）
// 运行：cd web && node --test tests/*.test.ts
import assert from "node:assert/strict";
import test from "node:test";
import {
  blankSpec,
  computeSnap,
  elBBox,
  elText,
  regenTexts,
  renderElementSvg,
  renderSpecSvg,
  SNAP_THRESHOLD,
  syncTextOnEdit,
  translateEl,
  type SpecDoc,
  type SpecEl,
} from "../lib/canvas.ts";

const specOf = (els: SpecEl[], extra: Partial<SpecDoc> = {}): SpecDoc => ({
  canvas: { width: 1280, height: 720 },
  palette: { primary: "#111111", accent: "#2B6CB0", card: "#EBF2FF", muted: "#8A97A8", bg: "#FFFFFF" },
  elements: els,
  ...extra,
});

/* ---------- elText / elBBox / translateEl ---------- */

test("elText：lines 优先于 text，缺省空串", () => {
  assert.equal(elText({ id: "a", type: "text", lines: ["L1", "L2"], text: "T" }), "L1\nL2");
  assert.equal(elText({ id: "a", type: "text", text: "T" }), "T");
  assert.equal(elText({ id: "a", type: "text" }), "");
});

test("elBBox：盒子原样、文本按字号估宽、线段取最小角+绝对尺寸", () => {
  assert.deepEqual(elBBox({ id: "a", type: "rect", x: 5, y: 6, w: 100, h: 50 }), { x: 5, y: 6, w: 100, h: 50 });

  const tb = elBBox({ id: "t", type: "text", x: 10, y: 20, size: 20, lines: ["AB", "C"] });
  assert.equal(tb.x, 10);
  assert.equal(tb.y, 20);
  assert.equal(tb.w, Math.round(2 * 20 * 0.62));
  assert.ok(Math.abs(tb.h - 2 * 1.45 * 20) < 1e-6);

  const seg = elBBox({ id: "s", type: "line", x1: 300, y1: 100, x2: 100, y2: 40 });
  assert.deepEqual(seg, { x: 100, y: 40, w: 200, h: 60 });

  // 缺省字段不抛错
  assert.deepEqual(elBBox({ id: "z", type: "rect" }), { x: 0, y: 0, w: 0, h: 0 });
});

test("translateEl：盒子与线段分别平移并取整", () => {
  const box: SpecEl = { id: "b", type: "rect", x: 10.4, y: 5, w: 10, h: 10 };
  translateEl(box, 1.6, -2);
  assert.equal(box.x, 12);
  assert.equal(box.y, 3);

  const seg: SpecEl = { id: "s", type: "line", x1: 0, y1: 0, x2: 10, y2: 10 };
  translateEl(seg, 5, -3);
  assert.deepEqual([seg.x1, seg.y1, seg.x2, seg.y2], [5, -3, 15, 7]);
});

/* ---------- renderElementSvg（与 svgout 同语义断言） ---------- */

test("renderElementSvg：rect——fill 键缺失回退 palette.card，fill:null（键存在）→ 透明", () => {
  const s = specOf([]);
  const missing = renderElementSvg(s, { id: "r1", type: "rect", x: 0, y: 0, w: 10, h: 10 });
  assert.match(missing, /fill="#EBF2FF"/); // card
  const transparent = renderElementSvg(s, { id: "r2", type: "rect", x: 0, y: 0, w: 10, h: 10, fill: null });
  assert.match(transparent, /fill="none"/);
  const stroked = renderElementSvg(s, { id: "r3", type: "rect", x: 0, y: 0, w: 10, h: 10, fill: "#123456", stroke: "#ABCDEF", stroke_width: 2.5 });
  assert.match(stroked, /fill="#123456"/);
  assert.match(stroked, /stroke="#ABCDEF" stroke-width="2.5"/);
});

test("renderElementSvg：circle→ellipse、pill rx=h/2、rrect 默认 rx 与显式 rx", () => {
  const s = specOf([]);
  assert.match(renderElementSvg(s, { id: "c", type: "circle", x: 10, y: 20, w: 40, h: 20 }), /<ellipse id="c" cx="30" cy="30" rx="20" ry="10"/);
  assert.match(renderElementSvg(s, { id: "p", type: "pill", x: 0, y: 0, w: 80, h: 20 }), /rx="10"/);
  assert.match(renderElementSvg(s, { id: "q", type: "rrect", x: 0, y: 0, w: 80, h: 20 }), /rx="2"/); // min*0.1
  assert.match(renderElementSvg(s, { id: "q2", type: "rrect", x: 0, y: 0, w: 80, h: 20, rx: 12 }), /rx="12"/);
});

test("renderElementSvg：文本对齐锚点/粗细/调色板回退/旋转/内嵌文本同步旋转", () => {
  const s = specOf([]);
  const left = renderElementSvg(s, { id: "t1", type: "text", x: 5, y: 5, size: 16, text: "你好" });
  assert.match(left, /text-anchor="start"/);
  assert.match(left, /fill="#111111"/); // color 缺失 → palette.primary
  const center = renderElementSvg(s, { id: "t2", type: "text", x: 5, y: 5, size: 16, text: "你", align: "center", bold: true });
  assert.match(center, /text-anchor="middle"/);
  assert.match(center, /font-weight="bold"/);
  const right = renderElementSvg(s, { id: "t3", type: "text", x: 5, y: 5, size: 16, text: "你", align: "right" });
  assert.match(right, /text-anchor="end"/);
  const rot = renderElementSvg(s, { id: "t4", type: "text", x: 100, y: 60, size: 16, rotate: -15, text: "斜" });
  assert.match(rot, /transform="rotate\(345 100 60\)"/); // -15 → 345 绕锚点

  const box = renderElementSvg(s, { id: "b1", type: "rrect", x: 0, y: 0, w: 100, h: 40, fill: "#123456", rotate: 30, text: "盒内文", size: 14 });
  assert.match(box, /transform="rotate\(30 50 20\)"/); // 盒子绕中心
  assert.match(box, /id="b1-text"/);
  assert.match(box, /transform="rotate\(30 50 20\)"/g); // 内嵌文本同 transform
});

test("renderElementSvg：line 默认色/宽度；arrow 线段+三角头两个节点；未知类型空串", () => {
  const s = specOf([]);
  const line = renderElementSvg(s, { id: "l", type: "line", x1: 0, y1: 0, x2: 100, y2: 50 });
  assert.match(line, /<line id="l" x1="0" y1="0" x2="100" y2="50" stroke="#8A97A8" stroke-width="1"/);

  const arrow = renderElementSvg(s, { id: "a", type: "arrow", x1: 0, y1: 0, x2: 100, y2: 0, stroke: "#FF0000" });
  assert.match(arrow, /<line id="a"/);
  assert.match(arrow, /<polygon id="a-head" points="100,0 [^"]+" fill="#FF0000"\/>/);
  assert.match(arrow, /x2="9[0-9.]*"/); // 线段止于头部之前（留出三角）

  assert.equal(renderElementSvg(s, { id: "x", type: "hexagon" } as SpecEl), "");
});

/* ---------- renderSpecSvg ---------- */

test("renderSpecSvg：viewBox/data-canvas/背景层；选中与悬停覆盖层互斥", () => {
  const els: SpecEl[] = [
    { id: "e1", type: "rect", x: 10, y: 10, w: 50, h: 40, fill: "#123456" },
    { id: "e2", type: "text", x: 20, y: 30, size: 16, text: "标签" },
  ];
  const plain = renderSpecSvg(specOf(els));
  assert.match(plain, /viewBox="0 0 1280 720" width="1280" height="720" data-canvas="1280x720"/);
  assert.match(plain, /<rect x="0" y="0" width="1280" height="720" fill="#FFFFFF"\/>/); // bg
  assert.doesNotMatch(plain, /class="ov-(sel|hov)"/);

  const sel = renderSpecSvg(specOf(els), { selectedIds: ["e1"], hoverId: "e2" });
  assert.match(sel, /class="ov-sel" x="7" y="7" width="56" height="46"/); // bbox+3pad
  assert.match(sel, /class="ov-hov"/); // 悬停与选中的是不同元素 → 两层都出
  const same = renderSpecSvg(specOf(els), { selectedIds: ["e1"], hoverId: "e1" });
  assert.match(same, /class="ov-sel"/);
  assert.doesNotMatch(same, /class="ov-hov"/); // 同一元素只出选中层

  const hov = renderSpecSvg(specOf(els), { hoverId: "e2" });
  assert.match(hov, /class="ov-hov"/);
});

/* ---------- regenTexts / syncTextOnEdit / blankSpec ---------- */

test("regenTexts：从元素重建清单并去重（lines 元素合并为一条）", () => {
  const texts = regenTexts(specOf([
    { id: "a", type: "text", text: "标题" },
    { id: "b", type: "text", text: "标题" },
    { id: "c", type: "text", lines: ["A", "B"] },
    { id: "d", type: "rect", x: 0, y: 0, w: 10, h: 10 },
  ]));
  assert.deepEqual(texts, ["标题", "A\nB"]);
});

test("syncTextOnEdit：替换/置空删除/新增追加；texts 非数组跳过", () => {
  const doc = specOf([{ id: "a", type: "text", text: "旧" }]);
  doc.texts = ["旧", "其他"];
  syncTextOnEdit(doc, "旧", "新");
  assert.deepEqual(doc.texts, ["新", "其他"]);
  syncTextOnEdit(doc, "新", "");
  assert.deepEqual(doc.texts, ["其他"]);
  syncTextOnEdit(doc, "不存在", "追加项");
  assert.deepEqual(doc.texts, ["其他", "追加项"]);
  const noArr = specOf([]);
  syncTextOnEdit(noArr, "a", "b"); // texts 缺失 → 不抛错
});

test("blankSpec：结构完整且元素/文案一一对应", () => {
  const b = blankSpec(800, 600);
  assert.equal(b.canvas!.width, 800);
  assert.equal(b.elements!.length, 2);
  assert.deepEqual(regenTexts(b), b.texts);
});

/* ---------- computeSnap ---------- */

const SNAP_T = SNAP_THRESHOLD;

test("computeSnap：垂直吸附——移动盒下缘距静态元素上缘 5px → 精确贴合并给参考线", () => {
  const moving: SpecEl = { id: "m", type: "rect", x: 0, y: 0, w: 100, h: 100 };
  const stat: SpecEl = { id: "s", type: "rect", x: 100, y: 200, w: 200, h: 100 };
  const r = computeSnap([moving], ["m"], [moving, stat], { w: 1280, h: 720 }, 0, 95, SNAP_T);
  assert.equal(r.dy, 100); // 195 → 200
  assert.deepEqual(r.guides.h, [200]);
});

test("computeSnap：画布右缘吸附 + 不吸附自身（movingIds 排除）", () => {
  const m: SpecEl = { id: "m", type: "rect", x: 0, y: 0, w: 100, h: 100 };
  const r = computeSnap([m], ["m"], [m], { w: 1280, h: 720 }, 1185, 0, SNAP_T);
  assert.equal(r.dx, 1180); // 右缘 1285 → 1280
  assert.deepEqual(r.guides.v, [1280]);
});

test("computeSnap：阈值外不吸附", () => {
  const m: SpecEl = { id: "m", type: "rect", x: 0, y: 0, w: 100, h: 100 };
  const stat: SpecEl = { id: "s", type: "rect", x: 100, y: 200, w: 200, h: 100 };
  const off = computeSnap([m], ["m"], [m, stat], { w: 1280, h: 720 }, 0, 95, 0);
  assert.equal(off.dy, 95);
  assert.deepEqual(off.guides.h, []);
  const far = computeSnap([m], ["m"], [m, stat], { w: 1280, h: 720 }, 0, 160, SNAP_T);
  assert.equal(far.dy, 160);
  assert.deepEqual(far.guides.h, []);
});

test("computeSnap：多元素组不吸组内成员；组内盒中线可吸画布中线", () => {
  const m1: SpecEl = { id: "m1", type: "rect", x: 0, y: 0, w: 100, h: 100 };
  const m2: SpecEl = { id: "m2", type: "rect", x: 100, y: 300, w: 100, h: 100 };
  const r = computeSnap([m1, m2], ["m1", "m2"], [m1, m2], { w: 1280, h: 720 }, 0, 8, SNAP_T);
  // m2 中心 350+8=358 距画布中线 360 差 2，优于 m1 上缘 8-0=8 → 取中线吸附
  assert.equal(r.dy, 10);
  assert.deepEqual(r.guides.h, [360]);
});
