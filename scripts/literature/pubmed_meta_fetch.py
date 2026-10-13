# -*- coding: utf-8 -*-
"""
pubmed_meta_fetch.py —— PubMed 文献元数据批量获取（卷期页核实，质量核查①用）

用途：从 PMID 列表批量拉取 标题/期刊/日期/卷/期/页/作者/DOI，落盘 JSON。
    —— 对应《文献调研流程手册》Step 1 前置：元数据事中核实，不事后返工。

用法：
    python pubmed_meta_fetch.py "12345678,23456789" [-o out.json]
    python pubmed_meta_fetch.py --file pmids.txt [-o out.json]   # 每行一个 PMID

输出：JSON dict {pmid: {title,journal,pubdate,volume,issue,pages,authors,doi}}

注意：
  - 依赖网络（eutils.ncbi.nlm.nih.gov），失败时检查代理/网络。
  - 期刊名取 fulljournalname（全称，符合用户"刊名使用全称"偏好）。
  - 卷期页缺失（如 online ahead of print / article number）时字段为空字符串，
    由下游证据表标注"在线预发表/待出版方确认"，勿硬填。
"""
import sys, os, json, argparse, urllib.request, time

def fetch_meta(pmids):
    """批量 esummary 拉取卷期页元数据"""
    out = {}
    # esummary 一次最多约 200 个，分批
    for i in range(0, len(pmids), 150):
        chunk = pmids[i:i+150]
        ids = ",".join(chunk)
        url = (f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
               f"?db=pubmed&id={ids}&retmode=json")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read().decode("utf-8"))
        for uid in chunk:
            if uid not in data.get("result", {}):
                out[uid] = {"error": "not found"}
                continue
            it = data["result"][uid]
            authors = it.get("authors", [])
            out[uid] = {
                "title": it.get("title", ""),
                "journal": it.get("fulljournalname", ""),
                "pubdate": it.get("pubdate", ""),
                "volume": it.get("volume", ""),
                "issue": it.get("issue", ""),
                "pages": it.get("pages", ""),
                "authors": ", ".join(a.get("name", "") for a in authors[:3]) + (" et al." if len(authors) > 3 else ""),
                "doi": next((x.get("value", "") for x in it.get("articleids", []) if x.get("idtype") == "doi"), ""),
            }
        time.sleep(0.4)  # NCBI 限速友好
    return out

def main():
    ap = argparse.ArgumentParser(description="PubMed 卷期页元数据批量获取")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("pmids", nargs="?", help="逗号分隔的 PMID 列表")
    src.add_argument("--file", help="含 PMID 的文件，每行一个")
    ap.add_argument("-o", "--out", default="pubmed_meta.json", help="输出 JSON 路径")
    args = ap.parse_args()

    if args.file:
        with open(args.file, encoding="utf-8") as f:
            pmids = [ln.strip() for ln in f if ln.strip().isdigit()]
    else:
        pmids = [p.strip() for p in args.pmids.split(",") if p.strip().isdigit()]
    if not pmids:
        sys.exit("未提供有效 PMID")

    print(f"[*] 拉取 {len(pmids)} 条元数据 ...")
    out = fetch_meta(pmids)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"[OK] 已落盘 {args.out}（{len(out)} 条）")
    for uid, it in out.items():
        if "error" in it:
            print(f"  {uid}: NOT FOUND")
        else:
            print(f"  {uid}: {it['journal'][:30]:32s} vol={it['volume'] or '-':4s} "
                  f"iss={it['issue'] or '-':4s} pp={it['pages'] or '-':10s} | {it['title'][:40]}")

if __name__ == "__main__":
    main()
