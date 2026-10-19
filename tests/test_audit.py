# -*- coding: utf-8 -*-
"""audit.py：类型识别、三种解析器、端到端跑样例。"""
from pathlib import Path

import audit

ROOT = Path(__file__).resolve().parent.parent


def test_dw_counts_cjk_as_two():
    assert audit.dw("ab") == 2
    assert audit.dw("中文") == 4


def test_pad_aligns_and_truncates():
    assert audit.pad("中文", 6) == "中文  "
    out = audit.pad("一二三四五", 6)
    assert audit.dw(out) == 6 and "…" in out


def test_detect_type_lecture():
    assert audit.detect_type("# 讲稿\n口播：大家好") == "讲稿"


def test_detect_type_note():
    assert audit.detect_type("结论 [Paper: p.3]\n推断 [Analysis]") == "精读笔记"


def test_detect_type_default():
    assert audit.detect_type("# 随便一段文字") == "论文/综述"


def test_parse_language():
    out = ("🔴 ② 排他性断言·未见出处 —— 2 处\n"
           "          L3  唯一      …正文…\n"
           "          L7  首次      …正文…\n")
    hits = audit.parse_language(out)
    assert [(h["line"], h["rule"]) for h in hits] == [
        (3, "排他性断言·未见出处"), (7, "排他性断言·未见出处")]


def test_parse_phrases():
    out = ("  ❌ 6 伪对立：1 处 — 说明\n"
           "        第 7 行：不是相关而是\n")
    hits = audit.parse_phrases(out)
    assert hits[0]["line"] == 7
    assert hits[0]["rule"] == "伪对立"


def test_parse_ref():
    out = ("⚠️ 正文引用但表内缺失：[3]\n"
           "⚠️ 表内有但正文未引用（悬挂）：[1, 2]\n")
    hits = audit.parse_ref(out)
    assert len(hits) == 2
    assert hits[0]["detail"] == "[3]"


def test_end_to_end_on_sample():
    dtype, findings, ran, _ = audit.collect(ROOT / "examples" / "bad.md", "", None)
    assert dtype == "论文/综述"
    assert {"language", "phrases", "ref_citations"} <= set(ran)
    assert len(findings) >= 8
    details = " ".join(f["detail"] for f in findings)
    assert "[3]" in details


def test_only_filters_checkers():
    _, findings, ran, skipped = audit.collect(
        ROOT / "examples" / "bad.md", "", {"phrases"})
    assert ran == ["phrases"]
    assert all(f["checker"] == "phrases" for f in findings)
    assert any("未选中" in s for s in skipped)


def test_level_of():
    assert audit.level_of("排他性断言·未见出处", "唯一") == "硬规则"
    assert audit.level_of("数字-口径（人工核对用）", "26%") == "信息"
    assert audit.level_of("空泛量词（建议换具体数）", "大量") == "建议"


def test_section_map_switches_at_appendix():
    text = "# 正文\n内容\n## 附录 A\n内容\n## 正文续\n内容"
    m = audit.section_map(text.split("\n"))
    assert m[2] == "正文"
    assert m[4] == "附录"
    assert m[6] == "正文"
