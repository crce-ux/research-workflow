# -*- coding: utf-8 -*-
"""check_talk 的规则测试。

锁的是**讲者侧的几条硬规则**：待核必须为 0、制作稿七项必须齐、加粗有上限。
它们不依赖语义判断，所以可以写死——本脚本正为此存在。
"""
import check_talk as ct


def _fails(text, kind="制作稿", minutes=None):
    fails, _ = ct.check(text, kind, minutes)
    return "\n".join(fails)


# ── ① 待核清零 ────────────────────────────────────────────────

def test_pending_marker_is_flagged():
    assert "待核" in _fails("## S1 · 封面\n**① 标题**：这是一处待核数据")


def test_todo_and_hourglass_are_flagged():
    assert "待核未清零" in _fails("## S1 · 封面\n⏳ 稍后补\nTODO 补图")


def test_clean_text_passes_pending():
    assert "待核" not in _fails("## S1 · 封面\n**① 标题**：干净的稿子")


# ── ② 洗白词 ──────────────────────────────────────────────────

def test_whitewash_is_flagged():
    assert "洗白词" in _fails("## S1 · 封面\n一般认为，该指标更优")


# ── ⑤ 加粗上限（每页 ≤3）────────────────────────────────────

def test_bold_over_limit_is_flagged():
    """加粗上限管的是**幻灯片上的文字** = 制作稿的 ③。"""
    page = "## S1 · 封面\n**③ 页面文字**：" + " ".join(f"**要点{i}**" for i in range(5))
    assert "加粗超限" in _fails(page)


def test_bold_in_notes_is_not_counted():
    """⑥ 讲稿备注 里的加粗不算——不是幻灯片上的字。"""
    page = ("## S1 · 封面\n**③ 页面文字**：干净\n**⑥ 讲稿备注**："
            + " ".join(f"**要点{i}**" for i in range(5)))
    assert "加粗超限" not in _fails(page)


# ── ⑥ 制作稿七项 ─────────────────────────────────────────────
# ⚠️ 2026-10-15 改：原先只数 `**①…**` 到 `**⑦…**` 有没有七个，不检查是哪七种。
#    写「① 项」…「⑦ 项」照样过检——撞上设计纪律 5（按形式找，不按信息找）。
#    现在按标签识别七种字段。下面把「哪些该报、哪些不该报」钉死，防它再退回数个数。

SEVEN_LABELS = ["标题", "版式建议", "页面文字", "表格数据", "图表说明", "讲稿备注", "口径提醒"]


def _page(marks="①②③④⑤⑥⑦", labels=None):
    labels = labels or SEVEN_LABELS
    return "## S1 · 封面\n" + "\n".join(
        f"**{m} {lb}**：内容" for m, lb in zip(marks, labels))


def test_missing_seven_item_is_flagged():
    assert "七项不全" in _fails(_page("①②③④⑤⑥"))


def test_full_seven_items_pass():
    assert "七项不全" not in _fails(_page())


def test_field_kinds_are_recognized():
    """七个编号齐、标签也是七种 —— 认得出，不报。"""
    f = _fails(_page())
    assert "缺字段" not in f and "认不出" not in f


def test_wrong_labels_are_flagged():
    """编号齐但字段不是那七种 —— 要报「认不出的字段」，不能静默通过。"""
    f = _fails(_page(labels=["项"] * 7))
    assert "认不出的字段" in f
    assert "缺字段" in f


def test_duplicated_field_leaves_a_gap():
    """七个编号齐、但「标题」用了两次 —— 缺「口径」要报出来。"""
    f = _fails(_page(labels=["标题"] * 7))
    assert "缺字段" in f and "口径" in f


def test_zhuangtu_alias_is_recognized():
    """手册叫「图注」，实际稿子常写「图表说明」——别名要认。"""
    f = _fails(_page(labels=["标题", "版式", "页面文字", "表格", "图表说明", "讲稿备注", "口径"]))
    assert "缺字段" not in f and "认不出" not in f


# ── 页分隔与类型识别 ─────────────────────────────────────────

def test_production_page_delimiter():
    pages = ct.split_pages("## S1 · 封面\n内容\n## B1 · 备用\n内容", "制作稿")
    assert len(pages) == 2


def test_script_page_delimiter():
    pages = ct.split_pages("# 01_封面\n内容\n# 02_开场\n内容", "讲稿")
    assert len(pages) == 2


def test_fallback_when_declared_kind_mismatches():
    """声明「讲稿」但实际是制作稿格式时，不该静默当成一页。"""
    pages = ct.split_pages("## S1 · 封面\n内容\n## S2 · 二页\n内容", "讲稿")
    assert len(pages) == 2


# ── ④ 总字数 ↔ 时长 ──────────────────────────────────────────

def test_wordcount_far_off_target_is_flagged():
    assert "总字数" in _fails("## S1 · 封面\n" + "字" * 100, "内容稿", minutes=25)
