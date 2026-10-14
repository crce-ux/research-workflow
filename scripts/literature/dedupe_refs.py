# -*- coding: utf-8 -*-
"""dedupe_refs.py —— 文献列表去重（DOI → PMID → 归一化标题）

【背景】
    从 PubMed / Zotero / 中文库 / 出版社网站分别导出再合起来，
    同一篇常出现三次。人眼比对又慢又不可靠——而**去重做没做干净，
    会一路带到覆盖声明**（N 里含重复 → M、K 全歪）。

【去重的判据次序】严格按可靠性：
    ① DOI 相同（归一化后）——最强
    ② 无 DOI 时，PMID 相同
    ③ 都没有时，**归一化标题**相同且长度 ≥ 20 字
       （标题太短容易误合并，宁可不合）

【它不查什么】
    ⭐ 判断「这两条是不是同一篇」的最后关口由人判断——
    尤其是标题相近的不同版本（预印本 / 正式版 / 会议摘要）。
    脚本给出的是**候选**，被合并的每一条都打印出来供人复核。

用法：
    python dedupe_refs.py <文献列表.csv|.tsv|.txt|.ris> [--out 去重后.csv]

    CSV/TSV 按**表头名**认列（DOI / 标题 / PMID 的各种写法都认）。
    RIS 按 TY/DO/AN/TI 标签解析。
    另有无表头的纯行模式：每行一条，按 Tab 或 | 切分。

退出码恒为 0——它是**整理工具，不是门禁**。
"""
import argparse
import csv
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DOI_KEYS = ("doi", "DOI", "Doi")
PMID_KEYS = ("pmid", "PMID", "Pmid", "pubmed")
TITLE_KEYS = ("title", "标题", "题名", "ti", "TI")

DOI_PREFIX = re.compile(r"^\s*(?:https?://)?(?:dx\.)?doi\.org/|^\s*doi:\s*", re.I)
NON_WORD = re.compile(r"[^\w一-鿿]+")
MIN_TITLE = 20


def norm_doi(v):
    if not v:
        return ""
    return DOI_PREFIX.sub("", str(v).strip()).strip().lower()


def norm_pmid(v):
    if not v:
        return ""
    m = re.search(r"\d+", str(v))
    return m.group() if m else ""


def norm_title(v):
    if not v:
        return ""
    return NON_WORD.sub("", str(v)).lower()


def pick(row, keys):
    for k in keys:
        if k in row and row[k]:
            return str(row[k]).strip()
    return ""


def read_csv_like(path):
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    if not text.strip():
        return [], []
    delim = "\t" if path.suffix.lower() == ".tsv" else ","
    try:
        dialect = csv.Sniffer().sniff(text[:2048], delimiters=",\t|")
        delim = dialect.delimiter
    except csv.Error:
        pass
    rows = list(csv.reader(text.splitlines(), delimiter=delim))
    if not rows:
        return [], []
    head = [c.strip() for c in rows[0]]
    if any(k in head for k in DOI_KEYS + PMID_KEYS + TITLE_KEYS):
        return head, [dict(zip(head, r)) for r in rows[1:] if any(r)]
    return None, [dict(enumerate(r)) for r in rows if any(r)]


def read_ris(path):
    recs, cur = [], {}
    for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        m = re.match(r"^([A-Z][A-Z0-9])\s*-\s?(.*)$", line)
        if not m:
            continue
        tag, val = m.group(1), m.group(2).strip()
        if tag == "TY" and cur:
            recs.append(cur)
            cur = {}
        cur[{"DO": "doi", "AN": "pmid", "TI": "title", "T1": "title"}.get(tag, tag)] = val
    if cur:
        recs.append(cur)
    return recs


def load(path):
    if path.suffix.lower() == ".ris":
        return None, read_ris(path)
    head, rows = read_csv_like(path)
    return head, rows


def key_of(row):
    d, p = norm_doi(pick(row, DOI_KEYS)), norm_pmid(pick(row, PMID_KEYS))
    if d:
        return ("doi", d)
    if p:
        return ("pmid", p)
    t = norm_title(pick(row, TITLE_KEYS))
    if len(t) >= MIN_TITLE:
        return ("title", t)
    return None


def main():
    ap = argparse.ArgumentParser(description="文献列表去重")
    ap.add_argument("refs")
    ap.add_argument("--out", default=None, help="去重结果写到哪里（CSV）")
    a = ap.parse_args()

    path = pathlib.Path(a.refs)
    head, rows = load(path)
    print(f"dedupe_refs · {path.name} · 读入 {len(rows)} 条")

    groups, order, nokey = {}, [], 0
    for r in rows:
        k = key_of(r)
        if k is None:
            nokey += 1
            k = ("__nokey__", f"#{nokey}")
        if k not in groups:
            groups[k] = []
            order.append(k)
        groups[k].append(r)

    merged = sum(len(v) - 1 for v in groups.values())
    print(f"  唯一 {len(groups)} 条 · 去重 {merged} 条"
          + (f" · {nokey} 条缺 DOI/PMID 且标题过短，按原样保留" if nokey else ""))

    for k in order:
        v = groups[k]
        if len(v) < 2:
            continue
        kind = {"doi": "DOI", "pmid": "PMID", "title": "归一化标题"}.get(k[0], "无键")
        print(f"\n  [{kind}] {k[1][:60]}")
        for i, r in enumerate(v):
            mark = "留" if i == 0 else "并"
            print(f"    {mark} {pick(r, TITLE_KEYS)[:70]}")

    dupes = [k for k in order if len(groups[k]) > 1]
    if dupes:
        print("\n  ⚠️ 以上是**候选**。标题相近的不同版本（预印本 / 正式版 /"
              "\n     会议摘要）不是重复——最后一道仍由人过。")

    if a.out:
        keep = [groups[k][0] for k in order]
        out = pathlib.Path(a.out)
        cols = list(keep[0].keys())
        with open(out, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            for r in keep:
                w.writerow({c: r.get(c, "") for c in cols})
        print(f"\n  ✍️ 已写 {out}（保留每组第一条）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
