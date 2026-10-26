# -*- coding: utf-8 -*-
"""check_phrases 的规则测试。

锁的是**十七组词表/句式**。每组都要有一个「会响」的用例——
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


def test_pseudo_contrast_with_comma():
    """「不是 A，而是 B」带逗号的常见写法要能抓到。"""
    assert 6 in groups("选这两项，不是因为它们流行，而是因为它们各回答一个不同的问题。")
    assert 6 in groups("这不是降低它的价值，而是把证据强度说清楚。")


def test_necessary_distinction_not_flagged():
    """「是 A，不是 B」式的必要区分不该算伪对立。"""
    assert 6 not in groups("屏状核是脑区，不是受体。")
    assert 6 not in groups("该研究是横断面诊断分类，不是治疗预测。")
    assert 6 not in groups("这是历史假说，不是证据。")


def test_neg_contrast_density():
    """全篇「不是」≥3 次 → 辩驳腔提示。"""
    assert 16 in groups("不是甲。不是乙。不是丙。")
    assert 16 not in groups("不是甲。不是乙。")


# ── 主次 ──────────────────────────────────────────────────

def test_postcomma_negation_group():
    """正面主张之后用否定收尾——否定占了句子的后半。"""
    assert 17 in groups("六种方法的差别，不是「先进与落后」，而是「所得信息的层级」。")
    assert 17 in groups("这是一份关于研究空白的调研，不是文献综述。")


def test_postcomma_negation_ignores_sentence_initial():
    """否定在句首不算后置；那种写法的处理在组 6 与组 16。"""
    assert 17 not in groups("不是方法问题，而是数据问题。")


def test_postcomma_negation_ignores_positive_text():
    assert 17 not in groups("本研究比较了两组的应答率，差异有统计学意义。")
    assert 17 not in groups("屏状核的胆碱能输入以烟碱型受体为主：α4、α5、α7。")


def test_postcomma_negation_tolerates_bold():
    """讲稿里「，**不是**」的加粗写法不能被漏掉。"""
    assert 17 in groups("这是全脑分析里的一个脑区，**不是**事先指定的感兴趣区。")


# ── 2026-10-26 吸收 Academic-Humanizer 的六组 ──────────────

def test_cue_colon_group():
    assert 18 in groups("一句话总结：这个方法在三个数据集上都有效。")
    assert 18 in groups("核心是：把两个模型放在同一批人上比较。")


def test_cue_colon_allows_definition_colon():
    """引出定义、原话的冒号是规范用法。"""
    assert 18 not in groups("模型包括两部分：测量模型和结构模型。")


def test_translationese_group():
    assert 19 in groups("对于野外调查人员来说，该方法更容易实施。")
    assert 19 in groups("在数据质量方面，两组的处理相同。")


def test_meta_narrative_group():
    assert 20 in groups("本节将介绍主要的数值结果。")
    assert 20 in groups("本章小结：三条假设都设有证伪条件。")


def test_worklog_group():
    assert 21 in groups("经过健全性检查，流水线继续执行下一步。")
    assert 21 in groups("随机种子固定为 42，求解器容差取 1e-8。")


def test_coined_label_group():
    assert 22 in groups("本文建立了一套质量保障机制。")
    assert 22 in groups("该研究提出了模型认证协议与治理闭环。")


def test_coined_label_skips_established_terms():
    """领域内已有定义的组合、普通形容词修饰的通用名词不报。"""
    assert 22 not in groups("本文使用了注意力机制与评价指标体系。")
    assert 22 not in groups("这属于病理机制的一部分。")
    assert 22 not in groups("该方法属于研究框架的一部分。")
    assert 22 not in groups("作者提到统一协议尚未建立。")


def test_coined_label_skips_defined_terms():
    """同句给出定义的标签不算杜撰。"""
    assert 22 not in groups("本文提出的质量保障机制，是指对每批数据做三项核对。")


def test_significance_without_test():
    assert 23 in groups("治疗组症状显著改善，两组差异明显。")
    assert 23 not in groups("治疗组症状显著改善（t 检验，p = 0.003）。")


def test_optimal_without_conditions():
    assert 23 in groups("该方案是最优的。")
    assert 23 not in groups("在命题 2 的假设下，该方案是最优的。")


def test_novelty_word_repetition():
    assert 24 in groups("首次报道。首次发现。首次验证。")
    assert 24 not in groups("首次报道。首次发现。")


# ── 句子节奏（组 25）─────────────────────────────────────

def hit_names(text, num):
    return [h[1] for h in cp.scan(text) if h[0] == num]


def test_adjacent_same_skeleton():
    t = "研究一纳入 120 例患者，随访六个月。研究二纳入 118 例患者，随访六个月。"
    assert "相邻句同款" in hit_names(t, 25)


def test_ordinal_clauses_are_not_same_skeleton():
    """序数编号的并列条款是结构，不是同款句。"""
    t = "第一，两组基线一致，样本量相同。第二，两组随访相同，失访率接近。"
    assert "相邻句同款" not in hit_names(t, 25)


def test_entry_lists_are_not_same_skeleton():
    """「妄想：Cascella 2011…」这类条目式并列是数据。"""
    t = "妄想：Cascella 2011 报告了颞叶。幻听：Mallikarjun 2023 报告了颞上回。"
    assert "相邻句同款" not in hit_names(t, 25)


def test_semicolon_density():
    assert "分号过密" in hit_names("模型分为三部分；测量模型；结构模型；", 25)
    assert "分号过密" not in hit_names("模型分为两部分；测量模型与结构模型。", 25)


def test_long_sentence():
    t = "本研究在三个中心招募了接受氯氮平治疗的精神分裂症患者共三百例，" * 3 + "并随访。"
    assert "长句" in hit_names(t, 25)


def test_frontmatter_is_skipped():
    t = "---\n标题: " + "很长的元数据" * 25 + "\n---\n正文一句。"
    assert "长句" not in hit_names(t, 25)


# ── 转折词（组 26）───────────────────────────────────────

def test_contrastive_but_is_flagged():
    assert 26 in groups("样本量偏小，但效应量稳定。")


def test_budan_and_danfan_are_not_flagged():
    """「不但…而且」「但凡」不是转折。"""
    assert 26 not in groups("该方案不但有效，而且安全。")
    assert 26 not in groups("但凡纳入的病例都做了核对。")


# ── 短句（组 27）────────────────────────────────────────

def test_short_sentence_density():
    t = ("第一句短。第二句也短。第三句短。第四句短。第五句短。"
         "第六句短。第七句短。第八句短。第九句短。第十句短。"
         "这一句写得足够长，用来说明短句连成串时才需要并回主句，否则读起来一顿一顿。")
    assert 27 in groups(t)


def test_normal_sentences_not_flagged():
    t = ("这一句长度适中，包含足够多的汉字，不会被算作短句。"
         "这里再给一句差不多长的，用来把短句比例压到阈值以下。")
    assert 27 not in groups(t)


def test_list_and_heading_lines_are_skipped():
    t = ("| 短 |\n| 句 |\n- 短\n# 短\n\n"
         "正文只有一句正常长度的话，写满了二十个汉字以上，用来稀释比例。")
    assert 27 not in groups(t)



def test_uniform_paragraph_is_flagged():
    """一段里四句一样长，CV 低于 0.30，单独报「段落句长太匀」。"""
    s = "这是一句长度约三十个字的话用来测试段落内的均匀程度。"
    names = [h[1] for h in cp._short_sentences(s * 4)]
    assert "段落句长太匀" in names


def test_varied_paragraph_not_flagged():
    """长短不一时不报「段落句长太匀」。"""
    t = ("第一句写得比较长，用两个分句交代这一段的背景与讨论范围。"
         "第二句把条件说清楚，包括时间、来源、适用人群与排除标准。"
         "第三句短。"
         "第四句把前面三个说法收拢成一个判断，并交代这个判断成立的条件与边界。"
         "第五句补上对照组的处理方式。"
         "第六句给出结果的方向与强度，不夸大也不缩小，并注明检验方法。"
         "第七句收尾，把落点放回开头的那个问题上，交代它对临床的意义。")
    names = [h[1] for h in cp._short_sentences(t)]
    assert "段落句长太匀" not in names
