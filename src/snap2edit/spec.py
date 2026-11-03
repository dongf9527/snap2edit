# -*- coding: utf-8 -*-
"""规格书（spec）加载与校验 —— 两条产线的唯一事实源。

规格书是一份 YAML：画布、幻灯片、字体、色板、文案清单（终检用）、
以及带 id 的元素列表。元素类型：

    rect / rrect / pill   矩形、圆角矩形、胶囊（可携带居中 text）
    circle                圆/椭圆（x,y,w,h 外接框；可携带居中 text）
    text                  自由文本（支持 lines 多行）
    line / arrow          直线、箭头（箭头渲染为 线段+三角 两个独立单元）

组件库（F6，几何与配色见 components.py，双产线各给原生实现）：

    cube                  立方体（depth 深度可选；可携带 text 于正面）
    matrix-cell           矩阵格子（rows/cols 必填、gap 间隙、texts 逐格文字）
    flow-box              流程框（title 色带标题 + text/lines 正文 + band 带高比例）
    icon                  参数化图标（name 取自 components.ICON_NAMES）

旋转（rotate）仅支持基础盒/文本类型；复合组件（cube/matrix-cell/
flow-box/icon）的多单元旋转易在两产线间漂移，rotate 键剔除并忽略。
"""

import re

import yaml

from .components import ICON_NAMES

SUPPORTED_TYPES = {"rect", "rrect", "pill", "circle", "text", "line", "arrow",
                   "cube", "matrix-cell", "flow-box", "icon"}
# 复合组件：多单元构成，rotate 不支持（键剔除，与线段/箭头同策略）
_COMPOSITE_TYPES = {"cube", "matrix-cell", "flow-box", "icon"}
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
        # 线段/箭头几何完全由端点承载，复合组件多单元旋转易漂移——均剔除
        if "rotate" in el:
            if t in ("line", "arrow") or t in _COMPOSITE_TYPES:
                el.pop("rotate", None)
            else:
                r = el["rotate"]
                if isinstance(r, bool) or not isinstance(r, (int, float)):
                    raise SpecError(f"{where}({eid}): rotate 必须是数字（度，顺时针）")
                el["rotate"] = round(float(r) % 360.0, 1)

        # ---- 圆角半径（可选）：rrect / matrix-cell / flow-box 共用，需非负数字 ----
        if t in ("rrect", "matrix-cell", "flow-box"):
            rx = el.get("rx")
            if rx is not None and (isinstance(rx, bool) or not isinstance(rx, (int, float)) or rx < 0):
                raise SpecError(f"{where}({eid}): rx 必须是非负数字（px 圆角半径）")

        # ---- 组件库类型约束（F6）----
        if t == "cube":
            d = el.get("depth")
            if d is not None and (isinstance(d, bool) or not isinstance(d, (int, float)) or d < 0):
                raise SpecError(f"{where}({eid}): depth 必须是非负数字（px，缺省 min(w,h)*0.2）")
        elif t == "matrix-cell":
            for k in ("rows", "cols"):
                v = el.get(k)
                if isinstance(v, bool) or not isinstance(v, int) or v < 1:
                    raise SpecError(f"{where}({eid}): {k} 必须是 ≥1 的整数")
            g = el.get("gap")
            if g is not None and (isinstance(g, bool) or not isinstance(g, (int, float)) or g < 0):
                raise SpecError(f"{where}({eid}): gap 必须是非负数字（px）")
            txts = el.get("texts")
            if txts is not None:
                if not isinstance(txts, list) or any(not isinstance(x, str) for x in txts):
                    raise SpecError(f"{where}({eid}): texts 必须是字符串列表（行优先）")
                if len(txts) > el["rows"] * el["cols"]:
                    raise SpecError(f"{where}({eid}): texts 共 {len(txts)} 条，超出格子数 "
                                    f"{el['rows']}x{el['cols']}={el['rows'] * el['cols']}")
                if txts and not el.get("size"):
                    raise SpecError(f"{where}({eid}): 携带 texts 的矩阵格子需要 size")
        elif t == "flow-box":
            b = el.get("band")
            if b is not None and (isinstance(b, bool) or not isinstance(b, (int, float))
                                  or not (0 < b < 1)):
                raise SpecError(f"{where}({eid}): band 必须是 0–1 之间的数字（色带高度占比）")
            if not el.get("title") and not (el.get("text") or el.get("lines")):
                raise SpecError(f"{where}({eid}): flow-box 需要 title 或 text/lines")
        elif t == "icon":
            if el.get("name") not in ICON_NAMES:
                raise SpecError(f"{where}({eid}): 未知图标 {el.get('name')!r}"
                                f"（可用: {', '.join(ICON_NAMES)}）")

        if t == "text":
            if not (el.get("text") or el.get("lines")):
                raise SpecError(f"{where}({eid}): 文本元素需要 text 或 lines")
        if (el.get("text") or el.get("title")) and not el.get("size"):
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
            except SpecError as e:  # pragma: no cover —— 防御：drop_none 路径不会抛错，保留双保险
                raise SpecError(f"palette.{k} 颜色值非法：{v!r}（需 #RRGGBB）") from e
    return spec


def texts_of(spec):
    """终检文案清单：spec.texts 优先；否则自动收集全部文字（含组件库文字）。"""
    listed = spec.get("texts")
    if listed:
        return [str(t) for t in listed]
    out = []
    for el in spec["elements"]:
        if el.get("type") == "flow-box" and el.get("title"):
            out.append(str(el["title"]))            # 流程框标题先于正文（与视觉顺序一致）
        if el.get("lines"):
            out.extend(str(x) for x in el["lines"])
        elif el.get("text"):
            out.append(str(el["text"]))
        if el.get("type") == "matrix-cell" and el.get("texts"):
            out.extend(str(x) for x in el["texts"])
    return out


def text_tag_count(spec):
    """产线① 将输出的 <text> 标签数（门1 数量覆盖的期望值）。

    一个元素至多输出一个 <text>（多行用 tspan）；矩阵格子逐格一个。
    """
    n = 0
    for el in spec["elements"]:
        t = el["type"]
        if t == "text":
            n += 1
        elif t in ("rect", "rrect", "pill", "circle", "cube") and el.get("text"):
            n += 1
        elif t == "matrix-cell":
            n += len(el.get("texts") or [])
        elif t == "flow-box":
            n += (1 if el.get("title") else 0) + \
                 (1 if (el.get("text") or el.get("lines")) else 0)
    return n
