# -*- coding: utf-8 -*-
"""让测试能 import scripts/ 下的模块（各子目录平铺进 sys.path）。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

for sub in ("scripts", "scripts/literature", "scripts/evidence", "scripts/checks",
            "scripts/data", "scripts/design", "scripts/ppt"):
    d = ROOT / sub
    if d.is_dir():
        sys.path.insert(0, str(d))
