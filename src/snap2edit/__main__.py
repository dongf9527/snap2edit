# -*- coding: utf-8 -*-
"""Snap2Edit 命令行入口（python -m snap2edit / snap2edit 均可）。"""
import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
