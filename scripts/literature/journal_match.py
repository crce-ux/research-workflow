# -*- coding: utf-8 -*-
"""
journal_match.py —— 选刊辅助：期刊候选池硬过滤（本地离线，权威表 CSV）

【用途】
    投稿前**从期刊全集里筛候选池**，而不是凭印象列几个刊名。
    回答的是："按我的学科与门槛，有哪些刊**客观上**够格？"
    **不回答**「哪本最容易中」——中不中取决于 scope 与稿件匹配度，属人工判断。

【背景】
    本库已有 `fetch_journal_metrics.py`（查**已知刊名**的指标）与 `_journal_data/` 权威表。
    缺的是**反向**用法：不知道投哪本时，从全集里筛。本脚本补上反向用法。
    ⚠️ 不需要外部选刊技能：外部技能内置的 IF 表比 `_journal_data/` 旧。

【用法】
    # 1) 筛选模式：按学科与门槛从全集筛候选池
    python journal_match.py --major 医学 --sub 精神病学 --min-if 3 --max-zone 2
    python journal_match.py --major 医学 --top --min-if 5 --sort if --limit 30
    python journal_match.py --sub 神经科学 --max-zone 1 --exclude-warn

    # 2) 查阅模式：给一批候选刊名，查它们的指标
    python journal_match.py --candidates my_journals.txt

    # 3) 只看筛选结果的统计
    python journal_match.py --major 医学 --sub 精神病学 --stats

【输出】
    Markdown 表（默认打印）。`--out x.md` 落盘。
    列：刊名 / 中科院大类分区 / 小类 / Top / IF(2024) / JCR 分区 / 预警

【对应流程】
    `SCI投稿_选刊流程.md` · 硬过滤段
    数据源与口径**完全复用** `fetch_journal_metrics.py`（见其脚本头「数据源」一节）

【依赖】
    标准库。需 `_journal_data/` 下的三个 CSV（中科院2025-升级版 / JCR2024 / 预警2025）。

【⚠️ 规则（沿用 G0 质量快筛的四条精神）】
    1. **相关度是门槛，影响因子只是排序。**
       本脚本只做"客观门槛筛选"，**scope 匹配必须人工判**。
    2. **中科院分区有基础版/升级版差异，且逐年变动**——
       输出里带版本年份，引用时**必须连口径一起写**。
    3. **预警名单是硬排除**（默认开），不因 IF 高而放行。
    4. **筛出来的候选池是"够格的"，不是"该投的"。**

【踩坑教训】
    • 复用 `fetch_journal_metrics.load_cas()` —— 它内含两遍建索引的修正
      （短名不得覆盖完整名），自己另写会重踩同一坑
    • `--sub` 匹配的是**小类**字段，期刊可能有多个小类（小类1..6）
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    import fetch_journal_metrics as FJM
except ImportError:
    sys.exit("[错误] 找不到 fetch_journal_metrics.py（应与本脚本同目录）")

WARN_CSV = FJM.WARN_CSV


def subcategories(cas_row_raw):
    """从原始 CSV 行取全部小类（小类1..小类6）。"""
    out = []
    for i in range(1, 7):
        v = (cas_row_raw.get(f"小类{i}") or "").strip()
        if v:
            out.append(v)
    return out


def load_cas_with_sub():
    """在 fetch_journal_metrics.load_cas 之上，补出「全部小类」字段。

    不重写 load_cas——其中有两遍建索引的修正（踩坑教训），重写会重踩。
    """
    import csv
    by_name, by_issn = FJM.load_cas(FJM.CAS_CSV)

    # 单独读一遍原始 CSV，只为补 sub 字段
    subs = {}
    with open(FJM.CAS_CSV, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            name = (row.get("Journal") or "").strip()
            if name:
                subs[FJM.norm_full(name)] = subcategories(row)

    for key, rec in by_name.items():
        rec.setdefault("subs", subs.get(FJM.norm_full(rec["name"]), []))
    return by_name, by_issn


def build_pool(cas_n, jcr_n):
    """把 cas_n 里每一条并上 JCR 的 IF / 分区。"""
    pool = []
    for key, rec in cas_n.items():
        if key != FJM.norm_full(rec["name"]):
            continue                      # 只用完整名条目，避免短名重复计数
        j = jcr_n.get(FJM.norm_full(rec["name"])) or jcr_n.get(FJM.norm_short(rec["name"]))
        item = {
            "name": rec["name"],
            "major": rec.get("major", ""),
            "zone": rec.get("zone", ""),
            "zone_raw": rec.get("zone_raw", ""),
            "top": rec.get("top", ""),
            "year": rec.get("year", ""),
            "subs": rec.get("subs", []),
            "if": (j or {}).get("if", ""),
            "if_year": (j or {}).get("year", ""),
            "quartile": (j or {}).get("quartile", ""),
            "issn": rec.get("issn_raw", ""),
        }
        pool.append(item)
    return pool


def filter_pool(pool, args, warn):
    out = []
    for it in pool:
        if args.major and args.major not in it["major"]:
            continue
        if args.sub:
            joined = " ".join(it["subs"]) + " " + it["major"]
            if args.sub not in joined:
                continue
        if args.top and it["top"] != "是":
            continue
        if args.max_zone and it["zone"]:
            try:
                if int(it["zone"]) > int(args.max_zone):
                    continue
            except ValueError:
                continue
        if args.min_if and it["if"]:
            try:
                if float(it["if"]) < float(args.min_if):
                    continue
            except ValueError:
                continue
        if args.min_if and not it["if"]:
            continue                      # 要求了 IF 但查不到 → 排除，不硬凑
        it["warn"] = it["name"] in warn or FJM.norm_full(it["name"]) in warn
        if args.exclude_warn and it["warn"]:
            continue
        out.append(it)
    return out


def sort_pool(pool, key):
    if key == "if":
        return sorted(pool, key=lambda x: float(x["if"] or 0), reverse=True)
    if key == "zone":
        return sorted(pool, key=lambda x: (int(x["zone"] or 9), -float(x["if"] or 0)))
    return sorted(pool, key=lambda x: x["name"])


def render(pool, limit):
    rows = ["| 刊名 | 中科院大类分区 | 小类 | Top | IF | JCR | 预警 |",
            "|---|---|---|---|---|---|---|"]
    for it in pool[:limit]:
        zone = f"{it['major']}{it['zone']}区({it['year']})" if it["zone"] else "—"
        subs = " / ".join(it["subs"][:2]) or "—"
        iff = f"{it['if']} ({it['if_year']} JCR)" if it["if"] else "—"
        rows.append(f"| {it['name']} | {zone} | {subs} | {it['top'] or '—'} | "
                    f"{iff} | {it['quartile'] or '—'} | {'⚠️' if it.get('warn') else ''} |")
    return "\n".join(rows)


def main():
    ap = argparse.ArgumentParser(
        description="选刊辅助：期刊候选池硬过滤（本地权威表，离线）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="⚠️ 本脚本只做客观门槛筛选；**scope 匹配必须人工判**。")
    ap.add_argument("--major", help="中科院大类，如 医学 / 神经科学 / 生物学")
    ap.add_argument("--sub", help="小类关键词，如 精神病学 / 神经科学 / 临床神经病学")
    ap.add_argument("--min-if", dest="min_if", type=float, help="最低 IF（2024 JCR）")
    ap.add_argument("--max-zone", dest="max_zone", type=int, help="中科院分区不差于此，如 2")
    ap.add_argument("--top", action="store_true", help="只看中科院 Top 期刊")
    ap.add_argument("--exclude-warn", action="store_true", default=True,
                    help="排除《国际期刊预警名单》（默认开）")
    ap.add_argument("--no-exclude-warn", dest="exclude_warn", action="store_false",
                    help="不排除预警名单（仅用于核查）")
    ap.add_argument("--sort", choices=["if", "zone", "name"], default="if", help="排序轴")
    ap.add_argument("--limit", type=int, default=40, help="输出条数（默认 40）")
    ap.add_argument("--candidates", help="候选刊名文件（每行一个），改用查阅模式")
    ap.add_argument("--out", help="落盘到文件（默认打印）")
    ap.add_argument("--stats", action="store_true", help="只输出筛选结果统计")
    args = ap.parse_args()

    cas_n, cas_i = load_cas_with_sub()
    jcr_n, jcr_i = FJM.load_jcr(FJM.JCR_CSV)
    warn = FJM.load_warn(WARN_CSV)

    if args.candidates:
        names = [l.strip() for l in open(args.candidates, encoding="utf-8") if l.strip()]
        res = []
        for n in names:
            # ⚠️ lookup() 返回**单个 dict**（不是元组）；查不到时 matched 为空、match_how=FAILED
            rec = FJM.lookup(n, cas_n, cas_i, jcr_n, jcr_i, warn)
            matched = rec.get("matched") or n
            # 补出小类：从 cas_n 按匹配到的完整名回取
            cas_rec = cas_n.get(FJM.norm_full(matched)) or {}
            res.append({
                "name": matched,
                "major": rec.get("cas_major", ""), "zone": rec.get("cas_zone", ""),
                "zone_raw": rec.get("cas_zone_raw", ""), "top": rec.get("cas_top", ""),
                "year": rec.get("cas_year", ""), "subs": cas_rec.get("subs", []),
                "if": rec.get("if", ""), "if_year": rec.get("if_year", ""),
                "quartile": rec.get("jcr_quartile", ""), "issn": "",
                "warn": bool(rec.get("warning")),
                "how": rec.get("match_how", ""),
            })
            if rec.get("match_how") == "FAILED":
                print(f"  ⚠️ 未匹配到：{n}（请人工核对刊名）", file=sys.stderr)
        pool = sort_pool(res, args.sort)
    else:
        pool = filter_pool(build_pool(cas_n, jcr_n), args, warn)
        pool = sort_pool(pool, args.sort)

    if args.stats:
        print(f"候选池：**{len(pool)}** 本")
        from collections import Counter
        print("  分区分布:", dict(sorted(Counter(f"{p['zone']}区" for p in pool if p["zone"]).items())))
        print("  Top 数:", sum(1 for p in pool if p["top"] == "是"))
        print("  预警数:", sum(1 for p in pool if p.get("warn")))
        return 0

    if not pool:
        print("⚠️ 无符合条件的期刊。放宽 --min-if / --max-zone，或换 --sub 关键词。")
        print("   提示：中科院「小类」名与直觉可能不同，可先用 --major 只看大类。")
        return 0

    md = render(pool, args.limit)
    header = (f"# 期刊候选池（{len(pool)} 本，显示前 {min(len(pool), args.limit)}）\n\n"
              f"> 筛选：大类={args.major or '不限'} · 小类={args.sub or '不限'} · "
              f"IF≥{args.min_if or '不限'} · 分区≤{args.max_zone or '不限'} · "
              f"{'Top' if args.top else '不限Top'} · "
              f"{'已排除预警' if args.exclude_warn else '**未排除预警**'}\n\n"
              f"> ⚠️ **本表是「够格的」，不是「该投的」。**\n"
              f"> 相关度是门槛、影响因子只是排序；**scope 匹配必须人工判**。\n"
              f"> 分区口径：中科院 2025 升级版；引用时须连口径一起写。\n\n")

    text = header + md + "\n"
    if args.out:
        open(args.out, "w", encoding="utf-8").write(text)
        print(f"✅ 已写入 {args.out}（{len(pool)} 本，显示 {min(len(pool), args.limit)}）")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
