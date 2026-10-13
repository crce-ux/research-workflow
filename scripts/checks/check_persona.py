# -*- coding: utf-8 -*-
"""
check_persona.py —— 文稿「身份匹配」机检（只报可疑，不下判决）

【为什么有它】
    `PPT与讲稿_身份匹配约束.md` 定了三问（术语层 / 引据层 / 立场层）与两条边界。
    其中**只有一部分能机器查** —— 本脚本只做那一部分，其余留给人判断。

    ⚠️ **命中不等于要改。** 「可能」在写**证据边界**时是正确用法，
    在写**结论**时才是逃避。脚本分不清，你能分清。

【查什么】
    C1 过度保守     —— 保守词密度（边界 2：说虚了同样失真）
    C2 越级表述     —— 断言词、承诺句（立场层）
    C3 引据悬空     —— 「有研究表明」但附近没有具体出处（引据层）
    C4 回指         —— 「那篇综述 / 该研究 / 前述」（幻灯片禁用，讲稿可用）
    C5 书面语       —— 「综上所述 / 值得注意的是」（讲稿里念着别扭）
    C6 缩写未展开   —— 首次出现无中文全称
    C7 长句         —— 一口气念不完（讲稿专用判据）

【两个轴是正交的，都要给对】
    --scene  身份（学生 / 审稿人 / 同门）→ 决定立场层阈值
    --kind   载体（讲稿 / 幻灯片 / 备注）→ 决定引用与长句要求

    ⚠️ 实测教训：最初把「回指」绑在 scene 上，结果对**讲稿**报了 3 处"该综述" ——
    但讲稿是**线性听**的，回指完全合理。回指只在**幻灯片**（跳读）上才是问题。

    ⚠️ 给 `--kind 幻灯片` 时，请传**幻灯片上的实际文字**，
    不要传制作稿 —— 制作稿含表格与口径提醒，不是给听众看的。（表格行已自动跳过）

【用法】
    python check_persona.py <文稿.md> --kind 讲稿 --scene 组会汇报
    python check_persona.py <幻灯片文字.md> --kind 幻灯片
    python check_persona.py <文稿.md> --only C1,C2       # 只查某几项
    python check_persona.py <文稿.md> --strict           # 有命中即退出码 1

【配套】
    `_流程与工具/PPT与讲稿_身份匹配约束.md`（框架与场景锚点）
"""
import argparse
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── 词表 ────────────────────────────────────────────────────
HEDGE = ["可能", "似乎", "或许", "也许", "大概", "应该是", "估计", "恐怕",
         "在一定程度上", "某种程度上", "或多或少", "不排除"]
OVERCLAIM = ["我保证", "一定能", "必然会", "毫无疑问", "显而易见", "众所周知",
             "肯定能", "必然", "毋庸置疑", "铁定"]
VAGUE_CITE = [r"有研究(表明|显示|发现|提示)", r"有文献(表明|显示|报道)",
              r"研究表明", r"有学者(认为|提出)", r"相关研究(表明|显示)"]
#: 幻灯片禁用（非线性阅读，每处引用必须自足）
BACKREF = ["那篇综述", "该研究", "前述文献", "上文提到", "前面提到", "如前述",
           "该综述", "这篇文章", "前面那篇"]
#: 讲稿里念着别扭的书面语
WRITTEN = ["综上所述", "值得注意的是", "由此可见", "不言而喻", "总而言之",
           "需要指出的是", "首先.*其次.*最后", "基于以上分析"]
#: C8 口语化 —— **两种文体都清**（降智解释 / 自问自答 / 空泛夸张 / 非科学措辞）
COLLOQ_ALWAYS = [r"这句话的意思是", r"也就是说，?", r"说白了", r"意思就是",
                 r"极其", r"非常重要", r"分量最重", r"绕不开", r"卡在", r"为什么独"]
#: C8 口语化 —— **仅幻灯片清**（讲稿里这些是口语节拍，是对的）
COLLOQ_SLIDE = [r"我觉得", r"咱们", r"其实", r"挺[好重要]", r"蛮[好重要]",
                r"有点", r"然后", r"接下来我", r"所以呢"]

#: ⚠️ 六份清单/脚本各管一个轴，别混（详见 `写作禁用词与句式清单.md` §五）：
#:   本脚本          → 身份/表达轴
#:   check_language  → 引用自足 · 排他性断言 · 数字口径
#:   内容复盘 §三     → 说法准不准（八条标准）
#:   PPT文稿去味清单  → AI 味
#:   写作禁用词清单   → 措辞的文体适配（本脚本 C8 是它的机检部分）

#: 已知缩写 → 中文全称（可按项目增补）
ABBR = {"TRS": "难治性精神分裂症", "MMN": "失匹配负波", "ECC": "脑电",
        "MRI": "磁共振", "VBM": "基于体素的形态学分析", "CSF": "脑脊液",
        "FC": "功能连接", "PET": "正电子发射断层成像", "ACh": "乙酰胆碱",
        "DA": "多巴胺", "5-HT": "5-羟色胺", "GABA": "γ-氨基丁酸"}

#: ⚠️ 两个轴是**正交**的，别混：
#:   `scene` 定**身份**（学生 / 审稿人 / 同门）→ 决定立场层阈值
#:   `kind`  定**载体**（讲稿 / 幻灯片 / 备注）→ 决定引用与语句要求
#:
#: 实测教训（2026-09-15）：最初把「回指」绑在 scene 上，
#: 结果对**讲稿**报了 3 处"该综述"——但讲稿是**线性听**的，回指完全合理。
#: 回指只在**幻灯片**（非线性跳读）上才是问题。
KINDS = {
    "讲稿":   dict(backref=False, written=True,  max_sent=70, oral=True),
    "幻灯片": dict(backref=True,  written=False, max_sent=50, oral=False),
    "备注":   dict(backref=False, written=False, max_sent=90, oral=False),
}
SCENES = {
    "组会汇报": dict(hedge_max=8.0),
    "期刊审稿": dict(hedge_max=None),
    "回导师":   dict(hedge_max=20.0),
}


def sentences(text):
    """粗切句：按中文标点断，返回 (行号, 句子)

    ⚠️ **跳过表格行与纯标记行** —— 制作稿里的 `| 一 | D2 低亲和力 | … |` 不是
    幻灯片上的文字。实测（2026-09-15）：不跳过时，制作稿会报 172 处"长句"，
    全是表格行，信号被淹没。
    """
    out = []
    for ln, raw in enumerate(text.splitlines(), 1):
        s0 = raw.strip()
        if not s0 or s0.startswith("|"):          # 表格行
            continue
        if re.match(r"^[-*+]\s*$", s0):           # 空列表项
            continue
        for s in re.split(r"(?<=[。！？；])", s0):
            s = s.strip().lstrip("#>*-+ ").strip()
            if s:
                out.append((ln, s))
    return out


def strip_md(text):
    t = re.sub(r"^\s*-{3,}\s*$", "", text, flags=re.M)
    t = re.sub(r"\*\*(.+?)\*\*", r"\1", t, flags=re.S)
    return re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\1", t, flags=re.S)


def check(text, scene="组会汇报", kind="讲稿", only=None):
    cfg = {**SCENES.get(scene, SCENES["组会汇报"]),
           **KINDS.get(kind, KINDS["讲稿"])}
    body = strip_md(text)
    sents = sentences(body)
    n_char = max(1, len(re.sub(r"\s", "", body)))
    hits = {}

    def add(k, ln, s, note=""):
        hits.setdefault(k, []).append((ln, s.strip()[:70], note))

    # C1 过度保守：先给全篇密度，再挑"整句只有保守词没有实义"的
    n_hedge = sum(body.count(w) for w in HEDGE)
    dens = n_hedge / n_char * 1000
    if cfg["hedge_max"] and dens > cfg["hedge_max"]:
        add("C1", 0, f"全篇保守词 {n_hedge} 个，密度 {dens:.1f}/千字"
                     f"（阈值 {cfg['hedge_max']}）—— 边界 2：说虚了同样失真")
    for ln, s in sents:
        ws = [w for w in HEDGE if w in s]
        if len(ws) >= 2:
            add("C1", ln, s, f"一句里 {len(ws)} 个保守词：{ws}")

    # C2 越级表述
    for ln, s in sents:
        for w in OVERCLAIM:
            if w in s:
                add("C2", ln, s, f"断言词「{w}」—— 立场层：学生拿不住这个口气")

    # C3 引据悬空（该句有泛指引用，但整句没有任何 [n] / 年份 / 刊名）
    for ln, s in sents:
        if any(re.search(p, s) for p in VAGUE_CITE):
            if not (re.search(r"\[\d+\]", s) or re.search(r"(19|20)\d{2}", s)
                    or re.search(r"[A-Z][a-z]+ [A-Z]", s)):
                add("C3", ln, s, "泛指引用且无具体出处 —— 引据层：被问「哪一篇」答不上")

    # C4 回指
    if cfg["backref"]:
        for ln, s in sents:
            for w in BACKREF:
                if w in s:
                    add("C4", ln, s, f"回指「{w}」—— 幻灯片非线性阅读，引用须自足")

    # C5 书面语（讲稿场景）
    if cfg["written"]:
        for ln, s in sents:
            for w in WRITTEN:
                if re.search(w, s):
                    add("C5", ln, s, f"书面语「{w}」—— 讲稿要念得出来")

    # C6 缩写首次出现未展开
    seen = set()
    for ln, s in sents:
        for ab, full in ABBR.items():
            if re.search(rf"\b{re.escape(ab)}\b", s) and ab not in seen:
                seen.add(ab)
                if full not in body:
                    add("C6", ln, s, f"缩写 {ab} 首次出现，全篇未见中文全称「{full}」")

    # C8 口语化措辞
    #    ⚠️ 口语节拍 ≠ 口语化 ——「三条原因。」这种承担节奏的短句要**保留**，
    #    只清「卡在哪」这类偷懒的措辞。判据：它在承担节奏功能，还是在偷懒？
    for ln, s in sents:
        for pat in COLLOQ_ALWAYS:
            if re.search(pat, s):
                add("C8", ln, s, f"口语化「{re.search(pat, s).group()}」—— 两种文体都该清")
        if not cfg.get("oral"):          # 仅幻灯片
            for pat in COLLOQ_SLIDE:
                if re.search(pat, s):
                    add("C8", ln, s, f"口语化「{re.search(pat, s).group()}」—— 幻灯片要书面")

    # C7 长句（讲稿一口气念不完）
    for ln, s in sents:
        core = re.sub(r"\s", "", s)
        if len(core) > cfg["max_sent"]:
            add("C7", ln, s, f"该句 {len(core)} 字 —— 念到一半要换气")

    if only:
        want = {x.strip().upper() for x in only.split(",")}
        hits = {k: v for k, v in hits.items() if k in want}
    return hits, dict(n_char=n_char, n_sent=len(sents), hedge=dens)


NAMES = {"C1": "过度保守", "C2": "越级表述", "C3": "引据悬空", "C4": "回指",
         "C5": "书面语", "C6": "缩写未展开", "C7": "长句", "C8": "口语化措辞"}


def main():
    ap = argparse.ArgumentParser(description="文稿身份匹配机检（只报可疑，不下判决）")
    ap.add_argument("file", help="讲稿 / 制作稿 / 幻灯片文字（md 或 txt）")
    ap.add_argument("--scene", default="组会汇报", choices=list(SCENES), help="身份场景（决定立场层阈值）")
    ap.add_argument("--kind", default="讲稿", choices=list(KINDS),
                    help="载体：讲稿（线性听）/ 幻灯片（跳读）/ 备注 —— 决定引用与长句要求")
    ap.add_argument("--only", help="只查某几项，如 C1,C2")
    ap.add_argument("--strict", action="store_true", help="有命中即退出码 1")
    a = ap.parse_args()

    if not os.path.isfile(a.file):
        print(f"❌ 找不到：{a.file}"); return 1
    text = open(a.file, encoding="utf-8").read()
    hits, stat = check(text, a.scene, a.kind, a.only)

    print(f"═══ 身份匹配机检 · 身份「{a.scene}」× 载体「{a.kind}」 ═══")
    print(f"    {os.path.basename(a.file)} ｜ {stat['n_char']} 字 ｜ {stat['n_sent']} 句 "
          f"｜ 保守词密度 {stat['hedge']:.1f}/千字\n")

    if not hits:
        print("  ✅ 未发现可疑项")
    total = 0
    for k in sorted(hits):
        rows = hits[k]
        total += len(rows)
        print(f"  ── {k} {NAMES[k]}（{len(rows)} 处）──")
        for ln, s, note in rows[:8]:
            loc = f"L{ln}" if ln else "全篇"
            print(f"     {loc:>5}  {s}")
            if note:
                print(f"            └ {note}")
        if len(rows) > 8:
            print(f"     … 另有 {len(rows)-8} 处")
        print()

    print(f"═══ 合计 {total} 处待人工判断 ═══")
    print("  ⚠️ 命中不等于要改。保守词在写「证据边界」时是正确用法，")
    print("     在写「结论」时才是逃避 —— 判断权在你。")
    return 1 if (a.strict and total) else 0


if __name__ == "__main__":
    sys.exit(main())
