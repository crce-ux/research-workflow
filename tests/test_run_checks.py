# -*- coding: utf-8 -*-
"""run_checks（落表驱动）的测试。

它接的是闭环最后一环：检查器跑完 → 发现写进待修清单。
必须成立的三件事：
  ① **按目标分段**——跑目标 B 不能冲掉目标 A 的发现；
  ② **幂等**——同一次输入跑两遍，结果一样；
  ③ **不收单一路径参数的检查器要跳过**，不能把 argparse 的 usage 当发现收进来。
"""
import pathlib

import run_checks as RC


LEDGER = """# 待修清单

## 未处置

<!-- AUTO:BEGIN · 生成 -->
## 目标：/a/设计书.md

| 检查器 | 发现 | 状态 |
|---|---|---|
| `check_design` | G1 没写证伪条件 | ☐ |
| `check_note` | N1 缺定位方式 | ☐ |

## 目标：/b/综述.md

| 检查器 | 发现 | 状态 |
|---|---|---|
| `check_review_article` | R2 有 2 行待核 | ☐ |
<!-- AUTO:END -->

## 已处置

_（空）_
"""


def _fake_checker(tmp_path, body, name="check_fake.py"):
    p = tmp_path / name
    p.write_text(body, encoding="utf-8")
    return p


def test_parse_auto_splits_by_target():
    secs = RC.parse_auto(LEDGER)
    assert set(secs) == {"/a/设计书.md", "/b/综述.md"}
    assert "check_design" in secs["/a/设计书.md"]
    assert "check_review_article" in secs["/b/综述.md"]


def test_parse_rows_skips_header_and_separator():
    secs = RC.parse_auto(LEDGER)
    rows = RC.parse_rows(secs["/a/设计书.md"])
    assert rows == {("check_design", "G1 没写证伪条件"),
                    ("check_note", "N1 缺定位方式")}


def test_running_one_target_keeps_the_other(tmp_path):
    """⭐ 核心：跑 /a 不能把 /b 的发现冲掉。"""
    secs = RC.parse_auto(LEDGER)
    secs["/a/设计书.md"] = RC.render_section(
        pathlib.Path("/a/设计书.md"), [("check_design", "G1 还是没写")], set(), [], "t")
    joined = "\n".join(secs[k] for k in sorted(secs))
    assert "check_review_article" in joined      # /b 还在
    assert "G1 还是没写" in joined                 # /a 已更新
    assert "N1 缺定位方式" not in joined            # /a 旧条目已换掉


def test_render_section_lists_findings_and_skips(tmp_path):
    # ⚠️ 用相对路径——`Path("/x.md")` 在 Windows 上会被解析成 `\x.md`
    txt = RC.render_section(pathlib.Path("x.md"),
                            [("check_design", "G1 缺证伪条件")],
                            set(), ["check_lit"], "2026-10-14 13:00")
    assert "## 目标：x.md" in txt
    assert "| `check_design` | G1 缺证伪条件 | ☐ |" in txt
    assert "`check_lit`" in txt


def test_render_section_flags_not_reproduced(tmp_path):
    txt = RC.render_section(pathlib.Path("x.md"), [], {("check_design", "旧条目")},
                            [], "t")
    assert "本次未复现" in txt and "消失 ≠ 已处置" in txt


def test_run_one_collects_findings(tmp_path):
    s = _fake_checker(tmp_path, 'print("  ❌ a.md：G1 缺证伪条件")\n'
                                'print("  ○ a.md：N4 提示")\n'
                                'print("  ✅ 全过")\n')
    fs, status = RC.run_one(s, tmp_path)
    assert status == "ok"
    assert ("a.md：G1 缺证伪条件") in fs
    assert any("N4" in f for f in fs)
    assert not any("全过" in f for f in fs)        # ✅ 行不收


def test_run_one_skips_argparse_misfits(tmp_path):
    """不收单一路径参数的检查器（如 --root 型）→ skip，不把 usage 当发现。"""
    s = _fake_checker(tmp_path, "import argparse\n"
                                "ap=argparse.ArgumentParser()\n"
                                "ap.add_argument('--root', required=True)\n"
                                "ap.parse_args()\n")
    fs, status = RC.run_one(s, tmp_path)
    assert status == "skip" and fs == []


def test_run_one_dedupes_repeated_lines(tmp_path):
    s = _fake_checker(tmp_path, 'for _ in range(3):\n'
                                '    print("  ❌ a.md：同一条")\n')
    fs, _ = RC.run_one(s, tmp_path)
    assert fs == ["a.md：同一条"]
