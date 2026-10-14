# -*- coding: utf-8 -*-
"""check_language 的规则测试。

本文件的测试锁的是**判据本身**——排他性断言必须有出处、回指必须点名。
它们是本仓工作流里少数可以客观验证的规则，所以值得写死。
"""
import check_language as cl

ONLY_EXCLUSIVE = [2]
ONLY_ANAPHORA = [1]


def _flat(hits, key):
    """把某类的命中拉平成一串 token，便于断言。"""
    return [tok for _, tok, _ in hits.get(key, [])]


# ── ② 排他性断言（硬规则）────────────────────────────────────

def test_exclusive_without_citation_is_flagged():
    """无出处的排他性断言 → 必须报出。"""
    hits = cl.check("本研究首次证明了该机制。", terms=set(), only=ONLY_EXCLUSIVE)
    assert "首次" in _flat(hits, "② 排他性断言·未见出处 ⚠️硬规则")


def test_exclusive_with_citation_is_not_flagged():
    """附近有具体出处 → 不报。"""
    text = "该结论为当前主流观点（Smith 等 2020 年综述）。"
    hits = cl.check(text, terms=set(), only=ONLY_EXCLUSIVE)
    assert _flat(hits, "② 排他性断言·未见出处 ⚠️硬规则") == []


def test_exclusive_with_search_disclosure_is_not_flagged():
    """写明检索分层与库名 → 不报（合规写法）。"""
    text = "在 PubMed / Europe PMC / OpenAlex 三库交叉检索下，有效 1 篇。"
    hits = cl.check(text, terms=set(), only=ONLY_EXCLUSIVE)
    assert _flat(hits, "② 排他性断言·未见出处 ⚠️硬规则") == []


# ── ① 回指（启发式）──────────────────────────────────────────

def test_anaphora_without_prior_naming_is_flagged():
    """「那篇综述」而前文未点名 → 报。"""
    hits = cl.check("那篇综述给出了相反的证据。", terms=set(), only=ONLY_ANAPHORA)
    assert len(hits.get("① 回指词·跨段未点名（引用须自足）", [])) >= 1


def test_anaphora_with_prior_naming_is_skipped():
    """前文已点名 → 跳过（同段紧邻回指属正常行文）。"""
    text = "Smith 等 2020 年的综述系统回顾了该问题。那篇综述给出了相反的证据。"
    hits = cl.check(text, terms=set(), only=ONLY_ANAPHORA)
    assert hits.get("① 回指词·跨段未点名（引用须自足）", []) == []


# ── 输出契约 ─────────────────────────────────────────────────

def test_check_returns_dict_of_tuples():
    """返回结构稳定：dict[str, list[tuple]]。"""
    hits = cl.check("首次发现。那篇文献说得很清楚。", terms=set(), only=[1, 2])
    assert isinstance(hits, dict)
    for key, rows in hits.items():
        assert isinstance(key, str)
        assert isinstance(rows, list)
        for row in rows:
            assert isinstance(row, tuple)
            assert len(row) == 3


def test_only_selector_limits_scope():
    """only 只跑指定类别。"""
    text = "本研究首次证明。那篇综述也说。"
    only2 = cl.check(text, terms=set(), only=[2])
    assert not any(k.startswith("①") for k in only2)
    only1 = cl.check(text, terms=set(), only=[1])
    assert not any(k.startswith("②") for k in only1)
