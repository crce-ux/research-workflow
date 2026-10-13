# -*- coding: utf-8 -*-
"""
make_notes.py —— 讲稿 → PPT 备注（每页一个 .md，供 ppt_build 自动带进 PPTX）

【为什么有它】
    ppt-master 的导出器**默认读 `<项目>/notes/`**，把内容写进 PowerPoint 备注栏。
    我们此前从没建过这个目录 —— 备注栏一直是空的，讲的时候要另开一个讲稿窗口。

    已有讲稿（`组会汇报_讲稿_v3_新页序_*.md`）本来就是**口语化的全文**，
    几乎可以直接当备注。本脚本只做三件清洗：去掉 Markdown 强调标记、
    去掉分隔线、把 `## NN · 标题` 转成文件名。

【用法】
    # 基本：讲稿 → notes/（文件名 = NN_标题.md）
    python make_notes.py 讲稿.md -o <项目目录>/notes

    # 推荐：按已有 svg 文件名对齐（按数字前缀匹配，保证一一对应）
    python make_notes.py 讲稿.md -o <项目>/notes --match-svg <项目>/svg

    # 去掉【停顿】【翻页】这类舞台提示（默认**保留** —— 给人看有用）
    python make_notes.py 讲稿.md -o out --drop-stage

    # 排除「备用」页（默认排除 —— 备用页不在片子里）
    python make_notes.py 讲稿.md -o out --with-backup

【产出】
    notes/01_封面.md … notes/16_交叉空白….md

【配套】
    `PPT工具链速查_20260915.md` §七 讲稿备注
"""
import argparse
import glob
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

#: 页标题行：`## 07 · 屏状核：位置、体积与连接` 或 `## 备用 · 研究切入点与假设`
RE_PAGE = re.compile(r"^##\s+([0-9]{1,2}|备用)\s*[·.、]\s*(.+?)\s*$", re.M)

#: 舞台提示（默认保留）
RE_STAGE = re.compile(r"【[^】]{1,12}】")

#: 非法文件名字符
RE_BADNAME = re.compile(r'[\\/:*?"<>|\n\r\t]')


def clean_body(text, drop_stage=False):
    """把讲稿正文洗成适合放进 PPT 备注栏的纯文本"""
    t = text
    t = re.sub(r"^\s*-{3,}\s*$", "", t, flags=re.M)     # 分隔线
    t = re.sub(r"\*\*(.+?)\*\*", r"\1", t, flags=re.S)  # 粗体标记
    t = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\1", t, flags=re.S)  # 斜体
    if drop_stage:
        t = RE_STAGE.sub("", t)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t).strip()
    return t


def split_pages(md):
    """切成 [(编号 or '备用', 标题, 正文)]"""
    out = []
    ms = list(RE_PAGE.finditer(md))
    for i, m in enumerate(ms):
        end = ms[i + 1].start() if i + 1 < len(ms) else len(md)
        out.append((m.group(1), m.group(2).strip(), md[m.end():end]))
    return out


def svg_prefix_map(svg_dir):
    """扫 svg 目录，返回 {数字前缀: 完整文件名主干}"""
    m = {}
    for f in glob.glob(os.path.join(svg_dir, "*.svg")):
        stem = os.path.splitext(os.path.basename(f))[0]
        hit = re.match(r"^(\d{1,2})[_\-. ]", stem)
        if hit:
            m[int(hit.group(1))] = stem
    return m


def main():
    ap = argparse.ArgumentParser(description="讲稿 → PPT 备注（每页一个 .md）")
    ap.add_argument("script", help="讲稿 markdown（含 `## NN · 标题` 分页）")
    ap.add_argument("-o", "--out", required=True, help="输出目录（通常是 <项目>/notes）")
    ap.add_argument("--match-svg", help="按此目录里的 svg 文件名对齐（按数字前缀）")
    ap.add_argument("--drop-stage", action="store_true", help="去掉【停顿】【翻页】等舞台提示")
    ap.add_argument("--with-backup", action="store_true", help="包含「备用」页")
    a = ap.parse_args()

    if not os.path.isfile(a.script):
        print(f"❌ 找不到讲稿：{a.script}"); return 1
    md = open(a.script, encoding="utf-8").read()
    pages = split_pages(md)
    if not pages:
        print("❌ 没解析到页。讲稿需要 `## NN · 标题` 形式的标题行"); return 1

    os.makedirs(a.out, exist_ok=True)
    svgmap = svg_prefix_map(a.match_svg) if a.match_svg else {}

    made, skipped = [], []
    for num, title, body in pages:
        if num == "备用" and not a.with_backup:
            skipped.append(title)
            continue
        note = clean_body(body, a.drop_stage)
        # 文件名：优先跟随已有 svg 名；否则 NN_标题
        if num.isdigit() and int(num) in svgmap:
            fname = svgmap[int(num)] + ".md"
        else:
            safe = RE_BADNAME.sub("_", title)[:40].strip("_ ")
            fname = f"{num}_{safe}.md" if num.isdigit() else f"备用_{safe}.md"
        path = os.path.join(a.out, fname)
        open(path, "w", encoding="utf-8").write(note + "\n")
        made.append((fname, len(note)))

    print(f"✅ 写入 {len(made)} 个备注 → {a.out}\n")
    for f, n in made:
        print(f"   {f:<44} {n:>4} 字")
    if skipped:
        print(f"\n   跳过备用页 {len(skipped)} 个：{skipped}")
    if a.match_svg and svgmap:
        unmatched = [n for n, _, _ in
                     [(x[0], 0, 0) for x in pages] if n.isdigit() and int(n) not in svgmap]
        if unmatched:
            print(f"\n   ⚠️ 这些页号在 svg 目录里没有对应文件：{unmatched}")
    print(f"\n   下一步：python _scripts/ppt_build.py <项目目录> --only pptx")
    return 0


if __name__ == "__main__":
    sys.exit(main())
