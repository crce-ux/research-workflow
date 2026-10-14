# -*- coding: utf-8 -*-
"""convergence_log 的测试。

⭐ 最要紧的一条是 **C3**：某一轮出现「上轮漏看」时，本轮**作废**，
   不能拿它当「又跑了一轮」。实测里人最容易忘的就是 C3 规则本身。
"""
import pytest

import convergence_log as CL

HEAD = ("| 轮次 | 维度 | 实质 | 语言 | 未查 | 回流 |\n"
        "|---|---|---|---|---|---|\n")


def _log(*rows):
    return HEAD + "".join(
        f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} |\n" for r in rows)


def test_全过():
    recs = CL.parse(_log(("R1", "D1", 0, 2, 2, 0)))
    ok, reasons = CL.verdict(recs[0])
    assert ok and reasons == []


@pytest.mark.parametrize("实质,语言,未查,回流", [
    (1, 0, 0, 0),        # C1a 不归零
    (0, 3, 0, 0),        # C1b 超 2
    (0, 0, 3, 0),        # C2 超 2
])
def test_单条不过(实质, 语言, 未查, 回流):
    recs = CL.parse(_log(("R1", "D1", 实质, 语言, 未查, 回流)))
    ok, reasons = CL.verdict(recs[0])
    assert not ok and reasons


def test_C3_回流即作废():
    recs = CL.parse(_log(("R2", "D2", 0, 1, 1, 2)))
    ok, reasons = CL.verdict(recs[0])
    assert not ok
    assert any("作废" in r for r in reasons)


def test_作废轮不计入序列(tmp_path):
    """R1 作废、R2 干净 → 末轮看 R2，判收敛。"""
    f = tmp_path / "log.md"
    f.write_text(_log(
        ("R1", "D1", 4, 6, 15, 0),
        ("R2", "D2", 0, 1, 2, 0),
    ), encoding="utf-8")
    recs = CL.parse(f.read_text(encoding="utf-8"))
    valid = [r for r in recs if r["回流"] == 0]
    assert len(valid) == 2
    assert CL.verdict(valid[-1])[0]


def test_找不着表头报格式错():
    with pytest.raises(SystemExit) as e:
        CL.parse("这是一份没有表的记录。\n")
    assert "表头" in str(e.value)


def test_缺数字的行被跳过():
    """行里有非数字单元格（如空的备注行）→ 跳过，不炸。"""
    text = HEAD + "| R1 | D1 | 0 | 1 | 2 | 0 |\n| R2 | D2 | — | — | — | — |\n"
    recs = CL.parse(text)
    assert len(recs) == 1 and recs[0]["轮次"] == "R1"


def test_数字带单位也能读():
    recs = CL.parse(_log(("R1", "D1", "0处", "1处", "2项", "0")))
    assert recs[0]["实质"] == 0 and recs[0]["未查"] == 2


def test_止损线是六轮():
    assert CL.MAX_ROUNDS == 6
