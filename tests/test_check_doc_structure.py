# -*- coding: utf-8 -*-
"""check_doc_structure 的规则测试。

锁的是四类判定：层级跳跃 / 独子节 / 空节 / 可合并。
这个检查器只报可疑，退出码恒为 0，所以测试直接看报告内容，不看退出码。
"""
import check_doc_structure as cds


def kinds(md, min_chars=100):
    nodes = cds.parse(md.splitlines())
    return [k for k, _ln, _msg in cds.report(nodes, min_chars)]


def test_level_jump():
    md = "# 一\n\n正文。\n\n### 三\n\n正文。\n"
    assert "层级跳跃" in kinds(md)


def test_no_jump_with_intermediate_level():
    md = "# 一\n\n## 二\n\n正文。\n\n### 三\n\n正文。\n"
    assert "层级跳跃" not in kinds(md)


def test_single_child_section():
    md = "# 一\n\n正文。\n\n## 二\n\n正文。\n"
    assert "独子节" in kinds(md)


def test_two_children_not_flagged():
    md = "# 一\n\n## 二\n\n正文。\n\n## 三\n\n正文。\n"
    assert "独子节" not in kinds(md)


def test_empty_section():
    md = "# 一\n\n# 二\n"
    assert "空节" in kinds(md)


def test_section_with_children_is_not_empty():
    md = "# 一\n\n## 二\n\n正文。\n"
    assert "空节" not in kinds(md)


def test_short_siblings_can_merge():
    md = "# 一\n\n## 甲\n\n短。\n\n## 乙\n\n短。\n"
    assert "可合并" in kinds(md)


def test_long_siblings_not_flagged():
    md = "# 一\n\n## 甲\n\n" + "字" * 200 + "\n\n## 乙\n\n" + "字" * 200 + "\n"
    assert "可合并" not in kinds(md)


def test_heading_inside_code_fence_is_ignored():
    md = "# 一\n\n```\n# 不是标题\n```\n\n正文。\n"
    assert len(cds.parse(md.splitlines())) == 1
