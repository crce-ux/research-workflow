# -*- coding: utf-8 -*-
"""
renumber_refs.py —— 引用重编号工具（防级联错位）

用途：将文档正文的 [旧编号] 引用映射为新编号。用"单遍正则 + 字典映射"一次性替换，
    避免逐个 .replace() 导致旧→新后再次被后续替换误伤（级联错位）。
    教训：候选课题文档从挂靠综述编号改为独立编号 [1]-[21] 时即用此思路。

用法：
    python renumber_refs.py --doc 候选课题.md \
        --map "5:8,6:6,7:10,15:1,26:5,38:3,39:4,45:7,47:9,61:11,75:2"

    # 若新编号表是连续 [1]-[N]，可只给旧编号列表：
    python renumber_refs.py --doc x.md --old-list "5,6,7,15,26,38,39,45,47,61,75" --new-start 1

参数：
    --doc        文档路径
    --map        "旧:新,旧:新,..."（优先）
    --old-list   "旧,旧,..."（配合 --new-start 生成连续新编号）
    --new-start  连续新编号起始（默认1）
    -o           输出文件（默认覆盖原文件前生成 .bak）

注意：
    - 仅替换 [数字] 形式引用，不触碰文字中的编号表述
    - 未被映射的编号原样保留（不会误伤）
    - 建议先备份（默认自动生成 <doc>.bak）
"""

import sys
import re
import argparse
import shutil

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def build_map(old_list, new_start=1):
    return {str(o): str(new_start + i) for i, o in enumerate(old_list)}


def main():
    ap = argparse.ArgumentParser(description="引用重编号")
    ap.add_argument("--doc", required=True, help="文档路径")
    ap.add_argument("--map", help="'旧:新,旧:新,...'")
    ap.add_argument("--old-list", help="'旧,旧,...'（配合 --new-start）")
    ap.add_argument("--new-start", type=int, default=1)
    ap.add_argument("-o", help="输出文件（默认覆盖原文件，自动备份 .bak）")
    args = ap.parse_args()

    if args.map:
        mapping = {k.strip(): v.strip() for k, v in (p.split(":") for p in args.map.split(","))}
    elif args.old_list:
        mapping = build_map([x.strip() for x in args.old_list.split(",")], args.new_start)
    else:
        sys.exit("需提供 --map 或 --old-list")

    path = args.doc
    shutil.copyfile(path, path + ".bak")
    text = open(path, encoding="utf-8").read()

    def repl(m):
        old = m.group(1)
        return f"[{mapping.get(old, old)}]"

    new_text = re.sub(r"\[(\d+)\]", repl, text)

    out = args.o or path
    with open(out, "w", encoding="utf-8") as f:
        f.write(new_text)

    print(f"[OK] 已备份原文件 → {path}.bak")
    print(f"[OK] 已重编号 → {out}")
    print(f"[OK] 映射 {len(mapping)} 个编号：{mapping}")


if __name__ == "__main__":
    main()
