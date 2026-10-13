# -*- coding: utf-8 -*-
"""check_persona 的结构与选择器测试。

⚠️ 这个脚本的判据是**启发式**的——docstring 自己就写着「命中 ≠ 要改」。
所以测试**只锁结构与选择器**，不去断言「某句话必须被抓」，
否则就是在把启发式当成硬规则来维护。

接口：check(...) -> (hits: dict[str, list[tuple]], stats: dict)
"""
import check_persona as cp


def test_returns_hits_and_stats():
    result = cp.check("首先，我们认为这项技术具有重要意义。")
    assert isinstance(result, tuple) and len(result) == 2
    hits, stats = result
    assert isinstance(hits, dict)
    assert isinstance(stats, dict)


def test_hits_rows_are_triples():
    hits, _ = cp.check("那篇综述指出，综上所述，该研究具有重要意义。")
    for key, rows in hits.items():
        assert isinstance(key, str)
        assert isinstance(rows, list)
        for row in rows:
            assert isinstance(row, tuple)
            assert len(row) == 3


def test_stats_has_expected_keys():
    _, stats = cp.check("这是两句话。这是第二句。")
    for key in ("n_char", "n_sent"):
        assert key in stats
    assert stats["n_sent"] >= 1


def test_kind_selects_medium():
    """讲稿与幻灯片的要求不同，两个 kind 都应能跑通。"""
    text = "那篇综述指出，综上所述，该研究具有重要意义。"
    for kind in ("讲稿", "幻灯片"):
        hits, _ = cp.check(text, kind=kind)
        assert isinstance(hits, dict)


def test_scene_is_accepted():
    """不同身份场景都能跑，不抛异常。"""
    for scene in ("组会汇报", "期刊审稿", "文献综述"):
        hits, _ = cp.check("本研究证明了该结论。", scene=scene)
        assert isinstance(hits, dict)


def test_clean_text_produces_no_backreference_hit():
    """点名到位的引用不应被回指规则命中。"""
    text = "Smith 等 2020 年在 Biological Psychiatry 报告的队列研究给出了相反结果。"
    hits, _ = cp.check(text, kind="幻灯片")
    flat = " ".join(tok for rows in hits.values() for _, tok, _ in rows)
    assert "那篇" not in flat
