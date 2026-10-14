# -*- coding: utf-8 -*-
"""check_vault.py —— 科研库的命名与结构规范机检

【背景】
    `manuals/` 49 份手册里写了一批**命名 / 结构 / 必填字段**的硬规范——
    精读笔记怎么命名、最终稿带不带日期、ADR 编号、工作日志字段、变量字典必填列、
    SAP 偏离记录、AI 声明要素、国自然八层、理解确认清单无空白。
    命名 / 结构 / 必填字段规范全是纯格式。

【它不查什么】
    内容对不对、方法学选得好不好——一律不碰。本脚本只查**长得对不对**。

【每组的规范出处】见各函数 docstring（都引自 `manuals/`，不是自创）。

【搬走的两条 · 2026-10-14】
    原 S2「变量字典必填列」与 S3「SAP 偏离记录列」已搬到 `check_data.py`——
    check_vault 管的是**科研库命名与结构**，而变量字典与 SAP 偏离属于**数据管线的口径**，
    不该挂在 check_vault 名下。

【撤回记录 · 2026-10-14】
    有两条规则写出来了，但**判据不成立**，已撤回，理由留档：

    · **国自然架构八层**（原 S5）。想出过三种判据，全不成立：
      ① 按正文出现八层关键词——库里三份「国自然标书_XX手册」讲的是**怎么写标书**，
         不是标书，全部误报；
      ② 按八层有没有作为小标题出现——「背景」「空白」「科学问题」是**任何研究文档**
         的常规小标题，实测每一份论文草稿、调研报告都被打成「缺七层」；
      ③ 按文件名——同上，手册和标书同名同姓，分不开。
      根因：**「这份文档是不是一份标书骨架」属语义判断**，机检做不到。
      判据不成立就不该有规则——一条只在误报时响的规则比没有规则更坏。

    · **理解确认清单的「术语表/数字表无空白」**（原 S6 的一半）。模板 §七 是**填完后**
      的通过标准，而清单里的空格正是**留给人手填的作答栏**——实测真实清单的术语表有
      86 处空格，全是待填列。用空格数当判据，会把工作表本身打成不合格。只留
      「未解决项须显式列出」一条（这条有实例、可判定）。

用法：
    python check_vault.py <文件或目录> [--only N1,N3]
    python check_vault.py 科研/工作日志/ --only S1

退出码 = 命中条数（0 = 全过）
"""
import argparse
import fnmatch
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATE_SUFFIX = re.compile(r"[_\-—](20\d{2}|20\d{2}[-_.]\d{2}[-_.]\d{2}|20\d{2}\d{4})\b")
ADR_NAME = re.compile(r"^\d{4}-.+\.md$")
JINGDU_NAME = re.compile(r"^精读笔记_.+?\d{4}_.+\.md$")

# 分类上是「表单」而非「实例」——表单不必满足自己规定的规则，一律不查结构。
NOT_AN_INSTANCE = ("模板", "README", "索引", "MOC")

# 精读笔记正文的阅读深度枚举（日常精读手册）——目前真实笔记用「**方式**：全文精读」表述，
# 故只作记录，不设机检（没有可核对的实例，写了也是空转）。


# ── 命名类（只看文件名）─────────────────────────────────────

def n1_jingdu_name(p):
    """精读笔记命名：`精读笔记_<第一作者><年份>_<主题>.md`（日常精读手册 §3.1）"""
    if not p.name.startswith("精读笔记_") or p.suffix != ".md":
        return []
    return [] if JINGDU_NAME.match(p.name) else \
        [f"{p.name}：应为 `精读笔记_<第一作者><年份>_<主题>.md`"]


def n2_final_name(p):
    """交付物命名：**最终稿不带日期，过程稿带日期**（文本迭代自查流程 §八）

    ⚠️ 只认「终稿」这个**版本标记**，不认正文里的「最终」二字——
    「竞争团队文献表_最终核实报告」里的「最终」是修饰「核实」的，不是版本号（实测误报）。
    """
    if p.suffix not in (".md", ".docx") or "终稿" not in p.stem:
        return []
    m = DATE_SUFFIX.search(p.stem)
    return [f"{p.name}：最终稿不应带日期（过程稿才带）—— 命中「{m.group(0)}」"] if m else []


def n3_adr_name(p):
    """ADR 命名：`NNNN-短标题.md`（第三方技能库评估 §A3）

    目录里的 README / 索引不是 ADR，豁免——否则每建一个都误报。
    """
    if p.parent.name != "决策记录" or p.suffix != ".md":
        return []
    if any(k in p.stem for k in ("README", "索引")):
        return []
    return [] if ADR_NAME.match(p.name) else [f"{p.name}：应为 `NNNN-短标题.md`"]


# ── 结构类（看内容）─────────────────────────────────────────

def s1_worklog(text, p):
    """工作日志：frontmatter 六字段 + 正文四要素 + **条目倒序**（工作日志模板）"""
    if "工作日志" not in p.name or p.suffix != ".md":
        return []
    bad = []
    fm = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not fm:
        return [f"{p.name}：缺 frontmatter"]
    for k in ("title", "tags", "project", "type", "created"):
        if not re.search(rf"^{k}\s*:", fm.group(1), re.M):
            bad.append(f"frontmatter 缺 `{k}`")
    for k in ("项目：", "索引：", "起始：", "规则："):
        if k not in text:
            bad.append(f"正文缺「{k}」行")
    dates = re.findall(r"^##\s*(20\d{2}-\d{2}-\d{2})", text, re.M)
    if dates != sorted(dates, reverse=True):
        bad.append("条目没倒序（规则：最新条目在最上）")
    return [f"{p.name}：{b}" for b in bad]




def s4_ai_declaration(text, p):
    """AI 使用声明五要素（AI使用情况声明模板 §二/§五）——同 S2，按文件名触发。"""
    if "AI使用" not in p.name and "AI 使用" not in p.name:
        return []
    need = [("工具/版本", r"工具|模型|版本"),
            ("时间范围", r"时间范围|20\d{2}"),
            ("人工核实方式", r"人工核实"),
            ("未使用 AI 直接生成正文", r"未使用\s*AI\s*直接生成正文")]
    miss = [n for n, pat in need if not re.search(pat, text)]
    return [f"{p.name}：AI 声明缺 {'/'.join(miss)}"] if miss else []


def s6_understanding(text, p):
    """理解确认清单：**未解决项须显式列出**（理解确认清单模板 §七）

    ⚠️ 只查「未解决项须显式列出」这一条。模板 §七 的另两条——「术语表无空白 / 数字表无空白」——**不机检**：
    属**填完后**的通过标准，而清单里的空白格正是**留给人手填的作答栏**
    （实测真实清单的术语表有 86 处空格，全是待填列，不是缺陷）。
    用空格数当判据会把工作表本身打成不合格——判据不成立，故不设。
    """
    if "理解确认清单" not in p.name:
        return []
    if "未解决项" not in text:
        return [f"{p.name}：缺「未解决项」小节（可以为空，但不能没写）"]
    return []


RULES = [
    ("N1", "精读笔记命名", None, n1_jingdu_name),
    ("N2", "最终稿不带日期", None, n2_final_name),
    ("N3", "ADR 命名", None, n3_adr_name),
    ("S1", "工作日志字段+倒序", "*.md", s1_worklog),
    ("S4", "AI 声明要素", "*.md", s4_ai_declaration),
    ("S6", "理解确认清单", "*.md", s6_understanding),
]


def main():
    ap = argparse.ArgumentParser(description="科研库命名与结构规范机检")
    ap.add_argument("path")
    ap.add_argument("--only", default=None, help="只查指定组，如 N2,S1")
    a = ap.parse_args()
    only = {x.strip().upper() for x in a.only.split(",")} if a.only else None

    root = pathlib.Path(a.path)
    files = [root] if root.is_file() else sorted(root.rglob("*"))

    hits, nfile = [], 0
    for p in files:
        if not p.is_file():
            continue
        nfile += 1
        text = p.read_text(encoding="utf-8", errors="replace") if p.suffix in (".md",) else ""
        is_template = any(k in p.name for k in NOT_AN_INSTANCE)
        for rid, name, glob, fn in RULES:
            if only and rid not in only:
                continue
            if glob is None:
                # 命名类：只看文件名。模板文件名也该守命名规矩。
                found = fn(p)
            else:
                # 结构类：只看实例。表单不必满足自己规定的规则。
                if not fnmatch.fnmatch(p.name, glob) or is_template:
                    continue
                found = fn(text, p)
            hits += [(rid, name, m) for m in found]

    print(f"check_vault · {a.path} · 扫 {nfile} 个文件")
    if not hits:
        print("  ✅ 全过（八组规范）")
        return 0
    for rid, name, m in hits:
        print(f"  ❌ {rid} {name}：{m}")
    print(f"\n  共 {len(hits)} 处。⚠️ 只查格式，不查内容对不对。")
    return len(hits)


if __name__ == "__main__":
    raise SystemExit(main())
