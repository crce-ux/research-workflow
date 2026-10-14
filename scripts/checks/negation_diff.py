# -*- coding: utf-8 -*-
"""negation_diff.py —— 改写前后的**否定**比对

【背景】
    改写纪律是「只改表达，不改事实」。数字变了肉眼还能看出来，
    **否定丢了几乎看不见**：

        原文：两组差异不显著
        改写：两组差异显著          ← 「不」没了，结论反了
        原文：未发现剂量效应
        改写：剂量效应有待验证      ← 从「没有」变成「有但没验」

    库里有数字比对（`number_diff.py`）与受保护 token 比对
    （`check_token_diff.py`），但**都不管否定**。

【它怎么比】
    不按句对齐（改写会把句子全打散）。改成**抽否定短语**：
    每个否定词连同其后 6 个汉字算一个 token，两份文本各取一个集合，
    求差集——和 `number_diff.py` 同一个思路。

    ⚠️ 「原文有、改写后没有」是**最危险**的方向（可能把否定改掉了），
    单列在前面。

【它不查什么】
    ⭐ 它只报「这两个否定短语对不上」，不判**该不该**改。
    有些改动本来就是要把否定去掉（改错了要改回来）——
    每一条都要人看一眼，并说明为什么。

用法：
    python negation_diff.py <原文> <改写后> [--context 40]

退出码恒为 0——它是**辅助比对，不是判据**。
"""
import argparse
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 否定词。长词放前面，避免「无法」被「无」抢先吃掉
NEGATORS = ["无法", "不能", "并非", "而非", "不属于", "未见", "未发现",
            "不", "未", "无", "没", "非", "缺乏", "排除", "除外"]
CJK = r"一-鿿"
TOKEN = re.compile(r"(" + "|".join(map(re.escape, NEGATORS)) + r")"
                   r"([" + CJK + r"A-Za-z0-9]{0,6})")


def tokens(text):
    """否定短语 → 出现次数。"""
    got = {}
    for m in TOKEN.finditer(text):
        tok = m.group(1) + m.group(2)
        got[tok] = got.get(tok, 0) + 1
    return got


def contexts(text, tok, width):
    out = []
    for m in re.finditer(re.escape(tok), text):
        lo = max(0, m.start() - width)
        out.append(text[lo:m.end() + width].replace("\n", " "))
    return out[:2]


def report(title, only_in, text, width):
    if not only_in:
        return 0
    print(f"\n  【{title}】{len(only_in)} 条")
    for tok in only_in:
        print(f"    · 「{tok}」")
        for ctx in contexts(text, tok, width):
            print(f"        …{ctx}…")
    return len(only_in)


def main():
    ap = argparse.ArgumentParser(description="改写前后否定比对")
    ap.add_argument("original")
    ap.add_argument("revised")
    ap.add_argument("--context", type=int, default=40, help="上下文长度（字）")
    a = ap.parse_args()

    po, pr = pathlib.Path(a.original), pathlib.Path(a.revised)
    to = tokens(po.read_text(encoding="utf-8", errors="replace"))
    tr = tokens(pr.read_text(encoding="utf-8", errors="replace"))

    lost = sorted(set(to) - set(tr))
    gained = sorted(set(tr) - set(to))

    print(f"negation_diff · {po.name} → {pr.name}")
    print(f"  否定短语：原文 {len(to)} 种 / 改写后 {len(tr)} 种")

    n1 = report("原文有、改写后没有 —— ⚠️ 最危险：可能把否定改掉了",
                lost, po.read_text(encoding="utf-8", errors="replace"), a.context)
    n2 = report("改写后新增的否定", gained,
                pr.read_text(encoding="utf-8", errors="replace"), a.context)

    if not (n1 or n2):
        print("\n  ✅ 两边的否定短语集合一致")
        return 0

    print(f"\n  共 {n1 + n2} 条。⚠️ 只报「对不上」，不判该不该改——"
          f"\n     每一条都要人看一眼，说明为什么。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
