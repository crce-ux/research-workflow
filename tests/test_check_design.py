# -*- coding: utf-8 -*-
"""check_design 的规则测试。

一条铁律一个「会响」的用例。另锁两条实测踩过的坑：
① G6 必须全篇查（本库设计书用粗体伪标题，按章节切会漏）
② 风险表四列按表头查，不按正文关键词查
"""
import check_design as cd


GOOD = """# 某某研究设计书

## 2.4 研究假设与目标

**假设 H1**：A 与 B 正相关。若 A 与 B 无关（p>0.05 且效应量 <0.2），则 H1 不成立。
**假设 H2**：C 高于 D。若两组差异无统计学意义，则 H2 不成立。

## 3.2 研究对象与样本量

乐观情形：效应量 d=0.5，N=64。保守情形：效应量 d=0.3，N=176。
按脱落率 20% 上浮后需招募 N=220。

## 6.5.1 伦理审查

已取得伦理批件号 2026-KY-012。

## 6.5.3 预注册

将在 ChiCTR 注册，数据采集前完成。

## 8. 可行性评估与风险应对

### 8.1 可行性

可招募 300 例，需求 220 例，满足。

### 8.2 风险与应对

| 风险 | 概率 | 影响 | 应对 |
|---|---|---|---|
| 入组慢 | 中 | 延期 | 延长窗口 |
"""


def secs(t):
    return cd.sections(t)


def test_good_design_passes(tmp_path):
    p = tmp_path / "设计书.md"
    p.write_text(GOOD, encoding="utf-8")
    hits, _ = cd.check(p)
    assert hits == []


def test_g1_missing_falsification(tmp_path):
    p = tmp_path / "设计书.md"
    p.write_text(GOOD.replace("若 A 与 B 无关（p>0.05 且效应量 <0.2），则 H1 不成立。", ""),
                 encoding="utf-8")
    hits, _ = cd.check(p)
    assert any("G1" in h for h in hits)


def test_g2_missing_conservative(tmp_path):
    p = tmp_path / "设计书.md"
    p.write_text(GOOD.replace(
        "乐观情形：效应量 d=0.5，N=64。保守情形：效应量 d=0.3，N=176。",
        "效应量 d=0.5，N=64。"), encoding="utf-8")
    hits, _ = cd.check(p)
    assert any("G2" in h for h in hits)


def test_g3_missing_dropout(tmp_path):
    p = tmp_path / "设计书.md"
    p.write_text(GOOD.replace("按脱落率 20% 上浮后需招募 N=220。", ""), encoding="utf-8")
    hits, _ = cd.check(p)
    assert any("G3" in h for h in hits)


def test_g4_risk_table_missing_column(tmp_path):
    p = tmp_path / "设计书.md"
    p.write_text(GOOD.replace("| 风险 | 概率 | 影响 | 应对 |", "| 风险 | 概率 | 应对 |"),
                 encoding="utf-8")
    hits, _ = cd.check(p)
    assert any("G4" in h for h in hits)


def test_g6_scans_whole_document_not_just_the_section(tmp_path):
    """⚠️ 实测踩过：设计书用 `**（3）预注册**` 这种粗体伪标题，
    按章节切会漏掉平台，把「写了」判成「没写」。"""
    text = GOOD.replace("将在 ChiCTR 注册，数据采集前完成。", "见 5.7 第（3）节。")
    text += "\n\n## 5.7 统计严谨性\n\n**（3）预注册与透明度**\n\n预注册平台：**ClinicalTrials.gov** 或 OSF。\n"
    p = tmp_path / "设计书.md"
    p.write_text(text, encoding="utf-8")
    hits, _ = cd.check(p)
    assert not any("G6" in h and "注册" in h for h in hits)


def test_g6_fires_when_truly_absent(tmp_path):
    text = GOOD.replace("将在 ChiCTR 注册，数据采集前完成。", "待定。")
    p = tmp_path / "设计书.md"
    p.write_text(text, encoding="utf-8")
    hits, _ = cd.check(p)
    assert any("G6" in h and "注册" in h for h in hits)


def test_g5_is_soft(tmp_path):
    text = GOOD.replace("可招募 300 例，需求 220 例，满足。", "预计可满足。")
    p = tmp_path / "设计书.md"
    p.write_text(text, encoding="utf-8")
    hits, soft = cd.check(p)
    assert not any("G5" in h for h in hits)
    assert any("G5" in s for s in soft)


def test_deliverables_lists_missing_kinds(tmp_path):
    notes = cd.check_deliverables(tmp_path)
    assert len(notes) == len(cd.DELIVERABLES)


def test_deliverables_finds_present_kind(tmp_path):
    (tmp_path / "01_研究设计书.md").write_text("x", encoding="utf-8")
    notes = cd.check_deliverables(tmp_path)
    assert not any("研究设计书" in n for n in notes)


def test_missing_sections_are_reported_as_not_evaluated(tmp_path):
    """⚠️ 实测踩过：设想稿没有假设节/样本量节，四条规则会**全部静默跳过**，
    屏幕上却显示「全过」——那是假象。必须把「没评到」说出来。"""
    p = tmp_path / "设计书.md"
    p.write_text("# 各设想的具体设计\n\n### D1 · 某个设想\n\n随便写写。\n", encoding="utf-8")
    hits, soft = cd.check(p)
    assert hits == []
    assert any("本次未评" in s for s in soft)
