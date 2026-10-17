# -*- coding: utf-8 -*-
"""check_routes：路由节存在、指向的文件真实、行数不超限。"""
import pathlib
import subprocess
import sys

CHECKS = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "checks"
SCRIPT = CHECKS / "check_routes.py"


def run(root: pathlib.Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), "--root", str(root)],
                          capture_output=True, text=True, encoding="utf-8",
                          env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})


def make_skill(root: pathlib.Path, name: str, body: str) -> pathlib.Path:
    d = root / name
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(body, encoding="utf-8")
    return d


GOOD = "# 甲\n\n## 读什么\n\n- 起草 → `references/drafting.md`\n"


def test_good_route_passes(tmp_path):
    d = make_skill(tmp_path, "甲", GOOD)
    (d / "references").mkdir()
    (d / "references" / "drafting.md").write_text("x", encoding="utf-8")
    r = run(tmp_path)
    assert r.returncode == 0, r.stdout


def test_missing_section_is_reported(tmp_path):
    make_skill(tmp_path, "乙", "# 乙\n\n## 正文\n")
    r = run(tmp_path)
    assert r.returncode == 1
    assert "没有 `## 读什么`" in r.stdout


def test_dangling_path_is_reported(tmp_path):
    make_skill(tmp_path, "丙", GOOD)          # 不建 references/drafting.md
    r = run(tmp_path)
    assert r.returncode == 1
    assert "不存在的文件" in r.stdout


def test_too_many_lines_is_reported(tmp_path):
    d = make_skill(tmp_path, "丁", GOOD)
    (d / "references").mkdir()
    (d / "references" / "drafting.md").write_text("x", encoding="utf-8")
    lines = "\n".join(f"- 第 {i} 行 → `references/drafting.md`" for i in range(13))
    (d / "SKILL.md").write_text("# 丁\n\n## 读什么\n\n" + lines + "\n", encoding="utf-8")
    r = run(tmp_path)
    assert r.returncode == 1
    assert "超过 12" in r.stdout
