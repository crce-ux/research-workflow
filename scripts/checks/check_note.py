# -*- coding: utf-8 -*-
"""check_note.py —— 精读笔记的结构与口径机检

【背景】
    `paper-reading` 的核心是**证据标签五态**——每条断言标出它是「论文说的」
    还是「我推断的」。但标签靠自觉：不查它，就会退化成「写了但没人标」；
    不标时默认按 [Paper] 算。

【它查什么】
    N1  必备字段（PMID / DOI / 年份 / 期刊 / 标签 / 阅读深度 / 定位方式）
    N2  至少用过一次证据标签
    N3  ★ **定位方式与引用形式必须一致**（本脚本最重要的一条）——
          标了 `source-limited`（仅摘要）却引用 `Table 2` 或 `PDF p.3` = **越界**
          （摘要里没有表格页码，属编造）
          标了 `structure-grounded` 却写 `PDF p.N` = 假精确
    N4  （软）没带标签的断言行——只报数，不拦

【它不查什么】
    标签**标得对不对**（这句到底算不算 [Analysis]）——语义，人工过。
    它只查「有没有标」与「引用形式和声明的可得性一致吗」。

用法：
    python check_note.py <精读笔记.md> [--dir <目录>]

退出码 = 硬命中条数（0 = 全过）
"""
import argparse
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ⚠️ 必备项按**信息**找，不按**字段名**找。
# 实测教训：真实笔记把「年份 / 期刊」放在 `**原文**：<完整引用>` 行上，
# 按字段名找会误报「缺 年份 / 期刊」——信息明明在，只是组织方式不同。
# 所以只留三项真正无法从别处推出的：标识符、阅读深度、定位方式。
REQUIRED = ["标识符", "阅读深度", "定位方式"]
LABELS = ("Paper", "External", "Analysis", "Hypothesis", "User")
LABEL_RE = re.compile(r"\[(" + "|".join(LABELS) + r")(?:\s*:[^\]]*)?\]")
# 既有的来源等级标记——真实笔记用 🟢/🟡/🔴 标来源可信度。
# ⚠️ 来源等级标记是**可信度轴**，五态标签是**归属轴**（谁说的）——两条不同的轴，都要认。
EMOJI_RE = re.compile(r"[🟢🟡🔴]")

# 可得性声明（正文式）——比字段更详细时也算数
AVAIL_DECL = re.compile(r"全文未获取|全文获取|仅摘要|来源[^｜|\n]{0,24}全文")

# 引用形式：越界判据
CITE_PAGE = re.compile(r"PDF\s*p\.\s*\d+|(?<![\w.])p\.\s*\d+", re.I)
CITE_TABLE = re.compile(r"\bTable\s*\d+|\bTab\.\s*\d+|表\s*\d+", re.I)
CITE_FIG = re.compile(r"\bFig(?:ure)?\.?\s*\d+|\b图\s*\d+", re.I)
CITE_LINE = re.compile(r"\bLine\s*\d+|第?\s*\d+\s*行", re.I)

# 深度 / 定位方式里的"仅摘要"类取值
SHALLOW = re.compile(r"摘要|abstract", re.I)
LOC_MODE = {
    "page": re.compile(r"page-grounded", re.I),
    "structure": re.compile(r"structure-grounded", re.I),
    "limited": re.compile(r"source-limited", re.I),
}

# 断言行：列表项 / 表格行 / 带冒号的短行——可能是断言
CLAIM_LINE = re.compile(r"^\s*(?:[-*+]\s+|\|\s*\S|\d+\.\s+)")


def field_of(text, key):
    m = re.search(rf"\*\*{key}\*\*\s*[:：]\s*(.+)", text)
    return m.group(1).strip() if m else None


def _label(name):
    """匹配「字段名 + 任意星号 + 冒号」。

    ⚠️ 必须容忍中间的 `**`：真实笔记写的是 `**精读方式**：全文精读`，
    而 `方式\\s*[:：]` 匹配不上（中间隔着 `**`）——实测踩过，报了一堆假阳性。
    """
    return re.compile(rf"\*{{0,2}}{name}\*{{0,2}}\s*[:：]")


IDENT_DOI = re.compile(r"\b10\.\d{4,}/\S+")
IDENT_PMID = re.compile(r"PMID\D{0,8}\d{4,}", re.I)


def required_status(text):
    """按**信息**找必备项，不按**字段名**找。返回 {项: 是否齐}。

    实测教训：真实笔记把年份/期刊放在 `**原文**：<完整引用>` 里、
    把深度写成 `**精读方式**：`、把 PMID 写在散文里 `（PMID 38626948）`。
    按字段名找会把**信息明明在**的条报成缺。
    """
    head = text[:1500]
    return {
        # 标识符：PMID 或 DOI 至少一个（综述也应有 DOI）
        "标识符": bool(IDENT_PMID.search(text) or IDENT_DOI.search(text)),
        # 可得性声明：字段式（阅读深度 / 精读方式 / 方式），
        # 或正文里更详细的声明（「全文未获取」「来源：…全文」）
        "阅读深度": bool(_label("阅读深度").search(head) or _label("精读方式").search(head)
                      or _label("方式").search(head)
                      or AVAIL_DECL.search(text)),
        # 定位方式：新概念，无既等价物
        "定位方式": bool(_label("定位方式").search(head)),
    }


def check(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    hits, soft = [], []

    # ── N1 必备信息（按信息找，不按字段名找）────────────────
    st = required_status(text)
    miss = [k for k in REQUIRED if not st[k]]
    if miss:
        hits.append(f"N1 缺必备信息：{' / '.join(miss)}")

    # ── N2 用过标签吗（五态 或 既有的来源等级标记）─────────
    n_label = len(LABEL_RE.findall(text))
    n_emoji = len(EMOJI_RE.findall(text))
    if n_label == 0 and n_emoji == 0:
        hits.append("N2 通篇没有任何标注——**不标时默认按论文原话处理**，"
                    "推断的话会被当成文献支持")
    elif n_label == 0:
        # 有来源等级标记，但没有归属标记——两轴只覆盖了一轴
        soft.append(f"N2 用了 {n_emoji} 处来源等级（🟢🟡🔴，可信度轴），"
                    f"但没有归属标记（[Analysis]/[Hypothesis]/[User]）——"
                    f"**「我推断的」仍与「论文说的」分不出来**")

    # ── N3 定位方式 vs 引用形式（最重要的一条）─────────────
    loc = field_of(text, "定位方式") or ""
    depth = field_of(text, "阅读深度") or ""
    mode = None
    for name, pat in LOC_MODE.items():
        if pat.search(loc):
            mode = name
            break
    limited_by_depth = bool(SHALLOW.search(depth)) and "全文" not in depth

    # 在全篇找引用串（含写在标签里的，如 `[Paper: PDF p.3]`；
    # 写在标签里的引用也是 source-limited 下要抓的越界写法）
    cites = {
        "页码": CITE_PAGE.findall(text),
        "表": CITE_TABLE.findall(text),
        "图": CITE_FIG.findall(text),
        "行号": CITE_LINE.findall(text),
    }
    cites = {k: v for k, v in cites.items() if v}

    if mode == "limited" or limited_by_depth:
        why = "标了 source-limited" if mode == "limited" else f"阅读深度是「{depth}」"
        if cites:
            detail = "、".join(f"{k}×{len(v)}（如 {v[0]}）" for k, v in cites.items())
            hits.append(f"N3 {why}，却出现了精确引用：{detail}——"
                        f"摘要里没有页码与表格，**出现精确引用就是在编**")
    elif mode == "structure":
        if CITE_PAGE.findall(text):
            hits.append(f"N3 标了 structure-grounded（页码不可靠），"
                        f"却写了页码引用（{CITE_PAGE.findall(text)[0]}）——假精确")

    # ── N4（软）没带标签的断言行 ───────────────────────────
    claims, unlabeled = 0, 0
    for line in text.splitlines():
        if not CLAIM_LINE.match(line) or len(line.strip()) < 25:
            continue
        claims += 1
        if not LABEL_RE.search(line):
            unlabeled += 1
    if claims and unlabeled:
        soft.append(f"N4 {unlabeled}/{claims} 条断言行没带标签"
                    f"（标签可写在行末，供日后判断哪条能直接引）")

    return hits, soft


def main():
    ap = argparse.ArgumentParser(description="精读笔记结构与口径机检")
    ap.add_argument("path", help="笔记文件，或 --dir 时的目录")
    ap.add_argument("--dir", action="store_true", help="按目录扫「精读笔记_*.md」")
    a = ap.parse_args()

    p = pathlib.Path(a.path)
    if a.dir or p.is_dir():
        files = sorted(p.rglob("精读笔记_*.md"))
        if not files:
            print(f"check_note · {a.path} · 未找到「精读笔记_*.md」——"
                  f"按命名约定找，不是按内容找")
            return 0
    else:
        files = [p]

    total, per_rule = 0, {}
    print(f"check_note · {a.path} · 扫 {len(files)} 篇")
    for f in files:
        hits, soft = check(f)
        for h in hits:
            print(f"  ❌ {f.name}：{h}")
            per_rule[h.split(" ")[0]] = per_rule.get(h.split(" ")[0], 0) + 1
        for s in soft:
            print(f"  ○ {f.name}：{s}")
        total += len(hits)

    # 同一组规则命中绝大多数文件时，多半是**格式迁移**而非逐篇缺陷——
    # 报一遍就够，不必刷 N 屏（否则会掩盖只出在个别篇上的问题）。
    for rule, n in sorted(per_rule.items()):
        if len(files) >= 3 and n >= len(files) * 0.8:
            print(f"\n  ⚠️ 汇总：{n}/{len(files)} 篇都命中 {rule}——"
                  f"更像**尚未迁移到新格式**，不是逐篇出错，先看 {rule} 这条规则。")

    if not total:
        print("  ✅ 全过（三组硬规则）")
    print(f"\n  共 {total} 处。⚠️ 只查「有没有标」，不查「标得对不对」。")
    return total


if __name__ == "__main__":
    raise SystemExit(main())
