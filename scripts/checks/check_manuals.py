# -*- coding: utf-8 -*-
"""check_manuals.py —— 手册与 skill 的去向表是否覆盖完整

【背景】
    `manuals/` 是源材料，`docs/manuals.md` 是唯一去向表。新增一份手册却不登记，
    下一次没人知道它有没有进 skill——这正是「手册更新、skill 不跟」的起点。

【它查什么】
    1. `manuals/` 下每份 .md（README 除外）在 `docs/manuals.md` 里有登记
    2. 去向表里写的每个 `manuals/...` 路径真实存在
    3. 每行都有结论（已收 / 不收 / 已收（已改定位））

【它不查什么】
    结论对不对——那是人的判断。

用法：
    python check_manuals.py [--root D:/Github/research-workflow]

退出码 = 命中条数（0 = 全过）
"""
import argparse
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CONCL = ("已收", "不收")
_ROW = re.compile(r"^\|\s*`(?:manuals/)?([^`]+\.md)`\s*\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None,
                    help="research-workflow 仓目录；默认取本文件往上三层")
    a = ap.parse_args()
    root = pathlib.Path(a.root) if a.root else pathlib.Path(__file__).resolve().parents[2]

    manuals = root / "manuals"
    table = root / "docs" / "manuals.md"
    if not manuals.exists():
        print(f"check_manuals · ⚠️ 本次未评——没有 manuals/（{manuals}）")
        return 0
    if not table.exists():
        print(f"check_manuals · ❌ 缺去向表 {table}")
        return 1

    hits = []
    registered: dict[str, str] = {}
    for line in table.read_text(encoding="utf-8", errors="replace").split("\n"):
        m = _ROW.match(line)
        if not m:
            continue
        rel, _n, concl = "manuals/" + m.group(1), m.group(2), m.group(3).strip()
        registered[rel] = concl
        if not any(concl.startswith(c) for c in CONCL):
            hits.append(f"{rel}: 结论「{concl}」不在 已收 / 不收 里")
        if not (root / rel).exists():
            hits.append(f"{rel}: 去向表里写了，但文件不存在")

    actual = {f"manuals/{p.relative_to(manuals).as_posix()}"
              for p in manuals.rglob("*.md") if p.name != "README.md"}
    for rel in sorted(actual - set(registered)):
        hits.append(f"{rel}: 未登记（跑 audit_manuals.py 后补进 docs/manuals.md）")

    print(f"check_manuals · 手册 {len(actual)} 份 · 登记 {len(registered)} 份")
    if not hits:
        print("  ✅ 全过")
    else:
        for h in hits:
            print("  ❌", h)
        print(f"  共 {len(hits)} 条")
    return len(hits)


if __name__ == "__main__":
    sys.exit(main())
