# -*- coding: utf-8 -*-
"""ledger_to_cv（成果台账 → 简历清单）的测试。

锁六件事：
  ① 按**表头**认表，不按位置
  ② 论文只导「已发表 / 已接收」——在投在写不进正式清单
  ③ 近 N 年筛选；**年份缺失的不筛掉，单列待补**
  ④ 论文按署名优先级排序
  ⑤ 整行占位的不进结果
  ⑥ 台账没有年份时，标题要说明「未按年份筛」，不能装作筛过了
"""
import ledger_to_cv as L


LEDGER = """# 成果台账

## 二、论文

| # | 状态 | 标题 | 期刊 | 年 | 卷期页 | DOI / PMID | 署名情况 | 作者总数 | 我的位次 | 项目归属 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 已发表 | 甲论文 | J1 | 2024 | 1(1):1-9 | 10.1/a | 其他（第 3 作者） | 8 | 3 | X |
| 2 | 已发表 | 乙论文 | J2 | 2022 | 2(2):2-9 | 10.1/b | 唯一第一作者 | 8 | 1 | X |
| 3 | 在投 | 丙论文 | J3 | 2024 | | 10.1/c | 唯一第一作者 | 5 | 1 | X |
| 4 | 已接收 | 丁论文 | J4 |  | | 10.1/d | 共同通讯作者 | 9 | 8 | X |
| — | — | *(待填)* | | | | | | | | |

## 三、基金项目

| # | 状态 | 项目名称 | 来源 | 编号 | 角色 | 起止 | 经费 |
|---|---|---|---|---|---|---|---|
| 1 | 在研 | 某基金 | NSFC | 123 | 主持 | 2023-2026 | 30万 |
| 2 | 结题 | 旧基金 | 校级 | 45 | 参与 | 2018-2020 | 5万 |
"""


def run(tmp_path):
    p = tmp_path / "成果台账.md"
    p.write_text(LEDGER, encoding="utf-8")
    return L.render(L.parse_tables(LEDGER), 5, 2026)


def test_recognizes_all_tables():
    t = L.parse_tables(LEDGER)
    assert set(t) == {"论文", "基金项目"}
    assert len(t["论文"][1]) == 4        # 占位行已跳过


def test_paper_section(tmp_path):
    md = run(tmp_path)
    # 2026 的近五年 = 2022–2026 → 甲(2024) 与 乙(2022) 在窗内；丙「在投」排除；
    # 丁无年份 → 进「年份待补」，不计入正文篇数
    assert "## 一、代表性论文（2 篇）" in md
    assert "甲论文" in md and "乙论文" in md and "丁论文" in md
    assert "丙论文" not in md
    assert "另有 1 条状态为「在投 / 在写」" in md


def test_five_year_window(tmp_path):
    md = run(tmp_path)
    assert "乙论文" in md            # 2022 是边界年，**在**窗内
    assert "旧基金" not in md         # 2018 出窗
    assert "某基金" in md


def test_missing_year_is_listed_not_dropped(tmp_path):
    md = run(tmp_path)
    assert "年份待补" in md and "丁论文" in md


def test_credit_order(tmp_path):
    """唯一第一作者（乙）应排在 其他（第3作者）（甲）之前。"""
    md = run(tmp_path)
    assert md.index("乙论文") < md.index("甲论文")


def test_no_year_header_says_so(tmp_path):
    p = tmp_path / "l.md"
    p.write_text(LEDGER.replace("2024", "").replace("2022", "")
                        .replace("2023-2026", "").replace("2018-2020", ""),
                 encoding="utf-8")
    md = L.render(L.parse_tables(p.read_text(encoding="utf-8")), 5, 9999)
    assert "未按年份筛" in md


def test_placeholder_rows_are_skipped():
    t = L.parse_tables(LEDGER)
    bodies = [" ".join(r) for r in t["论文"][1]]
    assert not any("待填" in b for b in bodies)
