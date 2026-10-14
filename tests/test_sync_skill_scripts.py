# -*- coding: utf-8 -*-
"""sync_skill_scripts 的测试。

锁三件事：
  ① 副本与正本一致时报 0，不一致时报出来；
  ② **改名映射**（skill_selfcheck.py ↔ selfcheck.py）认得出来；
  ③ **不参与分发的仓整仓跳过**——否则第三方仓的自带脚本会被逐条误报成「无正本」。
"""
import pathlib

import sync_skill_scripts as S


def _make_tree(tmp_path, canon_files, skills):
    """canon_files: {正本文件名: 内容}
    skills: {skill名: {运行版文件名: 内容}}"""
    root = tmp_path / "gh"
    canon = root / "research-workflow"
    (canon / "scripts" / "checks").mkdir(parents=True)
    (canon / "SKILL.md").write_text("x", encoding="utf-8")
    for name, body in canon_files.items():
        (canon / "scripts" / "checks" / name).write_text(body, encoding="utf-8")
    for sname, files in skills.items():
        sd = root / sname / "scripts"
        sd.mkdir(parents=True)
        (root / sname / "SKILL.md").write_text("x", encoding="utf-8")
        for name, body in files.items():
            (sd / name).write_text(body, encoding="utf-8")
    return root, canon.resolve()


def _run(root, canon):
    return S.survey(root, canon, S.build_index(canon))


def test_identical_copy_passes(tmp_path):
    root, canon = _make_tree(tmp_path,
                             {"check_a.py": "A"},
                             {"skill-x": {"check_a.py": "A"}})
    drift, orphan, copies, _ = _run(root, canon)
    assert drift == [] and copies == 1


def test_drift_is_reported_with_both_paths(tmp_path):
    root, canon = _make_tree(tmp_path,
                             {"check_a.py": "A"},
                             {"skill-x": {"check_a.py": "修正过的旧版"}})
    drift, _, _, _ = _run(root, canon)
    assert len(drift) == 1
    name, fname, src, dst = drift[0]
    assert (name, fname) == ("skill-x", "check_a.py")
    assert src.read_text(encoding="utf-8") == "A"


def test_rename_mapping_is_honoured(tmp_path):
    """正本 skill_selfcheck.py ↔ 运行版 selfcheck.py——唯一一处改名。"""
    root, canon = _make_tree(tmp_path,
                             {"skill_selfcheck.py": "S"},
                             {"skill-x": {"selfcheck.py": "S"}})
    drift, orphan, copies, _ = _run(root, canon)
    assert drift == [] and orphan == [] and copies == 1


def test_rename_mapping_detects_drift(tmp_path):
    root, canon = _make_tree(tmp_path,
                             {"skill_selfcheck.py": "S"},
                             {"skill-x": {"selfcheck.py": "旧"}})
    drift, _, _, _ = _run(root, canon)
    assert len(drift) == 1 and drift[0][1] == "selfcheck.py"


def test_skill_with_no_canonical_file_is_skipped(tmp_path):
    """第三方仓自带自己的脚本 → 整仓跳过，不逐条报「无正本」。"""
    root, canon = _make_tree(tmp_path,
                             {"check_a.py": "A"},
                             {"third-party": {"own_render.mjs": "x",
                                              "own_lint.py": "y"},
                              "skill-x": {"check_a.py": "A"}})
    _, orphan, _, skipped = _run(root, canon)
    assert orphan == []
    assert skipped == ["third-party"]


def test_readme_is_not_a_distributed_artifact(tmp_path):
    root, canon = _make_tree(tmp_path,
                             {"check_a.py": "A"},
                             {"skill-x": {"check_a.py": "A", "README.md": "自带说明"}})
    _, orphan, _, _ = _run(root, canon)
    assert orphan == []


def test_orphan_inside_participating_skill_is_reported(tmp_path):
    """参与的 skill 里冒出一个正本没有的 .py → 要报（可能是漏收正本）。"""
    root, canon = _make_tree(tmp_path,
                             {"check_a.py": "A"},
                             {"skill-x": {"check_a.py": "A", "check_new.py": "N"}})
    _, orphan, _, _ = _run(root, canon)
    assert orphan == [("skill-x", "check_new.py")]


def test_canonical_repo_itself_is_not_compared(tmp_path):
    """正本仓自己也含 SKILL.md，但它不该跟自己比。"""
    root = tmp_path / "gh"
    canon = root / "research-workflow"
    (canon / "scripts" / "checks").mkdir(parents=True)
    (canon / "SKILL.md").write_text("x", encoding="utf-8")
    (canon / "scripts" / "checks" / "check_a.py").write_text("A", encoding="utf-8")
    drift, orphan, copies, skipped = S.survey(root, canon.resolve(),
                                              S.build_index(canon.resolve()))
    assert (drift, orphan, copies) == ([], [], 0)
