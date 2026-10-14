# -*- coding: utf-8 -*-
"""check_token_diff.py —— 改写前后的「受保护 token」比对

【为什么有它】
    `grant-diagnosis` 的去机器味有一条铁律：**只改表达，不改事实。**
    而"事实"在文本里最容易被顺手改掉的形态，是一串**不该动的 token**——
    LaTeX 命令、引用 key、数字与单位、变量名、URL/DOI、状态 token。

    手册原文写的是「**输出前复核 token diff —— 这一项不可省；无脚本时手工列清单**」。
    这就是那个脚本。

【它查什么】
    给定**原文**与**改写后**两份文本，提取受保护 token 的多重集并比对：
      · **丢失**（原文有、改写后没有）→ 🔴 最危险，多半是把事实改掉了
      · **新增**（改写后多出来的）     → 需要解释，可能是补写了内容
      · 数字/单位类差异单独列 → 改写不得触碰

【它不查什么】
    改写得好不好、这话该不该这么说——语义，人工过。
    它只回答：**有没有 token 在改写中被动了。**

用法：
    python check_token_diff.py <原文> <改写后> [--quiet]

退出码 = 丢失 + 新增的条数（0 = 零 diff）
"""
import argparse
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── 受保护 token 的提取规则 ──────────────────────────────
PATTERNS = [
    # LaTeX 命令与环境（含 \cite{...} \ref{...} \item \texttt{...}）
    ("LaTeX", re.compile(r"\\[a-zA-Z]+\*?(?:\{[^{}]*\})*|\$\$?[^$]+\$\$?")),
    # 引用 key / label：\cite{a,b}、\label{x}
    ("引用key", re.compile(r"(?<=\\cite\{)[^}]*(?=\})|(?<=\\label\{)[^}]*(?=\})")),
    # 数字 + 单位（含百分比、时间、剂量）
    ("数字单位", re.compile(
        r"\d+(?:\.\d+)?\s*(?:%|‰|mg|g|kg|μg|ug|ng|ml|mL|L|μl|μL|mmHg|cm|mm|m|"
        r"h|min|s|d|wk|mo|yr|years?|人次|例|周|月|年|天|小时|分钟)")),
    # 裸数字（阈值 / 分母 / 样本量）
    ("数字", re.compile(r"(?<![\w.])\d+(?:\.\d+)?(?![\w.])")),
    # 状态 / 接口 token
    ("状态token", re.compile(r"H_0|H\+A|A-only|[A-Z]{3,}(?:[-_][A-Z0-9]+)*")),
    # 路径 / URL / DOI / 邮箱
    ("路径URL", re.compile(r"https?://\S+|10\.\d{4,}/\S+|\b[\w.-]+@[\w.-]+\.\w+\b|"
                        r"[A-Za-z]:[\\/][\S]+|(?<![\w.])[\w.-]+\.(?:py|md|json|yaml|yml|csv|xlsx|docx|pdf)\b")),
]

# 纯英文大写词里，这些是普通词而非状态 token，避免噪音
STOP_UPPER = {"AND", "OR", "NOT", "THE", "FOR", "WITH", "MRI", "CT", "EEG", "RCT",
              "ITT", "PP", "CI", "SD", "SE", "NSFC", "DOI", "URL", "AI", "CDSS",
              "PANSS", "SANS", "CGI", "SAS", "AIMS", "BARS", "MCCB", "PSP"}


def extract(text):
    """返回 {(类别, token): 次数}。"""
    out = Counter()
    for kind, pat in PATTERNS:
        for m in pat.findall(text):
            tok = m if isinstance(m, str) else m[0]
            tok = " ".join(tok.split())
            if not tok:
                continue
            if kind == "状态token" and tok in STOP_UPPER:
                continue
            out[(kind, tok)] += 1
    return out


def compare(a, b):
    lost = [(k, n) for k, n in (a - b).items() for _ in range(n)]
    added = [(k, n) for k, n in (b - a).items() for _ in range(n)]
    return lost, added


def main():
    ap = argparse.ArgumentParser(description="改写前后的受保护 token 比对")
    ap.add_argument("before")
    ap.add_argument("after")
    ap.add_argument("--quiet", action="store_true", help="只报数字与单位类的差异")
    a = ap.parse_args()

    for f in (a.before, a.after):
        if not Path(f).exists():
            sys.exit(f"文件不存在：{f}")

    ta = Path(a.before).read_text(encoding="utf-8", errors="replace")
    tb = Path(a.after).read_text(encoding="utf-8", errors="replace")
    lost, added = compare(extract(ta), extract(tb))

    print(f"check_token_diff · {Path(a.before).name} → {Path(a.after).name}")

    def show(title, items, mark):
        if not items:
            return 0
        # 数字类排前面——它们最不该动
        items.sort(key=lambda x: (x[0][0] != "数字单位", x[0][0] != "数字"))
        print(f"\n  {mark} {title}（{len(items)} 项）：")
        for (kind, tok), _ in items[:40]:
            print(f"      [{kind}] {tok}")
        if len(items) > 40:
            print(f"      … 另有 {len(items) - 40} 项")
        return len(items)

    n1 = show("原文有、改写后没了", lost, "🔴")
    n2 = show("改写后多出来的", added, "🟡")

    if not lost and not added:
        print("  ✅ token 零 diff")
    else:
        print(f"\n  ⚠️ 丢失的必须逐个解释：**只改表达，不改事实**——")
        print(f"     无法证明零损失 → 恢复原句，并标「人工确认」。")
    return n1 + n2


if __name__ == "__main__":
    raise SystemExit(main())
