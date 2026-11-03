# -*- coding: utf-8 -*-
"""Snap2Edit 命令行。

    snap2edit new <dir>                          生成规格书模板
    snap2edit build <dir>                        双渲染：HTML+SVG 与 PPTX
    snap2edit check <dir> [--original IMG]       四道校验门 + 报告
        [--no-shot]
"""

import argparse
import os

from . import __version__

TEMPLATE = """# Snap2Edit 规格书 —— 两条产线的唯一事实源
project: my-chart
canvas: {width: 1280, height: 720}        # viewBox 与画布 1:1
slide: {preset: "16:9"}                   # 或显式 emu_w/emu_h
font: {name: "Noto Sans SC", fallback: "Microsoft YaHei", pptx_name: "Microsoft YaHei"}
palette:
  primary: "#1F2937"                      # 标题/正文主色
  accent: "#2B6CB0"                       # 箭头/强调
  card: "#FFFFFF"                         # 卡片默认填充
  muted: "#8A97A8"                        # 次要文字/分隔线
texts:                                    # 终检文案清单（门1/门2 逐条核对）
  - "标题文字"
  - "卡片A"
  - "卡片B"
elements:
  - {id: bg, type: rect, x: 0, y: 0, w: 1280, h: 720, fill: "#F8FAFC"}
  - {id: title, type: text, x: 64, y: 48, size: 30, bold: true, text: "标题文字"}
  - {id: box-a, type: rrect, x: 120, y: 200, w: 440, h: 240, rx: 12, text: "卡片A", size: 18, bold: true}
  - {id: box-b, type: rrect, x: 720, y: 200, w: 440, h: 240, rx: 12, text: "卡片B", size: 18, bold: true}
  - {id: arrow-1, type: arrow, x1: 560, y1: 320, x2: 720, y2: 320}
"""


def cmd_new(args):
    d = args.dir
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, "spec.yaml")
    if os.path.exists(path):
        print(f"已存在: {path}")
        return 1
    with open(path, "w", encoding="utf-8") as f:
        f.write(TEMPLATE)
    print(f"✓ 规格书模板已生成: {path}")
    print("  下一步: 编辑 spec.yaml → snap2edit build " + d)
    return 0


def cmd_build(args):
    from . import pptxout, svgout
    from . import spec as specmod

    sp = specmod.load(os.path.join(args.dir, "spec.yaml"))
    name = sp.get("project", "output")
    build = os.path.join(args.dir, "build")
    os.makedirs(build, exist_ok=True)
    html_path = os.path.join(build, f"{name}.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(svgout.render_html(sp))
    pptx_path = os.path.join(build, f"{name}.pptx")
    pptxout.render_pptx(sp, pptx_path)
    print(f"✓ HTML+SVG → {html_path}")
    print(f"✓ PPTX     → {pptx_path}")
    return 0


def cmd_check(args):
    from . import spec as specmod, verify

    sp = specmod.load(os.path.join(args.dir, "spec.yaml"))
    ok = verify.run_checks(args.dir, sp,
                           original=args.original, do_shot=not args.no_shot)
    return 0 if ok else 2


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="snap2edit",
        description="Snap2Edit 截图复刻引擎 —— 一份布局规格，同步产出 HTML+SVG 与原生 PPTX")
    ap.add_argument("--version", action="version", version=f"snap2edit {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_new = sub.add_parser("new", help="生成规格书模板")
    p_new.add_argument("dir")
    p_new.set_defaults(func=cmd_new)

    p_build = sub.add_parser("build", help="双渲染：HTML+SVG 与 PPTX")
    p_build.add_argument("dir")
    p_build.set_defaults(func=cmd_build)

    p_check = sub.add_parser("check", help="四道校验门 + 报告")
    p_check.add_argument("dir")
    p_check.add_argument("--original", default=None, help="原图路径（可选，启用块差异对比）")
    p_check.add_argument("--no-shot", action="store_true", help="跳过 Playwright 截图")
    p_check.set_defaults(func=cmd_check)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    import sys
    sys.exit(main())
