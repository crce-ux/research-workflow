# -*- coding: utf-8 -*-
"""check_doc_structure.py —— 稿件章节结构的只报体检

【它查什么】
    Markdown 稿件的标题树与每节正文长度，报四类可判定的结构问题：
      · 标题层级跳跃（一级直接到三级）
      · 只有一个子节的节（该子节应并入父节，或补第二个子节）
      · 空节（有标题、无正文、无子节）
      · 同级相邻两节都很短（正文少于 100 个汉字）→ 可以合并

【它不查什么】
    节的内容合不合理、段内有没有两个论点、论证是否推进——判断，人工过。
    非 Markdown 文件（.tex / .docx）本次不作答，直接打印「本次未评」。

【为什么退出码恒为 0】
    结构问题属于「只报可疑」，不是硬门禁。要进 CI 时读输出，不要读退出码。

用法：
    python check_doc_structure.py 文稿.md [--min-chars 100]
"""
import argparse
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HEAD = re.compile(r"^(#{1,6})\s+(\S.*)$")
FENCE = re.compile(r"^\s*(```|~~~)")
CJK = re.compile(r"[一-鿿]")


def parse(lines):
    """返回 [(层级, 标题, 行号, 正文汉字数)]，跳过代码块内的井号。"""
    nodes, in_fence = [], False
    cur = None
    for i, line in enumerate(lines, 1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = HEAD.match(line)
        if m:
            if cur:
                nodes.append(cur)
            cur = [len(m.group(1)), m.group(2).strip(), i, 0]
            continue
        if cur:
            cur[3] += len(CJK.findall(line))
    if cur:
        nodes.append(cur)
    return nodes


def report(nodes, min_chars):
    issues = []
    # 1 层级跳跃
    for a, b in zip(nodes, nodes[1:]):
        if b[0] > a[0] + 1:
            issues.append(("层级跳跃", b[2],
                           f"「{a[1]}」（{'#' * a[0]}）直接跳到「{b[1]}」（{'#' * b[0]}）"))
    # 2、3 子节数量与空节
    for idx, (lv, title, ln, chars) in enumerate(nodes):
        children = []
        for nxt in nodes[idx + 1:]:
            if nxt[0] <= lv:
                break
            if nxt[0] == lv + 1:
                children.append(nxt)
        if not children and chars == 0:
            issues.append(("空节", ln, f"「{title}」有标题、无正文、无子节"))
        elif len(children) == 1:
            issues.append(("独子节", ln,
                           f"「{title}」只有一个子节「{children[0][1]}」"))
    # 4 同级相邻短节
    for a, b in zip(nodes, nodes[1:]):
        if a[0] == b[0] and a[3] < min_chars and b[3] < min_chars:
            issues.append(("可合并", b[2],
                           f"「{a[1]}」（{a[3]} 字）与「{b[1]}」（{b[3]} 字）都很短"))
    return issues


def main():
    ap = argparse.ArgumentParser(description="稿件章节结构只报体检")
    ap.add_argument("doc")
    ap.add_argument("--min-chars", type=int, default=100,
                    help="相邻短节的汉字上限（默认 100）")
    a = ap.parse_args()

    if not a.doc.lower().endswith(".md"):
        print(f"check_doc_structure · {a.doc}")
        print("  ⚠️ 非 Markdown 文件，本章节结构检查本次未评（只支持 .md）")
        return 0

    text = open(a.doc, encoding="utf-8", errors="replace").read()
    nodes = parse(text.splitlines())
    print(f"check_doc_structure · {a.doc}")
    if not nodes:
        print("  ⚠️ 识别到 0 个标题，本章节结构检查本次未评")
        return 0

    print(f"  识别到 {len(nodes)} 个标题 · 正文 {sum(n[3] for n in nodes)} 字")
    for lv, title, ln, chars in nodes:
        print(f"    {'  ' * (lv - 1)}{'#' * lv} {title}（{chars} 字）")

    issues = report(nodes, a.min_chars)
    print(f"\n  检查 4 项：层级跳跃 / 独子节 / 空节 / 可合并")
    if not issues:
        print("  ✅ 无问题")
    else:
        for kind, ln, msg in issues:
            print(f"  ○ {kind} 第 {ln} 行：{msg}")
        print(f"\n  共 {len(issues)} 处。只报可疑，改不改由人定。")
    print("  未评：段内两个论点、节与节之间的论证推进、节的内容合不合理")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
