# -*- coding: utf-8 -*-
"""check_credit 的规则测试。

锁的是成果台账 §八 点名要的那条：**署名情况与位次是否自洽**。
抄错一次，NSFC 简历上就是虚假标注。
"""
import pathlib

import check_credit as cc


HEADER = ("| # | 状态 | 标题 | 期刊 | 年 | 卷期页 | DOI | 署名情况 | 作者总数 | 我的位次 | 项目 |\n"
          "|---|---|---|---|---|---|---|---|---|---|---|\n")


def note(*rows):
    return "# 成果台账\n\n## 二、论文\n\n" + HEADER + "".join(rows)


def run(text, tmp_path):
    p = pathlib.Path(tmp_path) / "成果台账.md"
    p.write_text(text, encoding="utf-8")
    return cc.check(p)


GOOD = "| 1 | 已发表 | 某论文 | J | 2025 | 1(1):1-9 | 10.1/x | 唯一第一作者 | 8 | 1 | TRS_EEG |\n"


def test_good_row_passes(tmp_path):
    hits, _ = run(note(GOOD), tmp_path)
    assert hits == []


def test_placeholder_rows_are_skipped(tmp_path):
    hits, _ = run(note("| — | — | *(待填)* | | | | | | | | |\n"), tmp_path)
    assert hits == []


def test_c2_cofirst_with_wrong_rank(tmp_path):
    """⭐ 「共同第一作者」却写位次 3——这就是 §八 点名的那个例子。"""
    bad = GOOD.replace("唯一第一作者 | 8 | 1", "共同第一作者 | 8 | 3")
    hits, _ = run(note(bad), tmp_path)
    assert any("C2" in h and "位次" in h for h in hits)


def test_c2_corresponding_must_be_last(tmp_path):
    bad = GOOD.replace("唯一第一作者 | 8 | 1", "唯一通讯作者 | 8 | 2")
    hits, _ = run(note(bad), tmp_path)
    assert any("C2" in h and "通讯" in h for h in hits)


def test_c2_shared_corresponding_can_be_second_last(tmp_path):
    ok = GOOD.replace("唯一第一作者 | 8 | 1", "共同通讯作者 | 8 | 7")
    hits, _ = run(note(ok), tmp_path)
    assert not any("C2" in h for h in hits)


def test_c2_other_author_number_must_match_rank(tmp_path):
    bad = GOOD.replace("唯一第一作者 | 8 | 1", "其他（第 3 作者）| 8 | 5")
    hits, _ = run(note(bad), tmp_path)
    assert any("C2" in h and "对不上" in h for h in hits)


def test_c1_illegal_credit_value(tmp_path):
    bad = GOOD.replace("唯一第一作者", "第二作者")
    hits, _ = run(note(bad), tmp_path)
    assert any("C1" in h for h in hits)


def test_c3_missing_total_authors(tmp_path):
    bad = GOOD.replace("| 唯一第一作者 | 8 | 1 |", "| 唯一第一作者 |  | 1 |")
    hits, _ = run(note(bad), tmp_path)
    assert any("C3" in h and "作者总数" in h for h in hits)


def test_c4_status_enum(tmp_path):
    bad = GOOD.replace("| 已发表 |", "| 投出去了 |")
    hits, _ = run(note(bad), tmp_path)
    assert any("C4" in h for h in hits)


def test_surname_order_needs_no_rank(tmp_path):
    ok = GOOD.replace("唯一第一作者 | 8 | 1", "按姓氏排序 | 8 |  |")
    hits, _ = run(note(ok), tmp_path)
    assert not any("C3" in h for h in hits)


def test_missing_table_is_reported_not_silently_passed(tmp_path):
    hits, soft = run("# 随便一份文档\n\n没有表。", tmp_path)
    assert hits == []
    assert any("未评" in s for s in soft)
