# -*- coding: utf-8 -*-
"""pick_layout 的测试。

要钉死三件事：
  ① 特征只从**内容字段**抽，不读「版式建议」——否则成了自问自答
  ② 缺料要报出来，不能只排序了算
  ③ 配方表找不到时必须报「本次未评」，不静默通过
"""
import json
import pathlib
import sys

import pytest

import pick_layout as pl

RECIPES = pathlib.Path(__file__).resolve().parent.parent.parent / \
    "academic-slides" / "scripts" / "recipes.json"


def _recipes():
    if not RECIPES.is_file():
        pytest.skip(f"配方表不在：{RECIPES}")
    return json.loads(RECIPES.read_text(encoding="utf-8"))["recipes"]


def _page(labels, marks="①②③④⑤⑥⑦"):
    """labels = [(字段标签, 内容), …]，与七个编号一一对应。"""
    return "## S3 · 某页\n" + "\n".join(f"**{m} {lb}**：{tx}"
                                      for m, (lb, tx) in zip(marks, labels))


# ── 解析 ──────────────────────────────────────────────────────

def test_split_pages():
    t = "## S1 · 封面\n内容\n## S2 · 二页\n内容"
    assert [p[0] for p in pl.split_pages(t)] == ["S1", "S2"]


def test_parse_fields_recognizes_kinds():
    body = _page([("标题", "某页"), ("版式建议", "配方 17"),
                  ("页面文字", "三段"), ("表格数据", "无"),
                  ("图表说明", "不配图"), ("讲稿备注", "开场"),
                  ("口径提醒", "别念错")])
    f = pl.parse_fields(body)
    assert set(f) == {"标题", "版式", "正文", "表格", "图注", "讲稿", "口径"}


def test_zhuangtu_alias():
    f = pl.parse_fields("**⑤ 图表说明**：不配图")
    assert "图注" in f


# ── 特征只看内容字段 ──────────────────────────────────────────

def test_features_ignore_banshi_suggestion():
    """「版式建议」里写了「表格」两个字，不能把这一页判成有表格。"""
    a = _page([("标题", "x"), ("版式建议", "配方 4 表格+引出线"),
               ("页面文字", "一句话"), ("表格数据", "无"),
               ("图表说明", "不配图"), ("讲稿备注", ""), ("口径提醒", "")])
    fa = pl.features(pl.parse_fields(a))
    assert fa["tables"] == 0, "版式建议里的「表格」不该被算成内容里的表"


def test_table_field_counts():
    b = _page([("标题", "x"), ("版式建议", ""), ("页面文字", "一句话"),
               ("表格数据", "| A | B |\n| 1 | 2 |"), ("图表说明", ""),
               ("讲稿备注", ""), ("口径提醒", "")])
    fb = pl.features(pl.parse_fields(b))
    assert fb["tables"] == 1


def test_numbers_exclude_years():
    c = _page([("标题", "x"), ("版式建议", ""),
               ("页面文字", "2025 年发表，命中 15% 与 30 条"),
               ("表格数据", "无"), ("图表说明", ""),
               ("讲稿备注", ""), ("口径提醒", "")])
    fc = pl.features(pl.parse_fields(c))
    assert fc["numbers"] == 2, "年份不该算作关键数字"


# ── 排序与缺料 ────────────────────────────────────────────────

def test_data_card_page_ranks_shuju_kapian():
    """三个数据点的页面 → 数据卡片（配方 17）应进前列。"""
    d = _page([("标题", "氯氮平"), ("版式建议", ""),
               ("页面文字", "TRS 占 15–30%；氯氮平约 30–40% 不应答；共 300 例"),
               ("表格数据", "无"), ("图表说明", ""),
               ("讲稿备注", ""), ("口径提醒", "")])
    f = pl.parse_fields(d)
    feat = pl.features(f)
    content = "\n".join(pl.clean(f.get(k, "")) for k in pl.CONTENT_KINDS)
    top = [r["id"] for r, *_ in pl.rank(content, feat, _recipes(), 4)]
    assert 17 in top


def test_missing_material_is_reported():
    """制作稿没给数字，而配方要数字 → 要报缺料。"""
    recipes = _recipes()
    r17 = next(r for r in recipes if r["id"] == 17)
    e = _page([("标题", "x"), ("版式建议", ""), ("页面文字", "只有文字没有数"),
               ("表格数据", "无"), ("图表说明", ""),
               ("讲稿备注", ""), ("口径提醒", "")])
    f = pl.parse_fields(e)
    _, _, miss = pl.score(r17, pl.features(f),
                          "\n".join(pl.clean(f.get(k, "")) for k in pl.CONTENT_KINDS))
    assert miss and any("数字" in m for m in miss)


# ── 自检与「本次未评」─────────────────────────────────────────

def test_audit_passes_on_real_table():
    recipes = _recipes()
    here = pathlib.Path(pl.__file__).resolve().parent
    root = here.parent.parent.parent          # D:/Github
    doc = root / "academic-slides" / "references" / "layout-recipes.md"
    skel = root / "academic-slides" / "assets" / "skeletons"
    if not (doc.is_file() and skel.is_dir()):
        pytest.skip("配方文档或骨架目录不在")
    assert pl.audit(recipes, doc, skel) == 0


def test_audit_flags_missing_skeleton():
    recipes = [{"id": 99, "name": "x", "skeleton": "不存在.svg",
                "needs": {}, "triggers": []}]
    assert pl.audit(recipes, None, None) == 1


def test_missing_recipes_reports_not_evaluated(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(pl, "__file__", str(tmp_path / "scripts" / "pick_layout.py"))
    assert pl.find_recipes() is None
