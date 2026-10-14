# -*- coding: utf-8 -*-
"""check_review.py —— 审稿意见的结构与伦理机检

【查哪种格式】
    **编号直述体**（作者实际在用的体例，对齐团队样稿）：
        稿件编号 / 标题 / 审稿建议
        → 一段摘要
        → 编号意见 1..N（一句一事、每事带位置、每事有要求）
        → 给编辑的保密意见（若在，单列，标「不向作者展示」）
        → References（可选）

    ⚠️ **不是** SKILL.md §三 写的 `Summary / MAJOR POINTS / MINOR POINTS` 三段式。
    实测定稿（PSY-D-26-03918 等四个版本）全部是上面的编号体，没有 MAJOR/MINOR 分节。
    检查器以**实际体例**为准；SKILL.md §三 已补注另一种体例也成立。

【它不查什么】
    意见写得对不对、方法学判断准不准——语义，一律不碰。
    它查的是**该有的东西在不在、不该有的东西在不在**。

用法：
    python check_review.py <审稿意见.md>

退出码 = 命中条数（0 = 全过）
"""
import argparse
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 只查提交稿；草稿里的「给XX的备忘录」是内部节，不适用提交稿的规矩
DRAFT_MARKERS = ("勿提交", "不提交", "给陈晨的备忘录", "给作者的备忘录")

# 密评（给编辑的保密意见）——另一种文书，不套作者可见意见的规矩
CONF_LETTER = re.compile(r"不向作者展示|给编辑的密评|Confidential Comments to the Editor", re.I)

REC_LINE = re.compile(r"^\s*\*{0,2}(Recommendation|审稿建议|建议决定)\*{0,2}\s*[:：]\s*(.+)$", re.M)
TIERS = ("accept", "minor revision", "major revision", "reject", "小修", "大修", "拒稿", "接受")

# 作者可见区到此为止
EDITOR_HEAD = re.compile(r"^#{1,6}.*(给编辑|保密|不向作者展示|editor)|^\*\*附（给编辑|^\*{0,2}Confidential", re.M)
REF_HEAD = re.compile(r"^\s*(\*{0,2}References|参考文献)", re.M)

# 「给编辑」的节必须带显式排除标记——否则作者可能误读
CONF_HINT = re.compile(r"^#{1,6}.*(给编辑|保密|Confidential)|^\*\*附（给编辑", re.M)
EXCLUDE_MARK = re.compile(r"不向作者展示|勿提交|不提交|not.{0,20}shown.{0,20}author|for the editor", re.I)

# 目录模式只认「审稿意见」本身。
# ⚠️ 判据是 **文件名前缀** 或 **frontmatter 的 type**——不是「正文里有没有这四个字」。
#    否则《期刊审稿方法指南》《中文阅读与审稿意见报告》这类**讲审稿意见**的文档
#    会被判成审稿意见本身（实测命中一大片）。
IS_REVIEW_FM = re.compile(r"^type\s*:\s*审稿意见\s*$", re.M)

NUM_ITEM = re.compile(r"^(\d+)[.、]\s+", re.M)
LOC_REF = re.compile(
    r"Section\s*\d|§\s*\d|\d+\.\d+\s*节|Table\s*\d|Figure\s*\d|Fig\.?\s*\d|Line\s*\d"
    r"|表\s*\d|图\s*\d|第\s*\d+\s*页|abstract|introduction|methods|results|discussion"
    r"|摘要|引言|方法|结果|讨论", re.I)
REQUEST = re.compile(
    r"please|should|suggest|recommend|would (?:help|be helpful|be useful)|kindly"
    r"|请|建议|希望|烦请|应(?:当)?", re.I)
MISCONDUCT = re.compile(
    r"造假|伪造|篡改|抄袭|剽窃|学术不端|数据造假|图片重复|重复发表|一稿多投"
    r"|fabricat|plagiar|misconduct|salami", re.I)


def author_region(text):
    """切出「作者可见」的那一段：审稿建议之后，到 References / 保密意见之前。"""
    start = 0
    m = REC_LINE.search(text)
    if m:
        start = m.end()
    ends = [len(text)]
    for pat in (REF_HEAD, EDITOR_HEAD):
        mm = pat.search(text, start)
        if mm:
            ends.append(mm.start())
    return text[start:min(ends)], text[min(ends):]


def check(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    hits, soft = [], []

    if any(k in text for k in DRAFT_MARKERS):
        return [], [f"{path.name}：含「备忘录/勿提交」标记，像是草稿——提交稿才有意义，本次不判"]

    # 给编辑的**密评**是另一种文书：它本身就是那个「推荐」，没有作者可见的编号意见。
    # 库里有几份 frontmatter 也写 `type: 审稿意见`，靠正文首部的自述来分辨。
    if CONF_LETTER.search(text[:400]):
        return [], [f"{path.name}：自述为「不向作者展示」的密评——文书结构不同（无作者可见编号意见），本次不判"]

    author, editor = author_region(text)

    # V1 审稿建议：必须有，且是四档之一
    m = REC_LINE.search(text)
    if not m:
        hits.append("V1 缺「审稿建议 / Recommendation」行")
    elif not any(t in m.group(2).strip().lower() for t in TIERS):
        hits.append(f"V1 审稿建议取值不在四档内：「{m.group(2).strip()[:40]}」"
                    f"（应为 Accept / Minor Revision / Major Revision / Reject）")

    # V2 摘要段：审稿建议之后、第一条编号之前要有实质叙述
    # 阈值 60 字：只用来排除「缺」和「一行敷衍」，不用来评判摘要写得好不好。
    if m:
        for nm in NUM_ITEM.finditer(text, m.end()):
            lead = text[m.end():nm.start()]
            if len(re.sub(r"\s", "", lead)) < 60:
                hits.append("V2 摘要段过短或缺——提交前作者靠它判断「你读懂了没有」")
            break

    # V3 编号意见条数
    items = [(mm.start(), mm.end()) for mm in NUM_ITEM.finditer(author)]
    n = len(items)
    if n < 3:
        hits.append(f"V3 只有 {n} 条编号意见——少于 3 条通常意味着没审透")
    elif n > 8:
        hits.append(f"V3 有 {n} 条编号意见——多于 8 条通常意味着没收口")
    if n == 0:
        return hits, soft

    # 按条切块（最后一条到区末）
    blocks = []
    for i, (s, e) in enumerate(items):
        end = items[i + 1][0] if i + 1 < len(items) else len(author)
        blocks.append(author[e:end])

    # V4 每条要有可执行要求（只批评不给方向 = 违规）
    for i, b in enumerate(blocks, 1):
        if not REQUEST.search(b):
            hits.append(f"V4 第 {i} 条只提了问题、没给「要作者做什么」")

    # V5 不端指控不得出现在作者可见处——只该写进给编辑的保密意见
    for i, b in enumerate(blocks, 1):
        mm = MISCONDUCT.search(b)
        if mm:
            hits.append(f"V5 第 {i} 条含不端指控词「{mm.group(0)}」——"
                        f"诚信疑虑只能写进给编辑的保密意见，不能给作者看")

    # V6 「给编辑」的节必须带显式排除标记
    # ⚠️ 不能一见尾节就报——`**References (for the authors' consideration)**` 也是尾节，
    #    那是给作者看的。只在**确实**出现「给编辑 / 保密」标题时才要求标记。
    cm = CONF_HINT.search(text)
    if cm and not EXCLUDE_MARK.search(text[cm.start():cm.start() + 400]):
        hits.append("V6 有「给编辑 / 保密」节但没标明「不向作者展示 / 勿提交」——"
                    "作者看不到的东西必须让编辑一眼认出来")

    # V7（软）位置引用覆盖率——只报告，不拦
    no_loc = [i for i, b in enumerate(blocks, 1) if not LOC_REF.search(b)]
    if no_loc:
        soft.append(f"V7 {n - len(no_loc)}/{n} 条给了位置（章节/行/图表）；"
                    f"第 {'/'.join(map(str, no_loc))} 条没给——建议补，便于作者定位")

    return hits, soft


def main():
    ap = argparse.ArgumentParser(description="审稿意见结构与伦理机检（编号直述体）")
    ap.add_argument("path")
    a = ap.parse_args()
    p = pathlib.Path(a.path)

    if p.is_file():
        # ⚠️ 2026-10-14：单文件模式原先**完全不做适用性判断**——把《研究设计书》当审稿意见查，
        #    一次报出 60+ 条 V4（「第 N 条只提了问题、没给要作者做什么」）。
        #    目录模式早就有这条门控，**单文件模式漏了**——同一条判据要豁免两处（设计纪律 6）。
        fm = re.match(r"^---\n(.*?)\n---",
                      p.read_text(encoding="utf-8", errors="replace"), re.S)
        if p.name.startswith("审稿意见") or (fm and IS_REVIEW_FM.search(fm.group(1))):
            files, skipped = [p], 0
        else:
            files, skipped = [], 1
    else:
        files, skipped = [], 0
        for f in sorted(p.rglob("*.md")):
            fm = re.match(r"^---\n(.*?)\n---", f.read_text(encoding="utf-8", errors="replace"), re.S)
            if f.name.startswith("审稿意见") or (fm and IS_REVIEW_FM.search(fm.group(1))):
                files.append(f)
            else:
                skipped += 1

    total, softs = 0, []
    print(f"check_review · {a.path} · 扫 {len(files)} 个文件")
    if skipped:
        print(f"  （跳过 {skipped} 个非审稿意见文件：调研记录 / 图表核查 / 设计书 等——"
              f"只查文件名以「审稿意见」开头、或 frontmatter 标了 `type: 审稿意见` 的）")
    if not files:
        print("  ⚠️ 本次未评——不是查过了通过")
    for f in files:
        hits, soft = check(f)
        softs += soft
        for h in hits:
            print(f"  ❌ {f.name}：{h}")
        total += len(hits)
    for s in softs:
        print(f"  ○ {s}")
    if not total:
        print("  ✅ 全过（六组硬规则）")
    print(f"\n  共 {total} 处。⚠️ 只查结构，不查意见对不对。")
    return total


if __name__ == "__main__":
    raise SystemExit(main())
