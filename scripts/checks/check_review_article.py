# -*- coding: utf-8 -*-
"""check_review_article.py —— 综述文章的自洽机检（审稿意见检查见 check_review.py）

【背景】
    2026-08-08 一份真实核稿报告点了三条高优先问题，其中第 1 条是：

        🔴 标题自称「系统综述」，但**零方法学透明性**
           （无检索策略 / 无纳排标准 / 无质量评价流程，PRISMA 视角全部缺失）
           风险：任何系统综述审稿人第一轮就质疑「系统性何在」

    作者随后自行改为《…叙述性整合综述》并补了「方法与范围」节。
    作者写综述不止一篇（TRS / 致幻剂 / 焦虑症…），同一类问题会重复出现。

【查什么】
    R1（硬）**自称与配置自洽**：标题或摘要自称「系统综述 / 荟萃分析 / 范围综述」
           → 文档里必须有方法学要素；没有就是「名不副实」。
    R2（软）**未定项计数**：正文标了「待核 / 未获取全文 / 厂商 / 公司公布」的处数
           ——**只报数，不判**。投稿前你自己确认它们都标了来源等级。

【它不查什么】
    ① 正文 `[n]` ↔ 文末编号表 的**双向核对** → 用 `check_ref_citations.py`（质量核查④）
    ② 同一编号两处数字打架 → 语义，人工过
    ③ 「这段该不该这么写」→ 判断，不设检查

【R1 的判据】
    它查的是**文档自己声明的性质**与**文档自己的结构**之间矛不矛盾——
    同源自洽（跟成果台账查「署名 ↔ 位次」是一类），不是从词猜文体。

用法：
    python check_review_article.py <综述.md | 目录>

退出码 = R1 命中条数（软提示不进退出码）
"""
import argparse
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── R1 ────────────────────────────────────────────────────────
# 自称需要方法学透明性的名头
SELF_CLAIM = re.compile(
    r"系统(性)?综述|系统评价|systematic\s+review|meta[\s-]?analysis|荟萃分析|元分析"
    r"|范围综述|scoping\s+review",
    re.I,
)
# ⚠️ 摘要里出现「荟萃分析」**几乎都是在引用别人**——
#    「网络荟萃分析显示奥氮平…最差」「86 项 RCT、13 万余人荟萃分析未发现…」
#    这是综述摘要的常态，**不是自称**。实测：不加这条限制，20 篇真稿误报 3 篇。
#    故摘要只在**自我描述**句式下才算自称：本文/本综述 + 系/为/是/采用 + 名头。
SELF_DESC = re.compile(
    r"本(?:文|综述|研究|评价)\s*(?:系|为|是|采用|遵循|依据|按照)\s*(?:一项|一个)?\s*"
    r"(?:系统(?:性)?综述|系统评价|荟萃分析|元分析|范围综述)",
    re.I,
)
# 方法学要素（标题级）
METHOD_HEAD = re.compile(r"^#{1,6}[^\n]*?(方法|检索|纳入|排除|纳排|PRISMA)", re.M | re.I)
# 方法学要素（正文词组）
METHOD_PHRASES = [
    r"检索策略", r"检索式", r"检索来源", r"文献检索", r"纳[入排].{0,4}标准",
    r"排除标准", r"纳入与排除", r"PRISMA", r"去重", r"分级标准", r"证据评价",
]
# 标题行
TITLE = re.compile(r"^#\s+(.+)$", re.M)
ABSTRACT = re.compile(r"\*\*摘要\*\*\s*[:：](.{0,800})", re.S)

# ── R2（软）───────────────────────────────────────────────────
PENDING = re.compile(r"待核|未获取全文|全文待核|厂商|公司公布|新闻稿|企业发布")


def has_methods(text):
    """方法学透明性：有方法类标题，或正文出现 ≥2 个方法学词组。"""
    if METHOD_HEAD.search(text):
        return True
    hits = sum(1 for p in METHOD_PHRASES if re.search(p, text, re.I))
    return hits >= 2


def check(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    hits, softs = [], []

    m = TITLE.search(text)
    title = m.group(1) if m else ""
    am = ABSTRACT.search(text)
    abstract = am.group(1) if am else ""

    claim, where = SELF_CLAIM.search(title), "标题"
    if not claim:
        claim, where = SELF_DESC.search(abstract), "摘要（自我描述）"
    if claim and not has_methods(text):
        hits.append(
            f"R1 {where}自称「{claim.group(0)}」，但全文找不到方法学要素"
            f"（检索策略 / 纳排标准 / PRISMA 任一）——**名不副实**。"
            f"要么补方法节，要么把名头降为「叙述性综述」"
        )

    # 按**行**计，不按词计——一行里既写「厂商」又写「待核」是**一处**标注，不是两处
    pend_lines = [ln for ln in text.splitlines() if PENDING.search(ln)]
    if pend_lines:
        softs.append(f"R2 有 {len(pend_lines)} 行标了「待核 / 未定来源」——"
                     f"投稿前逐行确认其来源等级（尤其**厂商数据**不得当核心证据）")
    return hits, softs


def main():
    ap = argparse.ArgumentParser(description="综述文章自洽机检")
    ap.add_argument("path")
    a = ap.parse_args()
    p = pathlib.Path(a.path)

    files = [p] if p.is_file() else sorted(p.rglob("*综述*.md"))
    total, softs = 0, []
    print(f"check_review_article · {a.path} · 扫 {len(files)} 个文件")
    if not files:
        print("  ○ 没找到文件名含「综述」的 .md——本次未评")
    for f in files:
        hits, soft = check(f)
        softs += [f"{f.name}：{s}" for s in soft]
        for h in hits:
            print(f"  ❌ {f.name} · {h}")
        total += len(hits)
    for s in softs:
        print(f"  ○ {s}")
    if not total:
        print("  ✅ 自称与配置自洽（R1 过）")
    print(f"\n  共 {total} 处硬问题。⚠️ R2 只报数不判——来源等级由你定。")
    print("  ⚠️ 正文 [n] ↔ 文末编号表 的双向核对**不在这里**，跑 check_ref_citations.py。")
    return total


if __name__ == "__main__":
    raise SystemExit(main())
