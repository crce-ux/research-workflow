# -*- coding: utf-8 -*-
"""
ppt_style.py —— PPT 制作工具链的**单一真相源**

【背景】
    在此之前，配色 / 字号 / 边距在三处各写了一遍：
      · `PPT视觉规范_国自然风格_20260915.md`（文档）
      · 生成脚本（代码）
      · 目录索引 README
    结果是"改一处漏一处"——实测已发生：规范写「页面标题 30–32」，
    做 P05 时当 px 用了，比模板小一半。

    **本文件是唯一的数字来源。** 其他脚本 import 它。

【单位口径（关键，曾经踩坑）】
    画布 1600×900 px，对应 13.333 in × 7.5 in（16:9）
    1600 px / 13.333 in = 120 px/in；1 pt = 1/72 in
    ==>  **1 pt = 1.6667 px**

    规范文档里习惯用 pt（因为 PowerPoint 用 pt），SVG 里必须写 px。
    本文件两边都给：`PT` 字典是文档口径，`PX` 字典是 SVG 口径，由 `pt2px()` 派生。

【用法】
    from ppt_style import PX, C, G          # 字号(px) / 颜色 / 几何
    from ppt_style import pt2px, style_table # 换算 / 生成对照表

【改主色】
    只改本文件的 `C["main"]`，所有脚本与骨架重新生成即可全库换色。
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ══════════════════════════════════════════════════════════
#  画布与几何
# ══════════════════════════════════════════════════════════
G = {
    "w": 1600,          # 画布宽（px）
    "h": 900,           # 画布高（px）
    # ⚠️ 2026-09-22 由 40 改为 61：7 套国自然模板实测左边距中位 **3.8%**（range 3.1–7.9%），
    #    换算到 1600 画布 = 61px。改前我们 2.5%（40px）**低于全部 7 套的下限**。
    "margin": 61,
    "bar": 72,          # 顶部标题栏高（模板实测 10.7% 但我们保留 8%——
                        #   3 套里 2 套根本没有通栏标题带，不构成共性，故不动）
    "radius": 0,        # 结构件一律直角；胶囊/节点另给 rx
}

PX_PER_IN = G["w"] / 13.3333                 # 120.0 px/in（画布 1600px = 13.333in）
PX_PER_PT = PX_PER_IN / 72.0                 # 1.6667 px/pt
"""**1 pt = 1.6667 px**；反过来 1 px = 0.6 pt"""


def pt2px(pt):
    """pt（文档口径）→ px（SVG 口径）"""
    return int(round(pt * PX_PER_PT))


def px2pt(px):
    """px（SVG 口径）→ pt（文档口径）"""
    return round(px / PX_PER_PT, 1)


# ══════════════════════════════════════════════════════════
#  字号 —— 文档口径(pt) 与 SVG 口径(px)
#  依据：2026-09-15 量 6 份独立 deck 正文页实测（标题字高 54–71px 折算）
# ══════════════════════════════════════════════════════════
# ⚠️ 2026-09-22 依 7 套模板实测调整上限：
#    模板字号上限 = 117px@1280 = **146px@1600**（6/7 套恰好如此），
#    而改前我们最大只有 90px（cover 54pt）——**层次差一档**。
PT = {
    "statement": 88,  # ⭐ 新增：结尾页大标语 —— 模板比封面还大（117@1280 > 97@1280）
    "cover":   73,   # 封面主标题（54→73：模板封面 97px@1280 = 121px@1600）
    "title":   36,   # 页面标题（标题栏内）—— 模板实测约 36pt
    "section": 24,   # 章节小标题 / 卡片标题
    "body":    19,   # 正文
    "caption": 14,   # 图注 / 页脚 / 占位说明
    "big":     30,   # 数据卡片的大数字
}

PX = {k: pt2px(v) for k, v in PT.items()}
"""SVG 里直接用 PX 这一组：statement 147 ｜ cover 122 ｜ title 60 ｜ section 40 ｜ body 32 ｜ caption 23 ｜ big 50"""


# ══════════════════════════════════════════════════════════
#  配色（视觉规范 §1.2）
# ══════════════════════════════════════════════════════════
C = {
    # ⚠️ 2026-09-22：主色由 #123E6B 换为 #0046A4。
    #    依据：7 套模板主色全部高饱和（#0046A4 / #0B4FA1 / #11754F / #B22600 /
    #    #751497 / #0066CC / #0C56AE），旧的 #123E6B 偏暗偏灰，是异类。
    #    本次取材自 3深蓝白色系（配方 5 的出处）。
    "main":  "#0046A4",   # 主色：标题栏 / 表头 / 编号块 / 边框
    "tint":  "#E5EDF6",   # 浅底 = 主色 10% 混白（蓝调）
    "gray":  "#F2F2F2",   # ⭐ 中性浅底 —— 模板实测 35 处（卡片/区块底，比 tint 更中性）
    "edge":  "#D9D9D9",   # ⭐ 可见边框 —— 模板实测 124 处（卡片框/分隔线，比 line 更实）
    "red":   "#C00000",   # 强调：**只点关键词与数值**，不点整句（7/7 模板验证一致）
    "txt":   "#333333",   # 正文
    "weak":  "#7A8698",   # 弱文字：图注出处 / 占位说明
    "line":  "#E4E9EF",   # 细线：极浅分隔线（不用作卡片边框）
    "page":  "#FFFFFF",   # 页底
    "foot":  "#9AA5B4",   # 页脚文字
}

#: 允许出现在 slide 里的全部颜色。`ppt_check.py --palette` 用它查越色。
PALETTE = set(C.values()) | {"#FFFFFF", "#B9C4D2"}

#: 主色的透明变体 —— 只给渐变用（见 ppt_kit 的 grad_band / wash）
GRADIENT_STOPS = {"main": C["main"], "page": C["page"]}


# ══════════════════════════════════════════════════════════
#  文本宽度估算 —— 不渲染就能预判"文字放不放得下"
#  系数抄自 ppt-master `drawingml/utils.py:_estimate_character_width`
# ══════════════════════════════════════════════════════════
_CJK_RANGES = ((0x4E00, 0x9FFF), (0x3400, 0x4DBF), (0x2E80, 0x2EFF),
               (0x3000, 0x303F), (0xFF00, 0xFFEF), (0xF900, 0xFAFF),
               (0x20000, 0x2A6DF))


def is_cjk(ch):
    o = ord(ch)
    return any(a <= o <= b for a, b in _CJK_RANGES)


def estimate_text_width(text, font_size, weight=None):
    """估算一段文本的渲染宽度（px）。

    系数（ppt-master 实测）：
      CJK 1.0 ｜ 空格 0.3 ｜ m M w W O Q % 0.75 ｜ i I l j ! | 0.3 ｜ 其余 0.55

    ⚠️ 数字刻意按 0.55 而非窄字 —— 把 `1` 归到窄字会**低估**框宽，
    导致忽略 `wrap="none"` 的渲染器（如 LibreOffice）折行。
    """
    w = 0.0
    for ch in text:
        if is_cjk(ch):
            w += font_size
        elif ch == " ":
            w += font_size * 0.3
        elif ch in "mMwWOQ%":
            w += font_size * 0.75
        elif ch in "iIlj!|":
            w += font_size * 0.3
        else:
            w += font_size * 0.55
    if str(weight) in ("bold", "600", "700", "800", "900"):
        w *= 1.05
    return w


#: **行首禁则** —— 这些符号不得出现在一行开头。
#: 中文排版的「避头尾」：句末标点落在行首时，读者会把它读成下一句的起点。
#: ⚠️ 2026-10-16 补。此前折行只按宽度切，实测出现过「……各排掉一半」后面
#:    孤零零一行只有一个「。」（骨架试做第一册第 5 页）。
#: 处理办法是**挤压**：宁可让这一行多出一个标点的宽度，也不把它推到下一行。
NO_LINE_START = frozenset("，。、；：？！）］｝〕〉》」』】〗〞’”…—～·％")


def wrap_text(s, max_w, size):
    """按估算宽度折行（中文按字断，西文按词断），并做**行首禁则**。

    ⚠️ 别靠"看着够短"来避免出框 —— 实测（2026-09-15）B4 骨架的 300px 窄栏，
    占位说明超出 62px。
    """
    import re
    lines, cur = [], ""
    for tok in re.findall(r"[A-Za-z0-9.,%/·+\-]+|\s+|[^\s]", s):
        if (estimate_text_width(cur + tok, size) <= max_w or not cur
                or tok in NO_LINE_START):          # 行首禁则：挤压，不换行
            cur += tok
        else:
            lines.append(cur.rstrip())
            cur = "" if tok.isspace() else tok
    if cur.strip():
        lines.append(cur.rstrip())
    # 二次收口：折行时若某行仍以禁则字符开头（上一步断在空格后），把它挪回上一行。
    # 单靠循环里的挤压挡不住「断开处恰好紧邻标点」这一种。
    i = 1
    while i < len(lines):
        if lines[i] and lines[i][0] in NO_LINE_START and lines[i - 1]:
            lines[i - 1] += lines[i][0]
            lines[i] = lines[i][1:]
            if not lines[i]:
                lines.pop(i)
                continue
        i += 1
    return lines or [""]


# ══════════════════════════════════════════════════════════
#  字体栈
# ══════════════════════════════════════════════════════════
#: ⚠️ 末尾**不能**加 `sans-serif`——ppt-master 的 parse_font_family() 会把带引号的
#: Microsoft YaHei 归到 ea（中文），把 sans-serif 归到 latin（西文），
#: 结果是 PPTX 里西文全变 Segoe UI、与 SVG 渲染不一致（2026-09-21 实测）。
#: 去掉 generic 后 latin/ea 都是 Microsoft YaHei，两边一致。
FONT = "'Microsoft YaHei','Source Han Sans SC','Noto Sans CJK SC'"

#: 数字 / 拉丁字体栈 —— **数字优先 DIN**（模板 `1深蓝色系` 与 `6红色系` 同款：
#: 主题字体 majorLatin/minorLatin 均为 `DIN Black` / `DIN`）。
#: 用于数据卡片、效应量、样本量等**需要数字有力量感**的位置。
#: ppt-master 解析：latin→`DIN Next LT Pro`，ea→`Microsoft YaHei`，
#: 故**同一段文字里数字走 DIN、中文走雅黑**，正是模板的做法。
FONT_NUM = "'DIN Next LT Pro','Microsoft YaHei'"

#: ⚠️⚠️ **字重上限（2026-09-22 实测，勿幻想更多档）**
#: `svg_to_pptx/drawingml/text_properties.py:parse_project_font_weight` 把字重折成**布尔**：
#:     `raw in {'100'…'900'}` → `int(raw) >= 600` 即粗，否则常规
#: 也就是 **900 与 700 等价、500 与 300 等价**。
#: 实测（`_work/_msyh_test.png`）：数字字重 300/500/900 **全部无效**；只有 400/700 可辨。
#: → **PPTX 里中文字重只有 2 档。** 多出来的层次必须靠**字号 / 颜色 / 底块**做，
#:    不要靠字重——否则 SVG 预览（浏览器可上可变字体 5 档）与交付的 PPTX 不一致。
#: 浏览器端若把 `Noto Sans SC` 提到栈首可拿到 5 档，但 **ppt-master 会把它映射回
#: Microsoft YaHei**，结果是**预览骗人**。故本库字体栈保持 YaHei 打头。
WEIGHT = {"regular": 400, "bold": 700}

#: 显式家族名（仅对**拉丁**有效：`Microsoft YaHei Light` 会被 ppt-master 归到 latin，
#: 中文档仍回落 Regular）。需要轻量数字时用它。
FONT_NUM_LIGHT = "'DIN Next LT Pro Light','Microsoft YaHei'"

#: **页眉的两种形态**（没有全局开关，逐页用 `ppt_kit.slide(head=…)` 指定）：
#:
#:   `"bar"` —— 通栏主色色带，高 72，编号与标题白字。21 个骨架都用这个。
#:   `"corner"` —— 左上角块 + 大号章节号 + 章节名。实测 A116-红色 / B-201 那一族。
#:
#: 🔴 **页眉高度是版面的一部分，不是配色的一部分。** `"bar"` 占 72，
#:    `"corner"` 占到 163（角块 140 + 间隔 10 + 尾条 13）—— **同一页换了页眉，正文
#:    要整页重排**，不能只改一个值。实测把页眉换成 `"corner"` 而版面不动：
#:    大号章节号直接压在内容上（配方 32 的左色块被一个「02」压住）。
#:    所以这里**不设全局开关** —— 那会让人以为换一族只要改一行。
#:    **换族 = 按新页眉重排一套骨架。**
HEAD_CORNER = {"x": 40, "w": 76, "h": 140, "tail_h": 13, "tail_gap": 10,
               "num_x": 134, "num_y": 152, "name_x": 256, "name_y": 148,
               "num_size": 90, "name_size": 60}
HEAD_CORNER = {"x": 40, "w": 76, "h": 140, "tail_h": 13, "tail_gap": 10,
               "num_x": 134, "num_y": 152, "name_x": 256, "name_y": 148,
               "num_size": 90, "name_size": 60}

#: `"corner"` 页眉占掉的顶高 —— 按它重排正文起点。
HEAD_CORNER_H = HEAD_CORNER["h"] + HEAD_CORNER["tail_gap"] + HEAD_CORNER["tail_h"]

#: **校徽位**。填一个图片路径（相对项目 `images/`）就在页眉右上角画出来；
#: `None` = 不画。共享库不含任何机构的校徽文件。
#: 实测 A116-红色与 B-201 都在这个位置放校徽（约 289×81）。
LOGO = None
LOGO_BOX = (1245, 52, 289, 81)

#: **页脚形态**。两个取值：
#:
#:   `"line"` —— 极浅细线（`C["line"]`）+ 灰字页脚。本库默认。
#:   `"rule"` —— 页面底边一条 16px 的主色细带，页码与页脚文字压在带上方。
#:
#: ⚠️ 2026-10-16 依 19 份 deck 实测补 `"rule"`：**4 份用底边主色细带**
#:    （A116-红色 23 处、4白蓝色系 11 处、【B13】红/绿各 3 处），其余用细线。
#:    改这一处，重跑页面脚本后页脚一起换。
FOOT_STYLE = "line"

#: `FOOT_STYLE == "rule"` 时底边细带的高度（px）。实测模板是 12–16。
FOOT_RULE_H = 16

#: 页脚左侧文字 —— **项目级内容，共享库不含任何项目专有串**。
#:
#: 做新项目时，二选一：
#:   ① 页面脚本开头调用 `ppt_kit.set_footer("你的项目 · 汇报")`（推荐，不动共享库）
#:   ② `<项目>/ppt.json` 写 `{"footer": "…"}`，由 `ppt_build.py` 核对（不改 SVG，只提示）
#: `slide(..., footer_left="…")` 可逐页覆盖。
FOOTER_TEXT = "（项目名）· 汇报"

#: 占位说明前缀 —— 交付前 grep PLACEHOLDER_TAG 应清零
PLACEHOLDER_TAG = "【说明】"

#: **无栏页标记** —— 封面 / 结尾页不设标题栏与页脚，且内容居中，
#: 故不应按「页边距 = G['margin']」去查它。`ppt_kit.slide(cover=True)` 会写入本标记，
#: `ppt_check.py` 见到它就跳过边距 / 标题栏 / 页脚三项检查。
NO_CHROME_TAG = "整页无栏"


def pt2px_table():
    """生成「文档 pt ↔ SVG px」对照表（写进 README 或规范用）"""
    rows = [("级别", "pt(文档)", "px(SVG)", "用途")]
    usage = {
        "statement": "⭐ 结尾页大标语（模板最大档）",
        "cover": "封面主标题", "title": "页面标题（标题栏内）",
        "section": "章节小标题 / 卡片标题", "body": "正文",
        "caption": "图注 / 页脚 / 占位说明", "big": "数据卡片大数字",
    }
    for k in PT:
        rows.append((k, str(PT[k]), str(PX[k]), usage[k]))
    return rows


def style_summary():
    """打印一份可粘进文档的参数摘要"""
    out = ["画布 %d×%d ｜ 边距 %d ｜ 标题栏高 %d（页高 %.0f%%）"
           % (G["w"], G["h"], G["margin"], G["bar"], G["bar"] / G["h"] * 100),
           "换算：1 pt = %.4f px（%.1f px/in ÷ 72）" % (PX_PER_PT, PX_PER_IN)]
    out.append("字号：" + " ｜ ".join(f"{k} {PT[k]}pt={PX[k]}px" for k in PT))
    out.append("色板：" + " ｜ ".join(f"{k} {v}" for k, v in C.items()))
    return "\n".join(out)


if __name__ == "__main__":
    print(style_summary())
    print()
    for r in pt2px_table():
        print("  %-9s %-9s %-9s %s" % r)
