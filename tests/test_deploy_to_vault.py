# -*- coding: utf-8 -*-
"""deploy_to_vault 的测试。

它管的是**第三套副本**——观测库 `.claude/skills/` 下真正被 agent 加载的目录。
本文件只测纯函数：比对、覆盖、以及**哪些文件不该参与比对**。
"""
import pathlib

import deploy_to_vault as DV


def _mk(base, files):
    for rel, body in files.items():
        p = base / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
    return base


def test_diff_detects_all_three_kinds(tmp_path):
    src = _mk(tmp_path / "repo", {"SKILL.md": "v2", "a.md": "same", "new.md": "n"})
    dst = _mk(tmp_path / "vault", {"SKILL.md": "v1", "a.md": "same", "old.md": "o"})
    only_src, only_dst, changed = DV.diff_one(src, dst)
    assert only_src == ["new.md"]
    assert only_dst == ["old.md"]
    assert changed == ["SKILL.md"]


def test_gitignore_不参与比对(tmp_path):
    """⭐ .gitignore 是**仓的元数据**，不是 skill 内容。
    不排掉它会永远报一条假差异，把真信号淹掉。"""
    src = _mk(tmp_path / "repo", {"SKILL.md": "x", ".gitignore": "__pycache__/"})
    dst = _mk(tmp_path / "vault", {"SKILL.md": "x"})
    assert DV.diff_one(src, dst) == ([], [], [])


def test_pycache_与_github_不参与比对(tmp_path):
    src = _mk(tmp_path / "repo", {
        "SKILL.md": "x",
        ".github/workflows/ci.yml": "on: push",
        "scripts/__pycache__/x.cpython-311.pyc": "junk",
    })
    dst = _mk(tmp_path / "vault", {"SKILL.md": "x"})
    assert DV.diff_one(src, dst) == ([], [], [])


def test_copy_tree_覆盖差异(tmp_path):
    src = _mk(tmp_path / "repo", {"SKILL.md": "v2", "new.md": "n"})
    dst = _mk(tmp_path / "vault", {"SKILL.md": "v1"})
    DV.copy_tree(src, dst)
    assert (dst / "SKILL.md").read_text(encoding="utf-8") == "v2"
    assert (dst / "new.md").is_file()
    assert DV.diff_one(src, dst) == ([], [], [])


def test_copy_tree_不删库里的多余文件(tmp_path):
    """⚠️ 方向是仓 → 库，**只增改，不删**。
    库里多出来的东西由人判断——自动删是不可逆的。"""
    src = _mk(tmp_path / "repo", {"SKILL.md": "v2"})
    dst = _mk(tmp_path / "vault", {"SKILL.md": "v1", "local-only.md": "keep"})
    DV.copy_tree(src, dst)
    assert (dst / "local-only.md").is_file()
