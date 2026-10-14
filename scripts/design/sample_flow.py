# -*- coding: utf-8 -*-
"""sample_flow.py —— 样本量 → 需招募 → 可招募，三段数字摆出来

【为什么有它】
    study-design 的 D2 写着「给区间 + 假设来源 + 脱落率」，D4 写着
    「**可招募数 ≥ 样本量需求**——要算，要摆出两个数字」。
    这两条都是算术，但写在手册里就没人算——最后方案里只有一句
    「预计可满足」，而这正是可行性最常见的一票否决点。

【它算什么】
    ① 主分析样本量需求 → 加上脱落率 → **需招募数**（乐观 / 保守两套）
    ② 按分组比 → 每组需招募
    ③ 可招募数 = 年门诊量 × 入排符合比例 × 年数
    ④ 两者对比：**最保守的需求**够不够

【它不查什么】
    ⭐ **样本量本身怎么来**（效应量、效能、检验方法）不在这——
    那是 SAP 与统计学家的事，也在 study-design 的 D2（效应量降级铁律）。
    本脚本只做「已经拿到主分析样本量之后」的换算与对比。

用法：
    python sample_flow.py --need 120 --dropout 0.20 --dropout-range 0.15,0.30
    python sample_flow.py --need 120 --dropout 0.20 --annual 600 --eligible 0.35 --years 1.5
    python sample_flow.py --need 120 --dropout 0.20 --ratio 2:1

不给 --dropout-range 就按 ±5 个百分点给两套。
退出码：可招募数 < 最保守需求时为 1（一票否决），否则 0。
"""
import argparse
import math
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def inflate(need, dropout):
    """主分析样本量 → 需招募数。"""
    if not 0 <= dropout < 1:
        raise SystemExit(f"脱落率要在 [0,1)；收到 {dropout}")
    return math.ceil(need / (1 - dropout))


def split(total, ratio):
    """按 a:b 拆到每组（向上取整，和可能略大于 total）。"""
    a, b = ratio
    per = total / (a + b)
    return [math.ceil(per * a), math.ceil(per * b)]


def parse_ratio(s):
    try:
        a, b = s.replace("：", ":").split(":")
        return int(a), int(b)
    except ValueError:
        raise SystemExit(f"--ratio 写成 a:b，如 1:1 或 2:1；收到 {s!r}")


def main():
    ap = argparse.ArgumentParser(description="样本量 → 需招募 → 可招募")
    ap.add_argument("--need", type=int, required=True, help="主分析样本量需求")
    ap.add_argument("--dropout", type=float, required=True, help="预期脱落率，如 0.2")
    ap.add_argument("--dropout-range", default=None, help="两个脱落率，如 0.15,0.30")
    ap.add_argument("--ratio", default="1:1", help="分组比，默认 1:1")
    ap.add_argument("--annual", type=float, default=None, help="年门诊 / 年可接触病例量")
    ap.add_argument("--eligible", type=float, default=1.0, help="符合入排的比例，如 0.35")
    ap.add_argument("--years", type=float, default=1.0, help="招募年数")
    a = ap.parse_args()

    ratio = parse_ratio(a.ratio)
    if a.dropout_range:
        try:
            lo, hi = (float(x) for x in a.dropout_range.split(","))
        except ValueError:
            raise SystemExit(f"--dropout-range 写成 0.15,0.30；收到 {a.dropout_range!r}")
    else:
        lo, hi = max(0.0, a.dropout - 0.05), min(0.95, a.dropout + 0.05)

    print(f"sample_flow · 主分析样本量需求 {a.need} · 分组比 {'：'.join(map(str, ratio))}")
    print(f"  按脱落率换算需招募：")
    rows = []
    for label, d in (("乐观", lo), ("预期", a.dropout), ("保守", hi)):
        n = inflate(a.need, d)
        arms = split(n, ratio)
        rows.append((label, d, n, arms))
        print(f"    {label}  脱落 {d:5.1%} → 需招募 {n:>4}"
              f"   （每组 {' / '.join(map(str, arms))}）")
    worst = max(r[2] for r in rows)

    if a.annual is not None:
        pool = a.annual * a.eligible * a.years
        print(f"\n  可招募数 = 年可接触 {a.annual:g} × 入排符合 {a.eligible:.0%} "
              f"× {a.years:g} 年 = {pool:.0f}")
        ok = pool >= worst
        print(f"  与**最保守需求** {worst} 对比："
              f"{'✅ 够，余量 %.0f' % (pool - worst) if ok else '❌ 差 %.0f' % (worst - pool)}")
        if not ok:
            print("     → 收紧入排、延长招募、加中心、或下调假设——"
                  "**不要用「预计可满足」把这一条糊过去**")
        print("\n  ⚠️ 两个数字都要写进方案，只写一个不算算过。")
        return 0 if ok else 1

    print(f"\n  ⚠️ 还没给可招募数——D4 的可行性判据是"
          f"「可招募数 ≥ {worst}」，缺一半。")
    print("     补 --annual / --eligible / --years 再跑一次。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
