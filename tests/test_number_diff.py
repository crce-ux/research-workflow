# -*- coding: utf-8 -*-
"""number_diff 的规则测试。

锁的是**数字归一**这一段——跨语言/跨格式比对全押在它身上，
而千分位与小数点在这里是同一批字符，最容易搞反。
"""
import number_diff as nd


def test_thousands_separator_is_collapsed():
    assert nd.normalise("1,234") == "1234"
    assert nd.normalise("1.234") == "1234"
    assert nd.normalise("1,234,567") == "1234567"


def test_decimal_point_is_kept():
    assert nd.normalise("0.75") == "0.75"
    assert nd.normalise("12.5") == "12.5"


def test_comma_decimal_becomes_dot():
    """欧陆写法 0,75 应与 0.75 等价。"""
    assert nd.normalise("0,75") == "0.75"


def test_percent_sign_normalised():
    assert nd.normalise("50％") == "50%"
    assert nd.normalise("50%") == "50%"


def test_collect_skips_zero_and_groups_context():
    d = nd.collect("共 48 例，应答率 50%，另有 0 例。")
    assert "0" not in d          # 0 是噪声，不收
    assert "48" in d and "50%" in d
    assert "例" in d["48"][0]     # 上下文一并留下


def test_collect_keeps_every_occurrence():
    d = nd.collect("N=48 是总数；另有 48 例来自 B 组。")
    assert len(d["48"]) == 2


def test_same_numbers_different_format_match(tmp_path):
    a = tmp_path / "a.md"
    b = tmp_path / "b.md"
    a.write_text("共 1,234 例，应答率 50%。", encoding="utf-8")
    b.write_text("Total 1234 cases, response 50%.", encoding="utf-8")
    na, nb = nd.collect(nd.read_text(a)), nd.collect(nd.read_text(b))
    assert set(na) == set(nb)


def test_missing_number_is_detected(tmp_path):
    a = tmp_path / "a.md"
    b = tmp_path / "b.md"
    a.write_text("共 48 例，A 组 25 例，B 组 23 例。", encoding="utf-8")
    b.write_text("共 48 例，A 组 25 例。", encoding="utf-8")   # 漏了 B 组
    na, nb = nd.collect(nd.read_text(a)), nd.collect(nd.read_text(b))
    only_a = [k for k in na if k not in nb]
    assert "23" in only_a


def test_unsupported_suffix_exits(tmp_path):
    p = tmp_path / "x.xyz"
    p.write_text("1", encoding="utf-8")
    try:
        nd.read_text(p)
    except SystemExit as e:
        assert "不支持" in str(e)
    else:
        raise AssertionError("应报不支持格式")
