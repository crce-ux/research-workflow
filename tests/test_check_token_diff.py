# -*- coding: utf-8 -*-
"""check_token_diff 的规则测试。

锁的是「改写不得动事实」在机器上唯一可判定的形态——
受保护 token 有没有在改写中被丢掉或凭空多出来。
"""
import check_token_diff as ctd


def keys(text):
    return {(k, t) for (k, t) in ctd.extract(text)}


def test_numeric_token_lost_is_detected():
    a = ctd.extract("随访 12 周，失访率 8%。")
    b = ctd.extract("随访 12 周。")
    lost, _ = ctd.compare(a, b)
    assert any("8%" in tok for (_, tok), _ in lost)


def test_identical_text_has_zero_diff():
    t = "纳入 48 例，随访 6 个月，$H_0$ 成立。"
    lost, added = ctd.compare(ctd.extract(t), ctd.extract(t))
    assert lost == [] and added == []


def test_latex_command_preserved():
    t = r"见 \cite{Zhang2025} 与 \ref{fig:1}。"
    assert any(k == "LaTeX" for k, _ in keys(t))


def test_latex_command_lost_is_detected():
    a = ctd.extract(r"见 \cite{Zhang2025}。")
    b = ctd.extract("见相关文献。")
    lost, _ = ctd.compare(a, b)
    assert any("cite" in tok for (_, tok), _ in lost)


def test_status_token_preserved():
    t = r"若状态为 \texttt{RELEASE} 则赋分，否则 ABSTAIN。"
    ks = keys(t)
    assert any(tok == "ABSTAIN" for _, tok in ks)
    assert any(tok == "RELEASE" for _, tok in ks)


def test_common_uppercase_not_treated_as_status_token():
    """MRI / RCT / PANSS 是普通术语，不该被当状态 token 刷屏。"""
    ks = keys("本研究为 RCT，用 PANSS 与 MRI 评估。")
    assert not any(tok in ("RCT", "MRI", "PANSS") for _, tok in ks)


def test_doi_and_url_preserved():
    t = "数据见 https://example.org/x 与 doi 10.1001/jama.2026.0086。"
    ks = keys(t)
    assert any("10.1001/jama.2026.0086" in tok for _, tok in ks)
    assert any(tok.startswith("https://") for _, tok in ks)


def test_added_token_is_reported():
    """改写时凭空补写内容——新增 token 要报出来。"""
    a = ctd.extract("样本量为 48 例。")
    b = ctd.extract("样本量为 48 例，随访 24 周。")
    _, added = ctd.compare(a, b)
    assert any("24" in tok for (_, tok), _ in added)


def test_number_with_unit_is_its_own_kind():
    ks = keys("剂量 20 mg，疗程 8 周。")
    assert any(k == "数字单位" for k, _ in ks)


def test_file_path_token_preserved():
    ks = keys("脚本在 scripts/check_data.py，配置见 FACT.md。")
    assert any(tok.endswith(".py") for _, tok in ks)
