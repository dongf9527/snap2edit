// web/tests/spec.spec.test.ts —— lib/spec.ts 全量单元测试（rotate 专项见 spec.rotate.test.ts）
// 运行：cd web && node --test tests/*.test.ts   （Node 24 原生跑 TS）
import assert from "node:assert/strict";
import test from "node:test";
import {
  buildFixPrompt,
  buildSkeletonYaml,
  buildSystemPrompt,
  buildUserPrompt,
  dumpSpecYaml,
  extractCodeBlock,
  normalizeImageMeta,
  normalizeSpec,
  parseSpecJson,
  validateSpecYaml,
} from "../lib/spec.ts";

/* ---------- normalizeImageMeta ---------- */

test("normalizeImageMeta：越界字段剔除、类型收紧、palette 过滤", () => {
  const m = normalizeImageMeta({
    width: 1280.6,
    height: -5,
    filename: "x".repeat(200),
    palette: ["#AABBCC", "nothex", 42, "#12345G", "#FFFFFF"],
  });
  assert.equal(m.width, 1281);
  assert.equal(m.height, 0);
  assert.equal(m.filename!.length, 120);
  assert.deepEqual(m.palette, ["#AABBCC", "#FFFFFF"]);

  const empty = normalizeImageMeta(null);
  assert.deepEqual(empty, { width: 0, height: 0, filename: undefined, palette: undefined });
});

/* ---------- dumpSpecYaml ---------- */

test("dumpSpecYaml：字符串双引号风格（防 16:9 被读成六十进制）、key 朴素、不折行", () => {
  const y = dumpSpecYaml({ project: "t", slide: { preset: "16:9" }, a: 1 });
  assert.match(y, /preset: "16:9"/);
  assert.match(y, /^a: 1$/m);
  assert.match(y, /^project: "t"$/m);
});

/* ---------- 提示词 ---------- */

test("buildSystemPrompt：核心硬性规则齐备", () => {
  const p = buildSystemPrompt();
  assert.match(p, /只输出一个 JSON 对象/);
  assert.match(p, /texts 数组是全图文字清单/);
  assert.match(p, /禁止出现：XXX、TODO、待补充、【、undefined、NaN/);
  assert.match(p, /箭头用 type:arrow/);
});

test("buildUserPrompt：尺寸/文件名/主色按 meta 组装", () => {
  const withAll = buildUserPrompt({ width: 1280, height: 720, filename: "demo.png", palette: ["#123456"] });
  assert.match(withAll, /原图尺寸：1280 x 720 px/);
  assert.match(withAll, /文件名：demo\.png/);
  assert.match(withAll, /#123456/);
  const bare = buildUserPrompt({ width: 800, height: 600 });
  assert.match(bare, /原图尺寸：800 x 600 px/);
  assert.doesNotMatch(bare, /文件名/);
});

test("buildFixPrompt：错误清单 + YAML 参考 + 输出要求", () => {
  const p = buildFixPrompt(["门1 · 缺失文案", "门3 · 文本溢出"], "project: t\nelements: []");
  assert.match(p, /1\. 门1 · 缺失文案/);
  assert.match(p, /2\. 门3 · 文本溢出/);
  assert.match(p, /```yaml/);
  assert.match(p, /rotate 非法→改为 0-360 的数字或删除该键/);
  assert.match(p, /只输出修正后的完整 JSON 本体/);
});

/* ---------- extractCodeBlock / parseSpecJson ---------- */

test("extractCodeBlock：剥离围栏（带语言/无语言）、裸文本原样", () => {
  assert.equal(extractCodeBlock('```json\n{"a":1}\n```'), '{"a":1}');
  assert.equal(extractCodeBlock('```\n{"a":1}\n```'), '{"a":1}');
  assert.equal(extractCodeBlock('{"a":1}'), '{"a":1}');
});

test("parseSpecJson：直解/围栏/尾逗号修复/根节点/坏 JSON", () => {
  assert.deepEqual(parseSpecJson('{"a":1}'), { ok: true, spec: { a: 1 } });
  assert.deepEqual(parseSpecJson('```json\n{"a":1}\n```'), { ok: true, spec: { a: 1 } });
  assert.deepEqual(parseSpecJson('{"a":[1,2,],}'), { ok: true, spec: { a: [1, 2] } });
  const r1 = parseSpecJson("null");
  assert.ok(!r1.ok && r1.error.includes("根节点必须是对象"));
  const r2 = parseSpecJson("{oops");
  assert.ok(!r2.ok && r2.error.includes("JSON 解析失败"));
});

/* ---------- normalizeSpec ---------- */

test("normalizeSpec：多行 text 拆分（y 按行高递增）并备注", () => {
  const { spec, notes } = normalizeSpec({
    elements: [{ id: "x", type: "text", x: 10, y: 100, size: 20, line_h: 1.5, text: "A\nB\nC" }],
  });
  const els = spec.elements as Record<string, unknown>[];
  assert.equal(els.length, 3);
  assert.equal(els[0].y, 100);
  assert.equal(els[1].y, 130); // 100 + 20*1.5
  assert.equal(els[2].y, 160);
  assert.ok(notes.some((n) => n.includes("多行文本")));
});

test("normalizeSpec：texts 清单对齐——包含/前缀回填/剔除 + 重编号", () => {
  const { spec, notes } = normalizeSpec({
    texts: ["标题", "被截断的清单项目全文", "清单里多出来的"],
    elements: [
      { id: "z9", type: "text", x: 0, y: 0, size: 16, text: "标题" },
      { id: "z2", type: "text", x: 0, y: 40, size: 16, text: "被截断的清单" }, // ≥6 字符才触发前缀回填
    ],
  });
  const els = spec.elements as Record<string, unknown>[];
  assert.deepEqual(els.map((e) => e.id), ["e1", "e2"]); // 全量重编号
  assert.equal(els[1].text, "被截断的清单项目全文"); // 前缀回填
  assert.deepEqual(spec.texts, ["标题", "被截断的清单项目全文"]); // 多余项剔除
  assert.ok(notes.some((n) => n.includes("回填")));
  assert.ok(notes.some((n) => n.includes("剔除")));
});

test("normalizeSpec：texts 非字符串项被过滤；全部无效时保留原数组交校验器报错", () => {
  const { spec } = normalizeSpec({
    texts: ["ok", 42, null],
    elements: [{ id: "a", type: "rect", x: 0, y: 0, w: 10, h: 10 }],
  });
  // "ok" 不在任何元素文本中 → 被剔除 → finalTexts 空 → 不写回，保留原始数组（校验器报错 → 回询）
  assert.deepEqual(spec.texts, ["ok", 42, null]);
  assert.equal((spec.elements as unknown[]).length, 1);
});

/* ---------- validateSpecYaml ---------- */

const baseYaml = (elements: string, extra = 'texts: ["文案A"]') =>
  [
    "project: 单元测试",
    "canvas: { width: 1280, height: 720 }",
    'palette: { primary: "#1F2937", accent: "#2B6CB0", card: "#FFFFFF", bg: "#FFFFFF" }',
    extra,
    "elements:",
    elements,
  ].join("\n");

test("validateSpecYaml：YAML 语法错 / 根节点 / project / canvas / elements 逐项报错", () => {
  const bad = validateSpecYaml("a: [1, 2");
  assert.ok(!bad.ok && bad.errors.some((e) => e.includes("YAML 解析失败")));

  const root = validateSpecYaml("42"); // 标量/空根 → 根节点错（数组根走逐项报错）
  assert.ok(!root.ok && root.errors.includes("spec 根节点必须是对象"));

  const noProj = validateSpecYaml(baseYaml("  - { id: e1, type: rect, x: 0, y: 0, w: 10, h: 10 }").replace("project: 单元测试", ""));
  assert.ok(!noProj.ok && noProj.errors.some((e) => e.includes("project")));

  const noCanvas = validateSpecYaml(baseYaml("  - { id: e1, type: rect, x: 0, y: 0, w: 10, h: 10 }").replace(/canvas:.*/, ""));
  assert.ok(!noCanvas.ok && noCanvas.errors.some((e) => e.includes("canvas")));

  const noEls = validateSpecYaml(baseYaml("").replace(/elements:.*/, ""));
  assert.ok(!noEls.ok && noEls.errors.some((e) => e.includes("elements")));
});

test("validateSpecYaml：类型/几何/id 重复/文本内容/字号 逐项报错", () => {
  const v = validateSpecYaml(
    baseYaml(
      [
        '  - { id: e1, type: hexagon, x: 0, y: 0, w: 10, h: 10 }',
        "  - { id: e2, type: rect, x: 0, y: 0 }",
        "  - { id: e3, type: text, x: 0, y: 0, size: 14 }",
        "  - { id: e4, type: rect, x: 0, y: 0, w: 10, h: 10 }",
        "  - { id: e4, type: rect, x: 0, y: 0, w: 10, h: 10 }",
      ].join("\n")
    )
  );
  assert.ok(!v.ok);
  assert.ok(v.errors.some((e) => e.includes("type 非法")));
  assert.ok(v.errors.some((e) => e.includes("缺少数值字段 w")));
  assert.ok(v.errors.some((e) => e.includes("缺少文字内容")));
  assert.ok(v.errors.filter((e) => e.includes("id 重复")).length === 1);
});

test("validateSpecYaml：告警——text 缺 size、坐标越界、texts 缺失自动回填（fixedYaml）", () => {
  const v = validateSpecYaml(
    baseYaml("  - { id: e1, type: text, x: 1300, y: 700, text: '越界文案' }", "texts: []")
  );
  assert.ok(v.ok);
  assert.ok(v.warnings.some((w) => w.includes("缺少 size")));
  assert.ok(v.warnings.some((w) => w.includes("越出画布")));
  assert.ok(v.warnings.some((w) => w.includes("texts 清单缺失")));
  assert.ok(v.fixedYaml && v.fixedYaml.includes("越界文案"));
});

test("validateSpecYaml：texts 全字符串校验 + 占位符黑名单（含回填后扫描）", () => {
  const badType = validateSpecYaml(
    baseYaml("  - { id: e1, type: rect, x: 0, y: 0, w: 10, h: 10 }", "texts: [1, 2]")
  );
  assert.ok(!badType.ok && badType.errors.some((e) => e.includes("texts 数组必须全部为字符串")));

  const ph = validateSpecYaml(
    baseYaml('  - { id: e1, type: text, x: 0, y: 0, size: 14, text: "待补充的说明" }', "texts: []")
  );
  assert.ok(!ph.ok && ph.errors.some((e) => e.includes("待补充")));
});

/* ---------- buildSkeletonYaml ---------- */

test("buildSkeletonYaml：主色取非白、骨架自身过校验；空 palette 走默认", () => {
  const s1 = buildSkeletonYaml({ width: 1280, height: 720, filename: "季度汇报.png", palette: ["#FFFFFF", "#2B6CB0", "#F7F9FC"] });
  assert.match(s1, /project: "季度汇报"/);
  assert.match(s1, /"#2B6CB0"/);
  assert.ok(validateSpecYaml(s1).ok);

  const s2 = buildSkeletonYaml({ width: 0, height: 0 });
  assert.match(s2, /width: 1280/);
  assert.ok(validateSpecYaml(s2).ok);
});
