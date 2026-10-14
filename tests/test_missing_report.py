# -*- coding: utf-8 -*-
"""missing_report 的测试。

⚠️ 这里守的是**一条纪律**：「不适用」不是缺失。
   算缺失率时把它摘出去，否则缺失率虚高、插补会用到不该用的人身上。
   所以每个用例都同时断言**粗缺失率**与**真缺失率**——两个数不能混。
"""
import csv

import missing_report as MR


def _write(tmp_path, rows, header=None, name="d.csv"):
    p = tmp_path / name
    header = header or list(rows[0].keys())
    with open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        w.writerows(rows)
    return p


def test_不适用从真缺失率里摘除(tmp_path):
    """⭐ 4 例：1 个不适用、1 个未评、1 个空、1 个有值。

    粗缺失 = 3/4 = 75%；真缺失 = 2/(4-1) = 66.7%。
    """
    p = _write(tmp_path, [
        {"id": "1", "x": "3"},
        {"id": "2", "x": "未评"},
        {"id": "3", "x": "不适用"},
        {"id": "4", "x": ""},
    ])
    rows, _ = MR.read_rows(p)
    m = MR.measure(rows, "x", MR.DEFAULT_CODES)
    assert m["n"] == 4
    assert m["na"] == 1
    assert m["missing"] == 3
    assert m["crude"] == 0.75
    assert abs(m["real"] - 2 / 3) < 1e-9


def test_全是不适用时真缺失率分母为零不炸(tmp_path):
    """整列都是「不适用」——真缺失率没有分母，返回 0 而不是 ZeroDivisionError。"""
    p = _write(tmp_path, [{"x": "不适用"}, {"x": "不适用"}])
    rows, _ = MR.read_rows(p)
    m = MR.measure(rows, "x", MR.DEFAULT_CODES)
    assert m["real"] == 0.0
    assert m["crude"] == 1.0


def test_空格与NA写法都算没填(tmp_path):
    p = _write(tmp_path, [{"x": " "}, {"x": "N/A"}, {"x": "nan"}, {"x": "1"}])
    rows, _ = MR.read_rows(p)
    m = MR.measure(rows, "x", MR.DEFAULT_CODES)
    assert m["blank"] == 3
    assert m["missing"] == 3


def test_未标码的缺失单独计数(tmp_path):
    """空与码是两回事：空**归不进四类**，所以要单独报，不能被当成某一类。"""
    p = _write(tmp_path, [{"x": ""}, {"x": "失访"}])
    rows, _ = MR.read_rows(p)
    m = MR.measure(rows, "x", MR.DEFAULT_CODES)
    assert m["blank"] == 1
    assert m["by_code"]["失访"] == 1


def test_逐时点分段(tmp_path):
    p = _write(tmp_path, [
        {"id": "1", "t": "基线", "x": "1"},
        {"id": "2", "t": "基线", "x": "1"},
        {"id": "1", "t": "8周", "x": "失访"},
        {"id": "2", "t": "8周", "x": "1"},
    ])
    rows, _ = MR.read_rows(p)
    base = [r for r in rows if r["t"] == "基线"]
    wk8 = [r for r in rows if r["t"] == "8周"]
    assert MR.measure(base, "x", MR.DEFAULT_CODES)["real"] == 0.0
    assert MR.measure(wk8, "x", MR.DEFAULT_CODES)["real"] == 0.5


def test_gbk回退(tmp_path):
    """Windows 上中文 CSV 常是 GBK——读不了要回退，不能直接崩。"""
    p = tmp_path / "gbk.csv"
    p.write_bytes("编号,备注\n1,未评\n".encode("gbk"))
    rows, enc = MR.read_rows(p)
    assert enc == "gbk" and rows[0]["备注"] == "未评"
