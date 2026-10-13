# -*- coding: utf-8 -*-
"""check_talk.py —— 讲者侧「可判定」规则的机检

【为什么有它】
    本 skill 里有一批规则是**纯计数 / 存在性**，不需要判断：
    待核清零、每页字数区间、加粗上限、总字数↔时长、制作稿七项齐不齐。
    它们过去只写在 SKILL.md 里，**每一轮都要模型重新读、重新判**——慢，且不可复现。

【它不查什么（重要）】
    理解确认四测试的**判据**、磕巴判据、去味分力度、九条红线里的 1/2/9
    —— 全是判断，本脚本**一律不碰**。
    **命中 ≠ 要改**：加粗 4 处、某页 520 字，可能都是有意的。

【页的认法】（按真实产物的格式，不是自创）
    制作稿   `## S1 · 封面` / `## B1 · …`      （S = 正片，B = 备用页）
    讲稿     `# 01_封面`
    用 --page-re 可覆盖。

用法：
    python check_talk.py 制作稿.md [--kind 制作稿|讲稿|内容稿] [--minutes 25]

退出码 = 失败项数（0 = 全过）
"""
import argparse
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── ① 待核清零：手册原文给的词表（不要改，改了就跟手册脱钩）
PENDING = re.compile(r"待核|⏳|疑为|核不到|需回原文|待回原文|待补|暂缺|TODO")
# ── ② 洗白词：把「没查过」伪装成「查过了」
WHITEWASH = re.compile(r"一般认为|据估计|通常认为|据悉")
# ── 制作稿七项
SEVEN = ["①", "②", "③", "④", "⑤", "⑥", "⑦"]
SEVEN_RE = re.compile(r"\*\*[①②③④⑤⑥⑦]\s*[^*]*\*\*")
# ── 讲稿必带六样（按手册的表头找，不硬编标题）
SIX_HINTS = [
    ("用时表", re.compile(r"用时表|每页秒数|累计")),
    ("本页纪律", re.compile(r"本页纪律")),
    ("落点清单", re.compile(r"必须说出口的落点|落点清单")),
    ("主动交代", re.compile(r"主动交代")),
    ("可压缩页", re.compile(r"可压缩页|不可压页")),
    ("页码对应", re.compile(r"页码对应|与内容稿.*对应")),
]
MY_PAGE = {
    "制作稿": re.compile(r"^##\s*[SB]\d+\s*·", re.M),
    "讲稿": re.compile(r"^#\s*\d{1,2}[_\.、 ]", re.M),
    "内容稿": re.compile(r"^#{1,3}\s*\d{1,2}[_\.、 ]", re.M),
}
CN = re.compile(r"[一-鿿]")
BOLD = re.compile(r"\*\*(.+?)\*\*", re.S)

PAGE_MIN, PAGE_MAX = 200, 500
WORDS_PER_MIN = 240
BOLD_MAX_PER_PAGE = 3


def split_pages(text, kind):
    pat = MY_PAGE[kind]
    idx = [m.start() for m in pat.finditer(text)]
    if not idx:
        # 声明的类型认不出页 → 换别的页格式再试一次（别静默当成「一页」）
        for other in ("制作稿", "讲稿", "内容稿"):
            if other == kind:
                continue
            idx = [m.start() for m in MY_PAGE[other].finditer(text)]
            if idx:
                pat = MY_PAGE[other]
                break
    if not idx:
        return [("（无分页）", text)]
    idx.append(len(text))
    return [
        (text[idx[i]:idx[i] + 40].split("\n")[0].strip(), text[idx[i]:idx[i + 1]])
        for i in range(len(idx) - 1)
    ]


def cjk_len(s):
    return len(CN.findall(s))


def body_of(page, kind):
    """取「该页真正会被人看到/听到的字」——制作稿取 ③页面文字，其余取全文。"""
    if kind != "制作稿":
        return page
    m = re.search(r"\*\*③\s*页面文字\*\*[：:]\s*(.*?)(?=\n\*\*[④⑤⑥⑦]|\Z)", page, re.S)
    return m.group(1) if m else ""


def check(text, kind, minutes):
    fails = []

    # ① 待核清零
    hits = PENDING.findall(text)
    if hits:
        lines = [f"        第 {i} 行：{l.strip()[:60]}"
                 for i, l in enumerate(text.splitlines(), 1) if PENDING.search(l)]
        fails.append(f"① 待核未清零：{len(hits)} 处 → 必须 = 0\n" + "\n".join(lines[:10]))

    # ② 洗白词
    if WHITEWASH.search(text):
        fails.append("② 出现洗白词（一般认为/据估计…）：把「没查过」伪装成「查过了」")

    pages = split_pages(text, kind)

    # ③ 每页字数 + ⑤ 加粗
    over, under, bold_over = [], [], []
    for name, page in pages:
        body = body_of(page, kind)
        n = cjk_len(body)          # 中文按字计
        if n and n > PAGE_MAX:
            over.append((name, n))
        elif n and n < PAGE_MIN and kind != "制作稿":
            under.append((name, n))
        # ⚠️ findall 带一个捕获组时返回的是**组内容字符串**，不是元组——
        #    写成 x[0] 只会取到首字，判据永远不成立（此 bug 由测试抓出）。
        b = len([x for x in BOLD.findall(body) if cjk_len(x) >= 2])
        if b > BOLD_MAX_PER_PAGE:
            bold_over.append((name, b))
    if over:
        fails.append("③ 超页字数上限（>500）：" +
                     "；".join(f"{n}({c})" for n, c in over[:8]))
    if under:
        fails.append("③ 低于页字数下限（<200，过渡页可例外）：" +
                     "；".join(f"{n}({c})" for n, c in under[:8]))
    if bold_over:
        fails.append("⑤ 加粗超限（>3 处）：" +
                     "；".join(f"{n}({c})" for n, c in bold_over[:8]))

    # ④ 总字数 ↔ 时长
    if minutes:
        want = minutes * WORDS_PER_MIN
        got = cjk_len(text)
        if abs(got - want) > want * 0.15:
            fails.append(f"④ 总字数 {got} 与 {minutes} 分钟 × 240 = {want} 差超过 15%")

    # ⑥ 制作稿七项齐不齐
    if kind == "制作稿":
        miss = []
        for name, page in pages:
            found = {m.group(0)[2] for m in SEVEN_RE.finditer(page)}
            lack = [s for s in SEVEN if s not in found]
            if lack:
                miss.append(f"{name} 缺 {'/'.join(lack)}")
        if miss:
            fails.append("⑥ 制作稿七项不全：\n" + "\n".join("        " + m for m in miss[:10]))

    # ⑦ 讲稿六样
    if kind == "讲稿":
        lack = [n for n, r in SIX_HINTS if not r.search(text)]
        if lack:
            fails.append("⑦ 讲稿必带六样缺：" + "、".join(lack))

    return fails, len(pages)


def main():
    ap = argparse.ArgumentParser(description="讲者侧可判定规则机检")
    ap.add_argument("doc")
    ap.add_argument("--kind", choices=list(MY_PAGE), default=None,
                    help="文稿类型；不给则按内容猜")
    ap.add_argument("--minutes", type=float, default=None, help="目标口播时长（分钟）")
    ap.add_argument("--page-re", default=None, help="自定义页分隔正则")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    text = open(a.doc, encoding="utf-8", errors="replace").read()

    kind = a.kind
    if kind is None:
        # 先认「页格式」，再认内容——`# 01_封面` 这种讲稿页头很确定，
        # 而「用时表」不一定写着（实测：v1 讲稿就没有，导致误判成内容稿）。
        if SEVEN_RE.search(text):
            kind = "制作稿"
        elif MY_PAGE["讲稿"].search(text):
            kind = "讲稿"
        else:
            kind = "内容稿"
    if a.page_re:
        MY_PAGE[kind] = re.compile(a.page_re, re.M)

    fails, npages = check(text, kind, a.minutes)

    print(f"check_talk · {a.doc} · 类型={kind} · {npages} 页")
    if not fails:
        print("  ✅ 全过（A 类规则）")
        return 0
    for f in fails:
        print(f"  ❌ {f}")
    print(f"\n  共 {len(fails)} 项未过。⚠️ 命中 ≠ 要改——判断仍在你。")
    return len(fails)


if __name__ == "__main__":
    raise SystemExit(main())
