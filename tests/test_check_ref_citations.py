# -*- coding: utf-8 -*-
"""check_ref_citations 的解析测试。

这组测试锁的是**编号解析的边界**——区间、逗号、方括号两种著录格式。
解析错一位，双向核对就会大面积误报。
"""
import check_ref_citations as crc


# ── 正文引用解析 ─────────────────────────────────────────────

def test_parse_cited_single():
    assert crc.parse_cited("见 [1]。") == {1}


def test_parse_cited_comma_list():
    assert crc.parse_cited("见 [1,2]。") == {1, 2}


def test_parse_cited_range():
    assert crc.parse_cited("见 [5-7]。") == {5, 6, 7}


def test_parse_cited_mixed():
    assert crc.parse_cited("见 [1] 与 [3,5] 以及 [8-10]。") == {1, 3, 5, 8, 9, 10}


def test_parse_cited_with_spaces():
    assert crc.parse_cited("见 [1, 2]。") == {1, 2}


def test_parse_cited_empty():
    assert crc.parse_cited("本文没有引用。") == set()


def test_parse_cited_dedupes():
    assert crc.parse_cited("[1] [1] [1]") == {1}


# ── 参考文献表编号解析（两种著录格式）─────────────────────────

def test_parse_listed_dot_format():
    refs = "1. Smith A. 2020.\n2. Chen B. 2021."
    assert crc.parse_listed(refs) == {1, 2}


def test_parse_listed_bracket_format():
    refs = "[1] Smith A. 2020.\n[2] Chen B. 2021."
    assert crc.parse_listed(refs) == {1, 2}


def test_parse_listed_ignores_non_line_start():
    """行中的 `2. ` 不算编号（避免正文里的序数被误读）。"""
    refs = "1. Smith A. 2020.\n本研究分 2. 阶段完成。"
    assert crc.parse_listed(refs) == {1}


# ── 双向核对的核心断言 ───────────────────────────────────────

def test_cited_but_not_listed():
    """正文引了但文末没列 → 差集非空。"""
    cited = crc.parse_cited("见 [1] 与 [9]。")
    listed = crc.parse_listed("1. Smith A.")
    assert cited - listed == {9}


def test_listed_but_not_cited():
    """文末列了但正文没引 → 差集非空。"""
    cited = crc.parse_cited("见 [1]。")
    listed = crc.parse_listed("1. Smith A.\n2. Chen B.")
    assert listed - cited == {2}
