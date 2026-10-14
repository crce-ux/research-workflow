# -*- coding: utf-8 -*-
"""check_review_article 的规则测试。

锁的是 2026-08-08 核稿报告点名的第 1 条：
**标题自称「系统综述」却零方法学透明性**——名不副实。
"""
import pathlib

import check_review_article as cra


def run(text, tmp_path):
    p = pathlib.Path(tmp_path) / "某综述.md"
    p.write_text(text, encoding="utf-8")
    return cra.check(p)


def test_systematic_claim_without_methods_fires(tmp_path):
    """他踩过的坑：标题说系统综述，全文没有检索策略/纳排/PRISMA。"""
    hits, _ = run("# 精神分裂症体重管理：系统综述\n\n引言……\n\n## 一、引言\n一堆内容。\n",
                  tmp_path)
    assert any("R1" in h and "系统综述" in h for h in hits)


def test_systematic_claim_with_methods_passes(tmp_path):
    hits, _ = run(
        "# 某病：系统综述\n\n## 一、引言\n\n## 二、方法\n### 检索策略\n"
        "本文检索 PubMed 与 Google，纳入随机对照试验，排除会议摘要，经去重后统一编号。\n",
        tmp_path)
    assert hits == []


def test_narrative_review_needs_no_methods(tmp_path):
    """叙述性综述**不**要求 PRISMA 的成套要素——不报。"""
    hits, _ = run("# 某病研究进展：叙述性综述\n\n## 一、引言\n随便写写。\n", tmp_path)
    assert hits == []


def test_abstract_claim_counts_too(tmp_path):
    """名头写在**摘要**里也算——不只查标题。"""
    hits, _ = run(
        "# 某病研究进展\n\n**摘要**：本文是一项荟萃分析，纳入 12 项 RCT……\n\n## 一、引言\n",
        tmp_path)
    assert any("R1" in h and "摘要" in h for h in hits)


def test_citing_meta_analysis_in_abstract_is_not_a_self_claim(tmp_path):
    """⭐ 实测误报源：综述摘要里出现「荟萃分析」几乎都是在**引用别人**。

    「网络荟萃分析显示奥氮平代谢副作用谱最差」——这是引用，不是本文自称。
    不加这条限制，20 篇真稿误报 3 篇。
    """
    hits, _ = run(
        "# GLP-1 受体激动剂在精神分裂症体重管理中的应用：研究进展综述\n\n"
        "**摘要**：…系统综述与网络荟萃分析显示，司美格鲁肽减重约 6–11 kg；"
        "86 项 RCT、13 万余人荟萃分析未发现风险增加…\n\n## 一、引言\n",
        tmp_path)
    assert hits == []


def test_method_heading_alone_suffices(tmp_path):
    hits, _ = run("# 某病：系统综述\n\n## 二、纳入与排除\n本文……\n", tmp_path)
    assert hits == []


def test_scoping_review_claim_is_covered(tmp_path):
    hits, _ = run("# 某病范围综述\n\n## 一、引言\n", tmp_path)
    assert any("R1" in h for h in hits)


def test_pending_items_are_soft_not_hard(tmp_path):
    hits, soft = run(
        "# 某病：系统综述\n\n## 二、方法\n### 检索策略\n检索 PubMed，纳入 RCT。\n\n"
        "## 三、结果\n某药数据（厂商公布，待核）\n另处（未获取全文）\n",
        tmp_path)
    assert hits == []
    # 按**行**计：两行各有一处标注 → 2；同一行里的「厂商」+「待核」只算一处
    assert any("R2" in s and "2 行" in s for s in soft)


def test_no_title_does_not_crash(tmp_path):
    hits, _ = run("没有标题的一段话。\n", tmp_path)
    assert hits == []
