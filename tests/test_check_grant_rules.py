# -*- coding: utf-8 -*-
"""check_grant_rules 的测试。

⭐ 「Never 写年度性数值进文档」出自 grant-diagnosis 自己的 Anti-Patterns：
   **Never 写年度性数值（篇幅/年龄/代码）进文档——现场取。**
   NSFC 每年改版，写死的值 1–2 年后不仅无用，还有害。

   它只做**存在性**：「有没有写死一个数」，不碰「写死的数对不对」。
"""
import pathlib

import check_grant_rules as CG


def P(name):
    return pathlib.Path(name)


def _hit(line, name="规则与取用指南.md"):
    return CG.scan(line, name)


def test_写死篇幅字数会被报():
    hits = _hit("正文篇幅不超过 8000 字。")
    assert hits and "篇幅（字数）" in hits[0]


def test_写死页数会被报():
    assert _hit("总页数控制在 20 页以内。")


def test_写死年龄会被报():
    assert _hit("申请人年龄不超过 35 周岁。")


def test_写死申请代码会被报():
    assert _hit("本课题申请代码为 H0902。")


def test_写死经费会被报():
    assert _hit("直接费用资助 60 万元。")


def test_写死资助期限会被报():
    assert _hit("资助期限为 4 年。")


def test_当年为准的不报():
    assert _hit("正文篇幅上限以当年《项目指南》为准。") == []
    assert _hit("资助期限现场取。") == []


def test_问句与举例的不报():
    """核对清单里的问句（「当年正文是几部分？」）与举例都不是写死。"""
    assert _hit("- [ ] 各部分篇幅上限是多少？") == []
    assert _hit("如 H09、H0902 等代码，具体以当年目录为准。") == []


def test_豁免要同行():
    """⭐ 跨行的理由不算——引用块折行很常见。
    上一行写了「以当年为准」，写了数值的那一行照样是写死。"""
    assert _hit("正文不超过 8000 字。")


def test_字符不算字数():
    assert _hit("摘要限 400 字符。") == []


def test_非指导类文件名跳过(tmp_path):
    """申请人的标书里出现代码、经费是正常的——只在指导类文档上触发。"""
    assert not CG.TRIGGER.search("申请人标书.md")
    assert not CG.TRIGGER.search("研究方案.md")
    assert CG.TRIGGER.search("规则与取用指南.md")
    assert CG.TRIGGER.search("申报前核对清单.md")
    assert CG.TRIGGER.search("SKILL.md")
