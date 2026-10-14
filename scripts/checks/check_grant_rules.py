# -*- coding: utf-8 -*-
"""check_grant_rules.py —— 国自然文档「不得硬编码年度性数值」

【背景】
    grant-diagnosis 自己立的规矩：**篇幅 / 年龄 / 申请代码 / 经费这类值
    一律现场取，不写进文档**。NSFC 每年改版——写死的值 1–2 年后即失效，
    照过期值写会出错。

    这条规矩是**存在性**：「有没有写死一个数」。不是「写死的数对不对」——
    后者要等当年《项目指南》，机器判不了。

【它查什么】
    篇幅（N 字 / N 页）、年龄（N 周岁）、申请代码（H0902 这类）、
    经费（N 万元）、资助期限（N 年）——出现在指导类文档里就报。

【它豁免什么】
    同一行里带以下这些词的，不算写死：当年 / 以…为准 / 现场取 / 核对 / 问号 / 举例。
    ⚠️ 豁免要**同行**——跨行的理由不算，因为引用块折行很常见。

【它不查什么】
    ⭐ 「对不对」与「有没有写」是两件事。本脚本只做后者。

用法：
    python check_grant_rules.py <文件或目录>

退出码 = 命中条数（0 = 全过）
"""
import argparse
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PATTERNS = [
    ("篇幅（字数）", re.compile(r"\d[\d,]*\s*字(?:以内|以下|以上|数)?(?!符)")),
    ("篇幅（页数）", re.compile(r"\d[\d,]*\s*页")),
    ("年龄", re.compile(r"\d{2}\s*周岁|年龄.{0,6}?\d{2}\s*岁")),
    ("申请代码", re.compile(r"(?<![A-Za-z0-9])[A-H]\d{2,4}(?![A-Za-z0-9])")),
    ("经费", re.compile(r"\d[\d,]*\s*万元")),
    ("资助期限", re.compile(r"资助(?:期限|年限).{0,4}?\d\s*年")),
]

# 同行出现任一，即视为「没有写死」
EXEMPT = re.compile(r"当年|以.{0,6}为准|现场取|核对|复核|\?|？|举例|例如|如：|示例|待核")

# 只在**指导类文档**上触发——申请人的标书里出现代码、经费是正常的
TRIGGER = re.compile(r"指南|提纲|填报|规则|rules|核对|清单|申报|模板|说明|SKILL\.md$", re.I)


def scan(text, name):
    hits = []
    for i, line in enumerate(text.splitlines(), 1):
        if EXEMPT.search(line):
            continue
        for label, pat in PATTERNS:
            m = pat.search(line)
            if m:
                hits.append(f"{name}:{i} 【{label}】写死了「{m.group()}」——"
                            f"年度性数值一律现场取，别写进文档（{line.strip()[:50]}）")
                break
    return hits


def main():
    ap = argparse.ArgumentParser(description="国自然文档：年度性数值硬编码检查")
    ap.add_argument("path")
    a = ap.parse_args()

    root = pathlib.Path(a.path)
    files = [root] if root.is_file() else sorted(root.rglob("*.md"))

    hits, nfile, evaluated = [], 0, 0
    for p in files:
        if not p.is_file():
            continue
        nfile += 1
        if not TRIGGER.search(p.name):
            continue
        evaluated += 1
        hits += scan(p.read_text(encoding="utf-8", errors="replace"), p.name)

    print(f"check_grant_rules · {a.path} · 扫 {nfile} 个文件，"
          f"其中 {evaluated} 个是指导类（其余跳过）")
    if not hits:
        if evaluated == 0:
            print("  ⚠️ 本次未评——目录里没有「指南 / 提纲 / 规则 / 核对 / 申报」类文档，"
                  "没有可评的文件。")
        else:
            print("  ✅ 已评的文件全过")
        return 0
    for h in hits:
        print(f"  ❌ {h}")
    print(f"\n  共 {len(hits)} 处。⚠️ 只查「有没有写死」，不查「写死的数对不对」——"
          f"后者以当年《项目指南》为准。")
    return len(hits)


if __name__ == "__main__":
    raise SystemExit(main())
