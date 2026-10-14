# -*- coding: utf-8 -*-
"""check_assets 第 2 类（脚本总数对账）的测试。

⚠️ 起因是一个**一直靠运气通过**的缺陷：
原先用 `most_common(1)` 自称值——README 写「脚本 44 个（Python 43 个 + setup.sh 1 个）」时
**两个数字出现次数相同，随便挑一个**；而且拿「总数」跟「只数 .py」的实际值比，
两边量的根本不是一回事。修完钉死在本用例。
"""
import pathlib

import check_assets as CA


def _tree(tmp_path, py=0, sh=0, readme=""):
    root = tmp_path / "rw"
    (root / "scripts").mkdir(parents=True)
    for i in range(py):
        (root / "scripts" / f"a{i}.py").write_text("x", encoding="utf-8")
    for i in range(sh):
        (root / "scripts" / f"s{i}.sh").write_text("x", encoding="utf-8")
    (root / "scripts" / "README.md").write_text(readme, encoding="utf-8")
    return root


def _run(root):
    rep = CA.Report()
    CA.check_script_count(root, set(), rep)
    return rep.by_cat(2)


def test_total_counts_py_and_sh(tmp_path):
    """⭐ README 自称的是**总数**，实际值必须含 .sh。"""
    root = _tree(tmp_path, py=3, sh=1,
                 readme="**脚本 4 个（Python 3 个 + `setup.sh` 1 个）。**")
    assert _run(root) == []


def test_uses_the_total_not_a_component(tmp_path):
    """⭐ 同一句里有 4 和 3 两个数——只认「脚本 N 个」句首的数字。"""
    root = _tree(tmp_path, py=3, sh=1,
                 readme="**脚本 4 个（Python 3 个 + `setup.sh` 1 个）。**")
    assert _run(root) == []          # 旧实现可能挑到 3 而误报


def test_mismatch_is_reported(tmp_path):
    root = _tree(tmp_path, py=3, sh=1, readme="**脚本 9 个（Python 8 个 + 1）。**")
    hits = _run(root)
    assert len(hits) == 1 and "9" in hits[0][3] and "4" in hits[0][3]


def test_missing_readme_is_reported(tmp_path):
    root = tmp_path / "rw"
    (root / "scripts").mkdir(parents=True)
    assert _run(root)                      # README 不存在 → 报
