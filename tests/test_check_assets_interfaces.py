# -*- coding: utf-8 -*-
"""check_assets 第 7 类（接口声明）的测试。

为什么要它：工序地图原先只说明「哪段归哪个 skill」，没说「谁的输出是谁的输入」。
十个 SKILL.md 之间对彼此的提及共三处，没有一处是接口声明。
2026-10-15 补完十个 skill 的「上下游接口」一节，立这条规则防它漂回去。

⚠️ 只查自研 skill——第三方仓（video-talkcraft）自动排除，下面钉死这一点。
"""
import pathlib

import check_assets as CA

SECTION = "\n## 上下游接口\n\n**上游给我什么**\n\n**我给下游什么**\n"


def _tree(tmp_path, skills):
    """skills: {目录名: 是否有接口节 或 None=没有 SKILL.md}"""
    root = tmp_path / "research-workflow"
    root.mkdir()
    sr = tmp_path / "gh"
    for name, has in skills.items():
        d = sr / name
        d.mkdir(parents=True)
        if has is None:
            continue
        body = "# x\n" + (SECTION if has else "\n## 别的节\n")
        (d / "SKILL.md").write_text(body, encoding="utf-8")
    return root, sr


def _run(root, sr):
    rep = CA.Report()
    CA.check_interfaces(root, rep, sr)
    return rep.by_cat(7)


def test_skill_with_section_passes(tmp_path):
    root, sr = _tree(tmp_path, {"a": True})
    assert _run(root, sr) == []


def test_missing_section_is_reported(tmp_path):
    root, sr = _tree(tmp_path, {"a": True, "b": False})
    hits = _run(root, sr)
    assert len(hits) == 1 and "上下游接口" in hits[0][3]


def test_partial_section_is_reported(tmp_path):
    """只有标题、缺两个子块，也要报——三样都算判据。"""
    root = tmp_path / "research-workflow"
    root.mkdir()
    sr = tmp_path / "gh"
    d = sr / "half"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text("# x\n## 上下游接口\n随便写点\n", encoding="utf-8")
    hits = _run(root, sr)
    assert len(hits) == 1
    assert "上游给我什么" in hits[0][3] and "我给下游什么" in hits[0][3]


def test_third_party_repo_is_skipped(tmp_path):
    """第三方仓没有这一节也不算错——归属过滤要盖住。"""
    root, sr = _tree(tmp_path, {"ours": True})
    third = sr / "third"
    (third / ".git").mkdir(parents=True)
    (third / ".git" / "config").write_text(
        "url = https://github.com/SomeoneElse/third.git\n", encoding="utf-8")
    (third / "SKILL.md").write_text("# x\n没有接口节\n", encoding="utf-8")
    assert _run(root, sr) == []


def test_nested_package_is_checked(tmp_path):
    """总仓内嵌的 skill 包也要查。"""
    root = tmp_path / "research-workflow"
    root.mkdir()
    sr = tmp_path / "gh"
    pack = sr / "total" / "skills" / "inner"
    pack.mkdir(parents=True)
    (pack / "SKILL.md").write_text("# x\n没有接口节\n", encoding="utf-8")
    hits = _run(root, sr)
    assert len(hits) == 1 and hits[0][1].name == "SKILL.md"


def test_missing_skills_root_reports_not_evaluated(tmp_path):
    root = tmp_path / "research-workflow"
    root.mkdir()
    rep = CA.Report()
    CA.check_interfaces(root, rep, tmp_path / "nope")
    hits = rep.by_cat(7)
    assert len(hits) == 1 and "未评" in hits[0][3]
