# -*- coding: utf-8 -*-
"""sample_flow 的测试。

它只做「拿到主分析样本量之后」的换算——**不碰效应量与效能**（那是 SAP 的事）。
这里钉住的是取整方向与分组拆分：**宁可多收，不能少收**。
"""
import math

import pytest

import sample_flow as SF


def test_脱落率换算():
    assert SF.inflate(120, 0.20) == 150
    assert SF.inflate(120, 0.0) == 120
    assert SF.inflate(120, 0.15) == 142          # 141.18 → 向上取整


def test_取整向上():
    """⭐ 宁可多收不能少收——141.18 例不存在，只有 142。"""
    n = SF.inflate(121, 0.20)
    assert n == math.ceil(121 / 0.8) == 152
    assert SF.inflate(1, 0.30) == 2


def test_脱落率非法时报错():
    with pytest.raises(SystemExit):
        SF.inflate(120, 1.0)
    with pytest.raises(SystemExit):
        SF.inflate(120, -0.1)


def test_分组比一比一():
    assert SF.split(150, (1, 1)) == [75, 75]


def test_分组比二比一():
    assert SF.split(150, (2, 1)) == [100, 50]


def test_分组比奇数也向上取():
    """150 按 1:1 拆不出整数时，各组分别向上取整——宁可多 1 例。"""
    assert SF.split(151, (1, 1)) == [76, 76]     # 和 152 > 151
    assert sum(SF.split(151, (1, 1))) >= 151


def test_parse_ratio_全角冒号():
    assert SF.parse_ratio("2：1") == (2, 1)
    assert SF.parse_ratio("1:1") == (1, 1)


def test_parse_ratio_非法():
    with pytest.raises(SystemExit):
        SF.parse_ratio("一比一")
