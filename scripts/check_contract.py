#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_contract.py —— 阶段收尾检查 + 自动记账。

【做什么】
    ① 按阶段跑对应的检查器（复用 audit.py 的解析与分级）
    ② 若给了 --raw（外部工具原始产出），复制一份快照并算出人工改动行数
    ③ 追加一行到 JSONL 日志
    ④ 打印判定；硬规则未过时退出码 1

【为什么要有」
    检查器只查可判定项。换了外部工具、改了契约之后，判断「这次是变好还是变差」
    需要两个数：机器命中多少、人改了多少。两个数同时记下来，才谈得上修订契约。

【用法】
    python scripts/check_contract.py --stage drafting --file draft.md --raw draft.raw.md
    python scripts/check_contract.py --stage review --file review.md

【阶段】reading · drafting · polishing · slides · review · proposal
    其余阶段（retrieval / figures / statistics）暂未接管，调用会直接报出。

【退出码】
    0 通过 · 1 硬规则未过 · 2 参数或文件问题
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import audit  # noqa: E402

DEFAULT_LOG = HERE.parent / "contracts" / "_log.jsonl"

#: 阶段 → (强制文档类型, 参与检查的检查器)
STAGES = {
    "reading": ("精读笔记", ["language", "phrases", "note"]),
    "drafting": ("论文/综述", ["language", "phrases", "ref_citations"]),
    "polishing": ("论文/综述", ["language", "phrases", "ref_citations"]),
    "slides": ("制作稿", ["language", "phrases", "talk"]),
    "review": ("审稿意见", ["language", "phrases", "review"]),
    "proposal": ("设计书", ["language", "phrases", "design"]),
}

NOT_TAKEN_OVER = {
    "retrieval": "检索阶段暂未接管：逐库计数与覆盖声明脚本尚未实现",
    "figures": "配图阶段暂未接管：图规格校验尚未实现",
    "statistics": "统计阶段暂未接管：无可判定的检查器",
}


def diff_lines(raw: Path, final: Path) -> int:
    """人工改动的行数：新增 + 删除的行数。"""
    a = raw.read_text(encoding="utf-8", errors="replace").splitlines()
    b = final.read_text(encoding="utf-8", errors="replace").splitlines()
    n = 0
    for line in difflib.unified_diff(a, b, lineterm="", n=0):
        if line.startswith("+") or line.startswith("-"):
            if line.startswith(("+++", "---")):
                continue
            n += 1
    return n


def main() -> int:
    ap = argparse.ArgumentParser(description="阶段收尾检查 + 记账")
    ap.add_argument("--stage", required=True, choices=list(STAGES) + list(NOT_TAKEN_OVER))
    ap.add_argument("--file", required=True, help="待检的中间格式文件")
    ap.add_argument("--raw", help="外部工具的原始产出；给了就算人工改动行数")
    ap.add_argument("--log", default=str(DEFAULT_LOG))
    ap.add_argument("--contract", default="v0.1", help="契约版本号")
    ap.add_argument("--tool", default="", help="本次使用的外部工具")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    if a.stage in NOT_TAKEN_OVER:
        print(f"[未接管] {NOT_TAKEN_OVER[a.stage]}")
        return 2

    doc = Path(a.file)
    if not doc.is_file():
        print(f"[错误] 找不到 {doc}")
        return 2

    dtype, checkers = STAGES[a.stage]
    _, findings, ran, skipped, _ = audit.collect(doc, "", set(checkers), dtype)

    levels = {"硬规则": 0, "建议": 0, "信息": 0}
    per_checker: dict[str, int] = {}
    for f in findings:
        levels[f.get("level", "建议")] = levels.get(f.get("level", "建议"), 0) + 1
        per_checker[f["checker"]] = per_checker.get(f["checker"], 0) + 1

    human_diff = None
    snap_path = None
    if a.raw:
        raw = Path(a.raw)
        if not raw.is_file():
            print(f"[错误] 找不到原始产出 {raw}")
            return 2
        human_diff = diff_lines(raw, doc)
        snapdir = Path(a.log).parent / "snap"
        snapdir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        snap_path = snapdir / f"{ts}_{a.stage}.raw{raw.suffix}"
        shutil.copy2(raw, snap_path)

    verdict = "fail" if levels["硬规则"] else "pass"
    rec = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "stage": a.stage,
        "file": str(doc),
        "tool": a.tool,
        "contract": a.contract,
        "hits": per_checker,
        "levels": levels,
        "ran": ran,
        "skipped": skipped,
        "human_diff_lines": human_diff,
        "snapshot": str(snap_path) if snap_path else None,
        "verdict": verdict,
    }
    logp = Path(a.log)
    logp.parent.mkdir(parents=True, exist_ok=True)
    with open(logp, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    if not a.quiet:
        print(f"contract · {a.stage} · {doc.name}")
        print(f"  硬规则 {levels['硬规则']} · 建议 {levels['建议']} · 信息 {levels['信息']}")
        if human_diff is not None:
            print(f"  与原始产出相比，人工改动 {human_diff} 行")
        if skipped:
            print(f"  未运行：{'、'.join(skipped)}")
        print(f"  判定：{'通过' if verdict == 'pass' else '未过'}"
              + ("" if verdict == "pass" else f"（硬规则 {levels['硬规则']} 条）"))
        print(f"  日志：{logp}")
        print()
        print("  下一步（机器无法判定的三项）：")
        print(f"    python scripts/confirm.py --spec contracts/review-form.json "
              f"--out {doc.stem}_复核.json")

    return 0 if verdict == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
