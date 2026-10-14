# -*- coding: utf-8 -*-
"""negation_diff 的测试。

⭐ 它补的是 number_diff 与 check_token_diff 之间的空白：
   数字变了看得见，**否定丢了几乎看不见**——
   而「不显著 → 显著」是改写里结论级的事故。
"""
import negation_diff as ND


def test_抽出否定短语():
    got = ND.tokens("两组差异不显著。")
    assert "不显著" in got


def test_长否定词优先():
    """「无法」不能被「无」抢先吃掉——否则同一句会碎成两个半截 token。"""
    got = ND.tokens("无法完成随访。")
    assert "无法完成随访" in got
    assert "无" not in got


def test_未发现被整体抽出():
    assert "未发现剂量效应" in ND.tokens("本研究未发现剂量效应。")


def test_否定被删掉能被抓到():
    o = ND.tokens("两组差异不显著（p=0.08）。")
    r = ND.tokens("两组差异显著（p=0.08）。")
    assert sorted(set(o) - set(r)) == ["不显著"]


def test_新增否定也能抓到():
    o = ND.tokens("该指标可用。")
    r = ND.tokens("该指标不可用。")
    assert sorted(set(r) - set(o)) == ["不可用"]


def test_两边一致时无差():
    t = "未发现剂量效应；安全性良好。"
    assert set(ND.tokens(t)) == set(ND.tokens(t))


def test_排除与缺乏也算否定():
    got = ND.tokens("排除感染因素；缺乏对照。")
    assert any(x.startswith("排除") for x in got)
    assert "缺乏对照" in got


def test_计数按出现次数():
    got = ND.tokens("不显著。不显著。")
    assert got["不显著"] == 2
