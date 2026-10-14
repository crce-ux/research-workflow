# -*- coding: utf-8 -*-
"""dedupe_refs 的测试。

⭐ 判据次序 DOI → PMID → 归一化标题，且**标题太短宁可不合**——
   去重做没做干净会一路带到覆盖声明（N 含重复 → M、K 全歪）。
"""
import pathlib

import dedupe_refs as DR


def test_doi_归一化去掉前缀与大小写():
    assert DR.norm_doi("https://doi.org/10.1000/ABC") == "10.1000/abc"
    assert DR.norm_doi("doi:10.1000/Abc ") == "10.1000/abc"
    assert DR.norm_doi("10.1000/abc") == "10.1000/abc"
    assert DR.norm_doi("") == ""


def test_pmid_取数字():
    assert DR.norm_pmid("PMID: 41234567") == "41234567"
    assert DR.norm_pmid("PMID 41234567") == "41234567"
    assert DR.norm_pmid("无") == ""


def test_标题归一化():
    assert DR.norm_title("Clozapine Response: A Meta-analysis!") == \
           DR.norm_title("clozapine response  a metaanalysis")


def test_doi优先于标题():
    a = {"doi": "10.1/x", "title": "完全不同的标题一"}
    b = {"doi": "10.1/X", "title": "完全不同的标题二"}
    assert DR.key_of(a) == DR.key_of(b)


def test_无doi时用pmid():
    a = {"doi": "", "pmid": "12345", "title": "标题甲"}
    b = {"doi": "", "pmid": "PMID:12345", "title": "标题乙"}
    assert DR.key_of(a) == DR.key_of(b)


def test_都没有时用归一化标题():
    t = "Clozapine response and claustrum connectivity in TRS"
    assert DR.key_of({"title": t}) == DR.key_of({"title": t.upper()})


def test_短标题不给键():
    """⭐ 标题太短容易误合并——宁可不合。"""
    assert DR.key_of({"title": "Editorial"}) is None
    assert DR.key_of({"title": ""}) is None


def test_读ris():
    p = pathlib.Path(__file__).parent / "_tmp.ris"
    p.write_text("TY  - JOUR\nTI  - Title A\nDO  - 10.1/a\n\n"
                 "TY  - JOUR\nTI  - Title B\nDO  - 10.1/A\n", encoding="utf-8")
    try:
        _, rows = DR.load(p)
        assert len(rows) == 2
        assert DR.key_of(rows[0]) == DR.key_of(rows[1])
    finally:
        p.unlink()


def test_读csv按表头认列(tmp_path):
    f = tmp_path / "refs.csv"
    f.write_text("标题,DOI,PMID\n标题甲,10.1/a,111\n标题乙,10.1/A,222\n",
                 encoding="utf-8")
    head, rows = DR.load(f)
    assert head == ["标题", "DOI", "PMID"]
    assert DR.key_of(rows[0]) == DR.key_of(rows[1])


def test_读无表头的纯行(tmp_path):
    f = tmp_path / "refs.txt"
    f.write_text("标题甲|10.1/a\n标题乙|10.1/A\n", encoding="utf-8")
    head, rows = DR.load(f)
    assert head is None and len(rows) == 2
