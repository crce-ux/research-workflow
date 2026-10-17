# -*- coding: utf-8 -*-
"""check_manuals：手册是否都有登记、登记是否指向真实文件、结论是否合法。"""
import os
import pathlib
import subprocess
import sys

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "checks" / "check_manuals.py"


def run(root: pathlib.Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), "--root", str(root)],
                          capture_output=True, text=True, encoding="utf-8",
                          env={**os.environ, "PYTHONIOENCODING": "utf-8"})


def build(root: pathlib.Path, rows: str, manuals: list[str]) -> None:
    (root / "manuals").mkdir(parents=True)
    (root / "docs").mkdir()
    (root / "docs" / "manuals.md").write_text(
        "| 手册 | 节数 | 结论 | 去向 | 备注 |\n|---|---:|---|---|---|\n" + rows,
        encoding="utf-8")
    for m in manuals:
        p = root / "manuals" / m
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# x\n", encoding="utf-8")


def test_fully_registered_passes(tmp_path):
    build(tmp_path, "| `甲.md` | 1 | 已收 | a |  |\n", ["甲.md"])
    r = run(tmp_path)
    assert r.returncode == 0, r.stdout


def test_unregistered_manual_is_reported(tmp_path):
    build(tmp_path, "| `甲.md` | 1 | 已收 | a |  |\n", ["甲.md", "乙.md"])
    r = run(tmp_path)
    assert r.returncode == 1
    assert "未登记" in r.stdout


def test_row_pointing_at_missing_file_is_reported(tmp_path):
    build(tmp_path, "| `已删.md` | 1 | 不收 | — |  |\n", ["甲.md"])
    r = run(tmp_path)
    assert r.returncode >= 1
    assert "文件不存在" in r.stdout


def test_unknown_conclusion_is_reported(tmp_path):
    build(tmp_path, "| `甲.md` | 1 | 待定 | a |  |\n", ["甲.md"])
    r = run(tmp_path)
    assert r.returncode == 1
    assert "不在 已收 / 不收 里" in r.stdout


def test_no_manuals_dir_is_not_an_error(tmp_path):
    r = run(tmp_path)
    assert r.returncode == 0
    assert "本次未评" in r.stdout
