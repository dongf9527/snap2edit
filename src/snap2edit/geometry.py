# -*- coding: utf-8 -*-
"""坐标换算：画布 px → 幻灯片 EMU / 字号 pt —— 两条公式定全场。

    EMU/px = 幻灯片宽 EMU ÷ 画布 px 宽
    pt/px  = (幻灯片高 EMU ÷ 914400 × 72) ÷ 画布 px 高

例：16:9 幻灯片(12192000×6858000 EMU) 配 1280×720 画布
    → 9525 EMU/px、0.75 pt/px
"""

SLIDE_16_9 = (12192000, 6858000)   # 13.333in × 7.5in
EMU_PER_INCH = 914400


class Mapper:
    """持有单张画布的 px→EMU 与 px→pt 换算系数。"""

    def __init__(self, canvas_w, canvas_h, slide_emu=None):
        w, h = slide_emu or SLIDE_16_9
        self.emu_px = w / float(canvas_w)
        self.pt_px = (h / float(EMU_PER_INCH) * 72.0) / float(canvas_h)

    def emu(self, px):
        return int(round(px * self.emu_px))

    def pt(self, px):
        return px * self.pt_px


def resolve_slide_emu(spec):
    """从规格书解析幻灯片尺寸（EMU）。"""
    slide = spec.get("slide") or {}
    if slide.get("preset") == "16:9" or not slide:
        return SLIDE_16_9
    if slide.get("emu_w") and slide.get("emu_h"):
        return (int(slide["emu_w"]), int(slide["emu_h"]))
    raise ValueError('slide 需要 preset: "16:9" 或显式 emu_w/emu_h')
