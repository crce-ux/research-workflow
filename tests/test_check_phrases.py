# -*- coding: utf-8 -*-
"""check_phrases 的规则测试。

锁的是**九组词表/句式**。每组都要有一个「会响」的用例——
否则某组可能写了正则却永远匹配不上（真实素材不一定恰好含对应词）。

注：原来的「降智解释」组已并回 `check_persona.py` 的 C8（一条规则一个家），故不在此测。
"""
import check_phrases as cp


def groups(text):
    return {n for n, *_ in cp.scan(text)}


def test_self_deprecation_group():
    assert 1 in groups("本研究效果有限，仍明显落后于既有方法")


def test_cliche_group():
    assert 2 in groups("随着社会的发展，该问题越来越受到广泛关注")


def test_abstract_label_group():
    assert 3 in groups("本研究具有重要的理论意义")


def test_media_metaphor_group():
    assert 4 in groups("进口双雄与仿制大军的价格战混战")


def test_rhetorical_question_group():
    assert 5 in groups("那唯一的一篇是什么？——是 Altar 1986")


def test_false_dichotomy_group():
    assert 6 in groups("这不是方法问题而是数据问题")


def test_nominalization_group():
    assert 7 in groups("我们对三组数据进行了分析")


def test_overranked_citation_group():
    assert 8 in groups("按 CONSORT 要求，Methods 2.3 节应报告随机化")


def test_connector_pileup_group():
    assert 9 in groups("首先发现问题，其次分析原因，最后给出方案")


def test_clean_text_hits_nothing():
    assert cp.scan("本研究比较了两组的应答率，差异有统计学意义。") == []


def test_plain_yi_alone_is_not_flagged():
    """单字「仅」不收——它在文稿里是正常用词，收了会淹没信号。"""
    assert 1 not in groups("仅 3 例完成随访")


def test_out_of_scope_group_is_reported_separately():
    """越级引用只在审稿/回导师场景算，幻灯片里命中不计入退出码。"""
    found = {n: kinds for n, _name, kinds, _note, _f in cp.scan("按 CONSORT 报告")}
    assert "幻灯片" not in found[8]


# ── 防御性写作（D1/D2/D5/D6/D3/D7）──────────────────────────

def test_d1_prebuttal():
    assert 10 in groups("It should be noted that the sample is small.")


def test_d2_non_claim():
    assert 11 in groups("We do not claim that this generalizes.")


def test_d5_omission_defense():
    assert 12 in groups("We did not include a healthy control group because of recruitment limits.")


def test_d6_fairness_defense():
    assert 13 in groups("For a fair comparison, all methods use the same backbone.")


def test_d7_preliminary_repetition():
    text = "初步结果显示有效性。初步分析提示趋势。初步证据支持该假设。"
    assert 15 in groups(text)


def test_d7_two_mentions_not_flagged():
    assert 15 not in groups("初步结果显示有效性。初步分析提示趋势。")


def test_d3_caveat_stacking():
    text = "结果虽然可能在一定程度上提示该指标或许与疗效有关。"
    assert 14 in groups(text)


def test_necessary_limitation_not_flagged():
    """真正的方法学局限不该被防御性规则误伤。"""
    text = "本研究为单中心设计，样本量有限，结论外推需谨慎。"
    hit = groups(text)
    assert not (hit & {10, 11, 12, 13, 14, 15})


def test_d5_colloquial_negation():
    """「没有纳入…因为」与「未报告…因为」都算省略辩护。"""
    assert 12 in groups("我们没有纳入健康对照组，因为招募困难。")
    assert 12 in groups("本研究未报告该指标，因为采集流程不支持。")


def test_d1_chinese_variants():
    """「需要说明的是」「常被问的一个问题」也是 D1。"""
    assert 10 in groups("需要说明的是，该研究是横断面设计。")
    assert 10 in groups("常被问的一个问题是：两个都加会不会重复。")
    assert 10 in groups("这里需要强调，参数按 AMP 协议执行。")
