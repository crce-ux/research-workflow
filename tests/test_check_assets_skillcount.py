# -*- coding: utf-8 -*-
"""check_assets 第 6 类（skill 数对账）的测试。

为什么要它：2026-10-14 一次扩张（6 → 12 个 skill）在同一份文档集里留下 3 处旧数字，
**全是人肉扫出来的**——第 2 类只对脚本总数。这条补上。

⚠️ 首版判据 `(\\d+) 个…skill` 在真库上 **8 个命中里 5 个是误报**
（「科研助手有 32 个 skill」「榜单 10 个 skill」……说的都是**外部** skill）。
本文件把「哪些不该报」钉死，防它再放宽回去。
"""
import pathlib

import check_assets as CA


def _tree(tmp_path, docs, skills):
    """docs: {相对路径: 内容}；skills: {目录名: 是否有 SKILL.md}"""
    root = tmp_path / "research-workflow"
    for rel, body in docs.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
    skills_root = tmp_path / "gh"
    for name, has_skill in skills.items():
        d = skills_root / name
        d.mkdir(parents=True, exist_ok=True)
        if has_skill:
            (d / "SKILL.md").write_text("x", encoding="utf-8")
    return root, skills_root


def _run(root, skills_root):
    files = list(CA.iter_markdown(root, set()))
    rep = CA.Report()
    CA.check_skill_count(root, files, rep, skills_root)
    return rep.by_cat(6)


def test_matching_count_passes(tmp_path):
    root, sr = _tree(tmp_path,
                     {"README.md": "沉淀成 **2 个**可安装的 skill"},
                     {"a": True, "b": True})
    assert _run(root, sr) == []


def test_mismatched_count_is_reported(tmp_path):
    root, sr = _tree(tmp_path,
                     {"README.md": "沉淀成 **6 个**可安装的 skill"},
                     {"a": True, "b": True, "c": True})
    hits = _run(root, sr)
    assert len(hits) == 1 and "6" in hits[0][3] and "3" in hits[0][3]


def test_external_skill_count_is_not_our_business(tmp_path):
    """「科研助手有 32 个 skill」说的是**别人**——首版就是在这上面误报的。"""
    root, sr = _tree(tmp_path,
                     {"docs/x.md": "科研助手 `pubmed-zotero` 有 32 个 skill，全套都在。"},
                     {"a": True})
    assert _run(root, sr) == []


def test_historical_and_foreign_phrases_are_ignored(tmp_path):
    """历史记录 / 外部调研里的数字都带别的限定词——不该报。"""
    root, sr = _tree(tmp_path, {"manuals/n.md":
                                "关闭 20 个重复/无关/低频 skill\n"
                                "## 榜单 10 个 skill 逐个体检\n"
                                "### 装 1 个 skill\n"}, {"a": True})
    assert _run(root, sr) == []


def test_qualified_phrases_are_checked(tmp_path):
    """本库自己的总量声明——带限定词的三种写法都要认。"""
    root, sr = _tree(tmp_path, {"d.md":
                                "12 个配套 skill\n6 个自研 skill\n共 3 个 skill\n"},
                     {"a": True})
    hits = _run(root, sr)
    assert len(hits) == 3


def test_third_party_repo_is_not_counted(tmp_path):
    """第三方仓（remote 不是本项目）不算进来——否则 12 会变成 13。"""
    root = tmp_path / "research-workflow"
    root.mkdir()
    (root / "README.md").write_text("沉淀成 **1 个**可安装的 skill", encoding="utf-8")
    sr = tmp_path / "gh"
    for name, owner in (("ours", "github.com/crce-ux/ours"),
                        ("third", "github.com/SomeoneElse/third")):
        d = sr / name
        (d / ".git").mkdir(parents=True)
        (d / ".git" / "config").write_text(f'url = https://{owner}.git\n',
                                           encoding="utf-8")
        (d / "SKILL.md").write_text("x", encoding="utf-8")
    assert _run(root, sr) == []


def test_missing_skills_root_reports_not_evaluated(tmp_path):
    root, _ = _tree(tmp_path, {"README.md": "x"}, {})
    rep = CA.Report()
    CA.check_skill_count(root, list(CA.iter_markdown(root, set())), rep,
                         pathlib.Path(tmp_path) / "nope")
    hits = rep.by_cat(6)
    assert len(hits) == 1 and "未评" in hits[0][3]
