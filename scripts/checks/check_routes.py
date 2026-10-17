# -*- coding: utf-8 -*-
"""check_routes.py —— 每个 skill 的「读什么」路由节是否存在且指得准

【背景】
    skill 被触发时只加载 SKILL.md；references/ 是按需读的。没有路由节，agent
    只读到 SKILL.md 就停，后面的判据永远到不了手上。路由节写错（指向不存在的
    文件或章节），同样读不到。

【它查什么】
    1. 每个含 SKILL.md 的 skill 目录里，SKILL.md 有 `## 读什么` 一节
    2. 这一节里每个反引号路径（references/*.md、scripts/*.py 等）真实存在
    3. 路由节不超过 12 行

【它不查什么】
    路由指得对不对（该不该指到那一节）——属判断，机器判不了。

用法：
    python check_routes.py [--root D:/Github]

退出码 = 命中条数（0 = 全过）
"""
import argparse
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MAX_LINES = 12
_PATH = re.compile(r"`([^`]*?\.(?:md|py|sh|json))`")
SKIP_DIRS = {"vendor", "node_modules", ".git", "__pycache__"}
OURS = "crce-ux"          # 本项目的 GitHub 属主


def is_ours(d: pathlib.Path) -> bool:
    """靠 git remote 判归属；判不了算自己的（宁可多算，不漏计）。"""
    cfg = d / ".git" / "config"
    if not cfg.is_file():
        return True
    try:
        return OURS in cfg.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return True


def skills(root: pathlib.Path) -> list[pathlib.Path]:
    out = []
    for p in root.rglob("SKILL.md"):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if not is_ours(p.parent):
            continue
        out.append(p.parent)
    return sorted(out)


def section_lines(text: str) -> list[str] | None:
    lines = text.split("\n")
    try:
        i = next(k for k, l in enumerate(lines) if l.strip() == "## 读什么")
    except StopIteration:
        return None
    body = []
    for l in lines[i + 1:]:
        if l.startswith("## "):
            break
        body.append(l)
    return body


def scan(skill: pathlib.Path) -> list[str]:
    hits = []
    p = skill / "SKILL.md"
    text = p.read_text(encoding="utf-8", errors="replace")
    body = section_lines(text)
    if body is None:
        return [f"{skill.name}: 没有 `## 读什么`"]
    meaningful = [l for l in body if l.strip()]
    if len(meaningful) > MAX_LINES:
        hits.append(f"{skill.name}: 路由节 {len(meaningful)} 行，超过 {MAX_LINES}")
    for line in meaningful:
        for raw in _PATH.findall(line):
            target = skill / raw
            if not target.exists():
                hits.append(f"{skill.name}: 路由指向不存在的文件 `{raw}`")
    return hits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None,
                    help="skill 仓根目录；默认取本文件往上三层")
    a = ap.parse_args()
    root = pathlib.Path(a.root) if a.root else pathlib.Path(__file__).resolve().parents[3]

    dirs = skills(root)
    hits = []
    for d in dirs:
        hits += scan(d)

    print(f"check_routes · {root} · 扫 {len(dirs)} 个 skill")
    if not hits:
        print("  ✅ 全过")
    else:
        for h in hits:
            print("  ❌", h)
        print(f"  共 {len(hits)} 条")
    return len(hits)


if __name__ == "__main__":
    sys.exit(main())
