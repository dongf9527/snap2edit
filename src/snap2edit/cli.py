# -*- coding: utf-8 -*-
"""Snap2Edit 命令行。

    snap2edit new <dir>                          生成规格书模板
    snap2edit build <dir>                        双渲染：HTML+SVG 与 PPTX
    snap2edit check <dir> [--original IMG]       四道校验门 + 报告
        [--no-shot] [--json]                     --json 输出结构化结果（供 web API）
    snap2edit loop <dir> [--max-iters N]         build+check 自动迭代直至收敛（F5）
        [--fix CMD] [--fix-timeout S] [--original IMG] [--no-shot] [--json]

loop 迭代规则：
  - 每轮 build → check；全门通过即收敛（退出码 0）；
  - 未通过且指定 --fix CMD：以环境变量注入上下文后执行修正命令
    （SNAP2EDIT_DIR / SPEC / ITER / REPORT / FAILURES），CMD 负责改写 spec.yaml；
  - 每轮失败快照存 <dir>/loop/；未收敛时保留最少失败轮的
    best-spec.yaml（退出码 2），spec.yaml 本身不被改动。
"""

import argparse
import json
import os
import shlex
import subprocess

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


def _do_build(d, sp):
    """双渲染共入入口（build 与 loop 共用）：返回产物路径字典。"""
    from . import pptxout, svgout
    from . import spec as specmod

    name = specmod.safe_project(sp)
    build = os.path.join(d, "build")
    os.makedirs(build, exist_ok=True)
    html_path = os.path.join(build, f"{name}.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(svgout.render_html(sp))
    pptx_path = os.path.join(build, f"{name}.pptx")
    pptxout.render_pptx(sp, pptx_path)
    return {"name": name, "html": html_path, "pptx": pptx_path}


def cmd_build(args):
    from . import spec as specmod

    sp = specmod.load(os.path.join(args.dir, "spec.yaml"))
    out = _do_build(args.dir, sp)
    print(f"✓ HTML+SVG → {out['html']}")
    print(f"✓ PPTX     → {out['pptx']}")
    return 0


def cmd_check(args):
    from . import spec as specmod, verify

    sp = specmod.load(os.path.join(args.dir, "spec.yaml"))
    if args.json:
        import json

        data = verify.collect_checks(args.dir, sp, original=args.original,
                                     do_shot=not args.no_shot, log=None)
        print(json.dumps(data, ensure_ascii=False))
        return 0 if data["ok"] else 2
    ok = verify.run_checks(args.dir, sp,
                           original=args.original, do_shot=not args.no_shot)
    return 0 if ok else 2


def _run_fixer(fix, d, spec_path, it, report_path, failures, timeout, log):
    """执行外部修正命令；上下文经环境变量注入，返回是否成功执行。"""
    env = os.environ.copy()
    env.update({
        "SNAP2EDIT_DIR": os.path.abspath(d),
        "SNAP2EDIT_SPEC": os.path.abspath(spec_path),
        "SNAP2EDIT_ITER": str(it),
        "SNAP2EDIT_REPORT": os.path.abspath(report_path) if report_path else "",
        "SNAP2EDIT_FAILURES": json.dumps(failures, ensure_ascii=False),
    })
    cmd = shlex.split(fix)
    log(f"→ 执行修正命令: {fix}")
    try:
        r = subprocess.run(cmd, env=env, timeout=timeout)
    except subprocess.TimeoutExpired:
        log(f"  ✗ 修正命令超时（>{timeout}s）")
        return False
    except OSError as e:
        log(f"  ✗ 修正命令无法执行: {e}")
        return False
    if r.returncode != 0:
        log(f"  ⚠ 修正命令退出码 {r.returncode}（继续下一轮重试）")
    return True


def cmd_loop(args):
    from . import spec as specmod, verify

    if args.max_iters < 1:
        print(f"✗ --max-iters 必须 ≥ 1（当前 {args.max_iters}），未执行任何迭代")
        return 2

    d = args.dir
    spec_path = os.path.join(d, "spec.yaml")
    loop_dir = os.path.join(d, "loop")
    history = []

    for it in range(1, args.max_iters + 1):
        # --- build（spec 解析失败也计入失败，交给 fixer 修正后重试）---
        try:
            sp = specmod.load(spec_path)
            _do_build(d, sp)
            build_err = None
        except (specmod.SpecError, FileNotFoundError) as e:
            sp, build_err = None, str(e)

        # --- check ---
        if build_err is None:
            data = verify.collect_checks(d, sp, original=args.original,
                                         do_shot=not args.no_shot, log=None)
            ok, failures = data["ok"], data["failures"]
            report_path = data["report_md"]
            report_html = data.get("report_html")
        else:
            ok, failures, report_path, report_html = False, [f"spec 解析失败：{build_err}"], None, None
        history.append({"iter": it, "ok": ok, "failures": failures})

        print(f"[iter {it}/{args.max_iters}] " + ("✓ 收敛" if ok else f"✗ {len(failures)} 项未通过"))
        for msg in failures[:5]:
            print(f"   - {msg}")
        if len(failures) > 5:
            print(f"   … 以及另外 {len(failures) - 5} 项（详见报告）")

        if ok:
            summary = {"ok": True, "converged": True, "iterations": it,
                       "history": history,
                       "artifacts": {"report": report_path,
                                     "report_html": report_html}}
            if args.json:
                print(json.dumps(summary, ensure_ascii=False))
            else:
                msg = f"✓ loop 收敛于第 {it} 轮，报告: {report_path}"
                if report_html:
                    msg += f"（可视化: {os.path.basename(report_html)}）"
                print(msg)
            return 0

        # --- 失败快照（spec.yaml 不被改动）---
        os.makedirs(loop_dir, exist_ok=True)
        if sp is not None:
            with open(spec_path, encoding="utf-8") as f:
                snap = f.read()
            with open(os.path.join(loop_dir, f"spec-iter{it}.yaml"), "w", encoding="utf-8") as f:
                f.write(snap)
        if report_path and os.path.exists(report_path):
            with open(report_path, encoding="utf-8") as f:
                rep = f.read()
            with open(os.path.join(loop_dir, f"report-iter{it}.md"), "w", encoding="utf-8") as f:
                f.write(rep)
        if report_html and os.path.exists(report_html):  # F7 可视化报告逐轮快照（调试用）
            with open(report_html, encoding="utf-8") as f:
                rep = f.read()
            with open(os.path.join(loop_dir, f"report-iter{it}.html"), "w", encoding="utf-8") as f:
                f.write(rep)

        # （迭代耗尽由 range 上界自然结束，无需显式 break）

        if not args.fix:
            print("✗ 未指定 --fix 修正命令，无法自动迭代修正（可先手动改 spec.yaml 后重试）")
            break
        if it < args.max_iters:
            # 最后一轮无需再执行修正（没有下一轮了）；迭代耗尽由 range 上界自然结束
            _run_fixer(args.fix, d, spec_path, it, report_path, failures,
                       args.fix_timeout, log=print)

    # --- 未收敛：保留最少失败轮为最优 ---
    best = min(history, key=lambda h: len(h["failures"]))
    best_spec = os.path.join(loop_dir, f"spec-iter{best['iter']}.yaml")
    best_out = None
    if os.path.exists(best_spec):
        best_out = os.path.join(loop_dir, "best-spec.yaml")
        with open(best_spec, encoding="utf-8") as f:
            blob = f.read()
        with open(best_out, "w", encoding="utf-8") as f:
            f.write(blob)
    summary = {"ok": False, "converged": False, "iterations": len(history),
               "best_iter": best["iter"], "best_failures": len(best["failures"]),
               "best_spec": best_out, "history": history}
    if args.json:
        print(json.dumps(summary, ensure_ascii=False))
    else:
        print(f"✗ {len(history)} 轮未收敛；最少失败为第 {best['iter']} 轮"
              f"（{len(best['failures'])} 项）"
              + (f"，最优 spec 已保留: {best_out}" if best_out else ""))
    return 2


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
    p_check.add_argument("--json", action="store_true", help="输出结构化 JSON 结果（供 web API）")
    p_check.set_defaults(func=cmd_check)

    p_loop = sub.add_parser("loop", help="build+check 自动迭代直至收敛（可外接修正命令）")
    p_loop.add_argument("dir")
    p_loop.add_argument("--max-iters", type=int, default=3, help="最大轮数（默认 3）")
    p_loop.add_argument("--fix", default=None,
                        help="未通过时执行的修正命令（环境变量注入报告与失败清单，命令自行改写 spec.yaml）")
    p_loop.add_argument("--fix-timeout", type=int, default=300, help="单次修正命令超时秒数（默认 300）")
    p_loop.add_argument("--original", default=None, help="原图路径（透传给 check，启用块差异对比）")
    p_loop.add_argument("--no-shot", action="store_true", help="跳过 Playwright 截图")
    p_loop.add_argument("--json", action="store_true", help="输出结构化 JSON 汇总（供 Agent/CI）")
    p_loop.set_defaults(func=cmd_loop)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    import sys
    sys.exit(main())
