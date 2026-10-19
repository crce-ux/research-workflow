#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit.py —— 一条命令跑完一份稿件的检查，输出统一四列。

【用法】
    python scripts/audit.py <文件或目录>
    python scripts/audit.py <文件> --json
    python scripts/audit.py <文件> --only language,phrases
    python scripts/audit.py <文件> --strict     # 有问题时退出码 1

【做什么】
    ① 识别文档类型（论文 / 讲稿 / 制作稿 / 精读笔记 / 证据表 / 设计书 / 数据 / 审稿意见）
    ② 跑通用检查器（language、phrases、ref_citations、metadata）
    ③ 按类型追加专用检查器
    ④ 把各检查器的输出统一成：位置 / 检查项 / 问题 / 依据

【不做什么】
    · 不改稿
    · 不做语义判断——只把机检能判的部分列出来
    · 不保证覆盖完整：没跑的检查器会在末尾列出来

【退出码】
    0 无问题（或有问题但未加 --strict）· 1 有问题且加了 --strict · 2 输入不可用
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = Path(__file__).resolve().parent
CHECKS = HERE / "checks"

# ── 文档类型识别 ───────────────────────────────────────────
# 判据看内容，不看文件名。
TYPE_RULES = [
    # 制作稿与内容稿都有 ①②，按各自的专属字段分开判
    ("制作稿", [r"版式建议", r"图注", r"表格数据", r"讲稿备注"]),
    ("内容稿", [r"内容稿", r"页面文字", r"这一页要说什么", r"为什么放它"]),
    ("讲稿", [r"口播", r"逐字稿", r"讲稿"]),
    ("精读笔记", [r"\[Paper", r"\[Analysis", r"\[Hypothesis", r"精读笔记"]),
    ("证据表", [r"PICO", r"证据表", r"效应量\s*\|"]),
    ("设计书", [r"G1", r"G2", r"研究设计书", r"样本量估算"]),
    ("数据/SAP", [r"变量字典", r"SAP", r"缺失码"]),
    ("审稿意见", [r"审稿意见", r"MAJOR", r"MINOR"]),
]

# 每个类型追加的检查器（通用四件之外）
TYPE_CHECKS = {
    "制作稿": [("talk", ["{doc}", "--kind", "制作稿"])],
    "内容稿": [("talk", ["{doc}", "--kind", "内容稿"])],
    "讲稿": [("talk", ["{doc}", "--kind", "讲稿"])],
    "精读笔记": [("note", ["{doc}"])],
    "证据表": [("lit", ["{doc}"])],
    "设计书": [("design", ["{doc}"])],
    "数据/SAP": [("data", ["{doc}"])],
    "审稿意见": [("review", ["{doc}"])],
}

#: 可手动指定的类型
TYPES = ["论文/综述"] + list(TYPE_CHECKS)

# 检查器名 → 脚本名
SCRIPT = {
    "language": "check_language.py",
    "phrases": "check_phrases.py",
    "ref_citations": "check_ref_citations.py",
    "metadata": "check_metadata_leak.py",
    "talk": "check_talk.py",
    "note": "check_note.py",
    "lit": "check_lit.py",
    "design": "check_design.py",
    "data": "check_data.py",
    "review": "check_review.py",
}

# 通用四件：每项是 (名字, 参数模板)
GENERIC = [
    ("language", ["{doc}"]),
    ("phrases", ["{doc}", "--kind", "{kind}"]),
    ("ref_citations", ["--doc", "{doc}"]),
    ("metadata", ["{doc}"]),
]

LABEL = {
    "language": "语言与断言",
    "phrases": "措辞",
    "ref_citations": "引用编号",
    "metadata": "隐藏元数据",
    "talk": "讲者侧",
    "note": "精读笔记",
    "lit": "证据表",
    "design": "设计书",
    "data": "数据与 SAP",
    "review": "审稿意见",
}


def detect_type_detail(text: str):
    """返回 (类型, 命中标记数)。命中 ≤1 时把握低。"""
    best, score = "论文/综述", 0
    for name, pats in TYPE_RULES:
        s = sum(1 for p in pats if re.search(p, text))
        if s > score:
            best, score = name, s
    return best, score


def detect_type(text: str) -> str:
    return detect_type_detail(text)[0]


# ── 解析器：各检查器输出 → 统一结构 ────────────────────────
LANG_RULE = re.compile(r"^\s*(?:✅|🔴|⚠️)?\s*([①-⑩])\s*(.+?)\s*(?:⚠️硬规则)?\s*——\s*(\d+)\s*处")
LANG_HIT = re.compile(r"^\s+L(\d+)\s+(\S+)\s{2,}(.*)$")
PHRASE_RULE = re.compile(r"^\s*❌\s*(\d+)\s*(.+?)：(\d+)\s*处")
PHRASE_HIT = re.compile(r"^\s*第\s*(\d+)\s*行[：:]\s*(.+)$")
REF_MISS = re.compile(r"正文引用但表内缺失[：:]\s*\[([^\]]*)\]")
REF_DANGLING = re.compile(r"表内有但正文未引用（悬挂）[：:]\s*\[([^\]]*)\]")
MARK = re.compile(r"[✗❌⚠️]")


def parse_language(out: str):
    rule, hits = "", []
    for line in out.splitlines():
        m = LANG_RULE.match(line)
        if m:
            rule = m.group(2).strip()
            continue
        m = LANG_HIT.match(line)
        if m:
            hits.append({"line": int(m.group(1)), "rule": rule,
                         "detail": m.group(2) + "：" + m.group(3).strip()[:24]})
    return hits


def parse_phrases(out: str):
    rule, hits = "", []
    for line in out.splitlines():
        m = PHRASE_RULE.match(line)
        if m:
            rule = m.group(2).strip()
            continue
        m = PHRASE_HIT.match(line)
        if m:
            hits.append({"line": int(m.group(1)), "rule": rule,
                         "detail": m.group(2).strip()})
    return hits


def parse_ref(out: str):
    hits = []
    for line in out.splitlines():
        m = REF_MISS.search(line)
        if m:
            hits.append({"line": None, "rule": "正文引用但文末缺失",
                         "detail": "[" + m.group(1) + "]"})
        m = REF_DANGLING.search(line)
        if m:
            hits.append({"line": None, "rule": "文末条目未被正文引用",
                         "detail": "[" + m.group(1) + "]"})
    return hits


def parse_marked(out: str):
    """其余检查器：抓带 ✗ / ❌ / ⚠️ 的行。"""
    hits = []
    for line in out.splitlines():
        s = line.strip()
        if s and MARK.search(s) and not s.startswith(("===", "──")):
            hits.append({"line": None, "rule": "", "detail": s[:120]})
    return hits


PARSERS = {
    "language": parse_language,
    "phrases": parse_phrases,
    "ref_citations": parse_ref,
}


# ── 分节与分级 ─────────────────────────────────────────────
#: 附录类章节：命中不当作正文问题，默认折叠
APPENDIX_RE = re.compile(r"^#{1,6}\s*.*(附录|销项|对照|引用原文|核查记录|质控表|变更记录)")

#: 三级。硬规则必须处理；建议看情况；信息只供人工核口径。
LEVEL = {
    "硬规则": ("排他性断言", "引用编号", "正文引用但文末缺失", "文末条目未被正文引用"),
    "建议": ("空泛量词", "缩写", "名词化", "伪对立", "套话", "自我削弱", "抽象标签",
             "演义", "自问自答", "连接词", "回指", "讲者侧"),
    "信息": ("数字-口径", "隐藏元数据"),
}


def level_of(rule: str, detail: str) -> str:
    text = (rule or "") + (detail or "")
    for lv, keys in LEVEL.items():
        if any(k in text for k in keys):
            return lv
    return "建议"


def section_map(lines):
    """行号 → 所在章节类别（正文 / 附录）。"""
    cur, out = "正文", {}
    for i, ln in enumerate(lines, 1):
        if re.match(r"^#{1,6}\s", ln):
            cur = "附录" if APPENDIX_RE.match(ln) else "正文"
        out[i] = cur
    return out


def run_checker(name, argv, timeout=60):
    script = Path(argv[0])
    if not script.is_file():
        return None, f"缺脚本 {script.name}"
    try:
        p = subprocess.run([sys.executable] + argv,
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout,
                           env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        return p.stdout + p.stderr, None
    except subprocess.TimeoutExpired:
        return None, "超时"


def collect(doc: Path, kind: str, only: set[str] | None, forced: str | None = None):
    text = doc.read_text(encoding="utf-8", errors="replace")
    auto, score = detect_type_detail(text)
    dtype = forced or auto
    secmap = section_map(text.split("\n"))
    kind = "讲稿" if dtype in ("讲稿", "制作稿", "内容稿") else "论文"
    argv_sets = [(name, list(tpl)) for name, tpl in GENERIC]
    for name, tpl in TYPE_CHECKS.get(dtype, []):
        argv_sets.append((name, list(tpl)))

    findings, ran, skipped = [], [], []
    for name, base in argv_sets:
        if only and name not in only:
            skipped.append(f"{name}（未选中）")
            continue
        argv = [str(CHECKS / SCRIPT[name])] + [
            a.replace("{doc}", str(doc)).replace("{kind}", kind) for a in base]
        out, err = run_checker(name, argv)
        if out is None:
            skipped.append(f"{name}（{err}）")
            continue
        ran.append(name)
        parser = PARSERS.get(name, parse_marked)
        for hit in parser(out):
            sec = secmap.get(hit["line"], "正文") if hit.get("line") else "正文"
            findings.append({"file": str(doc), "checker": name,
                             "label": LABEL.get(name, name),
                             "section": sec,
                             "level": level_of(hit.get("rule", ""), hit.get("detail", "")),
                             **hit})
    return dtype, findings, ran, skipped, {"auto": auto, "score": score, "forced": forced}


def dw(s: str) -> int:
    """显示宽度：中日韩字符按 2 计。"""
    return sum(2 if ord(c) > 0x2E80 else 1 for c in s)


def pad(s: str, width: int) -> str:
    if dw(s) > width:
        limit, w, out = width - 1, 0, []
        for c in s:
            cw = 2 if ord(c) > 0x2E80 else 1
            if w + cw > limit:
                break
            out.append(c)
            w += cw
        s = "".join(out) + "…"
    return s + " " * (width - dw(s))


def render(dtype, findings, ran, skipped, files, show_all=False, meta=None):
    head = f"audit · {files} · 识别为「{dtype}」"
    if meta and meta.get("forced"):
        head += "（手动指定）"
    elif meta and meta.get("score", 0) <= 1:
        head += f"（自动识别把握低：{meta.get('score', 0)} 个标记，可用 --type 指定）"
    print(head + "\n")
    if not findings:
        print("  ✅ 未发现问题")
        print()
        print(f"  已运行：{'、'.join(ran) if ran else '无'}")
        if skipped:
            print(f"  未运行：{'、'.join(skipped)}")
        return

    def body_of(fs):
        for f in sorted(fs, key=lambda x: (x["line"] is None, x["line"] or 0)):
            loc = f"L{f['line']}" if f.get("line") else "—"
            print("  " + pad(loc, 8) + pad(f["label"], 14)
                  + pad(f["detail"], 46) + f["rule"][:20])

    def head(title, fs):
        print(f"  {title} · {len(fs)} 处")

    groups = {"硬规则": [], "建议": [], "信息": []}
    appx = []
    for f in findings:
        if f.get("section") == "附录":
            appx.append(f)
        else:
            groups.setdefault(f.get("level", "建议"), []).append(f)

    shown = 0
    for lv, mark in (("硬规则", "🔴"), ("建议", "·"), ("信息", "ⓘ")):
        fs = groups.get(lv, [])
        if not fs:
            continue
        if lv == "信息" and not show_all:
            head(f"{mark} 信息", fs)
            print("     默认折叠（加 --all 展开）：数字口径等，仅供人工核对")
            continue
        head(f"{mark} {lv}", fs)
        body_of(fs)
        shown += len(fs)
        print()

    if appx:
        head("附录", appx)
        if show_all:
            body_of(appx)
            shown += len(appx)
        else:
            print("     默认折叠（加 --all 展开）：附录 / 销项表 / 对照表中的命中")
        print()

    print(f"  共 {len(findings)} 处 · 显示 {shown} 处。命中不等于要改，逐条回原文核对。")
    print()
    print(f"  已运行：{'、'.join(ran) if ran else '无'}")
    if skipped:
        print(f"  未运行：{'、'.join(skipped)}")


def main() -> int:
    ap = argparse.ArgumentParser(description="一条命令跑完一份稿件的检查")
    ap.add_argument("path")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--only", help="只跑指定检查器，逗号分隔")
    ap.add_argument("--strict", action="store_true", help="有问题时退出码 1")
    ap.add_argument("--all", action="store_true", help="展开信息级与附录")
    ap.add_argument("--type", choices=TYPES, help="手动指定文档类型，跳过自动识别")
    a = ap.parse_args()

    p = Path(a.path)
    if not p.exists():
        print(f"[错误] 找不到 {p}")
        return 2
    if p.is_dir():
        docs = sorted(x for x in p.rglob("*.md") if x.is_file())
        if not docs:
            print(f"[错误] {p} 下没有 .md 文件")
            return 2
    else:
        docs = [p]

    only = set(x.strip() for x in a.only.split(",")) if a.only else None
    all_findings, report = [], []
    for doc in docs:
        dtype, findings, ran, skipped, meta = collect(doc, "", only, a.type)
        all_findings += findings
        report.append({"file": str(doc), "type": dtype, "meta": meta,
                       "findings": findings, "ran": ran, "skipped": skipped})

    if a.json:
        print(json.dumps({"files": report, "total": len(all_findings)},
                         ensure_ascii=False, indent=2))
    else:
        for r in report:
            render(r["type"], r["findings"], r["ran"], r["skipped"], r["file"],
                   a.all, r["meta"])
    return 1 if (a.strict and all_findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
