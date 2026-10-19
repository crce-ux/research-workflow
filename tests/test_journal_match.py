# -*- coding: utf-8 -*-
"""journal_match 的数值解析、排序与数据目录解析。

JCR 的 IF 列有 `<0.1` 这类区间写法，`sort_pool` 曾直接 `float()` 抛 ValueError。
"""
import importlib
import sys

import pytest


@pytest.fixture()
def jm(tmp_path, monkeypatch):
    for n in ("FQBJCR2025-UTF8.csv", "JCR2024-UTF8.csv", "GJQKYJMD2025.csv"):
        (tmp_path / n).write_text("", encoding="utf-8")
    monkeypatch.setenv("JOURNAL_DATA_DIR", str(tmp_path))
    sys.modules.pop("fetch_journal_metrics", None)
    sys.modules.pop("journal_match", None)
    return importlib.import_module("journal_match")


def test_ifnum_range_notation(jm):
    assert jm.ifnum("<0.1") == 0.1
    assert jm.ifnum("65.8") == 65.8
    assert jm.ifnum("") == 0.0
    assert jm.ifnum(None) == 0.0


def test_sort_pool_handles_range_if(jm):
    pool = [{"name": "A", "if": "<0.1", "zone": "4"},
            {"name": "B", "if": "9.0", "zone": "1"}]
    assert [x["name"] for x in jm.sort_pool(pool, "if")] == ["B", "A"]
    assert [x["name"] for x in jm.sort_pool(pool, "zone")] == ["B", "A"]


def test_data_dir_from_env(jm, tmp_path):
    assert jm.FJM.DATA_DIR == str(tmp_path)
