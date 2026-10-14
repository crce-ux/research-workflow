# -*- coding: utf-8 -*-
"""manuscript_triage 的测试。

⚠️ 这个工具只做**存在性**判断（「有没有写」），不碰「写得对不对」。
   所以用例都是「文中出现了某个说法 → 该项算报告了」。
   「未采用盲法」**要算报告了**——报告状态本身就是 CONSORT 的要求。
"""
import manuscript_triage as MT


RCT_FULL = """
# 随机、双盲、安慰剂对照试验

采用计算机生成的随机数字表进行区组随机。
分配隐藏通过密闭信封实现。
样本量估算基于预期效应量 d=0.5、检验效能 0.8，共 120 例。
主要终点为 12 周 PANSS 总分变化。
入组 132 例，流程图见 Figure 1，12 周失访 6 例。
分析集为 ITT；缺失数据用 MMRM 处理。
试验注册号 ChiCTR2400000000。
不良事件两组无差异。
"""


def test_rct_full_passes():
    assert MT.triage(RCT_FULL, "rct") == []


def test_rct_flags_missing_allocation_concealment():
    text = RCT_FULL.replace("分配隐藏通过密闭信封实现。", "")
    miss = MT.triage(text, "rct")
    assert any("分配隐藏" in m for m in miss)
    assert not any("样本量" in m for m in miss)


def test_未采用盲法也算报告了():
    """报告「没有盲法」本身就是要求——不能因为没有『双盲』二字就报缺。"""
    text = "本研究为开放标签设计，未采用盲法。"
    assert not any("盲法" in m for m in MT.triage(text, "rct"))


def test_只写入组人数不算写了样本量依据():
    text = "共纳入 120 例受试者。"
    miss = MT.triage(text, "rct")
    assert any("样本量依据" in m for m in miss)


def test_guess_type_rct():
    kind, _ = MT.guess_type(RCT_FULL)
    assert kind == "rct"


def test_guess_type_observational():
    kind, _ = MT.guess_type("这是一项回顾性队列研究，纳入 2015–2020 年住院患者。")
    assert kind == "observational"


def test_guess_type_none_on_empty():
    kind, _ = MT.guess_type("这是一份与临床研究无关的备忘录。")
    assert kind is None


def test_prediction_items_include_calibration():
    labels = [l for l, _ in MT.ITEMS["prediction"]]
    assert any("校准" in l for l in labels)
    assert any("过拟合" in l or "内部验证" in l for l in labels)
