# -*- coding: utf-8 -*-
"""check_lit.py —— 文献调研里「可判定」规则的机检

【为什么有它】
    覆盖声明（N→M→K）、证据表列级口径、对照列 NA、IF/分区带年份版本——
    这些全是**格式与存在性**，不需要判断，却一直只写在 SKILL.md 里，每轮靠模型重读。

【它不查什么（重要）】
    「这条证据真的支持这句话吗」「这篇文值不值得用」「这个空白是不是真的」——一律不碰。
    本脚本只查**长得对不对**，不查**说得对不对**。

用法：
    python check_lit.py --evtab 证据表_思路A.md
    python check_lit.py --coverage 调研报告.md

退出码 = 失败项数（0 = 全过）
"""
import argparse
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── 证据表：12 列（10 PICO + 2 期刊指标 + 1 意义列）——
#    来自真实产物 `证据表_思路A.md`，不是自创
HDR_HEAD = "文献"
HDR_TAIL = "对本课题的意义"
N_COLS = 12
COL_CTRL = "对照"          # 空 → 必须 NA
COL_IF = "期刊 IF"
COL_ZONE = "期刊分区"
COL_RESULT = "关键结果"

# 对照列允许的「无对照」写法
NA_OK = re.compile(r"^\**\s*(NA|N/?A|不适用|无)\s*\**$", re.I)
# IF 口径：`7.9 (2024 JCR)` / `4.1 **(2024 JCR)**`
IF_OK = re.compile(r"\d[\d.]*\s*\(?\s*\d{4}\s*JCR", re.I)
# 分区口径：`中科院医学1区(2025)` / `中科院医学2区(升级版2025)`
ZONE_OK = re.compile(r"中科院[^|/]*?区\s*[（(]\s*[^）)]*?\d{4}")
ZONE_BARE = re.compile(r"中科院[^|/]*?区(?!\s*[（(])")
# 关键结果里应有可核的量：效应量 / CI / p
RESULT_OK = re.compile(r"\d", re.S)

# ── 覆盖声明：三个数（N 可识别位置 → M 实际核查 → K 未覆盖）
COV_N = re.compile(r"(?:可识别位置|位置总数|总计|共)\D{0,6}(\d+)")
COV_M = re.compile(r"(?:实际核查|已核查|已核|核实)\D{0,6}(\d+)")
COV_K = re.compile(r"(?:未能覆盖|未覆盖|未核查|覆盖缺口)\D{0,6}(\d+)")


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse_tables(text):
    """返回 [(分区标题, 表头, [数据行…])]"""
    out, cur_title, tbl = [], None, None
    for raw in text.splitlines():
        if raw.startswith("## "):
            cur_title = raw[3:].strip()
        if raw.lstrip().startswith("|"):
            c = cells(raw)
            if set("".join(c)) <= set("-: "):       # 分隔行
                continue
            if tbl is None:
                tbl = []
            tbl.append(c)
        else:
            if tbl:
                out.append((cur_title, tbl[0], tbl[1:]))
                tbl = None
    if tbl:
        out.append((cur_title, tbl[0], tbl[1:]))
    return out


def check_evtab(text):
    """返回 (硬失败, 软提示, 数据行数)。

    ⚠️ 软硬之分是必须的：E6（关键结果里有没有数）**不是硬规则**——
    机制类文献本来就可能没有效应量。软项只提示，不算进退出码。
    """
    fails, soft, tables, n_rows = [], [], parse_tables(text), 0

    good = [(t, h, rows) for t, h, rows in tables
            if len(h) == N_COLS and h[0].startswith(HDR_HEAD)]
    if not good:
        fails.append(f"E1 找不到 12 列证据表（表头须以「{HDR_HEAD}」开头、共 {N_COLS} 列）")
        return fails, soft, 0

    bad_cols, bad_ctrl, bad_dup, bad_if, bad_zone, bad_result = [], [], [], [], [], []
    authors = {}
    for title, h, rows in good:
        if len(h) != N_COLS:
            bad_cols.append(f"{title}：{len(h)} 列")
        idx = {name: i for i, name in enumerate(h)}
        for r in rows:
            if len(r) != N_COLS:
                continue
            n_rows += 1
            tag = f"{title}·{r[idx.get('作者·年份', 1)]}"
            # E2 对照列
            c = r[idx.get(COL_CTRL, 5)]
            if c == "":
                bad_ctrl.append(tag)
            # E4/E5 期刊口径
            if idx.get(COL_IF) is not None:
                v = r[idx[COL_IF]]
                if v and not IF_OK.search(v):
                    bad_if.append(f"{tag}={v[:20]}")
            if idx.get(COL_ZONE) is not None:
                v = r[idx[COL_ZONE]]
                if v and ZONE_BARE.search(v) and not ZONE_OK.search(v):
                    bad_zone.append(f"{tag}={v[:24]}")
            # E6 关键结果非空且有数
            if idx.get(COL_RESULT) is not None:
                v = r[idx[COL_RESULT]]
                if v and not RESULT_OK.search(v):
                    bad_result.append(tag)
            # E3 同作者同年 → a/b
            key = r[idx.get("作者·年份", 1)]
            base = re.sub(r"\s*[ab]$", "", key)
            if base in authors and key == base:
                bad_dup.append(f"{tag} 与上一条同作者同年，需 a/b 后缀")
            authors[base] = True

    if bad_cols:
        fails.append("E1 列数不对：" + "；".join(bad_cols[:6]))
    if bad_ctrl:
        fails.append(f"E2 对照列为空（应填 NA）：{len(bad_ctrl)} 处 → " + "；".join(bad_ctrl[:6]))
    if bad_dup:
        fails.append("E3 同作者同年未加 a/b：" + "；".join(bad_dup[:6]))
    if bad_if:
        fails.append("E4 IF 未带年份口径（须 `数值 (YYYY JCR)`）：" + "；".join(bad_if[:6]))
    if bad_zone:
        fails.append("E5 分区未带版本年份（须 `中科院…N区(YYYY)`）：" + "；".join(bad_zone[:6]))
    if bad_result:
        soft.append(f"E6 关键结果里没有数字（机制类可豁免，定量研究须补效应量/CI/p）："
                    + "；".join(bad_result[:8]))
    if not any(re.match(r"^[A-Z]\d", (t or "")) for t, _, _ in good):
        fails.append("E7 缺分区标题（应为 `## A0 …` 这类）")
    return fails, soft, n_rows


def check_coverage(text):
    fails = []
    n, m, k = COV_N.search(text), COV_M.search(text), COV_K.search(text)
    miss = [name for name, hit in (("N 可识别位置总数", n), ("M 实际核查", m), ("K 未能覆盖", k))
            if not hit]
    if miss:
        fails.append("C1 覆盖声明不完整，缺：" + "、".join(miss) +
                     "（格式：`N → M → K`，只报「已检查」等于假装覆盖完整）")
    elif int(m.group(1)) + int(k.group(1)) != int(n.group(1)):
        fails.append(f"C2 三个数对不上：N={n.group(1)} ≠ M={m.group(1)} + K={k.group(1)}")
    # K 每条要带原因（⚠️ 用 splitlines 取后续行——正则里要求每行以 \n 结尾的话，
    #   末行没有换行符就漏掉，会把「写了原因」误判成「没写」）
    m = re.search(r"(?:未能覆盖|未覆盖|覆盖缺口)[^\n]*", text)
    if m and k and int(k.group(1)) > 0:
        body = "\n".join(text[m.end():].splitlines()[:20])
        if not re.search(r"因|理由|原因|付费墙|未读|超时|语言", body):
            fails.append("C3 未覆盖项没写原因（K 必须逐条给原因）")
    return fails


def main():
    ap = argparse.ArgumentParser(description="文献调研可判定规则机检")
    ap.add_argument("--evtab", help="证据表 markdown")
    ap.add_argument("--coverage", help="含覆盖声明的报告 markdown")
    a = ap.parse_args()
    if not (a.evtab or a.coverage):
        ap.error("至少给 --evtab 或 --coverage")

    total = 0
    if a.evtab:
        text = open(a.evtab, encoding="utf-8", errors="replace").read()
        fails, soft, n = check_evtab(text)
        print(f"check_lit · evtab · {a.evtab} · {n} 条")
        for f in fails:
            print(f"  ❌ {f}")
        for s in soft:
            print(f"  ⚠️ {s}")
        if not fails and not soft:
            print("  ✅ 全过（E 类规则）")
        elif not fails:
            print("  ✅ 硬规则全过（上方为软提示，可不改）")
        total += len(fails)
    if a.coverage:
        text = open(a.coverage, encoding="utf-8", errors="replace").read()
        fails = check_coverage(text)
        print(f"check_lit · coverage · {a.coverage}")
        for f in fails:
            print(f"  ❌ {f}")
        if not fails:
            print("  ✅ 全过（C 类规则）")
        total += len(fails)
    if total:
        print(f"\n  共 {total} 项未过。⚠️ 命中 ≠ 要改——判断仍在你。")
    return total


if __name__ == "__main__":
    raise SystemExit(main())
