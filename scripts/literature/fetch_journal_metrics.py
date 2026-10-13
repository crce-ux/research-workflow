# -*- coding: utf-8 -*-
"""
fetch_journal_metrics.py —— 期刊指标批量查询（中科院分区 + JCR 影响因子）

【用途】
    给证据表 / 文献表的「期刊 IF」「期刊分区」两列自动取值。
    输入期刊名（或 pubmed_meta_fetch.py 产出的 meta JSON），
    输出可直接回填的指标 JSON。

【数据源（本地 CSV，离线查询，快且口径明确）】
    `_流程与工具/_journal_data/`
      · FQBJCR2025-UTF8.csv —— **中科院分区表 2025（升级版）**
                                含 大类/大类分区/小类/Top/ISSN
      · JCR2024-UTF8.csv    —— **JCR 2024**：IF(2024) / IF Quartile / IF Rank
      · GJQKYJMD2025.csv    —— 国际期刊预警名单 2025
    数据来自开源仓库 Cuberskyleaf/cas-journal-mcp（2026-09-16 下载）。

【⚠️ 口径（写进证据表时必须带上）】
    · IF        → `{if} ({if_year} JCR)`，如 `3.5 (2024 JCR)`
    · 分区      → `中科院{大类}{zone}区({cas_year}) / JCR Q{n}`
                  如 `中科院医学2区(2025) / JCR Q1`
    · **中科院分区有基础版/升级版差异**，本脚本用的是 **2025 升级版**；
      若你的项目须用其他版本，请换对应 CSV，并在列内标明版本号。
    · ⚠️ **不写口径等于没写**——同一本刊换版本就换区。

【用法】
    # 1) 从 meta JSON 批量查（推荐）
    python fetch_journal_metrics.py --meta-file 思路A_meta.json -o 期刊指标.json

    # 2) 直接给刊名
    python fetch_journal_metrics.py --journals "Cell,Schizophrenia Research" -o 期刊指标.json

    # 3) 多个 meta 合并 + 增量并入已有缓存
    python fetch_journal_metrics.py --meta-file A.json --meta-file B.json \
        --cache 期刊指标.json -o 期刊指标.json

【输出格式】
    {"Schizophrenia research": {
        "matched": "Schizophrenia Research", "issn": "0920-9964",
        "if": "3.5", "if_year": "2024", "jcr_quartile": "Q1", "jcr_rank": "71/288",
        "cas_major": "医学", "cas_zone": "2", "cas_top": "否", "cas_year": "2025",
        "if_display": "3.5 (2024 JCR)",
        "rank_display": "中科院医学2区(2025) / JCR Q1"
    }, ...}

⚠️ 踩坑备忘：
  - PubMed 刊名常带副标题（如 "Clinical neurophysiology : official journal of ..."），
    本脚本自动截断 " : " 之前部分再匹配。
  - 匹配失败会**显式列出**（`"_unmatched"` 字段），不静默跳过——须人工补。
  - 第三方网站（如 xxx.com 类聚合站）数据**实测有误**（同一本刊 IF/分区三项全错），
    本脚本刻意不采用任何网络聚合站，只用权威表 CSV。
"""
import argparse
import csv
import difflib
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(HERE), "_journal_data")
CAS_CSV = os.path.join(DATA_DIR, "FQBJCR2025-UTF8.csv")
JCR_CSV = os.path.join(DATA_DIR, "JCR2024-UTF8.csv")
WARN_CSV = os.path.join(DATA_DIR, "GJQKYJMD2025.csv")


def norm_full(s):
    """完整规范化：**保留冒号后内容**，只去标点/压空格/转小写。

    ⚠️ 为什么保留冒号——踩坑教训（2026-09-16）：
       曾用「截断 ":" 后内容」的规则，结果把
         `Biological Psychiatry` 与 `Biological Psychiatry: Global Open Science`
       规范化成同一个键 → 前者被错配到后者的 IF 3.7（实际应为 9.0）。
       **刊名里的冒号可能是刊名的一部分，不是副标题。**
    """
    if not s:
        return ""
    s = str(s).strip()
    s = re.sub(r"\([^)]*\)", " ", s)      # 去括号内容：PubMed 常加地名后缀，如
                                          # "Journal of psychopharmacology (Oxford, England)"
    s = re.sub(r"[^\w\s&\-:]", " ", s)
    s = re.sub(r"\s+", " ", s).strip().lower()
    s = re.sub(r"^the\s+", "", s)         # 去前导冠词：PubMed 常写 "The Journal of X"，
                                          # 而 JCR 表写 "JOURNAL OF X"（否则降级为 fuzzy）
    return s


def norm_short(s):
    """截断**出版社式副标题**（PubMed 常见："Brain : a journal of neurology"）。

    只截断明显是副标题的（以 official / a journal of / an international 等开头），
    其余冒号一律保留。用作**次级索引**，优先级低于 norm_full。
    """
    s = str(s)
    s = re.split(r"\s*:\s*(?:official|a journal|an international|the official|publication|"
                 r"journal of the|revue|organ of)", s, flags=re.I)[0]
    return norm_full(s)


def load_cas(path):
    """中科院分区表：{norm_name: {...}, issn: {...}}"""
    by_name, by_issn, pending = {}, {}, []
    if not os.path.exists(path):
        sys.exit(f"[错误] 找不到中科院分区表：{path}\n[提示] 见脚本头「数据源」一节，需先下载 CSV。")
    with open(path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            name = (row.get("Journal") or "").strip()
            if not name:
                continue
            rec = {
                "name": name,
                "issn_raw": (row.get("ISSN/EISSN") or "").strip(),
                "major": (row.get("大类") or "").strip(),
                "zone_raw": (row.get("大类分区") or "").strip(),
                "top": (row.get("Top") or "").strip(),
                "year": (row.get("年份") or "").strip(),
            }
            zone = re.match(r"(\d+)", rec["zone_raw"])
            rec["zone"] = zone.group(1) if zone else ""
            pending.append((name, rec))
            for issn in re.split(r"[/,;\s]+", rec["issn_raw"]):
                if issn:
                    by_issn.setdefault(issn.strip(), rec)
    # ⚠️ 两遍建索引（踩坑教训 2026-09-16）：
    #   若一遍内混用 setdefault，子刊的「短名」可能抢先占用主刊的「完整名」槽位——
    #   实测 `Biological Psychiatry: Global Open Science`(IF 3.7) 抢占了
    #   `Biological Psychiatry`(IF 9.0) 的键，导致主刊被错配。
    #   正确顺序：先全部完整名，再用短名补空缺（短名不得覆盖任何完整名）。
    for name, rec in pending:
        by_name.setdefault(norm_full(name), rec)
    for name, rec in pending:
        sh = norm_short(name)
        if sh and sh not in by_name:
            by_name[sh] = rec
    return by_name, by_issn


def load_jcr(path):
    """JCR：{norm_name: {...}, issn: {...}}"""
    by_name, by_issn, pending = {}, {}, []
    if not os.path.exists(path):
        sys.exit(f"[错误] 找不到 JCR 表：{path}")
    with open(path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            name = (row.get("Journal") or "").strip()
            if not name:
                continue
            rec = {
                "name": name,
                "issn": (row.get("ISSN") or "").strip(),
                "eissn": (row.get("eISSN") or "").strip(),
                "if": (row.get("IF(2024)") or "").strip(),
                "quartile": (row.get("IF Quartile(2024)") or "").strip(),
                "rank": (row.get("IF Rank(2024)") or "").strip(),
                "year": "2024",
            }
            pending.append((name, rec))
            for issn in (rec["issn"], rec["eissn"]):
                if issn:
                    by_issn.setdefault(issn, rec)
    for name, rec in pending:
        by_name.setdefault(norm_full(name), rec)
    for name, rec in pending:
        sh = norm_short(name)
        if sh and sh not in by_name:
            by_name[sh] = rec
    return by_name, by_issn


def load_warn(path):
    """国际期刊预警名单"""
    warn = {}
    if not os.path.exists(path):
        return warn
    with open(path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            vals = [v for v in row.values() if v]
            for v in vals:
                warn.setdefault(norm_full(v), True)
    return warn


def generic_short(s):
    """通用截断（第一个冒号前）——**仅作查询期最后回退，不用于建索引**。

    理由：通用截断会误伤「本身就是含冒号刊名」的情况（见 norm_full 的踩坑注释），
    所以只能作为「精确索引都没命中」时的兜底；建索引时一律用 norm_full / norm_short。
    """
    return norm_full(str(s).split(":")[0])


def lookup(name, cas_n, cas_i, jcr_n, jcr_i, warn):
    """五级匹配：完整名 → 严格短名 → 通用截断 → 模糊(标记待核) → 失败"""
    key = norm_full(name)
    cas, jcr, how = cas_n.get(key), jcr_n.get(key), "exact"

    for label, k in (("exact-short", norm_short(name)), ("exact-generic", generic_short(name))):
        if not (cas or jcr) and k and k != key:
            cas, jcr = cas_n.get(k), jcr_n.get(k)
            if cas or jcr:
                how = label
                break

    if not (cas or jcr):
        # ⚠️ 模糊匹配阈值提到 0.92，且结果标记「待核」——
        #    实测 0.88 时 "Indian journal of physiology and pharmacology" 会被
        #    误配到 "CANADIAN JOURNAL OF PHYSIOLOGY AND PHARMACOLOGY"（完全不同刊）。
        probe = norm_short(name) or key
        cand = difflib.get_close_matches(probe, list(cas_n.keys()), n=1, cutoff=0.92)
        if cand:
            cas = cas_n[cand[0]]
            jcr = jcr_n.get(cand[0])
            how = f"fuzzy(待核):{cas['name']}"
        else:
            cand = difflib.get_close_matches(probe, list(jcr_n.keys()), n=1, cutoff=0.92)
            if cand:
                jcr = jcr_n[cand[0]]
                cas = cas_n.get(cand[0])
                how = f"fuzzy(待核):{jcr['name']}"

    rec = {"matched": (cas or jcr or {}).get("name", ""), "match_how": how if (cas or jcr) else "FAILED"}

    if cas:
        rec.update({
            "cas_major": cas["major"], "cas_zone": cas["zone"], "cas_zone_raw": cas["zone_raw"],
            "cas_top": cas["top"], "cas_year": cas["year"], "cas_issn": cas["issn_raw"],
        })
    if jcr:
        rec.update({
            "if": jcr["if"], "if_year": jcr["year"],
            "jcr_quartile": jcr["quartile"], "jcr_rank": jcr["rank"], "jcr_issn": jcr["issn"],
        })

    # 组装可直接写入表的两列
    if jcr:
        rec["if_display"] = f"{jcr['if']} ({jcr['year']} JCR)"
    else:
        rec["if_display"] = ""
    if cas and jcr:
        rec["rank_display"] = f"中科院{cas['major']}{cas['zone']}区({cas['year']}) / JCR {jcr['quartile']}"
    elif cas:
        rec["rank_display"] = f"中科院{cas['major']}{cas['zone']}区({cas['year']})"
    elif jcr:
        rec["rank_display"] = f"JCR {jcr['quartile']}"
    else:
        rec["rank_display"] = ""

    if rec.get("cas_top") == "是":
        rec["rank_display"] += " · Top"
    if warn.get(key):
        rec["warning"] = "⚠️ 在《国际期刊预警名单(2025)》中"
    return rec


def collect_names(args):
    """收集待查刊名"""
    names = []
    for j in (args.journals or "").split(","):
        if j.strip():
            names.append(j.strip())
    for mf in (args.meta_file or []):
        with open(mf, encoding="utf-8") as f:
            d = json.load(f)
        vals = d.values() if isinstance(d, dict) else d
        for v in vals:
            if isinstance(v, dict) and v.get("journal"):
                names.append(v["journal"].strip())
    # 去重（按规范化键）
    seen, uniq = set(), []
    for n in names:
        k = norm_full(n)
        if k and k not in seen:
            seen.add(k)
            uniq.append(n)
    return uniq


def main():
    ap = argparse.ArgumentParser(description="期刊指标批量查询（中科院分区 2025 + JCR 2024，本地 CSV）")
    ap.add_argument("--meta-file", action="append", help="pubmed_meta_fetch.py 产出的 meta JSON（可多次）")
    ap.add_argument("--journals", help="直接给刊名，逗号分隔")
    ap.add_argument("--cache", help="已有指标库 JSON（增量并入，避免重复记录）")
    ap.add_argument("-o", "--out", required=True, help="输出指标库 JSON")
    args = ap.parse_args()

    cas_n, cas_i = load_cas(CAS_CSV)
    jcr_n, jcr_i = load_jcr(JCR_CSV)
    warn = load_warn(WARN_CSV)
    print(f"[i] 载入 中科院分区表 {len(cas_n)} 刊 / JCR {len(jcr_n)} 刊 / 预警 {len(warn)} 条")

    result = {}
    if args.cache and os.path.exists(args.cache):
        with open(args.cache, encoding="utf-8") as f:
            result = json.load(f)
        print(f"[i] 并入已有缓存 {len(result)} 条")

    names = collect_names(args)
    # ⚠️ 保护手工修正：cache 中 match_how 以 manual 开头的条目**不再重查**，
    #    否则重跑会用自动结果覆盖人工核正过的值（踩坑教训 2026-09-16）。
    _manual = {k for k, v in result.items() if str(v.get("match_how", "")).startswith("manual")}
    _before = len(names)
    names = [n for n in names if n not in _manual]
    if _before != len(names):
        print(f"[i] 跳过 {_before - len(names)} 个已有手工修正的刊名")
    print(f"[i] 待查 {len(names)} 个刊名")
    ok = fail = 0
    unmatched = []
    for n in names:
        rec = lookup(n, cas_n, cas_i, jcr_n, jcr_i, warn)
        result[n] = rec
        if rec["match_how"] == "FAILED":
            unmatched.append(n)
            fail += 1
        else:
            ok += 1

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"[OK] 输出：{args.out}")
    print(f"[OK] 匹配 {ok} / 失败 {fail}")
    if unmatched:
        print("[!] 以下刊名未匹配，须人工补（可先用 OpenAlex 拿 ISSN 再查）：")
        for u in unmatched:
            print("   -", u)
    print("\n[i] 示例（前 3 条）：")
    for k, v in list(result.items())[:3]:
        print(f"   {k}\n      IF: {v.get('if_display','')}\n      分区: {v.get('rank_display','')}")


if __name__ == "__main__":
    main()
