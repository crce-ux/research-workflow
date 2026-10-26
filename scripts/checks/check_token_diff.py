# -*- coding: utf-8 -*-
"""check_token_diff.py —— 改写前后的「受保护 token」比对

【背景】
    `grant-diagnosis` 的去机器味有一条规则：**只改表达，不改事实。**
    而"事实"在文本里最容易被顺手改掉的形态，是一串**不该动的 token**——
    LaTeX 命令、引用 key、数字与单位、变量名、URL/DOI、状态 token。

    手册原文写的是「**输出前复核 token diff —— 这一项不可省；无脚本时手工列清单**」。

【它查什么】
    给定**原文**与**改写后**两份文本，提取受保护 token 的多重集并比对：
      · **丢失**（原文有、改写后没有）→ 🔴 最危险，多半是把事实改掉了
      · **新增**（改写后多出来的）     → 需要解释，可能是补写了内容
      · 数字/单位类差异单独列 → 改写不得触碰

【它不查什么】
    改写得好不好、改写后的句子该不该这么说——语义，人工过。
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

# ── 限定词：表达真实不确定性的词，去掉就把话说满了 ──────────
# 参考 junbolian/Academic-Humanizer（MIT）的 compare 输出：限定词减少要逐条列出。
QUAL_PATTERN = re.compile(
    r"可能|或许|也许|大概|大致|通常|一般而言|一般来说|往往|多数情况下|在某些情况下|"
    r"在一定程度上|提示|显示|表明|与[^。]{0,6}一致|"
    r"\b(?:may|might|could|likely|unlikely|possibly|potentially|perhaps|probably|"
    r"suggest|suggests|indicate|indicates|appear|appears|seem|seems|consistent with)\b",
    re.I)


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


def extract_quals(text):
    """返回限定词的多重集。"""
    return Counter(m.group(0) for m in QUAL_PATTERN.finditer(text))


def compare(a, b):
    lost = [(k, n) for k, n in (a - b).items() for _ in range(n)]
    added = [(k, n) for k, n in (b - a).items() for _ in range(n)]
    return lost, added


def main():
    ap = argparse.ArgumentParser(description="改写前后的受保护 token 比对")
    ap.add_argument("before")
    ap.add_argument("after")
    ap.add_argument("--quiet", action="store_true", help="只报数字与单位类的差异")
    ap.add_argument("--strict-quals", action="store_true",
                    help="限定词的丢失也计入退出码（默认只提示）")
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

    qa, qb = extract_quals(ta), extract_quals(tb)
    q_lost = [(k, n) for k, n in (qa - qb).items() for _ in range(n)]
    q_add = [(k, n) for k, n in (qb - qa).items() for _ in range(n)]
    total_a, total_b = sum(qa.values()), sum(qb.values())
    print(f"\n  ◇ 限定词：{total_a} → {total_b}")
    if q_lost:
        print("      LOST（每一条都把话说满一分，除非是有意改动）：")
        for (tok, _n) in q_lost[:20]:
            ln = ta[:ta.find(tok)].count("\n") + 1 if tok in ta else 0
            print(f"        {tok}  ← 原第 {ln} 行")
        if len(q_lost) > 20:
            print(f"        … 另有 {len(q_lost) - 20} 处")
    if q_add:
        print("      ADDED（新增的限定词同样要能指出来源）：")
        print("        " + "、".join(t for t, _ in q_add[:20]))

    if not lost and not added:
        print("  ✅ token 零 diff")
    else:
        print(f"\n  ⚠️ 丢失的必须逐个解释：**只改表达，不改事实**——")
        print(f"     无法证明零损失 → 恢复原句，并标「人工确认」。")
    if q_lost:
        print("  ⚠️ 限定词的丢失同样要逐条解释：删在已证明的结果上是有意改动，"
              "删在无证据支撑的断言上就是提高了结论强度。")
    return n1 + n2 + (len(q_lost) if a.strict_quals else 0)


if __name__ == "__main__":
    raise SystemExit(main())
