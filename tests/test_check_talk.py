# -*- coding: utf-8 -*-
"""check_talk 的规则测试。

锁的是**讲者侧的几条硬规则**：待核必须为 0、制作稿七项必须齐、加粗有上限。
这些规则不依赖语义判断，所以可以写死——也正是本脚本存在的理由。
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
    """⑥ 讲稿备注 里的加粗不算——那不是幻灯片上的字。"""
    page = ("## S1 · 封面\n**③ 页面文字**：干净\n**⑥ 讲稿备注**："
            + " ".join(f"**要点{i}**" for i in range(5)))
    assert "加粗超限" not in _fails(page)


# ── ⑥ 制作稿七项 ─────────────────────────────────────────────

def _page(marks="①②③④⑤⑥⑦"):
    return "## S1 · 封面\n" + "\n".join(f"**{m} 项**：内容" for m in marks)


def test_missing_seven_item_is_flagged():
    assert "七项不全" in _fails(_page("①②③④⑤⑥"))


def test_full_seven_items_pass():
    assert "七项不全" not in _fails(_page())


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
