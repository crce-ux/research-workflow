# -*- coding: utf-8 -*-
"""check_credit.py —— 成果台账的署名自洽机检

【为什么有它】
    成果台账本文件 §八「待建」里点名要这一条：

        **兜底校验：位次与署名情况是否自洽**
        （如「共同第一作者」但位次写 3）

    NSFC 明文要求「如实标注本人署名情况」，**不得改变作者排序含义**。
    台账是**唯一出处**——抄错一次，简历上就是虚假标注。

【查什么】
    C1 署名情况 ∈ 六种枚举
    C2 ⭐ **署名情况与位次自洽**
    C3 **三个数字齐**（作者总数 / 我的位次 / 署名情况）
    C4 状态 ∈ 四种枚举

【它不查什么】
    「这项成果该不该算你的」——语义，人工过。
    它只查台账**自己写下的几列之间**有没有互相矛盾。

用法：
    python check_credit.py <成果台账.md>

退出码 = 命中条数（0 = 全过）
"""
import argparse
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CREDIT_ENUM = ["唯一第一作者", "共同第一作者", "唯一通讯作者", "共同通讯作者"]
STATUS_ENUM = ["已发表", "已接收", "在投", "在写"]
PLACEHOLDER = re.compile(r"^\s*[—\-*（(]|待填|^$")

# 表头须同时含这两个词，才认作论文表
HEAD_MARKS = ("署名情况", "我的位次")


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def is_sep(cs):
    return bool(cs) and all(set(c) <= set("-: ") for c in cs)


def find_paper_table(text):
    """返回 (表头列名, [数据行…])。按表头找，不按位置找。"""
    rows, header = [], None
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cs = cells(line)
        if header is None:
            if all(m in " ".join(cs) for m in HEAD_MARKS):
                header = cs
            continue
        if is_sep(cs) or all(set(c) <= set("-: ") for c in cs):
            continue
        if len(cs) == len(header):
            rows.append(cs)
    return header, rows


def credit_kind(val):
    """把署名情况归类：一作 / 通讯 / 其他 / 按姓氏 / 不合法。"""
    v = re.sub(r"\s", "", val)
    if not v or PLACEHOLDER.search(v):
        return None
    if "按姓氏排序" in v:
        return "姓氏"
    if "第一作者" in v:
        return "一作"
    if "通讯作者" in v:
        return "通讯"
    if re.search(r"其他|第\s*\d+\s*作者", v):
        return "其他"
    return "非法"


def check(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    header, rows = find_paper_table(text)
    hits, evaluated = [], 0

    if header is None:
        return [], ["未找到含「署名情况」「我的位次」的论文表——本次未评"]

    i_status = next((i for i, h in enumerate(header) if "状态" in h), None)
    i_title = next((i for i, h in enumerate(header) if "标题" in h or "题名" in h), None)
    i_credit = next((i for i, h in enumerate(header) if "署名情况" in h), None)
    i_total = next((i for i, h in enumerate(header) if "作者总数" in h), None)
    i_rank = next((i for i, h in enumerate(header) if "位次" in h), None)

    for r, cs in enumerate(rows, 1):
        title = cs[i_title].strip() if i_title is not None else ""
        if not title or PLACEHOLDER.search(title):
            continue                       # 模板占位行，跳过
        evaluated += 1
        label = title[:24]

        credit = cs[i_credit].strip() if i_credit is not None else ""
        total = cs[i_total].strip() if i_total is not None else ""
        rank = cs[i_rank].strip() if i_rank is not None else ""

        # C4 状态枚举
        if i_status is not None:
            st = cs[i_status].strip()
            if st and not any(s in st for s in STATUS_ENUM):
                hits.append(f"C4 第 {r} 行「{label}」：状态「{st}」不在四态枚举内"
                            f"（{'/'.join(STATUS_ENUM)}）")

        kind = credit_kind(credit)

        # C1 署名枚举
        if kind == "非法":
            hits.append(f"C1 第 {r} 行「{label}」：署名情况「{credit}」不在六种枚举内"
                        f"（{'/'.join(CREDIT_ENUM)} / 其他（第 N 作者）/ 按姓氏排序）")
            continue

        # C3 三个数字齐
        if kind and kind != "姓氏":
            miss = [n for n, v in (("作者总数", total), ("我的位次", rank))
                    if not v or PLACEHOLDER.search(v)]
            if not credit or PLACEHOLDER.search(credit):
                miss.insert(0, "署名情况")
            if miss:
                hits.append(f"C3 第 {r} 行「{label}」：缺 {' / '.join(miss)}——"
                            f"**只写署名不写作者总数，还原不出真实贡献**"
                            f"（2 人中的第一 ≠ 20 人中的第一）")
                continue

        # C2 ⭐ 署名情况与位次自洽
        if kind in (None, "姓氏") or not rank.isdigit() or not total.isdigit():
            continue
        rk, tt = int(rank), int(total)
        if kind == "一作" and rk != 1:
            hits.append(f"C2 第 {r} 行「{label}」：署名是「{credit}」，位次却写 {rk}——"
                        f"第一作者位次必须为 1")
        elif kind == "通讯" and rk < tt - 1:
            hits.append(f"C2 第 {r} 行「{label}」：署名是「{credit}」，位次 {rk}/{tt}——"
                        f"通讯作者应排在末位（共同通讯允许倒数第二）")
        elif kind == "其他":
            m = re.search(r"第\s*(\d+)\s*作者", credit)
            if m and int(m.group(1)) != rk:
                hits.append(f"C2 第 {r} 行「{label}」：写「其他（第 {m.group(1)} 作者）」，"
                            f"位次却是 {rk}——两处对不上")
            elif rk == 1:
                hits.append(f"C2 第 {r} 行「{label}」：署名归入「其他」，位次却是 1——"
                            f"位次第一就该是第一作者类")

    # ⚠️ 一行有效数据都没有时，「全过」是假象——那是「没得评」，不是「评过了」
    if evaluated == 0:
        return hits, [f"论文表有 {len(rows)} 行，但**全是占位行**——本次未评，"
                      f"不是查过了通过"]
    return hits, []


def main():
    ap = argparse.ArgumentParser(description="成果台账署名自洽机检")
    ap.add_argument("path")
    a = ap.parse_args()
    p = pathlib.Path(a.path)

    files = [p] if p.is_file() else sorted(p.rglob("*成果台账*.md"))
    total, softs = 0, []
    print(f"check_credit · {a.path} · 扫 {len(files)} 个文件")
    for f in files:
        hits, soft = check(f)
        softs += [f"{f.name}：{s}" for s in soft]
        for h in hits:
            print(f"  ❌ {f.name} · {h}")
        total += len(hits)
    for s in softs:
        print(f"  ○ {s}")
    unevaluated = any("未评" in s for s in softs)
    if not total:
        print("  ⚠️ 本次未评——不是查过了通过" if unevaluated
              else "  ✅ 已评的表全过（三组硬规则）")
    print(f"\n  共 {total} 处。⚠️ 只查台账自己几列之间矛不矛盾，不查成果该不该算你的。")
    return total


if __name__ == "__main__":
    raise SystemExit(main())
