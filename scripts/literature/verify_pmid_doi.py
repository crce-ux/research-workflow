# -*- coding: utf-8 -*-
"""
verify_pmid_doi.py —— PMID/DOI 元数据校验器（防手填错误，质量核查①用）

用途：给定 DOI（或 PMID），反查 PubMed 确认文献真实身份，防止手填/记忆性 PMID/DOI 错误
    （教训：曾遇 20 篇中 19 篇手填 PMID 错误，指向无关论文）。
对应《文献调研流程手册》Step 1 前置：元数据事中核实，不事后返工。

用法：
    # 按 DOI 反查 PMID（推荐，DOI 唯一性高于记忆 PMID）
    python verify_pmid_doi.py --doi 10.1016/S2215-0366(19)30416-X
    python verify_pmid_doi.py --doi-file dois.txt          # 每行一个 DOI

    # 校验已有 PMID 与 DOI 是否匹配（表内自查）
    python verify_pmid_doi.py --pair "37965432|10.1016/j.eclinm.2023.102294"
    python verify_pmid_doi.py --pair-file pairs.txt        # 每行 "PMID|DOI"

输出：每条打印 反查PMID / 表内PMID / 标题 / 期刊 / DOI / 匹配状态（✅/❌）。

依赖：标准库（urllib），无需第三方。
"""

import sys
import json
import time
import argparse
import urllib.request
import urllib.parse

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def eutils(url):
    req = urllib.request.Request(url, headers={"User-Agent": "research-helper/1.0"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read().decode("utf-8"))


def doi_to_pmid(doi):
    """DOI -> PubMed PMID（esearch + esummary）"""
    q = f'"{doi}"[AID]'
    url = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
           f"?db=pubmed&retmode=json&term={urllib.parse.quote(q)}")
    ids = eutils(url)["esearchresult"]["idlist"]
    time.sleep(0.35)
    if not ids:
        return None, None
    s = eutils("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
               f"?db=pubmed&retmode=json&id={ids[0]}")
    it = s["result"].get(ids[0], {})
    real_doi = next((x["value"] for x in it.get("articleids", []) if x["idtype"] == "doi"), "")
    return ids[0], {
        "pmid": ids[0], "title": it.get("title", ""), "journal": it.get("source", ""),
        "pubdate": it.get("pubdate", ""), "doi": real_doi,
    }


def verify_pair(pmid, doi):
    """校验表内 PMID 是否对应给定 DOI"""
    real_pmid, meta = doi_to_pmid(doi)
    if meta is None:
        return f"❌ DOI 未命中 PubMed: {doi}", None
    ok = str(pmid) == real_pmid
    status = "✅ 匹配" if ok else f"❌ 不符：表内 {pmid} ≠ 实际 {real_pmid}"
    return status, meta


def main():
    ap = argparse.ArgumentParser(description="PMID/DOI 元数据校验")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--doi", help="单个 DOI 反查 PMID")
    g.add_argument("--doi-file", help="文件：每行一个 DOI")
    g.add_argument("--pair", help="'PMID|DOI' 校验匹配")
    g.add_argument("--pair-file", help="文件：每行 'PMID|DOI'")
    args = ap.parse_args()

    if args.doi:
        pmid, meta = doi_to_pmid(args.doi)
        if meta:
            print(f"[OK] {args.doi} → PMID {pmid}")
            print(f"  标题: {meta['title'][:80]}")
            print(f"  期刊: {meta['journal']} | {meta['pubdate']} | DOI {meta['doi']}")
        else:
            print(f"[FAIL] DOI 未命中: {args.doi}")
        return

    if args.doi_file:
        for line in open(args.doi_file, encoding="utf-8"):
            doi = line.strip()
            if not doi:
                continue
            pmid, meta = doi_to_pmid(doi)
            if meta:
                print(f"[OK] {doi} → PMID {pmid} | {meta['title'][:50]} | {meta['journal'][:30]}")
            else:
                print(f"[FAIL] {doi} → 未命中")
            time.sleep(0.35)
        return

    if args.pair:
        pmid, doi = args.pair.split("|")
        status, meta = verify_pair(pmid.strip(), doi.strip())
        print(f"[{status}] {doi}")
        if meta:
            print(f"  实际 PMID {meta['pmid']} | {meta['title'][:60]} | {meta['journal'][:30]}")
        return

    if args.pair_file:
        for line in open(args.pair_file, encoding="utf-8"):
            line = line.strip()
            if not line or "|" not in line:
                continue
            pmid, doi = line.split("|")
            status, meta = verify_pair(pmid.strip(), doi.strip())
            print(f"[{status}] {doi}")
            if meta:
                print(f"    PMID {meta['pmid']} | {meta['title'][:50]} | {meta['journal'][:30]}")
            time.sleep(0.35)


if __name__ == "__main__":
    main()
