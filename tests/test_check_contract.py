# -*- coding: utf-8 -*-
"""check_contract：阶段映射、改动行数、日志写入、退出码。"""
import json
from pathlib import Path

import pytest

import check_contract as cc

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = ROOT / "examples" / "bad.md"


def test_stage_tables_cover_expected():
    assert "drafting" in cc.STAGES
    assert "retrieval" in cc.NOT_TAKEN_OVER
    assert "figures" in cc.NOT_TAKEN_OVER


def test_diff_lines_counts_changes(tmp_path):
    a = tmp_path / "a.md"
    b = tmp_path / "b.md"
    a.write_text("一\n二\n三\n", encoding="utf-8")
    b.write_text("一\n二改\n三\n四\n", encoding="utf-8")
    # 改一行 = 一增一删；新增一行 = 一增
    assert cc.diff_lines(a, b) == 3


def test_diff_lines_zero_when_same(tmp_path):
    a = tmp_path / "a.md"
    a.write_text("同\n", encoding="utf-8")
    assert cc.diff_lines(a, a) == 0


def test_run_writes_log_and_fails(tmp_path, monkeypatch):
    log = tmp_path / "log.jsonl"
    monkeypatch.setattr("sys.argv", ["check_contract.py", "--stage", "drafting",
                                     "--file", str(SAMPLE), "--raw", str(SAMPLE),
                                     "--log", str(log), "--quiet"])
    rc = cc.main()
    assert rc == 1
    rec = json.loads(log.read_text(encoding="utf-8").strip())
    assert rec["stage"] == "drafting"
    assert rec["verdict"] == "fail"
    assert rec["levels"]["硬规则"] > 0
    assert rec["human_diff_lines"] == 0


def test_not_taken_over_returns_2(tmp_path, monkeypatch):
    log = tmp_path / "log.jsonl"
    monkeypatch.setattr("sys.argv", ["check_contract.py", "--stage", "retrieval",
                                     "--file", str(SAMPLE), "--log", str(log)])
    assert cc.main() == 2
    assert not log.exists()
