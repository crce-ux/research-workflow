# -*- coding: utf-8 -*-
"""ledger_to_cv.py —— 成果台账 → NSFC 简历用的成果清单

【背景】
    成果台账文件 §八「待建」点名要的：
        ☐ 导出脚本：`成果台账.json` → 生成 NSFC 简历格式的成果列表

    NSFC 简历要的是「近五年主持或参加的项目 / 课题」+ 代表性论文，
    「项目 / 课题」与「代表性论文」这两样都要从台账里挑，不能整张贴过去。

【它做什么】
    1. 解析台账里的四张表（论文 / 基金项目 / 专利软著 / 会议报告）
    2. 按 `--years`（默认 5）筛近五年；**年份缺失的不筛掉，单列待补**
    3. 论文只导 `已发表 / 已接收`（`在投 / 在写` 归「进行中」）
    4. 论文按署名优先级排序：一作 → 共同一作 → 通讯 → 共同通讯 → 其他
    5. 输出 markdown，字段按 NSFC 简历所需排列

【它不做什么】
    - **不替你填职称**——NSFC 要求各时间段职称逐段写，台账里没有「职称」这个字段
    - **不判该不该算你的成果**——语义，人工过
    - **不生成最终版式**——输出是**字段齐备的清单**，套模板是你的事

用法：
    python ledger_to_cv.py <成果台账.md> [--years 5] [--out 清单.md]

退出码 0（只读不判）
"""
import argparse
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 表头识别词——按**信息**找表，不按位置找
TABLES = {
    "论文": ("标题", "署名情况"),
    "基金项目": ("项目名称", "角色"),
    "专利/软著": ("名称", "申请号/授权号"),
    "会议报告": ("会议", "题目"),
}

# 论文署名优先级（越小越靠前）
CREDIT_ORDER = [
    ("唯一第一作者", 0), ("共同第一作者", 1),
    ("唯一通讯作者", 2), ("共同通讯作者", 3),
]
PAPER_OK = ("已发表", "已接收")
PLACEHOLDER = re.compile(r"^\s*[—\-*（(]|待填|^$")
YEAR = re.compile(r"(19|20)\d{2}")


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def is_sep(cs):
    return bool(cs) and all(set(c) <= set("-: ") for c in cs)


def parse_tables(text):
    """返回 {类别: (表头, [行])}。按表头识别词找表，不按位置。"""
    out, header, cur = {}, None, None
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            header = None
            continue
        cs = cells(line)
        if header is None:
            for kind, marks in TABLES.items():
                if all(any(m in c for c in cs) for m in marks):
                    header, cur = cs, kind
                    out.setdefault(kind, (cs, []))
                    break
            continue
        if is_sep(cs) or len(cs) != len(header):
            continue
        if all(PLACEHOLDER.search(c) for c in cs):
            continue                       # 整行占位
        out[cur][1].append(cs)
    return out


def col(header, *keys):
    for i, h in enumerate(header):
        if any(k in h for k in keys):
            return i
    return None


def year_of(row, header):
    for k in ("年", "起止", "时间"):
        i = col(header, k)
        if i is None or i >= len(row):
            continue
        m = YEAR.search(row[i])
        if m:
            return int(m.group(0))
    return None


def credit_rank(credit):
    for name, r in CREDIT_ORDER:
        if name in credit:
            return r
    return 9


def recent(rows, header, years, today_year):
    """返回 (近五年行, 年份待补行)。"""
    lo = today_year - years + 1
    got, unknown = [], []
    for r in rows:
        y = year_of(r, header)
        if y is None:
            unknown.append(r)      # 年份缺失不筛掉——宁可多给，标注待补
        elif y >= lo:
            got.append(r)
    return got, unknown


def render(tables, years, today_year):
    title = (f"# 成果清单（近 {years} 年，{today_year - years + 1}– ）"
             if today_year < 9000 else "# 成果清单（未按年份筛——台账里没有年份）")
    L = [title, ""]
    L += ["", "> 由 `ledger_to_cv.py` 从成果台账导出。"
              "**职称栏与版式由你补**——台账里没有「职称」「版式」这两个字段。", ""]

    # 一、论文
    if "论文" in tables:
        header, rows = tables["论文"]
        i_st, i_ti = col(header, "状态"), col(header, "标题")
        i_cr = col(header, "署名情况")
        i_ra, i_to = col(header, "位次"), col(header, "作者总数")
        i_jn, i_dy = col(header, "期刊"), col(header, "DOI", "PMID")
        ok = [r for r in rows
              if i_st is None or any(s in r[i_st] for s in PAPER_OK)]
        got, unknown = recent(ok, header, years, today_year)
        got.sort(key=lambda r: credit_rank(r[i_cr] if i_cr is not None else ""))
        L += [f"## 一、代表性论文（{len(got)} 篇）", ""]
        for n, r in enumerate(got, 1):
            t = r[i_ti] if i_ti is not None else ""
            j = r[i_jn] if i_jn is not None else ""
            d = r[i_dy] if i_dy is not None else ""
            cr = r[i_cr] if i_cr is not None else ""
            rk = r[i_ra] if i_ra is not None else ""
            tt = r[i_to] if i_to is not None else ""
            L.append(f"{n}. **{t}**．{j}．{d}"
                     + (f"　〔{cr}，{rk}/{tt}〕" if cr else ""))
        if unknown:
            L += ["", "**年份待补（未筛，请人工判断是否在近五年内）**", ""]
            L += [f"- {r[i_ti] if i_ti is not None else r}" for r in unknown]
        n_inprog = len(rows) - len(ok)
        if n_inprog:
            L += ["", f"_另有 {n_inprog} 条状态为「在投 / 在写」——不进正式清单。_"]

    # 二、基金项目
    if "基金项目" in tables:
        header, rows = tables["基金项目"]
        got, unknown = recent(rows, header, years, today_year)
        i_n, i_s = col(header, "项目名称"), col(header, "来源")
        i_c, i_role = col(header, "编号"), col(header, "角色")
        i_t, i_m = col(header, "起止"), col(header, "经费")
        L += ["", f"## 二、主持或参加的项目 / 课题（{len(got)} 项）", ""]
        for n, r in enumerate(got, 1):
            nm = r[i_n] if i_n is not None else ""
            src = r[i_s] if i_s is not None else ""
            c = r[i_c] if i_c is not None else ""
            role = r[i_role] if i_role is not None else ""
            t = r[i_t] if i_t is not None else ""
            m = r[i_m] if i_m is not None else ""
            bits = "．".join(x for x in (src, c, t, m) if x and not PLACEHOLDER.search(x))
            L.append(f"{n}. **{nm}**（{bits}）．{role}")
        if unknown:
            L += ["", "**年份待补（未筛）**", ""]
            L += [f"- {r[i_n] if i_n is not None else r}" for r in unknown]

    # 三、其他
    others = [k for k in ("专利/软著", "会议报告") if k in tables]
    if others:
        L += ["", "## 三、其他成果", ""]
        for kind in others:
            header, rows = tables[kind]
            got, unknown = recent(rows, header, years, today_year)
            i_n = col(header, "名称", "题目")
            L += [f"### {kind}（{len(got)} 项）", ""]
            for n, r in enumerate(got, 1):
                L.append(f"{n}. " + "．".join(x for x in r if x and not PLACEHOLDER.search(x)))
            if unknown:
                L += ["", f"_年份待补：{len(unknown)} 项_"]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description="成果台账 → NSFC 简历用成果清单")
    ap.add_argument("ledger")
    ap.add_argument("--years", type=int, default=5, help="近 N 年（默认 5）")
    ap.add_argument("--today", type=int, default=None, help="基准年（默认取台账里最大的年份）")
    ap.add_argument("--out", help="落盘路径（默认打印）")
    a = ap.parse_args()

    p = pathlib.Path(a.ledger)
    if not p.is_file():
        print(f"❌ 找不到台账：{p}")
        return 2
    text = p.read_text(encoding="utf-8", errors="replace")
    tables = parse_tables(text)
    if not tables:
        print("❌ 没认出任何成果表——检查表头（论文需含「标题」「署名情况」）")
        return 2

    if a.today:
        base = a.today
    else:
        ys = [year_of(r, h) for h, rows in tables.values() for r in rows]
        ys = [y for y in ys if y]
        base = max(ys) if ys else 0
        if not base:
            print("⚠️ 台账里没有任何年份——本次无法按「近 N 年」筛，全部列出")
            base = 9999

    md = render(tables, a.years, base)
    if a.out:
        pathlib.Path(a.out).write_text(md, encoding="utf-8")
        print(f"✍️ 已写入 {a.out}")
    else:
        print(md)
    print("⚠️ 只导字段，不判「该不该算你的成果」，也不填职称——判成果与填职称由人工过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
