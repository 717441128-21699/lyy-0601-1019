#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据要素交易材料生成自动化工具
主入口文件
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from gui.main_window import main


if __name__ == "__main__":
    main()
