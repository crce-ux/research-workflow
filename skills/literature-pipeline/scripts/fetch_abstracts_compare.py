# -*- coding: utf-8 -*-
"""
fetch_abstracts_compare.py —— 摘要批量拉取 + 关键结果比对（质量核查②用）

用途：按 PMID 列表批量拉取 PubMed 摘要，与证据表"关键结果"列逐篇比对，
    标记疑似未匹配数字（防证据表数值错误——教训：曾发现 Vancampfort16 RR、
    Kroeze03 相关系数等 10 处数值错误）。对应《文献调研流程手册》质量核查②。

用法：
    # 拉取摘要落盘（供人工/后续比对）
    python fetch_abstracts_compare.py --pmids "37965432,24313570" -o abstracts.txt

    # 拉取摘要 + 与证据表 xlsx 的"关键结果"列自动比对（数字抽核）
    python fetch_abstracts_compare.py --pmids-file pmids.txt --evtab 证据表_模块X.xlsx \
        --res-col 8 --out report.md

    # 或直接从证据表 xlsx 提取 PMID 列（第4列）+ 关键结果列（第8列）
    python fetch_abstracts_compare.py --evtab 证据表_模块X.xlsx --pmid-col 4 --res-col 8 \
        --out 模块X_数字核查报告.md

输出：abstracts.txt（摘要原文）/ report.md（逐篇数字比对报告：疑似未匹配 + 重点篇目抽核）。

依赖：标准库（urllib/openpyxl 仅 --evtab 模式需要）。
"""

import sys
import re
import time
import argparse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_UA = {"User-Agent": "research-helper/1.0"}


def fetch_abstract(pmid):
    url = (f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
           f"?db=pubmed&id={pmid}&rettype=abstract&retmode=xml")
    xml = urllib.request.urlopen(urllib.request.Request(url, headers=_UA), timeout=60) \
        .read().decode("utf-8", errors="replace")
    abs_texts = re.findall(r"<AbstractText[^>]*>(.*?)</AbstractText>", xml, re.S)
    full = " ".join(re.sub(r"<[^>]+>", " ", t) for t in abs_texts)
    return re.sub(r"\s+", " ", full).strip()


def norm_text(s):
    """归一化：统一全半角、去空格，便于数字比对"""
    if not s:
        return ""
    s = re.sub(r"[－–—~～−]", "-", s)
    s = re.sub(r"[，。、；：（）【】“”‘’]", " ", s)
    return re.sub(r"\s+", "", s.lower())


def digit_issues(res, ab):
    """从'关键结果'提取数字，检查摘要是否包含（忽略<1的小数与年份）"""
    res_n = norm_text(res)
    ab_n = norm_text(ab)
    nums = re.findall(r"\d+[.,]\d+|\d+", res_n)
    issues = []
    for v in nums:
        if re.fullmatch(r"\d{4}", v):      # 年份跳过
            continue
        if float(v.replace(",", ".")) < 1 and "." not in v:  # 小整数跳过
            continue
        if v not in ab_n:
            issues.append(v)
    return issues


def main():
    ap = argparse.ArgumentParser(description="摘要批量拉取 + 关键结果比对")
    ap.add_argument("--pmids", help="逗号分隔 PMID")
    ap.add_argument("--pmids-file", help="文件：每行一个 PMID")
    ap.add_argument("--evtab", help="证据表 xlsx 路径")
    ap.add_argument("--pmid-col", type=int, default=4, help="xlsx 中 PMID 所在列（默认4）")
    ap.add_argument("--res-col", type=int, default=8, help="xlsx 中'关键结果'所在列（默认8）")
    ap.add_argument("-o", "--out", default="abstracts.txt", help="输出文件（摘要或报告）")
    args = ap.parse_args()

    if args.evtab:
        from openpyxl import load_workbook
        import re as _re
        ws = load_workbook(args.evtab).active
        rows = []
        for r in range(2, ws.max_row + 1):
            res = ws.cell(row=r, column=args.res_col).value
            if args.pmid_col >= 1:
                pmid = ws.cell(row=r, column=args.pmid_col).value
            else:
                # pmid-col=0：从整行文本提取 PMID（适配"文献·DOI"列含 PMID 的格式）
                rowtext = " ".join(str(c.value or "") for c in ws[r] if c.value)
                m = _re.search(r"PMID\s*(\d+)", rowtext)
                pmid = m.group(1) if m else None
            if pmid:
                rows.append((str(pmid), res or ""))
        report = []
        issues_total = 0
        for pmid, res in rows:
            ab = fetch_abstract(pmid)
            time.sleep(0.35)
            iss = digit_issues(res, ab)
            if iss:
                issues_total += 1
                report.append(f"### {pmid}")
                report.append(f"- 关键结果：{res[:120]}")
                report.append(f"- 疑似未匹配数字：{sorted(set(iss))}")
                report.append("")
            else:
                report.append(f"### {pmid} ✅ 数字均在摘要中")
        out = args.out
        with open(out, "w", encoding="utf-8") as f:
            f.write("\n".join(report))
        print(f"[OK] 比对完成：{len(rows)} 篇，疑似未匹配 {issues_total} 篇")
        print(f"     报告已落盘：{out}")
    else:
        pmids = []
        if args.pmids:
            pmids = [p.strip() for p in args.pmids.split(",") if p.strip().isdigit()]
        elif args.pmids_file:
            pmids = [l.strip() for l in open(args.pmids_file, encoding="utf-8") if l.strip().isdigit()]
        with open(args.out, "w", encoding="utf-8") as f:
            for pmid in pmids:
                ab = fetch_abstract(pmid)
                f.write(f"===== PMID {pmid} =====\n{ab}\n\n")
                time.sleep(0.35)
        print(f"[OK] 已拉取 {len(pmids)} 篇摘要 → {args.out}")


if __name__ == "__main__":
    main()
