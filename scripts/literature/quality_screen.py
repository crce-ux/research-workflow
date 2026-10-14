# -*- coding: utf-8 -*-
"""
quality_screen.py —— 检索结果质量快筛（OpenAlex 指标）

【用途】
    对 A1 检索出来的文献批量拉取「影响力指标」，产出可排序的快筛表，
    供 G0 阶段决定**优先精读哪些**、以及给证据表补「影响力」列。

【指标口径】
    裸被引数会冤枉新文献（2026 年的新文引用当然少）。
    OpenAlex 的 **fwci** 与 **citation_normalized_percentile** 按
    「年份 + 领域」归一化，可用于判断"高被引"。

    实例（实测，某 2026 年新文）：
        被引 5 次，但 FWCI = 31.2、被引百分位 = 99.7%、Top 1%
    → 裸被引会说"才 5 次"，归一化指标说"本领域同龄里前 1%"。

【⚠️ 重要原则（脚本只给数据，判断在你）】
    1. **相关度是门槛，影响力是排序**——不能因为 IF 高就留一篇不相干的。
    2. **影响力不等于质量**。高被引论文也可能后来被推翻；
       权威团队也会犯错，而且**权威的错误更危险**（因为没人质疑）。
    3. **外在不该覆盖内在**——最终仍以证据本身（设计 / 样本 / 效应量）为准。
    4. 期刊分区（中科院/JCR）本脚本**不提供**，需人工核对或另配数据源。

【对应流程】
    全流程总纲 **G0 检索层质控**（第二部分：质量快筛）
    文献调研流程手册 §二·Step 0

【用法】
    python quality_screen.py --pmid-file pmids.txt -o 快筛表
    python quality_screen.py --doi-file dois.txt -o 快筛表
    python quality_screen.py --id "41335431,10.1001/jamapsychiatry.2026.0086" -o 快筛表
    python quality_screen.py --pmid-file p.txt -o 快筛表 --sort fwci

【依赖】纯标准库（urllib）。需联网访问 api.openalex.org。
【限流】OpenAlex 建议 ≤10 req/s。本脚本默认间隔 0.12s，可 --sleep 调。
"""
import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

API = "https://api.openalex.org"
UA = "research-assistant/1.0 (mailto:researcher@example.com)"   # OpenAlex 要求带 UA


def fetch(url, retries=3):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code in (429, 500, 502, 503) and i < retries - 1:
                time.sleep(2 ** i)
                continue
            raise
        except Exception:
            if i < retries - 1:
                time.sleep(2 ** i)
                continue
            raise
    return None


def norm_id(s):
    """把一行输入规范成 OpenAlex work 路径"""
    s = s.strip().lstrip("﻿")
    if not s:
        return None, None
    if s.lower().startswith("pmid:"):
        s = s[5:].strip()
    if re.fullmatch(r"\d{6,9}", s):
        return f"pmid:{s}", "PMID"
    m = re.search(r"(10\.\d{4,9}/[^\s]+)", s)
    if m:
        return f"doi:{m.group(1).rstrip('.')}", "DOI"
    return None, None


def work_row(d):
    src = (d.get("primary_location") or {}).get("source") or {}
    pct = d.get("citation_normalized_percentile") or {}
    au = d.get("authorships") or []
    corr = [a for a in au if a.get("is_corresponding")] or au[-1:]
    corr_names, corr_insts = [], []
    for a in corr:
        corr_names.append(a["author"]["display_name"])
        for i in (a.get("institutions") or []):
            if i.get("display_name"):
                corr_insts.append(i["display_name"])
    return {
        "标题": (d.get("title") or "")[:110],
        "年份": d.get("publication_year") or "",
        "期刊": src.get("display_name") or "",
        "被引数": d.get("cited_by_count") or 0,
        "FWCI": round(d.get("fwci"), 2) if d.get("fwci") else "",
        "被引百分位": round(pct.get("value"), 3) if pct.get("value") else "",
        "Top1%": "Y" if pct.get("is_in_top_1_percent") else "",
        "Top10%": "Y" if pct.get("is_in_top_10_percent") else "",
        "通讯作者": "; ".join(corr_names[:2]),
        "通讯机构": "; ".join(dict.fromkeys(corr_insts))[:60],
        "作者数": len(au),
        "DOI": (d.get("doi") or "").replace("https://doi.org/", ""),
        "PMID": ((d.get("ids") or {}).get("pmid") or "").replace("https://pubmed.ncbi.nlm.nih.gov/", ""),
        "_source_id": src.get("id") or "",
    }


def main():
    ap = argparse.ArgumentParser(description="OpenAlex 检索结果质量快筛")
    ap.add_argument("--id", help="逗号分隔的 PMID / DOI")
    ap.add_argument("--pmid-file", help="每行一个 PMID")
    ap.add_argument("--doi-file", help="每行一个 DOI")
    ap.add_argument("-o", "--out", required=True, help="输出前缀（生成 <前缀>.csv 与 <前缀>.md）")
    ap.add_argument("--sort", default="fwci",
                    choices=["fwci", "percentile", "cited", "year"], help="排序键，默认 fwci")
    ap.add_argument("--sleep", type=float, default=0.12, help="请求间隔秒，默认 0.12")
    args = ap.parse_args()

    raw = []
    if args.id:
        raw += args.id.split(",")
    for f in (args.pmid_file, args.doi_file):
        if f:
            raw += open(f, encoding="utf-8").read().splitlines()

    ids = []
    for s in raw:
        nid, _ = norm_id(s)
        if nid and nid not in ids:
            ids.append(nid)
    if not ids:
        print("❌ 没有可解析的 PMID/DOI")
        return 1
    print(f"待查 {len(ids)} 条…")

    rows, miss = [], []
    for i, nid in enumerate(ids, 1):
        try:
            d = fetch(f"{API}/works/{urllib.parse.quote(nid)}")
        except Exception as e:
            print(f"  ⚠ {nid} 请求失败: {type(e).__name__}")
            miss.append((nid, f"请求失败"))
            continue
        if not d:
            print(f"  ❌ {nid} 在 OpenAlex 无记录（**存在性可疑，回源核**）")
            miss.append((nid, "OpenAlex 无记录"))
            continue
        r = work_row(d)
        r["查询ID"] = nid
        rows.append(r)
        if i % 20 == 0:
            print(f"  …{i}/{len(ids)}")
        time.sleep(args.sleep)

    # 排序
    key = {"fwci": lambda r: r["FWCI"] or 0,
           "percentile": lambda r: r["被引百分位"] or 0,
           "cited": lambda r: r["被引数"],
           "year": lambda r: r["年份"] or 0}[args.sort]
    rows.sort(key=key, reverse=True)

    cols = ["查询ID", "标题", "年份", "期刊", "被引数", "FWCI", "被引百分位",
            "Top1%", "Top10%", "通讯作者", "通讯机构", "作者数", "DOI", "PMID"]
    csvp = args.out + ".csv"
    with open(csvp, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)

    mdp = args.out + ".md"
    with open(mdp, "w", encoding="utf-8") as f:
        f.write(f"# 检索结果质量快筛（OpenAlex）\n\n")
        f.write(f"> 共 {len(rows)} 条 · 按 **{args.sort}** 降序 · 生成于脚本运行时刻\n")
        f.write(f"> ⚠️ 影响力用于**排序**，不用于淘汰；相关度是门槛，以证据本身为准。\n\n")
        f.write("| # | 年份 | 期刊 | 被引 | FWCI | 百分位 | Top1% | 通讯作者 / 机构 | 标题 |\n")
        f.write("|---|---|---|---|---|---|---|---|---|\n")
        for i, r in enumerate(rows, 1):
            f.write(f"| {i} | {r['年份']} | {r['期刊'][:26]} | {r['被引数']} | "
                    f"{r['FWCI']} | {r['被引百分位']} | {r['Top1%']} | "
                    f"{r['通讯作者'][:18]} / {r['通讯机构'][:24]} | {r['标题'][:70]} |\n")

    print(f"\n✅ 输出：\n   {csvp}\n   {mdp}")
    if miss:
        print(f"\n⚠️ {len(miss)} 条未取到（**存在性可疑，务必回源核**）：")
        for nid, why in miss[:20]:
            print(f"   {nid}  — {why}")
    print("\n📌 下一步：把本表与本领域常识对照——")
    print("   · 相关度够不够（影响力再高，不相干也没用）")
    print("   · Top1%/Top10% 与 FWCI 排前的是否真是关键文献")
    print("   · 期刊分区（中科院/JCR）需人工核对，本脚本不提供")
    return 0


if __name__ == "__main__":
    sys.exit(main())
