# -*- coding: utf-8 -*-
"""
build_evtab.py —— 证据表生成器（单一数据源，Step 1 用）

用途：从模块文献数据（Python dict 列表）自动生成
    证据表_模块X.xlsx + 证据表_模块X.md（10 列 PICO + 2 列期刊指标 + 分区组织）。

对应《文献调研流程手册》Step 1：xlsx 是文献主数据源，讲解/综述/PPT 全部与之对齐。

【用法：三种方式之一】
A. 把本文件复制到你的项目 `_scripts/` 下，编辑下方 MODULE_DATA 数据字典，
   改 MODULE / OUT_DIR，运行：python build_evtab.py

B. 数据驱动（推荐）：将文献数据写到独立 data.json，脚本读入生成——
   python build_evtab.py --data 模块X_evidence.json [-o 输出目录] [--module 模块X]
   data.json 格式见下方 MODULE_DATA 注释（json 键名相同）。

【12 列模板】（2026-09-16 起：10 列 PICO + 2 列期刊指标）
    文献·DOI / 作者·年份 / 研究设计 / 人群(P) / 干预或暴露(I/E) /
    对照(C) / 主要结局(O) / 关键结果 / 局限 / **期刊 IF / 期刊分区** / 对本课题的意义

    ⚠️ 列序与「日常文献表」（`build_daily_ref.py`）**前 11 列完全对齐**——
       对接时是纯搬运（文献表 1–11 列 → 证据表 1–11 列），只需补末列「对本课题的意义」。
    ⚠️ 新增的 2 列（journal_if / journal_rank）**允许缺**（中文期刊、预印本、新刊常查不到），
       缺失留空即可。

    【口径要求（重要）】
      · journal_if  → **官方 JCR 影响因子**，须标明年份，如 "4.4 (2024 JCR)"
      · journal_rank→ **中科院分区 + JCR 分区并列**，须标明版本，如
                      "中科院医学2区(升级版2025) / JCR Q2"
      · 中科院分区存在**基础版/升级版**差异，不同年份也会变，**不写口径就不算写清**
      · ⚠️ OpenAlex 的 `2yr_mean_citedness` 只是**近似值**，不等于 JCR IF，
        若用近似值必须在列内标注"近似"

【分区组织】
    SECTIONS = [(分区标题, [文献dict,...]), ...]，每区前自动加藏青分区标题行；
    区内部建议证据等级高→低、同设计年份倒序（手工排）。

⚠️ 踩坑备忘：
  - 分区标题/期刊名勿拼进匹配逻辑（本脚本按 SECTIONS 结构组织，无匹配步骤，天然免疫）
  - 关键结果里的效应量/CI/p 值必须与 PubMed 摘要一致（质量核查②会逐条核对）
  - 卷期页缺失（在线预发表/article number）在"局限"列标注，不硬填
  - Windows 输出乱码：本脚本已 reconfigure utf-8
"""
import sys, os, json, argparse
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

HEADERS = ["文献·DOI", "作者·年份", "研究设计", "人群 (P)", "干预/暴露 (I/E)",
           "对照 (C)", "主要结局 (O)", "关键结果", "局限",
           "期刊 IF", "期刊分区", "对本课题的意义"]
WIDTHS = [30, 16, 18, 30, 28, 14, 24, 60, 40, 14, 26, 36]
NCOL = len(HEADERS)

# ============ 模块数据（方式 A 时编辑本段） ============
MODULE = "思路A"
OUT_DIR = r"<vault>/TRS_EEG/01_文献调研/思路A_药物反应预测"
SECTIONS = [
    ("A0 总体锚点（方向可行性与特征策略）", []),   # 示例：从 json 读取时留空
]
# =======================================================

def build_xlsx(module, sections, out_xlsx):
    wb = Workbook()
    ws = wb.active
    ws.title = f"证据表_{module}"
    # 标题行
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=NCOL)
    c = ws.cell(row=1, column=1, value=f"{module} 证据表（单一数据源 · 文献主数据）")
    c.font = Font(bold=True, size=14, color="FFFFFF")
    c.fill = PatternFill("solid", fgColor="1F3A5F")
    c.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 28
    # 表头
    hdr_font = Font(bold=True, color="FFFFFF")
    hdr_fill = PatternFill("solid", fgColor="3A6EA5")
    thin = Side(style="thin", color="BFBFBF")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    for col, h in enumerate(HEADERS, 1):
        cell = ws.cell(row=2, column=col, value=h)
        cell.font = hdr_font; cell.fill = hdr_fill; cell.border = border
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.column_dimensions[chr(64 + col)].width = WIDTHS[col - 1]
    # 数据 + 分区
    r = 3
    sec_font = Font(bold=True, color="FFFFFF")
    sec_fill = PatternFill("solid", fgColor="2C5F8A")
    n_data = 0
    for sec_title, rows in sections:
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=NCOL)
        cell = ws.cell(row=r, column=1, value=sec_title)
        cell.font = sec_font; cell.fill = sec_fill
        cell.alignment = Alignment(horizontal="left", vertical="center")
        r += 1
        for it in rows:
            vals = [ref_label(it), it["authors"],
                    it["design"], it["pop"], it["inter"], it["ctrl"], it["out"],
                    it["key"], it["limit"],
                    it.get("journal_if", ""), it.get("journal_rank", ""),
                    it["meaning"]]
            for col, v in enumerate(vals, 1):
                cell = ws.cell(row=r, column=col, value=v)
                cell.border = border
                cell.alignment = Alignment(vertical="top", wrap_text=True)
            r += 1; n_data += 1
    wb.save(out_xlsx)
    return n_data

def build_md(module, sections):
    md = [f"# {module} 证据表（单一数据源）", "",
          "> 10 列 PICO + 2 列期刊指标（IF / 分区）+ 分区组织（《文献调研流程手册》Step 1）。",
          "> 数据核实：PMID/DOI/卷期页经 PubMed esummary 批量核实；关键结果基于 PubMed 摘要。",
          "> 期刊指标口径：IF 为官方 JCR 值（标年份）；分区为中科院分区（标版本）+ JCR 分区。", ""]
    hdr = "| " + " | ".join(HEADERS) + " |"
    sep = "|" + "---|" * NCOL
    for sec_title, rows in sections:
        md.append(f"## {sec_title}\n")
        md.append(hdr)
        md.append(sep)
        for it in rows:
            md.append(f"| {ref_label(it)} | {it['authors']} "
                      f"| {it['design']} | {it['pop']} | {it['inter']} | {it['ctrl']} | {it['out']} "
                      f"| {it['key']} | {it['limit']} "
                      f"| {it.get('journal_if', '')} | {it.get('journal_rank', '')} "
                      f"| {it['meaning']} |")
        md.append("")
    return "\n".join(md)

# 必填字段（缺失即报错）：核心内容列。
#   ⚠️ 2026-09-16 调整：**pmid 不再是绝对必填**——预印本、会议摘要、中文期刊常无 PMID，
#      但只要有 DOI 同样可溯源。改由「pmid 与 doi 至少其一」的规则把关（见 normalize）。
#   其余列允许缺：ctrl 可填 NA；inter/limit 可选；
#   journal_if / journal_rank 中文刊、预印本、新刊常查不到，允许留空。
REQUIRED_FIELDS = ["authors", "design", "pop", "out", "key", "meaning"]
ALL_FIELDS = ["authors", "pmid", "doi", "design", "pop", "inter", "ctrl", "out", "key", "limit", "meaning",
              "journal_if", "journal_rank"]

def item_id(it, idx):
    """条目标识：优先 pmid，其次 authors，兜底序号"""
    for k in ("pmid", "authors"):
        if it.get(k):
            return str(it.get(k))
    return f"#{(idx or 0) + 1}"

def normalize(it, idx=None):
    """校验必填字段并补齐默认键；缺失必填字段 → 抛 ValueError（防静默空数据）"""
    missing = [k for k in REQUIRED_FIELDS if not str(it.get(k, "")).strip()]
    if missing:
        raise ValueError(f"[条目 {item_id(it, idx)}] 缺失必填字段: {', '.join(missing)}"
                         f"（必填: {', '.join(REQUIRED_FIELDS)}）")
    if not str(it.get("pmid", "")).strip() and not str(it.get("doi", "")).strip() \
            and not str(it.get("id_note", "")).strip():
        raise ValueError(f"[条目 {item_id(it, idx)}] pmid 与 doi 均为空——"
                         f"至少要有一个可溯源的标识；确属无标识者（如会议摘要），"
                         f"须显式填 `id_note` 说明原因。")
    return {k: it.get(k, "") for k in ALL_FIELDS}


def ref_label(it):
    """第 1 列：作者·年份（PMID x / DOI y）—— 缺 PMID 时只显示 DOI（预印本/会议摘要）"""
    parts = []
    if str(it.get("pmid", "")).strip():
        parts.append(f"PMID {it['pmid']}")
    if str(it.get("doi", "")).strip():
        parts.append(f"DOI {it['doi']}")
    suffix = " / ".join(parts) or str(it.get("id_note", "")).strip()
    authors = it.get("authors", "")
    return f"{authors}（{suffix}）" if suffix else authors

def main():
    ap = argparse.ArgumentParser(description="证据表生成器（xlsx + md，10 列 PICO + 2 列期刊指标）")
    ap.add_argument("--data", help="文献数据 JSON（列表 of dict，见脚本头注释格式）")
    ap.add_argument("-o", "--outdir", default=OUT_DIR, help="输出目录")
    ap.add_argument("--module", default=MODULE, help="模块名（用于文件名）")
    args = ap.parse_args()

    try:
        if args.data:
            with open(args.data, encoding="utf-8") as f:
                raw = json.load(f)
            if isinstance(raw, list) and raw and "title" in raw[0]:
                sections = [(s.get("title", "文献证据"),
                             [normalize(x, i) for i, x in enumerate(s.get("rows", []))])
                            for s in raw]
            else:
                sections = [("文献证据", [normalize(x, i) for i, x in enumerate(raw)])]
        else:
            sections = [(t, [normalize(x, i) for i, x in enumerate(rows)]) for t, rows in SECTIONS]
    except ValueError as e:
        sys.exit(f"[错误] 字段校验未通过：{e}\n[提示] 修正数据 JSON 后重跑，勿生成含空关键结果的证据表。")

    os.makedirs(args.outdir, exist_ok=True)
    xlsx = os.path.join(args.outdir, f"证据表_{args.module}.xlsx")
    md = os.path.join(args.outdir, f"证据表_{args.module}.md")

    # xlsx 可能被 Excel 占用（Windows 常见）→ 捕获后仍生成 md，不整体失败
    n = sum(len(rows) for _, rows in sections)
    try:
        n = build_xlsx(args.module, sections, xlsx)
        print(f"[OK] xlsx: {xlsx}")
    except PermissionError:
        print(f"[!] xlsx 写入失败（文件被占用，通常是 Excel 正打开着）：{xlsx}")
        print(f"    → 请关闭 Excel 后重跑本命令；**md 已照常生成**。")

    with open(md, "w", encoding="utf-8") as f:
        f.write(build_md(args.module, sections))
    print(f"[OK] md:   {md}")
    print(f"[OK] 共 {n} 篇文献，{len(sections)} 个分区")
    n_if = sum(1 for _, rows in sections for it in rows if it.get("journal_if"))
    n_rank = sum(1 for _, rows in sections for it in rows if it.get("journal_rank"))
    print(f"[i]  期刊指标填写情况：IF {n_if}/{n} · 分区 {n_rank}/{n}")

if __name__ == "__main__":
    main()
