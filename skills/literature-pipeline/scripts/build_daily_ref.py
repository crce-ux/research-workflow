# -*- coding: utf-8 -*-
"""
build_daily_ref.py —— 日常文献表生成器（文献精读 → 证据表 的上游沉淀）

用途：从日常精读积累的文献数据（JSON）生成「文献表.xlsx + 文献表.md」。
    列结构对齐《文献调研流程手册》Step 1 证据表的**前 9 列（PICO）**，
    另加 4 列管理字段（主题标签 / 精读状态 / 笔记链接 / 入库日期）。

【与证据表的关系】
    日常精读 = 人工筛选 + 理解，是**上游沉淀**；
    项目检索 / 主题分享时需要证据表，是**下游复用**。
    **前 11 列与证据表「文献·DOI … 期刊分区」完全对齐** → 对接时是纯搬运，
    只需补 1 列「对本课题的意义」+ 按叙事分区重组。

【期刊指标口径（journal_if / journal_rank）】
    · journal_if  → **官方 JCR 影响因子**，须标年份，如 "4.4 (2024 JCR)"
    · journal_rank→ **中科院分区（标版本）+ JCR 分区**并列，如
                    "中科院医学2区(升级版2025) / JCR Q2"
    · ⚠️ 中科院分区有基础版/升级版差异、逐年变动——**不写口径就不算写清**
    · ⚠️ OpenAlex 的 2yr_mean_citedness 只是**近似值**，用则须标注"近似"
    · 中文期刊 / 预印本 / 新刊常查不到 → **允许留空**

【用法】
    python build_daily_ref.py --data _文献表.json -o <输出目录>
    python build_daily_ref.py --data _文献表.json -o "<vault>/文献精读"

【数据 JSON 格式】（列表 of dict）
    [ { "authors": "Ciprian 2020", "pmid": "33513093", "doi": "10.1109/...",
        "design": "回顾性队列（单中心）", "pop": "57 例 TRS-SCZ ...",
        "inter": "氯氮平，平均 347 mg/d", "ctrl": "NA",
        "out": "氯氮平应答（PANSS 减分率）", "key": "准确率 95.83%、κ=0.91",
        "limit": "单中心；极端分组；无外部验证",
        "journal_if": "4.4 (2024 JCR)", "journal_rank": "中科院医学2区(升级版2025) / JCR Q2",
        "topic": "TRS/氯氮平反应预测/有效连接",
        "status": "✅已精读", "note": "[[精读笔记_xxx]]", "added": "2026-08-31" }, ... ]

【对接证据表（四步）】
    1. 从本表按「主题标签」筛选相关条目
    2. 补 "meaning"（对本课题的意义）字段 —— 此步需课题上下文，人工完成
    3. 按叙事分区组织 → 模块X_evidence.json（SECTIONS 结构，见 build_evtab.py 头注释）
    4. python build_evtab.py --data 模块X_evidence.json -o <项目目录> --module 模块X

⚠️ 踩坑备忘：
  - 「关键结果」列必须回**原文/全文**核对，不可仅凭摘要转抄（摘要常不载样本量与效应量，
    而精读的价值恰在于有全文）——否则对接证据表时仍要返工
  - 「人群」列须填全样本量（返工总表：「被追问答不上样本量」的根因就是摘要未载、未调全文）
  - 精读状态建议用：⬜未读 / 🔄在读 / ✅已精读 / 📝笔记完成
  - Windows 输出乱码：本脚本已 reconfigure utf-8
"""
import sys, os, json, argparse
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

# 第 1 列「文献·DOI」由 authors + pmid/doi 自动拼接；其余列与 KEYS 一一对应
# ⚠️ 前 11 列（文献·DOI … 期刊分区）与证据表 build_evtab.py **完全对齐** → 对接时是纯搬运
HEADERS = ["文献·DOI", "作者·年份", "研究设计", "人群 (P)", "干预/暴露 (I/E)",
           "对照 (C)", "主要结局 (O)", "关键结果", "局限",
           "期刊 IF", "期刊分区",
           "主题标签", "精读状态", "笔记链接", "入库日期"]
KEYS = ["authors", "design", "pop", "inter", "ctrl", "out", "key", "limit",
        "journal_if", "journal_rank",
        "topic", "status", "note", "added"]
WIDTHS = [36, 16, 18, 34, 30, 14, 22, 58, 42, 14, 26, 26, 12, 34, 12]

# 必填字段（缺失即报错）：核心溯源/内容列。doi/pmid/inter/ctrl/limit/note 允许缺
REQUIRED_FIELDS = ["authors", "design", "pop", "out", "key", "topic"]
ALL_FIELDS = ["authors", "pmid", "doi"] + KEYS

TITLE_FILL = "1F3A5F"   # 藏青（与证据表一致）
HDR_FILL = "3A6EA5"
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def ref_label(it):
    """第 1 列：作者·年份（PMID x / DOI y）—— 与证据表「文献·DOI」列格式一致"""
    parts = []
    if str(it.get("pmid", "")).strip():
        parts.append(f"PMID {it['pmid']}")
    if str(it.get("doi", "")).strip():
        parts.append(f"DOI {it['doi']}")
    suffix = " / ".join(parts)
    authors = it.get("authors", "")
    return f"{authors}（{suffix}）" if suffix else authors


def normalize(it, idx=None):
    """校验必填字段；缺失即抛 ValueError（防静默空数据）"""
    missing = [k for k in REQUIRED_FIELDS if not str(it.get(k, "")).strip()]
    if missing:
        ident = it.get("authors") or f"#{(idx or 0) + 1}"
        raise ValueError(f"[条目 {ident}] 缺失必填字段: {', '.join(missing)}"
                         f"（必填: {', '.join(REQUIRED_FIELDS)}）")
    return {k: str(it.get(k, "")) for k in ALL_FIELDS}


def build_xlsx(items, out_xlsx):
    wb = Workbook()
    ws = wb.active
    ws.title = "文献精读表"
    ncol = len(HEADERS)

    # 标题行
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=ncol)
    c = ws.cell(row=1, column=1, value="日常文献精读表（上游沉淀 · 可对接证据表）")
    c.font = Font(bold=True, size=14, color="FFFFFF")
    c.fill = PatternFill("solid", fgColor=TITLE_FILL)
    c.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 28

    # 表头
    for col, h in enumerate(HEADERS, 1):
        cell = ws.cell(row=2, column=col, value=h)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor=HDR_FILL)
        cell.border = BORDER
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(col)].width = WIDTHS[col - 1]

    # 数据（扁平表，按入库日期倒序由调用方决定；本脚本保持传入顺序）
    r = 3
    for it in items:
        vals = [ref_label(it)] + [it.get(k, "") for k in KEYS]
        for col, v in enumerate(vals, 1):
            cell = ws.cell(row=r, column=col, value=v)
            cell.border = BORDER
            cell.alignment = Alignment(vertical="top", wrap_text=True)
        r += 1

    ws.freeze_panes = "A3"   # 冻结标题与表头
    wb.save(out_xlsx)
    return len(items)


def build_md(items):
    md = ["# 日常文献精读表", "",
          "> 上游沉淀：日常精读（人工筛选 + 理解）→ 本表 →〔项目检索/主题分享〕→ 证据表。",
          "> 前 9 列对齐《文献调研流程手册》Step 1 证据表 PICO 列，对接时只需补「对本课题的意义」列 + 分区。",
          f"> 共 {len(items)} 篇 ｜ 真源：`_文献表.json`（本文件由 `build_daily_ref.py` 生成，勿直接编辑）", ""]
    md.append("| " + " | ".join(HEADERS) + " |")
    md.append("|" + "---|" * len(HEADERS))
    for it in items:
        vals = [ref_label(it)] + [it.get(k, "") for k in KEYS]
        md.append("| " + " | ".join(v.replace("\n", " ") for v in vals) + " |")
    md.append("")
    return "\n".join(md)


def main():
    ap = argparse.ArgumentParser(description="日常文献表生成器（xlsx + md）")
    ap.add_argument("--data", required=True, help="文献数据 JSON（见脚本头注释格式）")
    ap.add_argument("-o", "--outdir", required=True, help="输出目录")
    ap.add_argument("--name", default="_文献表", help="输出文件名（不含扩展名）")
    args = ap.parse_args()

    try:
        with open(args.data, encoding="utf-8") as f:
            raw = json.load(f)
        if not isinstance(raw, list):
            sys.exit("[错误] 数据 JSON 应为列表 of dict")
        items = [normalize(x, i) for i, x in enumerate(raw)]
    except ValueError as e:
        sys.exit(f"[错误] 字段校验未通过：{e}\n[提示] 修正数据 JSON 后重跑，勿生成含空关键结果的表。")

    os.makedirs(args.outdir, exist_ok=True)
    xlsx = os.path.join(args.outdir, f"{args.name}.xlsx")
    md = os.path.join(args.outdir, f"{args.name}.md")

    # xlsx 可能被 Excel 占用（Windows 常见）→ 捕获后仍生成 md，不整体失败
    n = len(items)
    try:
        n = build_xlsx(items, xlsx)
        print(f"[OK] xlsx: {xlsx}")
    except PermissionError:
        print(f"[!] xlsx 写入失败（文件被占用，通常是 Excel 正打开着）：{xlsx}")
        print(f"    → 请关闭 Excel 后重跑本命令；**md 已照常生成**。")

    with open(md, "w", encoding="utf-8") as f:
        f.write(build_md(items))
    print(f"[OK] md:   {md}")
    print(f"[OK] 共 {n} 篇文献")
    n_if = sum(1 for it in items if it.get("journal_if"))
    n_rank = sum(1 for it in items if it.get("journal_rank"))
    print(f"[i]  期刊指标填写情况：IF {n_if}/{n} · 分区 {n_rank}/{n}")


if __name__ == "__main__":
    main()
