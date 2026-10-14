# -*- coding: utf-8 -*-
"""check_vault 的规则测试。

九组规则一组一个「会响」的用例——否则某组可能写了正则却永远匹配不上。
命名类只吃文件名，用 pathlib 造假路径即可；结构类吃正文，直接喂字符串。
"""
import pathlib

import check_vault as cv


def P(name, parent="工作区"):
    return pathlib.Path(parent) / name


# ── 命名类 ─────────────────────────────────────────────

def test_n1_good_name_passes():
    assert cv.n1_jingdu_name(P("精读笔记_Altar1986_氯氮平抵抗.md")) == []


def test_n1_missing_year_is_flagged():
    assert cv.n1_jingdu_name(P("精读笔记_氯氮平.md"))


def test_n1_other_file_untouched():
    assert cv.n1_jingdu_name(P("普通笔记.md")) == []


def test_n2_final_with_date_is_flagged():
    assert cv.n2_final_name(P("毕业论文终稿_20261013.md"))


def test_n2_final_without_date_passes():
    assert cv.n2_final_name(P("毕业论文终稿.md")) == []


def test_n2_draft_with_date_is_fine():
    """过程稿带日期——正是规范要求的，不能误报。"""
    assert cv.n2_final_name(P("初稿_20261013.md")) == []


def test_n3_adr_bad_name():
    assert cv.n3_adr_name(P("并入E盘材料.md", parent="决策记录"))


def test_n3_adr_good_name():
    assert cv.n3_adr_name(P("0008-科研库并入E盘材料.md", parent="决策记录")) == []


def test_n3_not_in_decision_dir():
    assert cv.n3_adr_name(P("随便.md")) == []


# ── 结构类 ─────────────────────────────────────────────

GOOD_LOG = """---
title: TRS_EEG 工作日志
tags: [科研]
project: TRS_EEG
type: log
created: 2026-10-01
---

项目：TRS_EEG
索引：_MOC
起始：2026-09
规则：最新在最上

## 2026-10-13
今天入组 2 例。

## 2026-10-07
落地计划 v2。
"""


def test_s1_good_log_passes():
    assert cv.s1_worklog(GOOD_LOG, P("TRS_EEG工作日志.md")) == []


def test_s1_missing_frontmatter_field():
    bad = GOOD_LOG.replace("created: 2026-10-01\n", "")
    assert any("created" in m for m in cv.s1_worklog(bad, P("TRS_EEG工作日志.md")))


def test_s1_out_of_order_entries():
    reversed_log = GOOD_LOG.replace(
        "## 2026-10-13\n今天入组 2 例。\n\n## 2026-10-07\n落地计划 v2。",
        "## 2026-10-07\n落地计划 v2。\n\n## 2026-10-13\n今天入组 2 例。",
    )
    assert cv.s1_worklog(reversed_log, P("TRS_EEG工作日志.md"))


def test_s1_only_applies_to_worklog():
    assert cv.s1_worklog("随便什么", P("日记.md")) == []


def test_s2_vardict_missing_column():
    text = "# 变量字典\n| 字段名 | 含义 | 类型 | 取值域 | 缺失码 |"
    assert cv.s2_vardict(text, P("变量字典_TRS_EEG.md"))


def test_s2_vardict_complete():
    text = "变量字典\n字段名 含义 类型 取值域 缺失码 来源 对应假设"
    assert cv.s2_vardict(text, P("变量字典_TRS_EEG.md")) == []


def test_s3_sap_deviation_complete():
    text = "SAP 偏离记录：假设编号 / 原定 / 实际 / 一致 / 原因 / 批准人"
    assert cv.s3_sap_deviation(text, P("SAP_TRS_EEG.md")) == []


def test_s3_sap_deviation_incomplete():
    assert cv.s3_sap_deviation("SAP 偏离记录：假设编号 / 原定", P("SAP_TRS_EEG.md"))


def test_s4_ai_declaration_complete():
    text = """AI 使用情况声明
工具与版本：Claude
时间范围：2026-09 至 2026-10
人工核实方式：逐条回原文核对
本文未使用 AI 直接生成正文。
"""
    assert cv.s4_ai_declaration(text, P("AI使用情况声明_某稿.md")) == []


def test_s4_ai_declaration_missing_verify():
    text = "AI 使用情况声明\n工具：Claude\n时间范围：2026-09\n本文未使用 AI 直接生成正文。"
    assert any("人工核实" in m for m in cv.s4_ai_declaration(text, P("AI使用情况声明_某稿.md")))





def test_s6_understanding_blank_cells_are_not_flagged():
    """清单里的空格是留给人手填的作答栏，不是缺陷——不查空白。"""
    text = "## 术语表\n| 术语 | 释义 | 我能不能解释 |\n|---|---|---|\n| TRS | 治疗抵抗 |  |\n\n## 未解决项\n无"
    assert cv.s6_understanding(text, P("理解确认清单.md")) == []


def test_s6_understanding_missing_unresolved_section():
    assert any("未解决项" in m for m in cv.s6_understanding(
        "## 术语表\n| TRS | 治疗抵抗 |", P("理解确认清单.md")))


def test_s6_understanding_clean():
    assert cv.s6_understanding("## 未解决项\n无", P("理解确认清单.md")) == []


def test_s6_only_applies_to_the_checklist_itself():
    """其他文档提到「理解确认清单」四个字不算——否则整库误报。"""
    assert cv.s6_understanding("参见理解确认清单", P("新版PPT_讲稿_20261012.md")) == []


def test_n3_readme_in_decision_dir_is_exempt():
    assert cv.n3_adr_name(P("README.md", parent="决策记录")) == []


def test_rules_registry_is_wired():
    """每条规则都得在 RULES 里登记，否则写了也不会被跑到。"""
    ids = {r[0] for r in cv.RULES}
    assert ids == {"N1", "N2", "N3", "S1", "S2", "S3", "S4", "S6"}
