# -*- coding: utf-8 -*-
"""check_data.py —— 数据与统计分析流程的口径机检（E1–E4）

【为什么有它】
    `data-pipeline` 的核心是**可追溯**——方案里说好这么算，实际那么算了，
    有没有留下痕迹。其中最贵的一条是 **SAP 偏离**：
    **偏离本身不致命，不记录才致命**（审稿人必问「与注册方案不一致」）。

    这类「该有的在不在、该填的填没填」是纯格式，可以机查。

【⚠️ 从 check_vault 搬过来的两条】
    原先「变量字典必填列」与「SAP 偏离记录列」挂在 `check_vault.py` 名下，
    但 check_vault 管的是**科研库命名与结构**——那是**数据管线的家**，不是它的。
    借着这次建 data-pipeline 归位：**一条规则一个家**。

【查什么（按文件名触发）】
    D1 变量字典七列       字段名/含义/类型/取值域/缺失码/来源/对应假设
    D2 缺失码四类         ⭐ 未评 / 不适用 / 失访 / 拒答——**合并会毁掉缺失分析**
    D3 SAP 偏离七列       假设编号/原定/实际/一致/原因/何时决定/批准
                          ⚠️ 是**七**列，别漏「何时决定」——「谁批准」与「什么时候定的」
                          是两件事：事后补记的偏离与当场记录的偏离，可信度不同
    D4 偏离逐条填全       ⭐ 标了「偏离」的行，**原因与批准人不得为空**
    D5 结果报告           ⭐ 有 p 值却**没有 95%CI** = 只报显著性不报大小

    ⚠️ **按文件名触发，不按正文出现某词触发**——否则讲这些事的文档会被判成它本身
    （库里《数据与统计分析流程》手册就会中招）。

【它不查什么】
    该用哪个检验、这条偏离合不合理——语义，人工过。

用法：
    python check_data.py <文件或目录>

退出码 = 硬命中条数（0 = 全过）
"""
import argparse
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VARDICT_COLS = ["字段名", "含义", "类型", "取值域", "缺失码", "来源", "对应假设"]
MISSING_TYPES = ["未评", "不适用", "失访", "拒答"]
SAP_COLS = ["假设编号", "原定", "实际", "一致", "原因", "何时决定", "批准"]
DEVIATED = re.compile(r"偏离|⚠️|不一致|\bDEV\b", re.I)
P_VALUE = re.compile(r"\bp\s*[=<>≤≥]\s*0?\.\d+|\bP\s*值", re.I)
CI_VALUE = re.compile(r"95\s*%\s*CI|95%CI|置信区间|\bCI\s*[:：]|\[\s*-?[\d.]+\s*,\s*-?[\d.]+\s*\]")


def table_rows(text):
    """抽出 markdown 表格的数据行（跳过表头与分隔行）。"""
    rows = []
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if not cells or all(set(c) <= set("-: ") for c in cells):
            continue          # 分隔行 |---|---|
        rows.append(cells)
    return rows


def d1_vardict(text, p):
    """变量字典七列（数据与统计分析流程 §环节1）"""
    if "变量字典" not in p.name:
        return []
    miss = [c for c in VARDICT_COLS if c not in text]
    return [f"{p.name}：变量字典缺列 {'/'.join(miss)}"] if miss else []


def d2_missing_types(text, p):
    """缺失码必须分四类——合并会毁掉后面所有的缺失分析。"""
    if "变量字典" not in p.name:
        return []
    miss = [c for c in MISSING_TYPES if c not in text]
    if not miss:
        return []
    return [f"{p.name}：缺失码缺 {'/'.join(miss)}——"
            f"四类缺失（未评/不适用/失访/拒答）合并会毁掉缺失分析；"
            f"尤其「不适用」不是缺失，是逻辑上不存在"]


def d3_sap_cols(text, p):
    """SAP 偏离记录七列（数据与统计分析流程 §环节4）"""
    if "SAP" not in p.name:
        return []
    miss = [c for c in SAP_COLS if c not in text]
    return [f"{p.name}：SAP 偏离记录缺列 {'/'.join(miss)}"] if miss else []


def d4_deviation_filled(text, p):
    """⭐ 标了「偏离」的行，原因与批准人不得为空。

    这是本流程最贵的一条纪律：**偏离本身不致命，不记录才致命**。
    """
    if "SAP" not in p.name:
        return []
    hits = []
    for cells in table_rows(text):
        row = " ".join(cells)
        if not DEVIATED.search(row):
            continue
        # 该行里空着的单元格（✏️ 允许「—」「/」「无」这类占位）
        empty = [c for c in cells if c in ("", "-", "—", "/", "无", "N/A", "NA")]
        if empty:
            hits.append(f"{p.name}：有一行标了「偏离」，但有 {len(empty)} 个单元格为空——"
                        f"**偏离必须写清原因 / 何时决定 / 谁批准**（行：{row[:40]}…）")
    return hits[:3]      # 同样的毛病不刷屏


def d5_reporting(text, p):
    """结果报告：有 p 值却没有 95%CI。"""
    if "结果报告" not in p.name:
        return []
    if P_VALUE.search(text) and not CI_VALUE.search(text):
        return [f"{p.name}：报了 p 值却**没有任何 95%CI**——"
                f"p 说「可能不是偶然」，效应量说「有多大」；临床决策看的是后者"]
    return []


RULES = [d1_vardict, d2_missing_types, d3_sap_cols, d4_deviation_filled, d5_reporting]


def main():
    ap = argparse.ArgumentParser(description="数据与统计分析流程口径机检")
    ap.add_argument("path")
    a = ap.parse_args()

    root = pathlib.Path(a.path)
    files = [root] if root.is_file() else sorted(root.rglob("*.md"))

    hits, nfile, evaluated = [], 0, 0
    for p in files:
        if not p.is_file():
            continue
        nfile += 1
        text = p.read_text(encoding="utf-8", errors="replace")
        for fn in RULES:
            got = fn(text, p)
            if got:
                evaluated += 1
            hits += got

    print(f"check_data · {a.path} · 扫 {nfile} 个文件")
    if not hits:
        if evaluated == 0:
            print("  ⚠️ 本次未评——目录里没有「变量字典 / SAP / 结果报告」类文件。"
                  "这不是查过了通过。")
        else:
            print("  ✅ 已评的文件全过")
        return 0
    for h in hits:
        print(f"  ❌ {h}")
    print(f"\n  共 {len(hits)} 处。⚠️ 只查格式与留痕，不查统计方法对不对。")
    return len(hits)


if __name__ == "__main__":
    raise SystemExit(main())
