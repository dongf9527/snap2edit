# -*- coding: utf-8 -*-
"""规格书（spec）加载与校验 —— 两条产线的唯一事实源。

规格书是一份 YAML：画布、幻灯片、字体、色板、文案清单（终检用）、
以及带 id 的元素列表。元素类型（v0）：

    rect / rrect / pill   矩形、圆角矩形、胶囊（可携带居中 text）
    text                  自由文本（支持 lines 多行）
    line / arrow          直线、箭头（箭头渲染为 线段+三角 两个独立单元）
"""

import yaml

SUPPORTED_TYPES = {"rect", "rrect", "pill", "text", "line", "arrow"}
_GEOM_BOX = ("x", "y", "w", "h")
_GEOM_SEG = ("x1", "y1", "x2", "y2")
PLACEHOLDER_BLACKLIST = ("XXX", "TODO", "待补充", "【", "undefined", "NaN")


class SpecError(Exception):
    pass


def load(path):
    with open(path, encoding="utf-8") as f:
        spec = yaml.safe_load(f)
    return validate(spec)


def validate(spec):
    if not isinstance(spec, dict):
        raise SpecError("规格书必须是一个 YAML 映射")
    canvas = spec.get("canvas") or {}
    if not (isinstance(canvas.get("width"), (int, float))
            and isinstance(canvas.get("height"), (int, float))):
        raise SpecError("canvas.width / canvas.height 必须是数字")
    elements = spec.get("elements")
    if not elements:
        raise SpecError("elements 不能为空")

    seen = set()
    for i, el in enumerate(elements):
        where = f"elements[{i}]"
        t = el.get("type")
        if t not in SUPPORTED_TYPES:
            raise SpecError(f"{where}: 不支持的类型 {t!r}（支持: {sorted(SUPPORTED_TYPES)}）")
        eid = el.get("id")
        if not eid:
            raise SpecError(f"{where}: 缺少 id")
        if eid in seen:
            raise SpecError(f"{where}: id 重复 {eid!r}")
        seen.add(eid)

        if t == "text":
            need = ("x", "y")          # 自由文本只需锚点；宽度可选（用于居中/右对齐与边界校验）
        else:
            need = _GEOM_SEG if t in ("line", "arrow") else _GEOM_BOX
        missing = [k for k in need if not isinstance(el.get(k), (int, float))]
        if missing:
            raise SpecError(f"{where}({eid}): 缺少几何字段 {missing}")

        if t == "text":
            if not (el.get("text") or el.get("lines")):
                raise SpecError(f"{where}({eid}): 文本元素需要 text 或 lines")
        if el.get("text") and not el.get("size"):
            raise SpecError(f"{where}({eid}): 携带文字的元素需要 size")

    for bad in PLACEHOLDER_BLACKLIST:
        for el in elements:
            blob = str(el.get("text", "")) + "".join(el.get("lines") or [])
            if bad in blob:
                raise SpecError(f"元素 {el.get('id')}: 文案含占位符 {bad!r}，请先补全内容")
    return spec


def texts_of(spec):
    """终检文案清单：spec.texts 优先；否则自动收集全部文字。"""
    listed = spec.get("texts")
    if listed:
        return [str(t) for t in listed]
    out = []
    for el in spec["elements"]:
        if el.get("lines"):
            out.extend(str(x) for x in el["lines"])
        elif el.get("text"):
            out.append(str(el["text"]))
    return out
