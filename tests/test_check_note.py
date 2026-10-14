# -*- coding: utf-8 -*-
"""check_note 的规则测试。

最值钱的是 N3：**定位方式与引用形式必须一致**——
标了"仅摘要"却引用表格页码，就是在编。这条锁不住，五态标签就白设了。
"""
import pathlib

import check_note as cn


GOOD_HEAD = """## 某研究
**PMID**：12345678 ｜ **DOI**：10.1000/xyz123 ｜ **年份**：2025 ｜ **期刊**：Mol Psychiatry
**标签**：#TRS #RCT
**阅读深度**：全文
**定位方式**：page-grounded
"""


def run(text, tmp_path, name="精读笔记_X2025_主题.md"):
    p = pathlib.Path(tmp_path) / name
    p.write_text(text, encoding="utf-8")
    return cn.check(p)


def test_good_note_passes(tmp_path):
    text = GOOD_HEAD + "\n### 关键结果\n\n- 应答率 44% `[Paper: PDF p.4, Table 2]`\n"
    hits, _ = run(text, tmp_path)
    assert hits == []


def test_n1_missing_location_mode(tmp_path):
    text = GOOD_HEAD.replace("**定位方式**：page-grounded\n", "")
    hits, _ = run(text, tmp_path)
    assert any("N1" in h and "定位方式" in h for h in hits)


def test_n1_accepts_legacy_depth_field(tmp_path):
    """真实笔记用 `**方式**：全文精读`——同一个信息，不该按字段名报缺。"""
    text = GOOD_HEAD.replace("**阅读深度**：全文", "**方式**：全文精读")
    hits, _ = run(text, tmp_path)
    assert not any("N1" in h and "阅读深度" in h for h in hits)


def test_n1_accepts_either_identifier(tmp_path):
    """有 DOI 无 PMID 也算齐——不能要求两个都在。"""
    text = GOOD_HEAD.replace("**PMID**：12345678 ｜ ", "")
    hits, _ = run(text, tmp_path)
    assert not any("N1" in h and "标识符" in h for h in hits)


def test_n2_no_labels_at_all(tmp_path):
    text = GOOD_HEAD + "\n### 关键结果\n\n- 应答率 44%（p=0.008）\n"
    hits, _ = run(text, tmp_path)
    assert any("N2" in h for h in hits)


def test_n3_source_limited_must_not_cite_table(tmp_path):
    """标了 source-limited 却引用 Table 2——摘要里没有表，这是越界。"""
    text = GOOD_HEAD.replace("page-grounded", "source-limited")
    text += "\n- 应答率 44% `[Paper: Abstract]`（见 Table 2）\n"
    hits, _ = run(text, tmp_path)
    assert any("N3" in h and "在编" in h for h in hits)


def test_n3_abstract_depth_must_not_cite_page(tmp_path):
    """阅读深度是「摘要」，却写了页码引用。"""
    text = GOOD_HEAD.replace("**阅读深度**：全文", "**阅读深度**：摘要")
    text += "\n- 结论 `[Paper: PDF p.3]`\n"
    hits, _ = run(text, tmp_path)
    assert any("N3" in h for h in hits)


def test_n3_structure_grounded_must_not_cite_page(tmp_path):
    text = GOOD_HEAD.replace("page-grounded", "structure-grounded")
    text += "\n- 结果 `[Paper: PDF p.5]`\n"
    hits, _ = run(text, tmp_path)
    assert any("N3" in h and "假精确" in h for h in hits)


def test_structure_grounded_with_figure_is_fine(tmp_path):
    """structure-grounded 允许图表定位，只是不许写页码。"""
    text = GOOD_HEAD.replace("page-grounded", "structure-grounded")
    text += "\n- 结果 `[Paper: Fig.2]`\n"
    hits, _ = run(text, tmp_path)
    assert not any("N3" in h for h in hits)


def test_page_grounded_may_cite_page(tmp_path):
    text = GOOD_HEAD + "\n- 结果 `[Paper: PDF p.3, Fig.2]`\n"
    hits, _ = run(text, tmp_path)
    assert not any("N3" in h for h in hits)


def test_n4_is_soft(tmp_path):
    text = GOOD_HEAD + "\n- 这条断言很长很长很长很长很长很长很长很长但没有标签\n"
    hits, soft = run(text, tmp_path)
    assert not any("N4" in h for h in hits)
    assert any("N4" in s for s in soft)


def test_real_filename_needed_in_dir_mode(tmp_path):
    """目录模式按命名约定找，不按内容找。"""
    (tmp_path / "随手记.md").write_text(GOOD_HEAD, encoding="utf-8")
    assert list(tmp_path.rglob("精读笔记_*.md")) == []
