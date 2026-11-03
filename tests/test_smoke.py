# -*- coding: utf-8 -*-
"""冒烟测试：python tests/test_smoke.py 或 pytest"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from snap2edit import pptxout, spec as specmod, svgout, verify  # noqa: E402

DEMO = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "..", "examples", "demo", "spec.yaml")


def test_build_and_verify():
    sp = specmod.load(DEMO)

    # 产线①：HTML 全真实文本、无位图
    html = svgout.render_html(sp)
    assert "<image" not in html and "data:image" not in html, "HTML 不允许位图"
    assert html.count("<text") >= 10, "HTML 文本元素数量不足"
    assert all(r[1] for r in verify.check_html(html, sp)), "HTML 校验门未通过"

    # 产线②：PPTX 原生形状、Picture=0、文案齐全
    with tempfile.TemporaryDirectory() as td:
        pptx_path = os.path.join(td, "demo.pptx")
        pptxout.render_pptx(sp, pptx_path)
        res = verify.check_pptx(pptx_path, sp)
        assert all(ok for _, ok, _ in res), res

    # 门3：demo 自身不得有边界溢出
    assert verify.check_bounds(sp) == [], "demo 存在文本溢出"


if __name__ == "__main__":
    test_build_and_verify()
    print("smoke test passed ✓")
