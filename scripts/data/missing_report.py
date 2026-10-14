# -*- coding: utf-8 -*-
"""missing_report.py —— 逐变量逐时点的缺失率，按四类缺失码拆开

【背景】
    data-pipeline 环节③ 的头两步是「报缺失率（逐变量逐时点）」与「分缺失类型」。
    报缺失率与分缺失类型这两步纯机械，人做又慢又容易漏；人真正该判的是最后一步——
    「这个缺失率能不能接受、该不该插补」。

【🔴 它守的一条纪律：「不适用」不是缺失】
    逻辑上不存在的取值（男性问月经、未服药问副作用、未做检查问滴度）
    不该算进缺失率。算进去有两个后果：
      ① 缺失率虚高，看起来数据很差；
      ② 后面的插补用错人——把「不适用」当「没测到」补上，凭空造数据。
    所以每一列给**两个率**：
        粗缺失率 = （所有缺失码 + 空） / N
        真缺失率 = （所有缺失码 + 空 − 不适用） / （N − 不适用）
    **报告里该用哪个，看 SAP 怎么写。脚本只把两个都摆出来，不替你选。**

【它不查什么】
    缺失机制（MCAR / MAR / MNAR）是判断，不在本脚本；该不该插补、怎么插补也是判断。

用法：
    python missing_report.py <data.csv|data.xlsx> [--time 时点列] [--id 编号列]
                             [--warn 0.2] [--top 0]

    --codes   自定义缺失码（默认 未评,不适用,失访,拒答）
    --time    时点列名；给了就**逐时点**再算一遍
    --id      编号列名；只在输出里跳过它（不算缺失率）
    --warn    真缺失率 ≥ 该值标 ⚠️（默认 0.2）
    --top     只列前 N 个变量（0 = 全列）

退出码恒为 0——它是**报告工具，不是门禁**。
"""
import argparse
import collections
import csv
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_CODES = ["未评", "不适用", "失访", "拒答"]
NOT_APPLICABLE = "不适用"
# 空与各种 NA 写法都算「没填」——但**没有码**，无法归入四类，单独计
NA_TOKENS = {"", ".", "-", "—", "/", "NA", "N/A", "n/a", "na", "NULL", "null",
             "NaN", "nan", "None", "none", "#N/A"}
ENCODINGS = ("utf-8-sig", "utf-8", "gbk")


def read_rows(path):
    """读 csv/tsv。按 utf-8-sig → utf-8 → gbk 依次试，Windows 上非如此不可。"""
    p = pathlib.Path(path)
    if p.suffix.lower() in (".tsv", ".txt"):
        opener = lambda f: csv.DictReader(f, delimiter="\t")
    else:
        opener = csv.DictReader
    for enc in ENCODINGS:
        try:
            with open(p, encoding=enc, newline="") as f:
                return list(opener(f)), enc
        except UnicodeDecodeError:
            continue
    raise SystemExit(f"读不了 {p}：试过 {' / '.join(ENCODINGS)}")


def measure(rows, col, codes):
    """一列的缺失构成。返回 dict。"""
    n = len(rows)
    by_code = collections.Counter()
    blank = 0
    for r in rows:
        v = (r.get(col) or "").strip()
        if v in codes:
            by_code[v] += 1
        elif v in NA_TOKENS:
            blank += 1
    filled_codes = sum(by_code.values())
    total_missing = filled_codes + blank
    na = by_code.get(NOT_APPLICABLE, 0)
    denom = n - na                      # 真缺失率的分母：先摘掉「不适用」
    return {
        "n": n,
        "by_code": by_code,
        "blank": blank,
        "missing": total_missing,
        "na": na,
        "crude": (total_missing / n) if n else 0.0,
        "real": ((total_missing - na) / denom) if denom else 0.0,
    }


def fmt(col, m, codes, warn, width):
    parts = [f"{k} {m['by_code'].get(k, 0)}" for k in codes]
    if m["blank"]:
        parts.append(f"空/未标码 {m['blank']}")
    flag = " ⚠️" if m["real"] >= warn else ""
    return (f"  {col:<{width}} N={m['n']:<5} "
            f"粗缺失 {m['crude']:6.1%}   真缺失 {m['real']:6.1%}{flag}\n"
            f"  {'':<{width}} 构成：{' · '.join(parts)}")


def main():
    ap = argparse.ArgumentParser(description="逐变量逐时点缺失率（四类缺失码拆分）")
    ap.add_argument("data")
    ap.add_argument("--codes", default=",".join(DEFAULT_CODES))
    ap.add_argument("--time", default=None)
    ap.add_argument("--id", default=None)
    ap.add_argument("--warn", type=float, default=0.2)
    ap.add_argument("--top", type=int, default=0)
    a = ap.parse_args()

    codes = [c.strip() for c in a.codes.split(",") if c.strip()]
    rows, enc = read_rows(a.data)
    if not rows:
        raise SystemExit(f"{a.data}：没有数据行")
    if a.time and a.time not in rows[0]:
        raise SystemExit(f"{a.data}：找不到时点列「{a.time}」。现有列："
                         f"{' / '.join(rows[0].keys())}")

    skip = {a.id, a.time} - {None}
    cols = [c for c in rows[0] if c not in skip]

    print(f"missing_report · {pathlib.Path(a.data).name} · {enc} · "
          f"{len(rows)} 行 × {len(cols)} 变量")
    print(f"  缺失码：{' · '.join(codes)}　⚠️ 阈值：真缺失 ≥ {a.warn:.0%}")

    stats = {c: measure(rows, c, codes) for c in cols}
    order = sorted(cols, key=lambda c: stats[c]["real"], reverse=True)
    if a.top:
        order = order[:a.top]
    width = max((len(c) for c in order), default=8)

    print("\n── 全样本 ──")
    for c in order:
        print(fmt(c, stats[c], codes, a.warn, width))

    if a.time:
        times = []
        for r in rows:
            t = (r.get(a.time) or "").strip()
            if t and t not in times:
                times.append(t)
        print(f"\n── 逐时点（{a.time}：{' / '.join(times)}）──")
        print("  ⚠️ 逐时点看的是**失访**——真缺失率随时间的抬头，"
              "多半是人不来了，不是变量本身难测。")
        for t in times:
            sub = [r for r in rows if (r.get(a.time) or "").strip() == t]
            print(f"\n  【{t}】N={len(sub)}")
            for c in order:
                print(fmt(c, measure(sub, c, codes), codes, a.warn, width))

    print("\n  两个率都摆出来了——用哪个看 SAP。"
          "「不适用」在真缺失率里已摘除。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
