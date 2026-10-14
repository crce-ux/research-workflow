# -*- coding: utf-8 -*-
"""check_review 的规则测试。

锁六组硬规则 + 两类「不判」豁免。每条规则一个「会响」的用例，
否则某条可能写了正则却永远匹配不上。
"""
import pathlib

import check_review as cr


def W(text, name="审稿意见_X-1.md", tmp=None):
    p = pathlib.Path(tmp or ".") / name
    p.write_text(text, encoding="utf-8")
    return p


BASE = """**Manuscript ID:** X-1

**Recommendation:** Minor Revision

本研究在 N 例患者中探讨了暴露与结局的关系，问题有临床意义，设计总体可靠，
但有几处需要澄清，结论方为稳妥。以下是若干可能有助于改进本文的意见。

1. The definition of the outcome is not stated in the Methods. Please state it.
2. In Table 2 the confidence intervals are missing. Please add them, and reconcile
   the N in line 187 with Figure 1.
3. The analysis set is unclear in the Results. Please explain the choice.

**References (for the authors' consideration)**
1. Smith J. Something. *J*. 2024;1(1):1-2.
"""


def run(text, name="审稿意见_X-1.md", tmp_path=None):
    p = W(text, name, str(tmp_path) if tmp_path else None)
    try:
        return cr.check(p)
    finally:
        p.unlink()


def test_good_review_passes(tmp_path):
    hits, _ = run(BASE, tmp_path=tmp_path)
    assert hits == []


def test_v1_missing_recommendation(tmp_path):
    hits, _ = run(BASE.replace("**Recommendation:** Minor Revision\n", ""), tmp_path=tmp_path)
    assert any("V1" in h for h in hits)


def test_v1_bad_tier(tmp_path):
    hits, _ = run(BASE.replace("Minor Revision", "Looks fine to me"), tmp_path=tmp_path)
    assert any("V1" in h for h in hits)


def test_v3_too_few(tmp_path):
    text = BASE.replace("2. In Table 2", "X. In Table 2").replace("3. The analysis", "Y. The analysis")
    hits, _ = run(text, tmp_path=tmp_path)
    assert any("V3" in h for h in hits)


def test_v4_comment_without_request(tmp_path):
    text = BASE.replace(
        "3. The analysis set is unclear in the Results. Please explain the choice.",
        "3. The analysis set is unclear in the Results.")
    hits, _ = run(text, tmp_path=tmp_path)
    assert any("V4" in h and "3" in h for h in hits)


def test_v5_misconduct_in_author_text(tmp_path):
    text = BASE.replace("in the Methods. Please state it.",
                        "in the Methods; this looks like data fabrication. Please state it.")
    hits, _ = run(text, tmp_path=tmp_path)
    assert any("V5" in h for h in hits)


def test_v5_misconduct_in_confidential_section_is_fine(tmp_path):
    """诚信疑虑写进保密节是对的，不能反被判违规。"""
    text = BASE + """
## 给编辑的保密意见（不向作者展示）

数据疑似造假，建议核查原始数据。
"""
    hits, _ = run(text, tmp_path=tmp_path)
    assert not any("V5" in h for h in hits)


def test_v6_confidential_section_without_marker(tmp_path):
    text = BASE + "\n## 给编辑的保密意见\n\n推荐 Minor Revision。\n"
    hits, _ = run(text, tmp_path=tmp_path)
    assert any("V6" in h for h in hits)


def test_references_tail_is_not_a_confidential_section(tmp_path):
    """真实定稿以 References 结尾——那不是密评节，不该报 V6。"""
    hits, _ = run(BASE, tmp_path=tmp_path)
    assert not any("V6" in h for h in hits)


def test_draft_is_skipped(tmp_path):
    text = BASE + "\n## 〇、给陈晨的备忘录（中文，勿提交此节）\n\n随便写点。\n"
    hits, soft = run(text, tmp_path=tmp_path)
    assert hits == []
    assert any("草稿" in s for s in soft)


def test_confidential_letter_is_skipped(tmp_path):
    text = "> **不向作者展示**。提交时填入 Confidential Comments to the Editor 字段。\n\n**Recommendation:** Minor Revision\n"
    hits, soft = run(text, tmp_path=tmp_path)
    assert hits == []
    assert any("密评" in s for s in soft)


def test_v7_reports_but_does_not_fail(tmp_path):
    text = BASE.replace("in the Methods. Please state it.", "and should be fixed. Please state it.")
    hits, soft = run(text, tmp_path=tmp_path)
    assert not any("V7" in h for h in hits)
    assert any("V7" in s for s in soft)
