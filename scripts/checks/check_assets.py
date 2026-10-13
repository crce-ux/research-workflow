# -*- coding: utf-8 -*-
"""
check_assets.py —— 资产静态完整性自检（死链 / 索引漂移 / 自称数字 / 跨文档重复）

【用途】
    补一个长期缺口：`_系统/` 已有 25+ 份文档且互相交叉引用，但**没有任何机制**
    保证这些引用还指得对。长文档系统有四种慢性病，**人工查不出来**：

      ① 死链       —— 改了文件名/移动了目录，引用它的文档还指着旧路径
      ② 索引漂移   —— 新增文档忘了登记进索引表；或索引写了但文件已删
      ③ 自称脱节   —— 文档里写死"脚本 21 个""33 个技能"，与实际不符
      ④ 跨文档重复 —— 同一件事在两份文档各写一遍（"改一处漏一处"的根因）

    ⚠️ 本脚本**只报问题，不自动改文件**。修正由人决定。

【用法】
    python check_assets.py                       # 检查默认库根
    python check_assets.py --root "<vault>"
    python check_assets.py --quiet               # 只看汇总
    python check_assets.py --only 5              # 只跑第 5 类（跨文档重复）
    python check_assets.py --no-exclude          # 连 _归档/_快照 一起查

    退出码 = **硬门禁**问题数（0 = 全过），可用于门禁。
    第 1–3 类为硬门禁；**第 4–5 类为软检查，只提示、不计入退出码**
    （对接《出稿检查总表》§四「门禁分两种」）。

【检查项】
    1  相对链接有效性      [文字](路径) 解析后必须真实存在
    2  脚本总数对账        `_scripts/README.md` 自称的脚本数 == 实际 .py 数
    3  索引覆盖对账        `出稿检查总表` §五 提到的资产必须存在；
                           且 `_流程与工具/` 下的 .md 须被索引覆盖
    4  文件名引用有效性    文档中 `xxx.py` / `xxx.md` 形式的引用，全库须能找到同名文件
    5  跨文档重复内容      ① 两份文档 ≥6 行完全相同；② 小节的表头/标题同名**且内容重叠**
                           ⚠️ **只比 `_系统/`（方法论区）**——项目目录里的快照副本
                           （`04_组会汇报/` ↔ `05_汇报成品/`）是刻意的存档约定
                           ⚠️ **同名 ≠ 重复**：「核查方法/」系列每份都有「可粘贴提示词」
                           小节但内容各异，那是并行结构；故要求内容也重叠才报，
                           仅同名的只汇总计数

【对应流程】
    `第三方技能库_可借鉴项与升级清单_20260919.md` A1 · 资产静态自检
    改编自 Research-OS-Studio `scripts/check-skills.py`（MIT）的思路：
    数量对账 / 链接有效 / 清单与目录树一致；**并保留其"豁免须显式登记"的做法**。

【依赖】
    标准库（re / argparse / pathlib / sys）。无需第三方。

【踩坑教训】
    • Windows 中文路径：本脚本全程用 pathlib + utf-8 读文件，不依赖 shell 展开
    • 中文输出：开头 reconfigure stdout（Windows GBK 坑，与 check_language 同）
    • **刻意保守**：只对"确定指得出来"的问题报警。
      裸文件名（如 `check_language.py`）只在全库找不到同名文件时才报，
      不做路径推断——否则假阳性会淹没真问题。

【冒烟测试】
    2026-09-19 于本库真实数据运行，见文件末尾记录。
    首轮抓出 3 类真问题（1 死链 / 1 脚本计数 / 7 份未索引文档），全部修复后退出码 0。
"""
import argparse
import re
import sys
from pathlib import Path

# Windows GBK 坑：中文输出前必须重设 stdout 编码
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# 本文件位于 <库根>/_系统/_流程与工具/_scripts/check_assets.py
#   parents[0]=_scripts  [1]=_流程与工具  [2]=_系统  [3]=<库根>
DEFAULT_ROOT = Path(__file__).resolve().parents[3]

# 默认跳过的目录——**这些不是你的资产**，其中的死链不构成问题：
#   _归档 / _快照   历史版本，引用旧路径属正常
#   _待装skill     第三方 skill 库的 zip 解压物（agilab / research-skills 等），
#                   其内部相对链接依赖各自仓库结构，在本库中必然失效
#   .claude         Agent 配置与已装 skill（含第三方 skill 的 SKILL.md），
#                   不是科研资产，其内部引用依赖各 skill 自己的结构
EXCLUDE_DIRS = {"_归档", "_快照", "_待装skill", ".obsidian", ".claude",
                "node_modules", ".git", "__pycache__", "_work"}

# 已知豁免：行内已注明原因，登记在此而非静默跳过
LINK_EXEMPT_SNIPPETS = (
    "<!--exempt-->",       # 行内显式豁免标记
)

# 相对链接（排除 http/mailto/锚点）
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+?)(?:\s+\"[^\"]*\")?\)")
# 代码跨度里引用的文件名
CODESPAN_RE = re.compile(r"`([^`\s]+\.(?:py|md))`")

# 已知占位符写法——**显式登记而非静默跳过**（沿用 check-skills.py 的豁免纪律）
# 命中这些模式的反引号引用不参与存在性判断
NAME_EXEMPT_PATTERNS = (
    r"模块X",          # 《文献调研流程手册》的模块占位（证据表_模块X.md 等）
    r"课题\d+_",       # 课题N_xxx 占位
    r"<[^>]+>",        # 角括号占位（<项目> <strand>）
    r"\{[^}]+\}",      # 花括号占位
    r"\.\.\.",         # 省略写法（..._20260903.md）
    r"\*",             # 通配（**/*.md）
    r"YYYY|MMDD",      # 日期占位（文献分级总表_YYYYMMDD.md）
    r"^笔记\.md$",     # 正文里的举例
)


def exempt_name(name: str) -> bool:
    """是否为已知占位符/通配写法（豁免存在性判断）。"""
    return any(re.search(p, name) for p in NAME_EXEMPT_PATTERNS)


def index_candidates(p: Path):
    """文档在索引里可能被写成哪些形式。

    索引为可读性常写**简称**：
        `PPT工具链速查`  ← 实际文件名 `PPT工具链速查_20260915.md`
        `PPT视觉规范`    ← 实际文件名 `PPT视觉规范_国自然风格_20260915.md`
    因此除全名外，还要试：去扩展名 / 去日期后缀 / 各下划线前缀（≥6 字）。
    """
    stem = p.stem
    cands = {p.name, stem}
    no_date = re.sub(r"[_-]\d{8}$", "", stem)
    cands.add(no_date)
    parts = no_date.split("_")
    for k in range(1, len(parts) + 1):
        seg = "_".join(parts[:k])
        if len(seg) >= 6:
            cands.add(seg)
    return {c for c in cands if c}
# README 里自称的脚本数：`脚本 **21 个**` / `（21 个）` / `脚本 21 个`
SCRIPT_COUNT_RE = re.compile(r"脚本\s*\*{0,2}(\d+)\*{0,2}\s*个")


class Report:
    def __init__(self):
        self.items = []  # (类别号, 文件, 行号, 消息)

    def add(self, cat, path, line, msg):
        self.items.append((cat, path, line, msg))

    def by_cat(self, cat):
        return [i for i in self.items if i[0] == cat]


def iter_markdown(root, exclude):
    """**报告对象**：非排除目录下的 .md。"""
    for p in root.rglob("*.md"):
        if any(part in exclude for part in p.parts):
            continue
        yield p


def build_name_index(root):
    """**存在性依据**：全库（含 _归档/_快照）的文件名 → 路径映射。

    ⚠️ 这里刻意**不排除**任何目录。
    引用一份归档文件（如 `_归档/.../组会汇报_PPT制作稿_20260912.md`）
    是完全正当的——文件确实存在，只是不在常用区。
    若按排除后的集合判断，"引用了归档文件"会被误报成死链。
    """
    idx = {}
    for p in root.rglob("*"):
        if any(part in (".git", "node_modules", "__pycache__") for part in p.parts):
            continue
        if p.is_file():
            idx.setdefault(p.name, []).append(p)
    return idx


def strip_code_blocks(text):
    """把 fenced code block 替换为等长空行，避免在代码块里误报链接。"""
    out, in_fence = [], False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            out.append("")
            continue
        out.append("" if in_fence else line)
    return out


# ---------------------------------------------------------------- 1 死链
def check_links(root, files, exclude, rep):
    for md in files:
        try:
            lines = strip_code_blocks(md.read_text(encoding="utf-8", errors="replace"))
        except Exception as e:
            rep.add(1, md, 0, f"无法读取：{e}")
            continue
        for i, line in enumerate(lines, 1):
            if any(s in line for s in LINK_EXEMPT_SNIPPETS):
                continue
            # Obsidian wikilink [[...]] 不是 markdown 链接，先摘掉再匹配
            line = re.sub(r"\[\[[^\]]*\]\]", "", line)
            for target in LINK_RE.findall(line):
                if target.startswith(("http://", "https://", "mailto:", "#", "obsidian://",
                                      "data:", "tel:")):
                    continue
                if re.fullmatch(r"\{[^}]*\}|<[^>]*>", target):
                    continue
                clean = target.split("#")[0].strip()
                if not clean:
                    continue
                resolved = (md.parent / clean).resolve()
                if not resolved.exists():
                    rep.add(1, md, i, f"链接目标不存在：{target}")


# ------------------------------------------------- 2 脚本总数对账
def check_script_count(root, exclude, rep):
    readme = root / "_系统" / "_流程与工具" / "_scripts" / "README.md"
    if not readme.exists():
        rep.add(2, readme, 0, "`_scripts/README.md` 不存在——脚本总数无唯一出处")
        return
    scripts = sorted(p.name for p in
                     (root / "_系统" / "_流程与工具" / "_scripts").glob("*.py"))
    actual = len(scripts)

    text = readme.read_text(encoding="utf-8", errors="replace")
    claimed = [int(m) for m in SCRIPT_COUNT_RE.findall(text)]
    if not claimed:
        rep.add(2, readme, 0, f"未找到自称的脚本总数（实际 {actual} 个）——README 应为唯一出处")
        return
    # 取出现次数最多的那个数作为自称值（避免把"新增 1 个"之类误当总数）
    from collections import Counter
    declared = Counter(claimed).most_common(1)[0][0]
    if declared != actual:
        rep.add(2, readme, 0,
                f"脚本总数对账失败：README 自称 {declared} 个，实际 {actual} 个"
                f"（差 {actual - declared:+d}）")


# ------------------------------------------------- 3 索引覆盖对账
def check_index(root, exclude, rep):
    index = root / "_系统" / "_流程与工具" / "出稿检查总表.md"
    if not index.exists():
        rep.add(3, index, 0, "`出稿检查总表.md` 不存在——资产索引无落点")
        return
    text = index.read_text(encoding="utf-8", errors="replace")
    name_index = build_name_index(root)

    # 3a 索引中提到的 .md / .py 必须存在
    named = set(CODESPAN_RE.findall(text))
    named |= {t.split("#")[0] for t in LINK_RE.findall(text)
              if not t.startswith(("http", "mailto:", "#")) and t.endswith(".md")}

    for name in sorted(named):
        if exempt_name(name):
            continue
        base = Path(name.replace("\\", "/")).name
        if base not in name_index and not (index.parent / name).exists():
            rep.add(3, index, 0, f"资产索引提到的文件全库找不到：{name}")

    # 3b `_流程与工具/` 下的 .md 应被索引覆盖（新文档别忘登记）
    #    ⚠️ 只查**目录顶层**；子目录（_scripts / _journal_data / 核查方法 / 决策记录）
    #       各有自己的 README 或总览，不要求逐个进 §五
    tools_dir = root / "_系统" / "_流程与工具"
    if tools_dir.exists():
        for p in sorted(tools_dir.glob("*.md")):
            if any(c in text for c in index_candidates(p)):
                continue
            rep.add(3, p, 0, f"未被《出稿检查总表》§五 资产索引覆盖：{p.name}")


# ------------------------------------------------- 4 文件名引用有效性（**提示级**）
def check_filename_refs(root, files, rep):
    """只查 `.md` 引用。

    ⚠️ **本类为提示级，不计入退出码。**
    理由：文档里的 `.py` 引用多为**库外或临时**产物——上游 skill 自带的脚本
    （`svg_quality_checker.py`）、用后即删的 `_work/*.py`、待装 skill 的路径。
    这些"找不到"是正常的，不是资产腐烂。若计入硬门禁会淹没真问题。
    见《出稿检查总表》§四「门禁分两种」。
    """
    name_index = build_name_index(root)
    reported = set()

    for md in files:
        try:
            lines = strip_code_blocks(md.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            continue
        for i, line in enumerate(lines, 1):
            for name in CODESPAN_RE.findall(line):
                if not name.endswith(".md") or exempt_name(name):
                    continue
                # ① 按原样（可能是相对本文件的路径）② 取 basename 全库找
                base = Path(name.replace("\\", "/")).name
                if (md.parent / name).exists() or base in name_index:
                    continue
                key = (md.name, base)
                if key in reported:
                    continue
                reported.add(key)
                rep.add(4, md, i, f"引用的文档全库找不到：`{name}`")


# ------------------------------------------------- 5 跨文档重复（**提示级**）
# 约定俗成的通用节名——**各文档本就该有**，不算重复。
# 显式登记在此，不静默跳过（沿用 check-skills.py 与 NAME_EXEMPT_PATTERNS 的豁免纪律）。
HEADING_CONVENTION_EXEMPT = {
    "版本记录", "修订记录", "变更记录", "修改记录",
    "背景与选项", "决定与理由", "代价与推翻条件",   # 决策记录模板的固定三段
    "使用时机", "适用范围", "来源", "出处", "参考", "参考来源", "相关文档",
    "前言", "概述", "总览", "说明", "注意事项", "附", "附录", "常见问题",
    "一句话", "一句话总结", "小结", "结论",
}


def norm_key(s: str) -> str:
    """规范化：去装饰符与空白，用于比较两行是否"同一句话"。"""
    return re.sub(r"[*`⭐⚠️🔴✅❌→·\s]", "", s.strip())


def doc_signature(path: Path, exclude):
    """返回 (有实义的行, 表头, 标题)。用于跨文档比对。"""
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return set(), set(), set()

    lines_clean = strip_code_blocks(raw)
    content, headers = set(), set()

    for i, ln in enumerate(lines_clean):
        s = ln.strip()
        if len(s) < 18:
            continue
        # 表格行：表头 = 紧跟着 |---| 分隔行的那一行
        if s.startswith("|"):
            nxt = lines_clean[i + 1].strip() if i + 1 < len(lines_clean) else ""
            if re.fullmatch(r"\|[\s:\-|]+\|", nxt):
                k = norm_key(s)
                if len(k) >= 6:
                    headers.add(k)
            k = norm_key(s)
            if len(k) >= 15:
                content.add(k)
        elif s.startswith(("- ", "* ", "> ")) or re.match(r"^\d+\.", s):
            k = norm_key(s)
            if len(k) >= 15:
                content.add(k)

    heads = set()
    for ln in raw.splitlines():
        m = re.match(r"^#{2,4}\s+(.*)$", ln)
        if not m:
            continue
        # 去掉章节序号（一、/ 1. / 3.1 等）再比，否则"§七 返工原因"与"§八 返工原因"不等
        t = re.sub(r"^[一二三四五六七八九十\d]+[、.·]?\s*", "", m.group(1).strip())
        t = re.sub(r"^\d+(\.\d+)*\s*", "", t)
        t = re.sub(r"[（(][^）)]*[）)]", "", t)   # 去括号补语：「踩坑清单（复用前必看）」→「踩坑清单」
        k = norm_key(t)
        if len(k) >= 4 and k not in HEADING_CONVENTION_EXEMPT:
            heads.add(k)
    return content, headers, heads


def check_cross_doc_dup(root, exclude, rep, min_lines=6):
    """**只比规范文档区（`_系统/`）**。

    ⚠️ 不扫项目目录——项目里的快照副本（`04_组会汇报/` ↔ `05_汇报成品/`）
    是刻意的存档约定，不是冗余。**重复只在"方法论区"才是问题**：
    那里每件事应有唯一出处。
    """
    scope = root / "_系统"
    if not scope.exists():
        return
    docs = [p for p in scope.rglob("*.md")
            if not any(x in p.parts for x in exclude)]
    sig = {d: doc_signature(d, exclude) for d in docs}

    reported = set()
    name_only = 0   # 只同名、内容不重叠 → 汇总计数，不逐条报

    for i, a in enumerate(docs):
        for b in docs[i + 1:]:
            ca, ha, ta = sig[a]
            cb, hb, tb = sig[b]
            shared_lines = ca & cb
            shared_head = ha & hb
            shared_title = ta & tb

            if len(shared_lines) >= min_lines:
                ex = sorted(shared_lines)[0][:58]
                rep.add(5, a, 0,
                        f"与《{b.name}》有 **{len(shared_lines)} 行完全相同** —— 例：{ex}…")

            for h in sorted(shared_head):
                if len(shared_lines) < 3:
                    name_only += 1
                    continue
                key = ("H", norm_key(a.name), norm_key(b.name), h)
                if key in reported:
                    continue
                reported.add(key)
                rep.add(5, a, 0, f"与《{b.name}》**表头相同且内容重叠**：{h}")

            for t in sorted(shared_title):
                if len(t) < 4:
                    continue
                # ⚠️ 关键收紧：**同名 ≠ 重复**。
                # 「核查方法/」系列每份都有「可粘贴提示词」小节，但内容各不相同——
                # 那是**并行结构**，不是副本。只有同题**且内容确有重叠**才值得报。
                if len(shared_lines) < 3:
                    name_only += 1
                    continue
                key = ("T", norm_key(a.name), norm_key(b.name), t)
                if key in reported:
                    continue
                reported.add(key)
                rep.add(5, a, 0, f"与《{b.name}》**同题且内容重叠**：{t}")

    if name_only:
        rep.add(5, scope / "（汇总）", 0,
                f"另有 {name_only} 处**仅小节同名、内容不重叠**（并行结构，通常不是问题）"
                f"—— 未逐条列出")


# ---------------------------------------------------------------- 主流程
def main():
    ap = argparse.ArgumentParser(
        description="资产静态完整性自检（死链 / 索引漂移 / 自称数字脱节）")
    ap.add_argument("--root", default=str(DEFAULT_ROOT), help="库根目录（默认《科研》根）")
    ap.add_argument("--only", type=int, default=0,
                    help="只跑第 N 类（1 死链 / 2 脚本总数 / 3 索引 / 4 文档引用 / 5 跨文档重复）")
    ap.add_argument("--no-exclude", action="store_true",
                    help="不跳过 _归档 / _快照 / _work（默认跳过）")
    ap.add_argument("--quiet", action="store_true", help="只看汇总")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"❌ 库根不存在：{root}")
        return 2

    exclude = set() if args.no_exclude else EXCLUDE_DIRS
    files = list(iter_markdown(root, exclude))
    rep = Report()

    run = args.only or 0
    if run in (0, 1):
        check_links(root, files, exclude, rep)
    if run in (0, 2):
        check_script_count(root, exclude, rep)
    if run in (0, 3):
        check_index(root, exclude, rep)
    if run in (0, 4):
        check_filename_refs(root, files, rep)
    if run in (0, 5):
        check_cross_doc_dup(root, exclude, rep)

    titles = {1: "相对链接有效性", 2: "脚本总数对账", 3: "索引覆盖对账",
              4: "文档引用有效性（提示级）", 5: "跨文档重复内容（提示级）"}
    GATE = (1, 2, 3)   # 硬门禁：计入退出码
    SOFT = (4, 5)      # 软检查：只提示

    def show(cat, limit=40):
        items = rep.by_cat(cat)
        tag = "硬门禁" if cat in GATE else "软检查"
        print(f"\n=== {cat} · {titles[cat]}［{tag}］：{len(items)} 个问题 ===")
        if not items:
            print("  ✅ 通过")
            return
        for _, path, line, msg in items[:limit]:
            try:
                loc = str(path.relative_to(root))
            except ValueError:
                loc = str(path)
            print(f"  {'❌' if cat in GATE else '⚠️ '} {loc}" + (f":{line}" if line else ""))
            print(f"     {msg}")
        if len(items) > limit:
            print(f"  … 另有 {len(items) - limit} 个（--quiet 看总数）")

    # ⚠️ 只显示**实际跑过**的类别——否则 --only 3 时前两类会假装"通过"
    ran = [c for c in (*GATE, *SOFT) if run in (0, c)]

    if not args.quiet:
        for cat in ran:
            show(cat)
        if rep.by_cat(4):
            print("\n  ⚠️ 第 4 类为提示级：`.py` 引用多为库外/临时产物，不计入退出码")
        if rep.by_cat(5):
            print("\n  ⚠️ 第 5 类为提示级：**重复 ≠ 一定要改**。"
                  "先判断哪一份是「唯一出处」，另一份改为指针")

    gate_n = sum(len(rep.by_cat(c)) for c in GATE if run in (0, c))
    soft_n = sum(len(rep.by_cat(c)) for c in SOFT if run in (0, c))
    print(f"\n{'=' * 46}")
    if gate_n == 0 and soft_n == 0:
        print("✅ 全部通过" + (f"（只跑了第 {run} 类）" if run else ""))
    else:
        parts = " / ".join(f"{titles[c]} {len(rep.by_cat(c))}"
                           for c in ran if rep.by_cat(c))
        flag = "✅ 硬门禁通过" if gate_n == 0 else f"⚠️  硬门禁 {gate_n} 个问题"
        print(f"{flag} ｜ {parts}")
        if soft_n:
            print(f"   （其中软检查 {soft_n} 个，供参考）")
        print("   ⚠️ 本脚本只报不改，修正由人决定")
    return gate_n


if __name__ == "__main__":
    sys.exit(main())

# 2026-09-19 第 5 类（跨文档重复）新增。
#   调参记录——**每一轮都是降假阳性**：
#     首轮 76 项 → 加约定俗成节名豁免（版本记录/背景与选项/决定与理由…）→ 12 项
#     → 收紧为「同名**且内容重叠**才报，仅同名的只汇总」→ **2 项**
#   最终 2 项 = 1 条真实重复（PPT文稿调研 ↔ 去味清单 12 行）+ 1 条同名汇总计数。
#   📌 教训：**同名 ≠ 重复**。第三轮才想明白——「核查方法/」四份各有「可粘贴提示词」
#      小节，那是**并行结构**（每份服务不同场景），报出来只是噪声。

# ---------------------------------------------------------------- 冒烟测试
# 2026-09-19 首次运行（真实库，默认排除 _归档/_快照/_待装skill/.claude/_work）
#
# 修假阳性过程中的四项修正（**每项都是误报，记录以备复用**）：
#   ① 库根层级算错（parents[2] 指到 _系统）→ 索引只扫了 _系统/，分类 2/3/4 大量误报
#   ② 排除目录同时用于"存在性判断" → 引用归档文件被误报死链。
#      改为：**报告对象**排除，**存在性依据**扫全库
#   ③ 索引写的是不带日期后缀的简称（`PPT工具链速查` vs `PPT工具链速查_20260915.md`）
#      → 加 index_candidates() 生成候选写法
#   ④ Obsidian wikilink [[...]] 被当成 markdown 链接 → 匹配前先摘除
#
# 首轮实际抓出（均为真问题）：
#   1 死链     1 处 —— 新增文档里写了示例链接 `[文字](路径)`
#   2 脚本总数 1 处 —— README 自称 21，实际 22（因新增本脚本）
#   3 索引覆盖 7 处 —— 7 份文档存在但未登记进《出稿检查总表》§五
#   4 文档引用 42 处（提示级，未处理）—— 多为库外/临时产物引用，属正常
#
# 修复后：硬门禁 0 问题，退出码 0 ✅
