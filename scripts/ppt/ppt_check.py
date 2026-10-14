# -*- coding: utf-8 -*-
"""
ppt_check.py —— PPT 单页 / 整册的**一键体检**

【背景】
    以前检查散在四处：手册 §3.0 版面体检、§三 视觉验证、render_and_qa_pptx 的像素体检、
    以及靠人眼逐张读 PNG。本脚本把这四处检查集中到一条命令。

【查什么】
    对 **SVG 源文件**（不需要渲染，秒级）：
      A 占位残留     —— 有 【说明】 未删
      B 画布/边距    —— 是否 1600×900、左右边距是否都 = 40
      C 越界         —— 内容超出画布或安全区
      D 调色板       —— 出现 ppt_style 里没有的颜色
      E 字号         —— font-size 不在字号表里（防手滑写成 30 而非 60）
      F 图片缩放比   —— 图为密度警告（判据 C 的可自动化部分）
      G 页脚/标题栏 —— 是否缺固定件
      J 对比度       —— 文字色 vs 背后一层纯色的对比度（借用 WCAG 阈值）

    对 **PPTX**：交给 `render_and_qa_pptx.py`（像素级），本脚本只管源。

【用法】
    python ppt_check.py <svg文件或目录> [...]
    python ppt_check.py <目录> --strict     # 有 ERROR 时退出码 1（可挂 CI）
    python ppt_check.py --contrast          # 只打印调色板配对矩阵（改配色后跑一次）
    python ppt_check.py <目录> --fix --dry-run   # 先看会改什么（推荐先跑 --fix --dry-run）
    python ppt_check.py <目录> --fix             # 降字号修文字出框（写前自动 .bak）

【产出】
    终端报告 + 可选 `--json <path>` 供其他脚本消费。
"""
import argparse
import glob
import os
import re
import sys
import json
import shutil
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ppt_style import (PX, C, G, PLACEHOLDER_TAG, PALETTE, NO_CHROME_TAG,
                       estimate_text_width)   # 估算器在真相源里，kit 与 check 共用
from ppt_kit import UNSUPPORTED_TEXT_PROPS

SVG_NS = "{http://www.w3.org/2000/svg}"

#: 允许的字号（正文派生的小号也放行）
OK_SIZES = {int(v) for v in PX.values()} | {
    int(PX["section"] * 1.2), int(PX["section"] * 0.8), int(PX["big"] * 0.6),
    int(PX["caption"] * 0.9), int(PX["caption"] * 0.8), int(PX["big"] * 2.4)}
TOL = 4          # 边距容差 px
SAFE = 8         # 安全区：内容不得进入边距以内 SAFE px 之外

# ── J 对比度 ────────────────────────────────────────────────────────────
# ⚠️ **阈值借用 WCAG 2.1（1.4.3）**：正常字号 ≥4.5:1，大字号 ≥3:1。
#    PPT 没有强制等效标准，**本脚本里是参考值不是合规判定**。
#    大字号判定同样借用 WCAG 定义：≥24pt，或 ≥18pt 且粗体。
#    本库字号以 px 计（120px/in）→ 24pt = 40px，18pt = 30px。
# ⭐ 页脚**有意低对比**（两份模板规范都以"不喧宾夺主"为目的）——
#    故 `C['foot']` 上的不达标单独列入 INFO，**不计入 WARN**，避免每页恒报。
CONTRAST_NORMAL = 4.5
CONTRAST_LARGE = 3.0
CONTRAST_BY_DESIGN = {C["foot"].upper()}


def _num(v, d=0.0):
    try:
        return float(re.sub(r"[^0-9.\-]", "", str(v)) or d)
    except Exception:
        return d


def _is_solid(el):
    """该元素是否有一层**可判定**的纯色填充。

    渐变（url(...)）、半透明、无 fill —— 一律"不可判定"，
    宁可漏报也不误报（底色是混合出来的，算不准）。
    """
    f = (el.get("fill") or "").strip()
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", f):
        return False
    for k in ("opacity", "fill-opacity"):
        v = el.get(k)
        if v is not None and _num(v, 1.0) < 0.999:
            return False
    return True


def _lum(hx):
    """WCAG 相对亮度"""
    hx = hx.lstrip("#")
    ch = []
    for i in (0, 2, 4):
        c = int(hx[i:i + 2], 16) / 255.0
        ch.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    r, g, b = ch
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(a, b):
    """WCAG 对比度（1~21）。a / b 为 '#RRGGBB'"""
    la, lb = _lum(a), _lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _min_ratio(fs, weight):
    """按字号/字重给出该处文字的对比度下限"""
    bold = _num(weight, 400) >= 600
    large = fs >= 40 or (fs >= 30 and bold)      # 24pt，或 18pt 粗体
    return CONTRAST_LARGE if large else CONTRAST_NORMAL


# ── I/J 文字溢出：判据与自动修复 ────────────────────────────────────────
#: `--fix` 允许用的字号：**只从字号表里已有的档往下试**，不凭空造字号。
#: 造一个新字号会立刻触发 E 项（字号不在表内），且破坏设计系统的一致性。
FIX_LADDER = sorted(OK_SIZES, reverse=True)

#: 缩到下限就不再缩了 —— 再小读不出来，属「不可修复」，须人工改措辞或改版式。
FIX_FLOOR = min(int(v) for v in PX.values())      # = caption 23px（图注/页脚档）

#: 允许的最大降幅（新字号 ÷ 原字号）。
#: 🔴 **40px 缩到 23px 属于重排** —— 它说明**文字本身就太长**，
#: 应当改措辞或扩大该框，不要把字缩到看不清。降幅超限一律不修、列进 refused。
FIX_MAX_DROP = 0.70


def overflow_of(t, rects, fs=None):
    """算一处文字是否出界。给了 `fs` 就按给定字号试算（供 `--fix` 试档用）。

    返回 `(kind, amount, box)`：

    | kind | 含义 | amount | box |
    |---|---|---|---|
    | `"canvas"` | 出画布 | 超出量 px | `None` |
    | `"box"` | 出容器 | 超出量 px | 容器 rect |
    | `None` | 没出界 | 0 | 容器（若有）|

    > **单一真相源**：`check_svg` 的 I 项与 `--fix` 都调它 ——
    > 否则「检出」与「修复」两套判据会各走各的，修完仍报错。
    """
    tt = dict(t) if fs is None else dict(t, fs=fs)
    tl, tr = text_bbox(tt)
    if tr > G["w"] - 1:
        return "canvas", tr - (G["w"] - 1), None
    if tl < 1:
        return "canvas", 1 - tl, None
    # 出容器：找「含住文字起点、面积最小」的 rect（最小 ≈ 最贴近文字的一层）
    cands = [r for r in rects
             if r["w"] > 20 and r["h"] > 16
             and r["x"] <= tt["x"] <= r["x"] + r["w"]
             and r["y"] - 4 <= tt["y"] <= r["y"] + r["h"] + 14]
    if not cands:
        return None, 0.0, None
    box = min(cands, key=lambda r: r["w"] * r["h"])
    band = max(tr - (box["x"] + box["w"]), box["x"] - tl)
    if band <= 1:
        return None, 0.0, box
    return "box", band, box


def box_tol(box):
    """出框容差：每边 ≤5px 忽略，或框宽的 5%"""
    return max(5, 0.05 * box["w"])


def _fits_at(t, rects, fs):
    """该文字换成 `fs` 字号后是否放得下"""
    kind, amt, box = overflow_of(t, rects, fs=fs)
    return kind is None or (kind == "box" and amt <= box_tol(box))


def fit_size(t, rects):
    """可用的**最大**字号；受 `FIX_FLOOR` 与 `FIX_MAX_DROP` 双重约束，放不下返回 `None`。

    在 `FIX_LADDER` 里**从大到小**试，第一个放得下的即最大可用档 ——
    改动幅度最小，对视觉层级影响最小。
    """
    cur = int(t["fs"])
    for fs in FIX_LADDER:
        if fs >= cur or fs < FIX_FLOOR or fs < cur * FIX_MAX_DROP:
            continue
        if _fits_at(t, rects, fs):
            return fs
    return None


def smallest_needed(t, rects):
    """**只受下限约束**时能放下的最大字号 —— 仅用于把拒绝理由说清楚。

    区分两种「修不了」：真放不下（返回 None）vs 放得下但降幅超限（返回该字号）。
    """
    for fs in FIX_LADDER:
        if fs >= int(t["fs"]) or fs < FIX_FLOOR:
            continue
        if _fits_at(t, rects, fs):
            return fs
    return None


def _bg_of(t, rects):
    """取文字背后**最近的一层纯色**。

    策略：在所有"含住文字起点"的矩形里，取**面积最小且有纯色填充**的矩形
    （面积最小 ≈ 最贴近文字的一层）。找不到可判定的就返回 None 放弃判定。
    """
    cands = [r for r in rects
             if r["w"] > 20 and r["h"] > 16
             and r["x"] <= t["x"] <= r["x"] + r["w"]
             and r["y"] - 4 <= t["y"] <= r["y"] + r["h"] + 14]
    solid = [r for r in cands if r.get("solid")]
    if solid:
        return min(solid, key=lambda r: r["w"] * r["h"])["fill"]
    if cands:                 # 只有渐变/半透明底 —— 算不准，放弃
        return None
    return C["page"]          # 直接落在页面上


def text_bbox(t):
    """按 text-anchor 算出文字的左右边界 (left, right)"""
    w = estimate_text_width(t["s"], t["fs"], t.get("weight"))
    a = t.get("anchor")
    if a == "middle":
        return t["x"] - w / 2, t["x"] + w / 2
    if a == "end":
        return t["x"] - w, t["x"]
    return t["x"], t["x"] + w


def parse(svg_path):
    """解析一个 SVG，返回元素清单"""
    root = ET.parse(svg_path).getroot()
    out = {"w": _num(root.get("width"), G["w"]), "h": _num(root.get("height"), G["h"]),
           "rects": [], "texts": [], "images": [], "colors": set(), "sizes": set(),
           "paths": 0, "lines": 0, "polygons": 0}
    for el in root.iter():
        tag = el.tag.replace(SVG_NS, "")
        if tag == "rect":
            out["rects"].append(dict(x=_num(el.get("x")), y=_num(el.get("y")),
                                     w=_num(el.get("width")), h=_num(el.get("height")),
                                     fill=el.get("fill"), solid=_is_solid(el)))
        elif tag == "text":
            # 只取直接文本；<tspan> 的内容由外层 text 的 itertext 合并
            s = "".join(el.itertext()).strip()
            out["texts"].append(dict(x=_num(el.get("x")), y=_num(el.get("y")), s=s,
                                     fs=_num(el.get("font-size"), PX["body"]),
                                     anchor=el.get("text-anchor"),
                                     weight=el.get("font-weight"),
                                     fill=el.get("fill"), solid=_is_solid(el)))
            if el.get("font-size"):
                out["sizes"].add(int(_num(el.get("font-size"))))
        elif tag == "image":
            out["images"].append(dict(href=el.get("href") or el.get("{http://www.w3.org/1999/xlink}href"),
                                      x=_num(el.get("x")), y=_num(el.get("y")),
                                      w=_num(el.get("width"), 1), h=_num(el.get("height"), 1)))
        elif tag == "path":
            out["paths"] += 1
        elif tag == "line":
            out["lines"] += 1
        elif tag == "polygon":
            out["polygons"] += 1
        for a in ("fill", "stroke"):
            v = el.get(a)
            if v and re.fullmatch(r"#[0-9A-Fa-f]{6}", v):
                out["colors"].add(v.upper())
    return out


def check_svg(path):
    """返回 (errors, warnings, info)"""
    E, Wn, I = [], [], []
    try:
        d = parse(path)
    except Exception as ex:
        return [f"解析失败：{ex}"], [], []

    name = os.path.basename(path)
    raw = open(path, encoding="utf-8").read()

    # ⭐ 无栏页（封面 / 结尾页）：不设标题栏与页脚，内容居中，
    #   故不按「页边距 = G['margin']」查它。标记由 `ppt_kit.slide(cover=True)` 写入。
    no_chrome = NO_CHROME_TAG in raw

    # A 占位残留
    # ⚠️ 必须先剥掉文件头的 HTML 注释 —— `slide()` 会在注释里写
    #    「交付前：grep "【说明】" 应清零」，注释本身会命中本检查，造成**每页恒报 1 条误警**。
    #    剥掉后本检查只数**真正的占位框**。
    body_raw = re.sub(r"<!--.*?-->", "", raw, flags=re.S)
    n_ph = body_raw.count(PLACEHOLDER_TAG)
    if n_ph:
        Wn.append(f"占位残留 {n_ph} 处（含「{PLACEHOLDER_TAG}」）—— 骨架文件正常，成品页应清零")

    # B 画布 / 边距
    if (d["w"], d["h"]) != (G["w"], G["h"]):
        E.append(f"画布 {d['w']:.0f}×{d['h']:.0f}，应为 {G['w']}×{G['h']}")
    body = [r for r in d["rects"] if not (r["x"] == 0 and r["y"] == 0 and r["w"] >= G["w"])]
    # ⚠️ 2026-09-26 修：文字边界一律走 `text_bbox`（它按 `text-anchor` 算真实左右沿）。
    #    此前用 `t["x"] + len*fs*0.6` 的裸公式 —— **忽略 text-anchor**，
    #    把右对齐（`anchor="end"`）和居中（`middle`）的文字都当成从 `x` 往右延伸，
    #    于是「贴着右边距右对齐」的页码被误报成越界。
    #    配方 30 的页码恰好卡在容差内（差 27.6 < 34）所以一直没暴露，
    #    配方 32 的字号更大（32px）就顶出了容差（38.4 > 34）—— 错在检查器，不在版式。
    xs = [r["x"] for r in body if r["w"] > 0] + [text_bbox(t)[0] for t in d["texts"] if t["s"]]
    if xs and not no_chrome:
        lo = min(xs)
        rmost = max([r["x"] + r["w"] for r in body if r["w"] > 1] +
                    [text_bbox(t)[1] for t in d["texts"] if t["s"]] or [0])
        if abs(lo - G["margin"]) > TOL:
            Wn.append(f"左边界 {lo:.0f}，距期望 {G['margin']} 差 {lo-G['margin']:+.0f}px")
        if abs((G["w"] - rmost) - G["margin"]) > TOL + 30:
            Wn.append(f"右边界约 {rmost:.0f}，右边距 {G['w']-rmost:.0f}px（期望 {G['margin']}±）")

    # C 越界
    for r in d["rects"]:
        if r["w"] <= 0 or r["h"] <= 0:
            continue
        if r["x"] < -1 or r["y"] < -1 or r["x"] + r["w"] > G["w"] + 1 or r["y"] + r["h"] > G["h"] + 1:
            if not (r["x"] == 0 and r["w"] >= G["w"]):     # 全宽色带是故意的
                E.append(f"元素越出画布：x={r['x']:.0f} y={r['y']:.0f} w={r['w']:.0f} h={r['h']:.0f}")
    for t in d["texts"]:
        if t["y"] > G["h"]:
            E.append(f"文字 y={t['y']:.0f} 超出画布：{t['s'][:20]}")

    # D 调色板
    bad_c = sorted(d["colors"] - {v.upper() for v in PALETTE})
    if bad_c:
        Wn.append(f"越色 {len(bad_c)} 种：{', '.join(bad_c[:6])}"
                  f"{' …' if len(bad_c) > 6 else ''}（不在 ppt_style.PALETTE 内）")

    # E 字号
    bad_s = sorted(s for s in d["sizes"] if s not in OK_SIZES)
    if bad_s:
        Wn.append(f"字号不在表内：{bad_s}（表={sorted(OK_SIZES)}）")

    # F 图片缩放比（判据 C 的可自动化部分）
    for im in d["images"]:
        hp = im["href"] or ""
        if hp.startswith("file:///"):
            hp = hp[8:]
        hp = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(path)),
                                           hp.replace("/", os.sep)))
        if not os.path.exists(hp):
            E.append(f"图片缺失：{os.path.basename(hp)}")
            continue
        try:
            from PIL import Image
            with Image.open(hp) as pim:
                nat = pim.width
        except Exception:
            Wn.append(f"图片打不开：{os.path.basename(hp)}")
            continue
        ratio = im["w"] / nat if nat else 0
        if ratio < 0.5:
            Wn.append(f"图「{os.path.basename(hp)}」缩放比 {ratio:.2f}"
                      f"（{nat}→{im['w']:.0f}px）—— 图内字若原为 18px，幻灯上仅 {18*ratio:.1f}px，需人工核判据 C")
        else:
            I.append(f"图 {os.path.basename(hp)} 缩放比 {ratio:.2f}")

    # I 文字溢出（估算宽度 + 容器包含）—— 最常见的真实缺陷
    #    阈值取自 `shared-standards-core.md:584-627`：每边 ≤1px 忽略，>5% 判失败
    #    判据本身在 `overflow_of()` —— `--fix` 共用同一份，防「检出/修复」两套标准
    for t in d["texts"]:
        if not t["s"]:
            continue
        kind, amt, box = overflow_of(t, d["rects"])
        if kind == "canvas":
            E.append(f"文字超出画布：{t['s'][:24]!r} 超出 {amt:.0f}px（画布 {G['w']}）")
            continue
        if kind == "box":
            tol = box_tol(box)
            msg = (f"文字可能出框：{t['s'][:24]!r} 超出 {amt:.0f}px"
                   f"（框宽 {box['w']:.0f}，容差 {tol:.0f}）")
            (E if amt > tol else Wn).append(msg)

    # H 导出兼容性 —— ⚠️ 用了不支持的属性，**一页失败整册导不出**
    for prop in sorted(UNSUPPORTED_TEXT_PROPS):
        if re.search(rf'[:"\s]{re.escape(prop)}\s*[:=]', raw):
            E.append(f"用了导出器不支持的属性 `{prop}` —— "
                     f"转 PPTX 时会抛 SvgNativeConversionError 且**整册失败**。"
                     f"竖排请改用 `ppt_kit.vtext()`")

    # J 对比度（借用 WCAG 阈值，见文件头常量注释）
    #    实测背景：`weak #7A8698` 在白底仅 3.69:1，而它的用途正是**图注/导语**这类小字。
    #    ⚠️ 跳过占位文字 —— 【说明】交付前会删掉，报它等于噪声（占位由 A 项单独管）。
    #    ⚠️ 同一页按 (文字色, 底色, 字号) 去重后只报一条 —— 否则一页能刷出十几条同样的。
    seen_j = {}
    for t in d["texts"]:
        if not t["s"] or not t.get("solid") or PLACEHOLDER_TAG in t["s"]:
            continue
        bg = _bg_of(t, d["rects"])
        if bg is None:
            continue
        r = contrast_ratio(t["fill"], bg)
        need = _min_ratio(t["fs"], t.get("weight"))
        if r >= need:
            continue
        key = (t["fill"].upper(), bg.upper(), int(t["fs"]), need)
        if key in seen_j:
            seen_j[key]["n"] += 1
            continue
        seen_j[key] = dict(n=1, r=r, sample=t["s"][:16])
    for (fg, bg, fs, need), v in seen_j.items():
        n = v["n"]
        msg = (f"对比度 {v['r']:.2f}:1 < {need}:1 —— {fg} on {bg}，"
               f"{fs}px ×{n} 处，如「{v['sample']}」")
        if fg in CONTRAST_BY_DESIGN:
            I.append(msg + "（页脚，有意低对比，参考项）")
        else:
            Wn.append(msg)

    # G 固定件（无栏页豁免）
    if not no_chrome:
        has_bar = any(r["y"] <= 2 and r["w"] >= G["w"] and 40 <= r["h"] <= 120 for r in d["rects"])
        if not has_bar:
            Wn.append("未见顶部标题栏（全宽色带）—— 若是有意为之（双横线版）请忽略")
        if not any(820 <= t["y"] <= 890 for t in d["texts"]):
            Wn.append("未见页脚文字")
    return E, Wn, I


# ══════════════════════════════════════════════════════════
#  --docs：跨文档口径核对（防"改一处漏一处"）
# ══════════════════════════════════════════════════════════
#: 仓库根 = `科研/`（本文件在 科研/_系统/_流程与工具/_scripts/，向上三层）
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", ".."))

#: (文件, 正则, 期望值的来源键, 人类可读名)
#: 每项 = (文档相对路径, 抓数字的正则, 事实键, 显示名)
#
# ⚠️ **本表只登记「应当写出数字」的位置。**
# 若某文档已刻意改为「指向单一出处、不复述数字」（见 全流程总纲 §「改一处漏一处」的诊断），
# 就**不该**在本表登记——否则会恒报「写 None」。
# 2026-09-22 清理：删除 3 条此类过期登记
#   · 全流程总纲「脚本数」「配方数」——该文已改为指向 `_scripts/README.md`
#   · 科研工作总览「脚本数」——该行已改为「总数见 `_scripts/README.md`」
DOC_CLAIMS = [
    (r"_系统\_流程与工具\_scripts\README.md", r"脚本清单（(\d+) 个）", "scripts", "脚本数"),
    # ⚠️ README **在两处写了脚本数**（§一 标题 + 页脚）。
    #    `check_assets` 只读页脚处，本脚本原先只读标题处 ——
    #    2026-09-26 因此出现「一个说 25、一个说 26，谁都没发现两处打架」。
    #    两处都登记，才能各自对得上。
    (r"_系统\_流程与工具\_scripts\README.md", r"脚本 \*\*(\d+) 个\*\*", "scripts", "脚本数·页脚"),
    (r"_系统\科研工作总览.md", r"\*\*(\d+) 个\*\*可套用配方", "recipes", "配方数"),
    (r"_系统\_流程与工具\PPT视觉规范_国自然风格_20260915.md", r"\*\*(\d+) 个\*\*具体版式", "recipes", "配方数"),
    (r"_系统\科研工作总览.md", r"\*\*(\d+) 个整页 SVG 骨架\*\*", "skeletons", "骨架数"),
    (r"_系统\_流程与工具\PPT工具链速查_20260915.md", r"\*\*(\d+) 个\*\*整页 SVG", "skeletons", "骨架数"),
    # ── 2026-09-26 补登：以下 4 处此前**只靠人工同步**，加配方 32 时全部需要手改。
    #    「人工同步的落点」= 下次必然漏的落点 —— 一并纳入机器核对。
    (r"_系统\_流程与工具\PPT工具链速查_20260915.md", r"\*\*(\d+) 个\*\*版式配方", "recipes", "配方数·速查"),
    (r"_系统\_流程与工具\PPT工具链手册.md", r"\*\*(\d+) 个版式配方\*\*", "recipes", "配方数·手册"),
    (r"_系统\_流程与工具\PPT工具链手册.md", r"\*\*(\d+) 个骨架（可复制）\*\*", "skeletons", "骨架数·手册"),
    (r"_系统\_流程与工具\_scripts\README.md", r"生成 (\d+) 个整页版式骨架", "skeletons", "骨架数·脚本README"),
    # ── 再补 3 处：加配方 32 时靠 grep 才找出来的"顺手提到骨架数"的地方。
    #    这类「顺带一提的数字」最容易漏 —— 登记进来，下次自动报。
    #    （dated 快照如《诊断_画面单调_20260922》《迁移检查_20260924》**刻意不登记**：
    #      它们记的是当时的实况，改了反而失真。）
    (r"_系统\_流程与工具\汇报PPT产出流程手册.md", r"（(\d+) 个整页骨架，复制即用", "skeletons", "骨架数·产出流程"),
    (r"_系统\_流程与工具\Token消耗估算_20260919.md", r"（(\d+) 个整页骨架，复制即用", "skeletons", "骨架数·Token估算"),
    (r"_系统\_流程与工具\核查方法\04_演讲产物审查协议.md", r"PPT版式配方库\s+(\d+) 个整页骨架", "skeletons", "骨架数·审查协议"),
]


def count_facts():
    """实测当前数量（唯一真相）"""
    S = os.path.join(ROOT, "_系统", "_流程与工具")
    # ⚠️ 用通配而不是写死日期后缀 —— 目录改名（PPT骨架模板_YYYYMMDD）不该把检查弄断
    n_svg = 0
    for d in glob.glob(os.path.join(S, "PPT骨架模板*")):
        n_svg += len([f for f in glob.glob(os.path.join(d, "*.svg"))])
    libs = sorted(glob.glob(os.path.join(S, "PPT版式配方库*.md")))
    n_rec = len(re.findall(r"^### 配方 (\d+)｜", open(libs[-1], encoding="utf-8").read(), re.M)) \
        if libs else 0
    n_scr = len([f for f in glob.glob(os.path.join(S, "_scripts", "*.py"))
                 if not os.path.basename(f).startswith("_")])
    return {"scripts": n_scr, "recipes": n_rec, "skeletons": n_svg}


def check_docs():
    facts = count_facts()
    print("═══ 跨文档口径核对 ═══\n")
    print("  实测：" + " ｜ ".join(f"{k} {v}" for k, v in facts.items()) + "\n")
    bad = 0
    for rel, pat, key, label in DOC_CLAIMS:
        p = os.path.join(ROOT, rel.replace("\\", os.sep))
        if not os.path.exists(p):
            print(f"  ⚠️  缺文件 {rel}"); bad += 1; continue
        m = re.search(pat, open(p, encoding="utf-8").read())
        got = int(m.group(1)) if m else None
        want = facts[key]
        ok = got == want
        if not ok:
            bad += 1
        print(f"  {'✅' if ok else '❌'} {label:<5} {os.path.basename(rel):<34} "
              f"写 {got}，应为 {want}")
    print(f"\n{'✅ 全库口径一致' if not bad else f'❌ {bad} 处不一致'}")
    return bad


def print_contrast_matrix():
    """调色板配对矩阵 —— **改配色后跑一次**。

    做成调色板级而非逐页的理由：调色板只有 10 色，配对有限，一次算清即可覆盖；
    逐页要解析每处文字背后的真实底色（渐变/半透明/图片都要处理），成本高、收益低。
    逐页部分由 `check_svg` 的 J 项负责。
    """
    T = ["txt", "main", "red", "weak", "foot"]
    B = ["page", "tint", "gray", "main"]
    print("═══ 调色板对比度矩阵 ═══")
    print("（阈值借用 WCAG 2.1：正常字 ≥4.5:1 ｜ 大字 ≥3:1 —— PPT 无强制等效标准，此处为参考）\n")
    print("text \\ bg".ljust(12) + "".join(b.ljust(12) for b in B))
    print("-" * (12 + 12 * len(B)))
    for t in T:
        row = t.ljust(12)
        for b in B:
            if t == b:
                row += "--".ljust(12)
                continue
            r = contrast_ratio(C[t], C[b])
            mark = "OK" if r >= CONTRAST_NORMAL else ("big" if r >= CONTRAST_LARGE else "LOW")
            row += f"{r:.2f} {mark}".ljust(12)
        print(row)
    print()
    for k in T + B:
        print(f"  {k:<6} {C[k]}")
    print("\nOK：≥4.5 ｜ big：3.0–4.5（仅够 24pt+ 或 18pt 粗体）｜ LOW：<3.0")
    print("⚠️ foot 是页脚色，低对比**有意为之**（不喧宾夺主）—— 投屏前建议人工确认")
    print("⚠️ weak 用于图注/导语，属小字，**应当 ≥4.5**")


# ══════════════════════════════════════════════════════════
#  --fix：文字出框的自动修复
# ══════════════════════════════════════════════════════════
def _text_tag_starts(raw):
    """raw 中每个顶层 `<text` 的起始下标（跳过 HTML 注释里的）。

    用途：`parse()` 按文档顺序给文字编号，写回时要找到**同一个**元素。
    直接对 raw 正则会把注释里的文字也算进来，故先把注释抹成**等长空格**再匹配
    —— 长度不变，得到的位置可直接用在原 raw 上。
    """
    masked = re.sub(r"<!--.*?-->", lambda m: " " * len(m.group(0)), raw, flags=re.S)
    return [m.start() for m in re.finditer(r"<text\b", masked)]


def fix_file(path, dry=False):
    """降字号修复文字出框。返回 `(changes, refused)`。

    🔴 **只做「降字号」这一种修复，不做扩框。**
    扩框会与邻元素撞车 —— 而本脚本**看不到版式意图**（哪根线必须对齐、
    哪个卡片和谁等宽）。改一个自己看不出后果的几何，比不修更危险。
    缩到下限仍放不下的，列进 `refused`，**交人工**改措辞或版式。
    """
    d = parse(path)
    raw = open(path, encoding="utf-8").read()
    starts = _text_tag_starts(raw)
    if len(starts) != len(d["texts"]):
        return [], [f"文字元素计数对不上（正则 {len(starts)} vs 解析 {len(d['texts'])}）"
                    f" —— 放弃修复：宁可不动，也不能改错位置"]
    changes, refused = [], []
    for i, t in enumerate(d["texts"]):
        if not t["s"]:
            continue
        kind, amt, box = overflow_of(t, d["rects"])
        if kind is None:
            continue
        if kind == "box" and amt <= box_tol(box):
            continue                                   # 容差内，不算问题
        new = fit_size(t, d["rects"])
        if new is None:
            # 分两种「修不了」，好让拒绝理由可操作
            need = smallest_needed(t, d["rects"])
            if need is None:
                why = f"缩到下限 {FIX_FLOOR}px 仍放不下 → 请改措辞或改版式"
            else:
                drop = 1 - need / int(t["fs"])
                why = (f"需缩到 {need}px 才放得下（降幅 {drop:.0%} > 上限 {1-FIX_MAX_DROP:.0%}）"
                       f" → 请改措辞或扩大该框，不要靠缩字")
            refused.append(f"{int(t['fs'])}px「{t['s'][:24]}」超出 {amt:.0f}px —— {why}")
            continue
        changes.append(dict(i=i, s=t["s"], old=int(t["fs"]), new=new, amt=amt))
    if dry or not changes:
        return changes, refused
    out = raw
    for c in reversed(changes):                        # ⚠️ 倒序改，否则前面的下标会错位
        s = starts[c["i"]]
        gt = out.index(">", s)                         # 开标签的结束位置
        head = out[s:gt]
        newhead = re.sub(r'font-size="[^"]*"', f'font-size="{c["new"]}"', head, count=1)
        if newhead == head:                            # 原本没写 font-size（走默认 body）
            newhead = head + f' font-size="{c["new"]}"'
        out = out[:s] + newhead + out[gt:]
    shutil.copy2(path, path + ".bak_autofit")
    open(path, "w", encoding="utf-8").write(out)
    return changes, refused


def run_fix(files, dry):
    """批量修复 + **复检**。复检变差就自动回滚 —— 改了必须自己证明改好了。

    返回**仍需人工处理**的处数（refused + 被回滚的），供 `--strict` 判退出码。
    """
    print(f"═══ PPT 文字出框修复（{'试算，不写文件' if dry else '降字号'}）："
          f"{len(files)} 个文件 ═══\n")
    tot_fixed = tot_left = tot_roll = 0
    for f in files:
        before = check_svg(f)
        n_before = len(before[0]) + len(before[1])
        changes, refused = fix_file(f, dry=dry)
        if not changes and not refused:
            print(f"  ✅ {os.path.basename(f)}  无需修复")
            continue
        print(f"  {os.path.basename(f)}")
        for c in changes:
            print(f"       {'拟改' if dry else '✏️ '} {c['old']}px → {c['new']}px  "
                  f"「{c['s'][:28]}」（原超出 {c['amt']:.0f}px）")
        for r in refused:
            print(f"       ⚠️  留人工：{r}")
        tot_left += len(refused)
        if changes and not dry:
            after = check_svg(f)
            n_after = len(after[0]) + len(after[1])
            if n_after > n_before:                     # 🔴 改坏了 → 自动回滚
                shutil.copy2(f + ".bak_autofit", f)
                os.remove(f + ".bak_autofit")
                tot_roll += len(changes)
                tot_left += len(changes)               # 没修成 = 仍需人工
                print(f"       🔴 复检变差（{n_before} → {n_after}）→ **已自动回滚**，文件未改动")
            else:
                tot_fixed += len(changes)
                print(f"       🔍 复检：ERROR {len(before[0])}→{len(after[0])} ｜ "
                      f"WARN {len(before[1])}→{len(after[1])}")
        elif changes:
            tot_fixed += len(changes)                  # dry-run：只是"能修"
    print(f"\n═══ 合计：{'可修' if dry else '修复'} {tot_fixed} 处 ｜ 留人工 {tot_left} 处"
          + (f" ｜ 自动回滚 {tot_roll} 处" if tot_roll else "") + " ═══")
    if not dry and tot_fixed:
        print("  备份后缀 `.bak_autofit`（确认无误后可删；回滚过的不会留 bak）")
    return tot_left


def main():
    ap = argparse.ArgumentParser(description="PPT 单页/整册体检（查 SVG 源）")
    ap.add_argument("--docs", action="store_true",
                    help="只做跨文档口径核对（脚本数/配方数/骨架数），不需要传路径")
    ap.add_argument("--contrast", action="store_true",
                    help="只打印调色板配对对比度矩阵（改配色后跑一次）")
    ap.add_argument("paths", nargs="*", help="SVG 文件或目录")
    ap.add_argument("--strict", action="store_true", help="有 ERROR 时退出码 1")
    ap.add_argument("--json", help="把结果写成 JSON")
    ap.add_argument("--fix", action="store_true",
                    help="自动修复文字出框（只降字号，且落在字号表内；写前自动 .bak）")
    ap.add_argument("--dry-run", action="store_true", help="与 --fix 同用：只报告，不改文件")
    a = ap.parse_args()

    if a.contrast:
        print_contrast_matrix()
        return 0
    if a.docs:
        n = check_docs()
        return 1 if (a.strict and n) else 0
    if not a.paths:
        ap.error("需要给出 SVG 路径，或用 --docs 做跨文档核对")

    files = []
    for p in a.paths:
        files += sorted(glob.glob(os.path.join(p, "*.svg"))) if os.path.isdir(p) else [p]
    if not files:
        print("❌ 没找到 SVG"); return 1

    if a.fix:
        n_left = run_fix(files, a.dry_run)
        return 1 if (a.strict and n_left) else 0

    allres, ne, nw = {}, 0, 0
    print(f"═══ PPT 体检：{len(files)} 个文件 ═══\n")
    for f in files:
        E, Wn, I = check_svg(f)
        try:
            key = os.path.relpath(f)
        except ValueError:          # 跨盘符（cwd 在 C:，文件在 D:）
            key = f
        allres[key] = dict(errors=E, warnings=Wn, info=I)
        ne += len(E); nw += len(Wn)
        if not E and not Wn:
            print(f"  ✅ {os.path.basename(f)}")
            continue
        print(f"  {'❌' if E else '⚠️ '} {os.path.basename(f)}")
        for x in E:  print(f"       ERROR  {x}")
        for x in Wn: print(f"       WARN   {x}")
    print(f"\n═══ 合计：ERROR {ne} ｜ WARN {nw} ═══")
    # ℹ️ 参考项按「消息去重 + 计数」汇总 —— 页脚对比度这类会在每页各报一条，
    #    逐页打印会刷屏；汇总成一行才能看出"是普遍现象还是个例"。
    notes = {}
    for r in allres.values():
        for x in r["info"]:
            notes[x] = notes.get(x, 0) + 1
    if notes:
        print(f"\n  ℹ️ 参考项 {sum(notes.values())} 条 / {len(notes)} 类（不计入 WARN）：")
        for x, n in sorted(notes.items(), key=lambda kv: -kv[1]):
            print(f"     ×{n:<4}{x}")
    if a.json:
        json.dump(allres, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"  → {a.json}")
    return 1 if (a.strict and ne) else 0


if __name__ == "__main__":
    sys.exit(main())
