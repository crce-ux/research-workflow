# -*- coding: utf-8 -*-
"""audit_manuals.py —— 手册与 skill 的去向核对

题目：`manuals/` 里每一节，在哪个 skill 的哪个文件里有对应？
输出是候选，不是判决——收没收由人定，结论写进 `docs/manuals.md`。

判据（B 类，只报可疑）：
    把每节切成 CJK 二元组与英文词，与每个 skill 文件比重合系数
    overlap = |A ∩ B| / min(|A|, |B|)
    取最高分；分数 ≥ 0.20 记为「有对应」，0.12–0.20 记为「弱对应」。
    低于 0.12 记为「未匹配」，进缺口清单。

⚠️ 分数只说明用词重合，不说明内容一致。改写过的章节分数会低——低分不等于没收录。
   所以本脚本给的是候选，复核由人做。

用法：
    python scripts/audit_manuals.py                        # 全量
    python scripts/audit_manuals.py --manual 日常精读手册    # 单份
    python scripts/audit_manuals.py --json out.json        # 机器可读
退出码恒为 0——这是审计工具，不是门禁。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent                     # D:/Github
MANUALS = HERE.parent / "manuals"
STRONG, WEAK = 0.20, 0.12

SELF_BUILT = [
    "paper-reading", "literature-pipeline", "ai-academic-writing", "academic-slides",
    "data-pipeline", "submission", "grant-diagnosis", "peer-review", "text-self-review",
    "study-design",
]

_CJK = re.compile(r"[\u4e00-\u9fff]")
_LATIN = re.compile(r"[A-Za-z][A-Za-z0-9_\-]{2,}")


def grams(text: str) -> set[str]:
    """CJK 二元组 + 英文词。"""
    out: set[str] = set()
    cjk = _CJK.findall(text)
    out.update(a + b for a, b in zip(cjk, cjk[1:]))
    out.update(w.lower() for w in _LATIN.findall(text))
    return out


def overlap(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


def sections(path: pathlib.Path) -> list[tuple[str, str]]:
    """按 ## 切节；没有二级标题就整份当一节。"""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    head, buf, out = "（开篇）", [], []
    for line in lines:
        if line.startswith("## "):
            if buf:
                out.append((head, "\n".join(buf)))
            head, buf = line[3:].strip(), []
        elif not line.startswith("# "):
            buf.append(line)
    if buf:
        out.append((head, "\n".join(buf)))
    return out or [(path.stem, "")]


def skill_corpus() -> dict[str, set[str]]:
    corpus: dict[str, set[str]] = {}
    for name in SELF_BUILT:
        d = ROOT / name
        if not d.exists():
            continue
        for f in [d / "SKILL.md"] + sorted((d / "references").glob("*.md")):
            if f.exists():
                rel = f"{name}/{f.relative_to(d).as_posix()}"
                corpus[rel] = grams(f.read_text(encoding="utf-8", errors="replace"))
    return corpus


def audit(only: str | None) -> list[dict]:
    corpus = skill_corpus()
    rows: list[dict] = []
    for m in sorted(MANUALS.rglob("*.md")):
        if m.name == "README.md":
            continue
        if only and only not in m.name and only not in str(m.parent.name):
            continue
        secs = []
        for head, text in sections(m):
            g = grams(head + " " + text)
            best, score = None, 0.0
            for rel, cg in corpus.items():
                s = overlap(g, cg)
                if s > score:
                    best, score = rel, s
            level = "有对应" if score >= STRONG else "弱对应" if score >= WEAK else "未匹配"
            secs.append(dict(head=head, best=best, score=round(score, 3), level=level))
        rows.append(dict(
            manual=str(m.relative_to(MANUALS)).replace("\\", "/"),
            sections=secs,
            tally={k: sum(1 for s in secs if s["level"] == k)
                   for k in ("有对应", "弱对应", "未匹配")},
        ))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manual", help="只看文件名或目录名包含该串的手册")
    ap.add_argument("--json", help="把结果写到这个路径")
    args = ap.parse_args()

    rows = audit(args.manual)
    total = defaultdict(int)
    print(f"{'手册':44} {'节':>3} {'有对应':>4} {'弱':>3} {'未匹配':>4}  最高分去向")
    print("-" * 118)
    for r in rows:
        t = r["tally"]
        for k, v in t.items():
            total[k] += v
        top = max(r["sections"], key=lambda s: s["score"])
        print(f"{r['manual'][:44]:44} {len(r['sections']):>3} {t['有对应']:>4} "
              f"{t['弱对应']:>3} {t['未匹配']:>4}  {top['score']:.2f} {top['best']}")
    print("-" * 118)
    print(f"合计 {sum(total.values())} 节：有对应 {total['有对应']} · "
          f"弱对应 {total['弱对应']} · 未匹配 {total['未匹配']}")

    if args.json:
        pathlib.Path(args.json).write_text(
            json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
        print("明细 →", args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
