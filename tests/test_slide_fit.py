# -*- coding: utf-8 -*-
"""slide_fit 的测试。

⭐ 三组容量数字直接钉住**手册自己给出的三个数**
   （内容区 1200×525 下 18px≈1123 / 20px≈910 / 24px≈632）——
   公式与手册必须对得上，否则「画之前先算」算的是另一套。
"""
import math

import slide_fit as SF

AREA = (1200.0, 525.0)


def test_手册给的三组容量能复现():
    assert round(SF.capacity(*AREA, 18)) == 1123
    assert round(SF.capacity(*AREA, 20)) == 910
    assert round(SF.capacity(*AREA, 24)) == 632


def test_字号越大容量越小():
    caps = [SF.capacity(*AREA, s) for s in (18, 20, 24, 32)]
    assert caps == sorted(caps, reverse=True)


def test_带高按整行数算():
    """320 字 @20px、宽 1200 → 每行 60 字 → 6 行 → 6×20×1.5 = 180 px。"""
    lines, h = SF.block_height(320, 20, 1200, 1.5)
    assert lines == 6
    assert h == 180.0


def test_不足一行也算一行():
    lines, _ = SF.block_height(1, 20, 1200, 1.5)
    assert lines == 1


def test_配图可读性判据():
    """⭐ 图内字号 × 显示宽 ÷ 图宽 < 9 px → 不可读。

    14px 的原图，2000 缩到 500（1/4）→ 只剩 3.5px。
    """
    assert 14 * 500 / 2000 == 3.5
    assert 14 * 500 / 2000 < SF.MIN_PX
    # 原样显示则没问题
    assert 14 * 2000 / 2000 >= SF.MIN_PX


def test_单字占位常数与手册一致():
    """单字占位 = 字号² × 1.35——由手册三组数反解，改它等于改判据。"""
    assert math.isclose(SF.CELL_FACTOR, 1.35)
    assert math.isclose(SF.LOSS, 0.78)
