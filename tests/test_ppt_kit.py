# -*- coding: utf-8 -*-
"""ppt_kit 的构件测试。

只钉两处**本轮新加的形态**，不重测老构件：
  一、`footer()` 的两种形态（细线 / 底边细带）
  二、`image()` 与 `imgslot()` —— 图位必须与文字区一眼可分，且缩放方式写在标签上
"""
import pytest

import ppt_kit as K
import ppt_style as S


# ══════════════════════════════════════════════════════════
#  页脚两形态
# ══════════════════════════════════════════════════════════
@pytest.fixture
def restore_foot_style():
    old = S.FOOT_STYLE
    yield
    S.FOOT_STYLE = old


def test_footer_default_is_a_thin_line():
    S.FOOT_STYLE = "line"
    out = K.footer("05", "项目 · 汇报")
    assert "<line" in out and 'stroke="#E4E9EF"' in out
    assert f'height="{S.FOOT_RULE_H}"' not in out


def test_footer_rule_style_puts_a_band_at_the_page_bottom(restore_foot_style):
    """实测 19 份 deck 里 4 份用底边主色细带（A116 23 处等），不是细线。"""
    S.FOOT_STYLE = "rule"
    out = K.footer("05", "项目 · 汇报")
    assert f'<rect x="0" y="{S.G["h"] - S.FOOT_RULE_H}"' in out
    assert f'width="{S.G["w"]}" height="{S.FOOT_RULE_H}"' in out
    assert f'fill="{S.C["main"]}"' in out
    assert "<line" not in out
    assert "项目 · 汇报" in out and ">05<" in out


def test_footer_rule_band_height_is_a_style_number():
    """16px 不是画在函数里的字面量 —— 改 ppt_style 一处，两个形态一起跟着变。"""
    assert S.FOOT_RULE_H == 16


# ══════════════════════════════════════════════════════════
#  图位
# ══════════════════════════════════════════════════════════
def test_imgslot_is_visibly_not_a_text_box():
    """图位此前与文字区长得一模一样（都是虚线框），整册图放不进去。"""
    out = K.imgslot(61, 100, 400, 300, "这里放结构 MRI")
    assert "【图位】" in out
    assert f'fill="{S.C["gray"]}"' in out          # 灰底，文字区没有底
    assert "这里放结构 MRI" in out


def test_imgslot_wraps_a_long_hint():
    out = K.imgslot(61, 100, 200, 300, "右栏：图（须紧贴它支持的那一条，不要装饰）")
    assert out.count("<text") >= 2


def test_headbar_two_forms_are_not_the_same_height():
    """页眉占高不同（72 对 163）—— 换页眉必须重排版面，不能只改一个值。

    实测把页眉换成 `"corner"` 而版面不动：大号章节号压在内容上
    （配方 32 的左色块被一个「02」压住）。
    """
    bar = K.headbar("标题", "03", "bar")
    corner = K.headbar("标题", "03", "corner")
    assert f'height="{S.G["bar"]}"' in bar
    assert f'height="{S.HEAD_CORNER["h"]}"' in corner
    assert S.HEAD_CORNER_H == S.HEAD_CORNER["h"] + S.HEAD_CORNER["tail_gap"] \
        + S.HEAD_CORNER["tail_h"]


def test_headbar_has_no_global_switch():
    """`ppt_style` 里不该有 `HEAD_STYLE` —— 有全局开关就会让人以为换族只要改一行。"""
    assert not hasattr(S, "HEAD_STYLE")


def test_corner_head_uses_the_corner_dimensions():
    out = K.headbar("研究结果", "03", "corner")
    d = S.HEAD_CORNER
    assert f'x="{d["x"]}" y="0" width="{d["w"]}" height="{d["h"]}"' in out
    assert "研究结果" in out and ">03<" in out


def test_logo_is_off_unless_given():
    old = S.LOGO
    try:
        S.LOGO = None
        assert K.logo() == ""
        S.LOGO = "../images/logo.png"
        assert 'href="../images/logo.png"' in K.logo()
    finally:
        S.LOGO = old


def test_image_pins_the_scaling_rule():
    """`preserveAspectRatio="xMidYMid meet"` 必须显式写出来。

    不写时浏览器同样按 meet 处理，但导出器（ppt-master）未必 ——
    写成 `slice` 会裁掉图边上的内容。
    """
    out = K.image(61, 100, 400, 300, "../images/x.png")
    assert 'href="../images/x.png"' in out
    assert 'preserveAspectRatio="xMidYMid meet"' in out
    assert 'width="400"' in out and 'height="300"' in out
