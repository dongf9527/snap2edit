# -*- coding: utf-8 -*-
"""规格书（spec）加载与校验 —— 两条产线的唯一事实源。

规格书是一份 YAML：画布、幻灯片、字体、色板、文案清单（终检用）、
以及带 id 的元素列表。元素类型（v0）：

    rect / rrect / pill   矩形、圆角矩形、胶囊（可携带居中 text）
    circle                圆/椭圆（x,y,w,h 外接框；可携带居中 text）
    text                  自由文本（支持 lines 多行）
    line / arrow          直线、箭头（箭头渲染为 线段+三角 两个独立单元）
"""

import re

import yaml

SUPPORTED_TYPES = {"rect", "rrect", "pill", "circle", "text", "line", "arrow"}
_GEOM_BOX = ("x", "y", "w", "h")
_GEOM_SEG = ("x1", "y1", "x2", "y2")
PLACEHOLDER_BLACKLIST = ("XXX", "TODO", "待补充", "【", "undefined", "NaN")


class SpecError(Exception):
    pass


def safe_project(spec):
    """项目名 → 可安全用作文件名的短串（VLM 产出的 project 可能含空格/斜杠）。"""
    name = str((spec or {}).get("project") or "output").strip() or "output"
    name = re.sub(r"[^\w\u4e00-\u9fff-]+", "_", name).strip("_-")
    return name[:60] or "output"


_COLOR_RE = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")
_NONE_WORDS = {"none", "transparent", "无", "透明"}


def norm_color(eid, field, v, drop_none=False):
    """颜色值规范化：'#RGB/#RRGGBB/#RRGGBBAA'→统一 #RRGGBB(大写)；
    none/transparent → None（drop_none=True 时删除该键语义，返回 (None, True)）；
    其他非法值 → SpecError（报错可读，供自动回询迭代修正）。"""
    if v is None:
        return None
    s = str(v).strip()
    if s.lower() in _NONE_WORDS:
        return None
    if _COLOR_RE.match(s):
        if len(s) == 4:  # #RGB → #RRGGBB
            return "#" + "".join(c * 2 for c in s[1:]).upper()
        return s.upper()
    # 十六进制杂讯容错：去空格/补全 # 后重试一次
    t = s.lstrip("#").strip()
    if t and all(c in "0123456789abcdefABCDEF" for c in t) and len(t) in (3, 6):
        if len(t) == 3:
            t = "".join(c * 2 for c in t)
        return f"#{t.upper()}"
    if drop_none:
        return None
    raise SpecError(f"元素 {eid}: 颜色字段 {field} 值非法：{v!r}（需 #RRGGBB 或 none）")


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

        # 颜色字段规范化（非法值给出可读错误；文本 color 的 none 删除键回退主色）
        if t == "text":
            c = norm_color(eid, "color", el.get("color"), drop_none=True)
            if c is None:
                el.pop("color", None)
            else:
                el["color"] = c
        else:
            for f in ("fill", "stroke"):
                if f in el or el.get(f) is not None:
                    el[f] = norm_color(eid, f, el.get(f))
            if t in ("line", "arrow"):
                el["stroke"] = norm_color(eid, "stroke", el.get("stroke"), drop_none=True)

        if t == "text":
            need = ("x", "y")          # 自由文本只需锚点；宽度可选（用于居中/右对齐与边界校验）
        else:
            need = _GEOM_SEG if t in ("line", "arrow") else _GEOM_BOX
        missing = [k for k in need if not isinstance(el.get(k), (int, float))]
        if missing:
            raise SpecError(f"{where}({eid}): 缺少几何字段 {missing}")

        # 旋转（可选）：度、顺时针；盒子绕自身中心，自由文本绕锚点；
        # 线段/箭头几何完全由端点承载，rotate 键忽略并剔除
        if "rotate" in el:
            if t in ("line", "arrow"):
                el.pop("rotate", None)
            else:
                r = el["rotate"]
                if isinstance(r, bool) or not isinstance(r, (int, float)):
                    raise SpecError(f"{where}({eid}): rotate 必须是数字（度，顺时针）")
                el["rotate"] = round(float(r) % 360.0, 1)

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

    pal = spec.get("palette")
    if isinstance(pal, dict):
        for k, v in pal.items():
            if v is None:
                continue
            try:
                pal[k] = norm_color(f"palette.{k}", k, v, drop_none=True)
            except SpecError as e:
                raise SpecError(f"palette.{k} 颜色值非法：{v!r}（需 #RRGGBB）") from e
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
