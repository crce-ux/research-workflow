# -*- coding: utf-8 -*-
"""check_data 的规则测试。

最值钱的是 D4：**标了「偏离」的行，原因与批准人不得为空**——
这条纪律是「偏离本身不致命，不记录才致命」的机检版。
D2 另锁「四类缺失不许合并」。
"""
import pathlib

import check_data as cd


def P(name):
    return pathlib.Path(name)


VAR_OK = """# 变量字典
| 字段名 | 含义 | 类型 | 取值域 | 缺失码 | 来源 | 对应假设 |
|---|---|---|---|---|---|---|
| panss_total_bl | PANSS 总分基线 | 连续 | 30–210 | -9 未评 / -8 不适用 | 量表表 | H1 |

缺失码四类：未评 -9 / 不适用 -8 / 失访 -7 / 拒答 -6
"""

SAP_OK = """# SAP 偏离记录
| 假设编号 | SAP 原定方法 | 实际执行方法 | 是否一致 | 原因 | 何时决定 | 批准 |
|---|---|---|---|---|---|---|
| H1 | MMRM | MMRM | 一致 | - | - | - |
| H2 | 多重插补 | 完整案例 | ⚠️ 偏离 | 某组 n<10，插补不稳定 | 2026-09-30 锁库前 | 统计师王 X |
"""


def test_d1_vardict_complete():
    assert cd.d1_vardict(VAR_OK, P("变量字典_TRS.md")) == []


def test_d1_vardict_missing_column():
    assert cd.d1_vardict(VAR_OK.replace("| 取值域 ", "| "), P("变量字典_TRS.md"))


def test_d2_missing_types_all_four():
    assert cd.d2_missing_types(VAR_OK, P("变量字典_TRS.md")) == []


def test_d2_missing_types_incomplete():
    bad = VAR_OK.replace("失访 -7 / 拒答 -6", "")
    hits = cd.d2_missing_types(bad, P("变量字典_TRS.md"))
    assert hits and "失访" in hits[0]


def test_d3_sap_cols_complete():
    assert cd.d3_sap_cols(SAP_OK, P("SAP_偏离记录.md")) == []


def test_d3_sap_cols_missing():
    assert cd.d3_sap_cols(SAP_OK.replace("| 批准 |", "| 备注 |"), P("SAP_偏离记录.md"))


def test_d3_needs_when_decided():
    """⭐ 是**七**列。「谁批准」与「何时决定」是两件事——
    事后补记的偏离与当场记录的偏离，可信度不同。漏「何时决定」要报出来。"""
    bad = SAP_OK.replace("| 何时决定 ", "| ")
    hits = cd.d3_sap_cols(bad, P("SAP_偏离记录.md"))
    assert hits and "何时决定" in hits[0]


def test_d4_deviation_row_must_be_filled():
    """标了偏离，但原因与批准人空着——这是代价最大的失误。"""
    bad = SAP_OK.replace("| ⚠️ 偏离 | 某组 n<10，插补不稳定 | 2026-09-30 锁库前 | 统计师王 X |",
                         "| ⚠️ 偏离 |  |  |  |")
    hits = cd.d4_deviation_filled(bad, P("SAP_偏离记录.md"))
    assert hits and "偏离" in hits[0]


def test_d4_clean_row_is_fine():
    assert cd.d4_deviation_filled(SAP_OK, P("SAP_偏离记录.md")) == []


def test_d4_aligned_rows_with_dash_are_ok():
    """一致的行用「-」占位是正常的，不能报空。"""
    assert cd.d4_deviation_filled(SAP_OK, P("SAP_偏离记录.md")) == []


def test_d5_p_without_ci():
    text = "# 结果报告\n\n两组差异有统计学意义，p=0.03。"
    hits = cd.d5_reporting(text, P("结果报告_模块A.md"))
    assert hits and "95%CI" in hits[0]


def test_d5_p_with_ci_passes():
    text = "# 结果报告\n\n两组差异 −1.36（95%CI −2.58 ~ −0.14，p=0.03）。"
    assert cd.d5_reporting(text, P("结果报告_模块A.md")) == []


def test_trigger_is_filename_based():
    """讲这些事的文档不该被当成它本身——实测过《数据与统计分析流程》手册会中招。"""
    text = "# 数据与统计分析流程\n\n变量字典要有缺失码；SAP 偏离要记录。p 值之外还要报 95%CI。"
    for fn in (cd.d1_vardict, cd.d2_missing_types, cd.d3_sap_cols,
               cd.d4_deviation_filled, cd.d5_reporting):
        assert fn(text, P("数据与统计分析流程.md")) == []


def test_missing_types_under_other_filename_is_ignored():
    """D2 只在变量字典上触发。"""
    assert cd.d2_missing_types("未评 不适用 失访 拒答", P("随手记.md")) == []
