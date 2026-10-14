# -*- coding: utf-8 -*-
"""check_lit 的规则测试。

真实证据表（思路 A–D，共 62 条）硬规则全过，所以 E2–E5 没被真实数据碰到——
必须用**埋雷样本**测，否则规则是「从没跑过」的。
"""
import check_lit as cl

HDR = ("| 文献·DOI | 作者·年份 | 研究设计 | 人群 (P) | 干预/暴露 (I/E) | 对照 (C) | "
       "主要结局 (O) | 关键结果 | 局限 | 期刊 IF | 期刊分区 | 对本课题的意义 |")
SEP = "|" + "---|" * 12


def row(author="Li 2025", ctrl="NA", res="OR=1.2 (95%CI 1.0-1.4)",
        iff="7.9 (2024 JCR)", zone="中科院医学1区(2025) / JCR Q1"):
    return f"| Li 2025 | {author} | RCT | 患者 | 药 | {ctrl} | 疗效 | {res} | 局限 | {iff} | {zone} | 意义 |"


def evtab(*rows, title="## A0 锚点"):
    return "\n".join([title, HDR, SEP, *rows])


def hard(text):
    fails, _soft, _n = cl.check_evtab(text)
    return "\n".join(fails)


def soft(text):
    _f, s, _n = cl.check_evtab(text)
    return "\n".join(s)


# ── E1 十二列 ────────────────────────────────────────────────

def test_full_table_passes_hard_rules():
    assert hard(evtab(row())) == ""


def test_missing_column_is_flagged():
    assert "找不到 12 列证据表" in hard("| 文献·DOI | 作者·年份 |\n|---|---|\n| a | b |")


# ── E2 对照列空 → NA ─────────────────────────────────────────

def test_empty_control_cell_is_flagged():
    assert "E2" in hard(evtab(row(ctrl="")))


def test_na_control_passes():
    assert "E2" not in hard(evtab(row(ctrl="NA")))


# ── E3 同作者同年 → a/b ──────────────────────────────────────

def test_same_author_year_without_suffix_is_flagged():
    assert "E3" in hard(evtab(row(author="Li 2025"), row(author="Li 2025")))


def test_ab_suffix_resolves_duplicate():
    assert "E3" not in hard(evtab(row(author="Li 2025a"), row(author="Li 2025b")))


# ── E4 / E5 口径必须带年份版本 ───────────────────────────────

def test_if_without_year_is_flagged():
    assert "E4" in hard(evtab(row(iff="7.9")))


def test_zone_without_version_year_is_flagged():
    assert "E5" in hard(evtab(row(zone="中科院医学1区 / JCR Q1")))


# ── E6 是软规则，不算硬失败 ──────────────────────────────────

def test_result_without_number_is_soft_only():
    t = evtab(row(res="结果方向一致"))
    assert "E6" not in hard(t)
    assert "E6" in soft(t)


# ── E7 分区标题 ──────────────────────────────────────────────

def test_missing_partition_title_is_flagged():
    assert "E7" in hard(evtab(row(), title="## 一般锚点"))


# ── 覆盖声明 C1 / C2 ─────────────────────────────────────────

def test_complete_coverage_declaration_passes():
    t = "可识别位置 28 处 → 实际核查 26 处 → 未能覆盖 2 处\n- 因付费墙未读取（2 处）"
    assert cl.check_coverage(t) == []


def test_missing_k_is_flagged():
    t = "可识别位置 28 处 → 实际核查 26 处"
    assert any("C1" in f for f in cl.check_coverage(t))


def test_three_numbers_must_add_up():
    t = "可识别位置 28 → 实际核查 20 → 未能覆盖 2"
    assert any("C2" in f for f in cl.check_coverage(t))
