# -*- coding: utf-8 -*-
"""check_phrases.py —— 措辞层的词表 / 句式机检

【它管什么】
    `ai-academic-writing` 里的**词表与句式**规则——自我削弱、套话、抽象标签、
    演义媒体化、降智解释、自问自答、伪对立、名词化、越级引用、连接词堆砌。
    这些词表与句式规则是纯匹配，不需要判断；原先只写在 references/ 里，每轮靠模型重读。

【它不管什么（避免重复）】
    · 口语动词 / 程度词 / 第一人称 / 指示代词 / 口头连接词 → `check_persona.py` 的 **C8**
    · 引用自足 / 排他性断言 / 数字口径 → `check_language.py`
    · 「这句话像不像人写的」整体判断 → 人工
    **混着查会互相误报**——本脚本只做上表列出的十组。

【词表来源】
    `manuals/checklists/写作禁用词与句式清单.md`（权威）+ `references/` 各轴。
    改词表请改手册，再同步本脚本。

用法：
    python check_phrases.py 文稿.md [--kind 幻灯片|讲稿|论文|标书] [--only 3,4]

退出码 = 命中组数（0 = 全过）
"""
import argparse
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# (组号, 组名, 适用范围, [正则…], 一句话)
GROUPS = [
    (1, "自我削弱", {"论文", "标书", "讲稿"},
     [r"遗憾的是", r"仍明显落后", r"效果有限", r"存在严重不足", r"未能超过"],
     "说得比证据弱——等于替审稿人备好反驳点"),
    # ⚠️ 手册原表里还有单字「仅」，但它在本项目文稿里是正常用词，命中率极高会掩盖真问题，故不收。
    (2, "套话", {"论文", "标书", "幻灯片"},
     [r"随着社会的发展", r"越来越受到广泛关注", r"日益受到(学界)?关注"],
     "开场套话——删掉不影响任何信息"),
    (3, "抽象标签", {"论文", "标书", "讲稿"},
     [r"具有重要(的)?理论意义", r"(本研究|本文)的关键抓手", r"具有重要意义"],
     "有标签无动作——还原成原文已有的动作"),
    (4, "演义媒体化", {"幻灯片", "讲稿", "论文", "标书"},
     [r"双雄", r"大军", r"混战", r"领跑", r"抢跑", r"洗牌", r"跳水", r"封神", r"神仙打架"],
     "戏谑化比喻——判据：能否出现在药监局公告里"),
    (5, "自问自答", {"幻灯片", "讲稿"},
     [r"[？?]\s*[—\-]{1,2}\s*", r"那么[，,]?\s*[^。？?]{0,20}(是什么|有哪些)[？?]"],
     "不设问——把答案直接写出来"),
    (6, "伪对立", {"论文", "标书"},
     [r"不是[^。，]{1,20}而是", r"不只是[^。，]{1,20}更是", r"并非[^。，]{1,20}而是"],
     "「不是 A 而是 B」多数是修辞，除非真在纠错"),
    (7, "名词化", {"论文", "标书"},
     [r"进行了[^。，]{0,6}(分析|研究|探讨|比较)", r"对[^。，]{1,16}进行(了)?(分析|研究|评估)"],
     "还原为动词：「进行了分析」→「分析」"),
    (8, "越级引用", {"期刊审稿", "回导师"},
     [r"§\s*\d", r"第\s*\d+\s*条", r"\b(CONSORT|SPIRIT|STROBE|PRISMA|STARD|TRIPOD|ARRIVE|CARE)\b"],
     "身份界限——学生/首次审稿人不引章节号、不点报告规范名"),
    (9, "连接词堆砌", {"论文", "标书", "幻灯片"},
     [r"首先[^。]{0,60}其次[^。]{0,60}(最后|再次)", r"因此[^。]{0,40}从而[^。]{0,40}进而"],
     "连接词成串出现——靠结构表达顺序，不靠连接词"),
]


def scan(text, only=None):
    hits = []
    for num, name, kinds, pats, note in GROUPS:
        if only and num not in only:
            continue
        found = []
        for p in pats:
            for m in re.finditer(p, text):
                ln = text[:m.start()].count("\n") + 1
                found.append((ln, m.group(0)[:30]))
        if found:
            hits.append((num, name, kinds, note, found))
    return hits


def main():
    ap = argparse.ArgumentParser(description="措辞层词表/句式机检")
    ap.add_argument("doc")
    ap.add_argument("--kind", default=None,
                    choices=["幻灯片", "讲稿", "论文", "标书", "期刊审稿", "回导师"])
    ap.add_argument("--only", default=None, help="只查指定组，如 3,4")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    text = open(a.doc, encoding="utf-8", errors="replace").read()
    only = {int(x) for x in a.only.split(",")} if a.only else None
    hits = scan(text, only)

    # 文体门控：不属于本文体的组只提示、不计入退出码
    inscope, outscope = [], []
    for h in hits:
        (inscope if (a.kind is None or a.kind in h[2]) else outscope).append(h)

    print(f"check_phrases · {a.doc} · 文体={a.kind or '未指定（全部按适用计）'}")
    if not hits:
        print("  ✅ 全过（十组词表）")
        return 0
    for num, name, kinds, note, found in inscope:
        print(f"  ❌ {num} {name}：{len(found)} 处 — {note}")
        for ln, s in found[:6]:
            print(f"        第 {ln} 行：{s}")
    for num, name, kinds, note, _f in outscope:
        print(f"  ○  {num} {name}：不属本文体（{'/'.join(sorted(kinds))}），未计")
    if inscope:
        print(f"\n  共 {len(inscope)} 组命中。⚠️ 命中不等于要改——「仅」「也就是说」这类有合法用法，仍由人判断。")
    return len(inscope)


if __name__ == "__main__":
    raise SystemExit(main())
