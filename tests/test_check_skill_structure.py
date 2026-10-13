# -*- coding: utf-8 -*-
"""check_skill_structure 的校验规则测试。

校验器本身也必须被校验——否则它就是「没人管的裁判」。
这里用 tmp_path 造出合规与不合规的 skill 目录，断言规则确实生效。
"""
import textwrap

import check_skill_structure as css
import pytest


def _make(tmp_path, dirname, frontmatter, body="正文。\n"):
    d = tmp_path / dirname
    d.mkdir()
    (d / "SKILL.md").write_text(f"---\n{frontmatter}\n---\n\n{body}", encoding="utf-8")
    return d


GOOD_FM = "name: my-skill\ndescription: 做某事。当用户说「做某事」时使用。"


# ── 合规 ─────────────────────────────────────────────────────

def test_valid_skill_passes(tmp_path):
    d = _make(tmp_path, "my-skill", GOOD_FM)
    errs, warns = css.check_skill(d, strict=False)
    assert errs == []


# ── name 规则 ────────────────────────────────────────────────

def test_name_must_match_directory(tmp_path):
    d = _make(tmp_path, "other-name", GOOD_FM)
    errs, _ = css.check_skill(d, strict=False)
    assert any("不一致" in e for e in errs)


def test_name_rejects_uppercase_and_underscore(tmp_path):
    d = _make(tmp_path, "My_Skill", "name: My_Skill\ndescription: x")
    errs, _ = css.check_skill(d, strict=False)
    assert any("只能是小写" in e for e in errs)


def test_name_rejects_leading_hyphen(tmp_path):
    d = _make(tmp_path, "-bad", "name: -bad\ndescription: x")
    errs, _ = css.check_skill(d, strict=False)
    assert any("只能是小写" in e for e in errs)


def test_name_rejects_double_hyphen(tmp_path):
    d = _make(tmp_path, "a--b", "name: a--b\ndescription: x")
    errs, _ = css.check_skill(d, strict=False)
    assert any("只能是小写" in e for e in errs)


def test_name_rejects_reserved_word(tmp_path):
    d = _make(tmp_path, "claude-helper", "name: claude-helper\ndescription: x")
    errs, _ = css.check_skill(d, strict=False)
    assert any("保留词" in e for e in errs)


def test_name_length_capped(tmp_path):
    long = "a" * 70
    d = _make(tmp_path, long, f"name: {long}\ndescription: x")
    errs, _ = css.check_skill(d, strict=False)
    assert any("64" in e for e in errs)


# ── description 规则 ─────────────────────────────────────────

def test_description_required(tmp_path):
    d = _make(tmp_path, "my-skill", "name: my-skill")
    errs, _ = css.check_skill(d, strict=False)
    assert any("缺 description" in e for e in errs)


def test_description_length_capped(tmp_path):
    d = _make(tmp_path, "my-skill", "name: my-skill\ndescription: " + "字" * 1100)
    errs, _ = css.check_skill(d, strict=False)
    assert any("1024" in e for e in errs)


# ── frontmatter 闭合 ─────────────────────────────────────────

def test_unclosed_frontmatter_is_error(tmp_path):
    d = tmp_path / "my-skill"
    d.mkdir()
    (d / "SKILL.md").write_text("---\nname: my-skill\n\n没有第二个 ---\n", encoding="utf-8")
    errs, _ = css.check_skill(d, strict=False)
    assert errs


# ── 正文长度 ─────────────────────────────────────────────────

def test_body_length_capped(tmp_path):
    d = _make(tmp_path, "my-skill", GOOD_FM, body="行。\n" * 600)
    errs, _ = css.check_skill(d, strict=False)
    assert any("500" in e for e in errs)


# ── 深链 ─────────────────────────────────────────────────────

def test_deep_reference_link_is_error(tmp_path):
    d = _make(tmp_path, "my-skill", GOOD_FM, body="见 `references/a/b.md`。\n")
    errs, _ = css.check_skill(d, strict=False)
    assert any("深链" in e for e in errs)


def test_single_level_reference_is_ok(tmp_path):
    d = _make(tmp_path, "my-skill", GOOD_FM, body="见 `references/a.md`。\n")
    errs, _ = css.check_skill(d, strict=False)
    assert errs == []


# ── 非规范字段（警告，不是错误）───────────────────────────────

def test_extra_frontmatter_field_warns(tmp_path):
    d = _make(tmp_path, "my-skill", GOOD_FM + "\nversion: 1.0.0")
    errs, warns = css.check_skill(d, strict=False)
    assert errs == []
    assert any("非规范字段" in w for w in warns)


def test_allowed_fields_do_not_warn(tmp_path):
    fm = GOOD_FM + "\nlicense: MIT\ncompatibility: 纯文本，无依赖"
    d = _make(tmp_path, "my-skill", fm)
    errs, warns = css.check_skill(d, strict=False)
    assert errs == []
    assert not any("非规范字段" in w for w in warns)


# ── Anti-Patterns 建议 ───────────────────────────────────────

def test_missing_anti_patterns_warns(tmp_path):
    d = _make(tmp_path, "my-skill", GOOD_FM)
    _, warns = css.check_skill(d, strict=False)
    assert any("Anti-Patterns" in w for w in warns)


def test_present_anti_patterns_does_not_warn(tmp_path):
    body = "## Anti-Patterns\n\n- **Never** 留下未核实的断言\n"
    d = _make(tmp_path, "my-skill", GOOD_FM, body=body)
    _, warns = css.check_skill(d, strict=False)
    assert not any("Anti-Patterns" in w for w in warns)


def test_vague_ban_in_anti_patterns_warns(tmp_path):
    body = "## Anti-Patterns\n\n- 不要写得不好\n"
    d = _make(tmp_path, "my-skill", GOOD_FM, body=body)
    _, warns = css.check_skill(d, strict=False)
    assert any("形容词式" in w for w in warns)
