# -*- coding: utf-8 -*-
"""
ppt_kit.py —— SVG 组件库（所有尺寸/配色从 `ppt_style` 读）

【定位】
    `ppt_style.py` = 数字（单一真相源）
    `ppt_kit.py`   = 零件（把数字拼成 SVG 片段）

    页面脚本 import 本模块，从而保证**全库版式一致**——
    改 `ppt_style` 一处，重跑页面脚本即同步。

【组件】
    slide()      整页外壳（说明注释 + 白底 + 渐变 defs + 标题栏 + 内容 + 页脚）
    titlebar()   顶部标题栏
    footer()     页脚
    card()       标准卡片（主色细边框 + 白底 + 标题 + 正文行）
    band()       色带（表头 / 结论条）
    tintbox()    浅底强调块（A5）—— 关键数值 / 要点句
    capsule()    胶囊节点（A7）
    ph()         虚线占位框 + 说明文字（交付前应清零）
    arrow()      箭头（C1 横 / C2 竖），端点落在给定坐标
    brace()      花括号（C6）
    bigstat()    数据卡片（大数字 + 小标签）

【⭐ 2026-09-22 新增（依 7 套国自然模板实测）】
    defs()         渐变定义（slide 自动注入，勿手写）
    grad_band()    色带淡出 —— 主色 opacity 0→1
    wash()         极淡色晕 —— 主色 opacity 0.10→0（给白底页纵深）
    cardhead()  ⭐  带表头小卡片 —— 模板内容区的主力形态
    cards_row()    把 N 个 cardhead 横向排开（等宽等距）
    badge()        编号角标
    dot()          色点
    rule()         装饰短线
    rulenum()      带色点的编号列表
    iconslot()     图标位（占位，交付前可换 <image>）
    image()    ⭐  真图片：按框等比缩放到框内，不裁不变形
    imgslot()  ⭐  **图位**：灰底 + 虚线内框 + 【图位】，与文字区一眼可分
    statement() ⭐  结尾页大标语（PX["statement"] = 147px，模板最大档）

⚠️ **字重只有 2 档**（常规 / 粗）。PPTX 端 `parse_project_font_weight` 把字重折成布尔，
   900≡700、500≡300。多出的层次请用**字号 / 颜色 / 底块**做，别用字重。
   详见 `ppt_style.WEIGHT` 处注释与 `_work/_msyh_test.png` 实测。

【约定】
    · 画布角点一律用绝对坐标；边距用 G["margin"]
    · 结构件直角；只有 capsule 用 rx
    · 禁止 python -c 传参写 SVG（中文会丢）；本模块由 Write 工具生成的脚本调用
"""
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import ppt_style as _style
from ppt_style import (C, G, PX, FONT, FONT_NUM, FONT_NUM_LIGHT, WEIGHT,
                       PLACEHOLDER_TAG, NO_CHROME_TAG,
                       estimate_text_width, wrap_text)

W, H, M, BAR = G["w"], G["h"], G["margin"], G["bar"]


def set_footer(text):
    """⭐ **做新项目的第一个动作**：设置页脚左侧文字。

    共享库（`ppt_style.py`）不含任何项目专有内容，页脚默认是占位
    `"（项目名）· 汇报"`。在你的页面脚本开头调用一次即可：

        from ppt_kit import set_footer
        set_footer("<你的项目> · 组会汇报")

    也可用 `slide(..., footer_left="…")` 逐页覆盖；
    或直接跑 `ppt_build.py <项目> --apply-footer`（读 `<项目>/ppt.json` 的 `footer`）。
    """
    _style.FOOTER_TEXT = text


def get_footer():
    """读当前页脚文字（`ppt_check --docs` / 项目核对用）"""
    return _style.FOOTER_TEXT


def esc(s):
    """XML 转义"""
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def txt(x, y, s, size=None, fill=None, weight=None, anchor=None, italic=False, opacity=None):
    """一段文字"""
    a = [f'x="{x}"', f'y="{y}"', f'font-size="{size or PX["body"]}"',
         f'fill="{fill or C["txt"]}"']
    if weight: a.append(f'font-weight="{weight}"')
    if anchor: a.append(f'text-anchor="{anchor}"')
    if italic: a.append('font-style="italic"')
    if opacity: a.append(f'opacity="{opacity}"')
    return f'  <text {" ".join(a)}>{s}</text>'


#: 导出器（ppt-master svg_to_pptx）**不支持的文字属性** —— 用了会抛
#: `SvgNativeConversionError`，且**一页失败整册都导不出**。
#: 来源：`svg_to_pptx/drawingml/text_properties.py` 的 `_UNSUPPORTED_TEXT_PROPERTIES`
UNSUPPORTED_TEXT_PROPS = frozenset({
    "alignment-baseline", "baseline-shift", "direction", "dominant-baseline",
    "font-kerning", "font-feature-settings", "font-size-adjust", "font-stretch",
    "font-synthesis", "font-variant", "font-variation-settings", "font",
    "hyphens", "kerning", "line-height", "overflow-wrap", "text-align",
    "text-align-last", "text-indent", "text-rendering", "text-shadow",
    "text-transform", "unicode-bidi", "vertical-align", "white-space",
    "word-spacing", "word-break", "writing-mode",
})


def vtext(x, y, s, size=None, fill=None, weight=None, lead=None):
    """竖排文字：**逐字堆叠**。

    ⚠️ **不要用 `writing-mode="tb"`** —— 导出器不支持，会抛异常且**整册导不出**。
    本函数用「每个字一个 <text>」实现竖排，是纯 SVG 子集，100% 可导出。
    """
    size = size or PX["body"]
    lead = lead or size * 1.2
    return "\n".join(
        txt(x, y + i * lead, esc(ch), size=size, fill=fill, weight=weight, anchor="middle")
        for i, ch in enumerate(s)
    )


def rect(x, y, w, h, fill="none", stroke=None, sw=1.4, dash=None, rx=None):
    a = [f'x="{x}"', f'y="{y}"', f'width="{w}"', f'height="{h}"', f'fill="{fill}"']
    if stroke: a.append(f'stroke="{stroke}" stroke-width="{sw}"')
    if dash: a.append(f'stroke-dasharray="{dash}"')
    if rx: a.append(f'rx="{rx}"')
    return f'  <rect {" ".join(a)}/>'


# ══════════════════════════════════════════════════════════
#  固定件
# ══════════════════════════════════════════════════════════
def titlebar(title, num="01", fs=None):
    """顶部标题栏：全宽主色色带 + 竖线锚点 + 编号 + 标题"""
    fs = fs or PX["title"]
    return "\n".join([
        rect(0, 0, W, BAR, fill=C["main"]),
        rect(M, 20, 4, 32, fill="#FFFFFF"),
        txt(M + 20, 48, esc(num), size=PX["section"], fill="#FFFFFF", weight=700),
        txt(M + 78, 48, esc(title), size=PX["section"], fill="#FFFFFF", weight=700),
    ])


def headbar(title, num="NN", style="bar"):
    """页眉。两种形态（**逐页指定，没有全局开关**）：

      · `"bar"` —— 通栏主色色带 + 编号 + 白字标题
      · `"corner"` —— 左上角块 + 大号章节号 + 章节名

    ⚠️ 两者的**占高不同**（72 对 163），正文起点必须跟着重排 ——
       换了 `"corner"` 而不动版面，大号章节号会压在内容上。见 `ppt_style.HEAD_CORNER_H`。
    """
    if style != "corner":
        return titlebar(title, num)
    d = _style.HEAD_CORNER
    return "\n".join([
        rect(d["x"], 0, d["w"], d["h"], fill=C["main"]),
        rect(d["x"], d["h"] + d["tail_gap"], d["w"], d["tail_h"], fill=C["main"]),
        txt(d["num_x"], d["num_y"], esc(num), size=d["num_size"],
            fill=C["main"], weight=700),
        txt(d["name_x"], d["name_y"], esc(title), size=d["name_size"], fill=C["txt"]),
    ])


def logo():
    """校徽位。`ppt_style.LOGO` 给了路径才画；没给返回空串。"""
    href = getattr(_style, "LOGO", None)
    if not href:
        return ""
    x, y, w, h = _style.LOGO_BOX
    return image(x, y, w, h, href)


def footer(page="00", left=None):
    """页脚。左文字取 `left` → 否则 `set_footer()` 设的值。

    形态由 `ppt_style.FOOT_STYLE` 定：
      · `"line"`（默认）—— 极浅细线 + 灰字
      · `"rule"` —— 页面底边一条 16px 主色细带，文字压在带上方
    """
    text, num = esc(left or _style.FOOTER_TEXT), esc(page)
    if getattr(_style, "FOOT_STYLE", "line") == "rule":
        h = getattr(_style, "FOOT_RULE_H", 16)
        return "\n".join([
            f'  <rect x="0" y="{H - h}" width="{W}" height="{h}" fill="{C["main"]}"/>',
            txt(M, 866, text, size=PX["caption"], fill=C["foot"]),
            txt(W - M, 866, num, size=PX["caption"], fill=C["foot"], anchor="end"),
        ])
    return "\n".join([
        f'  <line x1="{M}" y1="836" x2="{W-M}" y2="836" stroke="{C["line"]}" stroke-width="1.2"/>',
        txt(M, 866, text, size=PX["caption"], fill=C["foot"]),
        txt(W - M, 866, num, size=PX["caption"], fill=C["foot"], anchor="end"),
    ])


# ══════════════════════════════════════════════════════════
#  区块（A 库）
# ══════════════════════════════════════════════════════════
def band(x, y, w, text, h=None, fill=None, fs=None, anchor="start"):
    """A1 色带表头 / 结论条"""
    h = h or int(PX["body"] * 1.6)
    fs = fs or PX["body"]
    tx = x + 24 if anchor == "start" else x + w / 2
    return "\n".join([
        rect(x, y, w, h, fill=fill or C["main"]),
        txt(tx, y + h * 0.68, esc(text), size=fs, fill="#FFFFFF", weight=700, anchor=anchor),
    ])


def tintbox(x, y, w, h, label, value, stroke=None):
    """A5 浅底强调块：浅底 + 强调色细框 + 小标签 + 大数值"""
    return "\n".join([
        rect(x, y, w, h, fill=C["tint"], stroke=stroke or C["red"], sw=1.4),
        txt(x + w / 2, y + h * 0.36, esc(label), size=PX["caption"], fill=C["txt"], anchor="middle"),
        txt(x + w / 2, y + h * 0.78, esc(value), size=PX["big"] * 0.6,
            fill=C["red"], weight=700, anchor="middle"),
    ])


def card(x, y, w, h, title, lines=(), fill=None, stroke=None, tcol=None):
    """标准卡片：主色细边框 + 白底 + 标题 + 正文行"""
    s = [rect(x, y, w, h, fill=fill or "#FFFFFF", stroke=stroke or C["main"], sw=1.4),
         txt(x + 24, y + PX["section"] * 1.3, esc(title),
             size=PX["section"], fill=tcol or C["main"], weight=700)]
    for i, ln in enumerate(lines):
        s.append(txt(x + 24, y + PX["section"] * 1.3 + PX["body"] * (1.6 + i * 1.4),
                     esc(ln), size=PX["body"], fill=C["txt"]))
    return "\n".join(s)


def capsule(x, y, w, h, text, fill=None, tcol="#FFFFFF"):
    """A7 胶囊节点"""
    return "\n".join([
        rect(x, y, w, h, fill=fill or C["main"], rx=h / 2),
        txt(x + w / 2, y + h * 0.65, esc(text), size=PX["body"],
            fill=tcol, weight=700, anchor="middle"),
    ])


def bigstat(x, y, w, h, value, label):
    """数据卡片：大号彩色数值 + 小号深灰标签"""
    return "\n".join([
        rect(x, y, w, h, fill=C["tint"], stroke=C["main"], sw=1.4),
        txt(x + w / 2, y + h * 0.52, esc(value), size=PX["big"],
            fill=C["red"], weight=700, anchor="middle"),
        txt(x + w / 2, y + h * 0.80, esc(label), size=PX["caption"],
            fill=C["txt"], anchor="middle"),
    ])


def ph(x, y, w, h, label, dx=14, dy=None, wrap=True):
    """虚线占位框 + 【说明】文字（**自动折行**，不会出框）。

    交付前 `ppt_check.py` 的「【说明】残留」应清零。
    折行用 `ppt_style.wrap_text`（按估算宽度，不靠"看着够短"）。
    """
    size = PX["caption"]
    dy = dy or size + 12
    text = PLACEHOLDER_TAG + label
    lines = wrap_text(text, w - dx * 2, size) if wrap else [text]
    parts = [rect(x, y, w, h, fill="none", stroke=C["weak"], sw=1.6, dash="8,5")]
    for i, ln in enumerate(lines[:3]):          # 最多 3 行，超出就截断
        parts.append(txt(x + dx, y + dy + i * (size * 1.35), esc(ln),
                         size=size, fill=C["weak"]))
    return "\n".join(parts)


# ══════════════════════════════════════════════════════════
#  连接件（C 库）
# ══════════════════════════════════════════════════════════
def arrow(x1, y1, x2, y2, color=None, sw=3, head=13):
    """C1/C2 箭头：直线 + 三角头，**端点即给定坐标**（点必须落在目标边上）"""
    import math
    col = color or C["main"]
    ang = math.atan2(y2 - y1, x2 - x1)
    bx, by = x2 - head * math.cos(ang), y2 - head * math.sin(ang)
    p1 = (x2 - head * 1.6 * math.cos(ang) - head * 0.75 * math.sin(ang),
          y2 - head * 1.6 * math.sin(ang) + head * 0.75 * math.cos(ang))
    p2 = (x2 - head * 1.6 * math.cos(ang) + head * 0.75 * math.sin(ang),
          y2 - head * 1.6 * math.sin(ang) - head * 0.75 * math.cos(ang))
    pts = " ".join(f"{round(a,1)},{round(b,1)}" for a, b in [p1, p2, (x2, y2)])
    return "\n".join([
        f'  <line x1="{x1}" y1="{y1}" x2="{round(bx,1)}" y2="{round(by,1)}" '
        f'stroke="{col}" stroke-width="{sw}" stroke-linecap="round"/>',
        f'  <polygon points="{pts}" fill="{col}"/>',
    ])


def brace(x, y1, y2, text=None, color=None, span=26):
    """C6 花括号：跨住 y1..y2，尖端朝右"""
    col = color or C["main"]
    ym = (y1 + y2) / 2
    d = (f"M{x} {y1} C{x+span} {y1} {x+span} {ym} {x+span*1.6} {ym} "
         f"C{x+span} {ym} {x+span} {y2} {x} {y2}")
    s = [f'  <path d="{d}" fill="none" stroke="{col}" stroke-width="3.4" stroke-linecap="round"/>',
         f'  <line x1="{x+span*1.6}" y1="{ym}" x2="{x+span*1.6+24}" y2="{ym}" '
         f'stroke="{col}" stroke-width="3"/>']
    return "\n".join(s)


def leader(x1, y1, x2, y2, color=None):
    """C5 引出线（红=论点强调；黑/主色=中性技术标注）"""
    return (f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{color or C["red"]}" stroke-width="2.4"/>')


# ══════════════════════════════════════════════════════════
#  ⭐ 2026-09-22 新增（依 7 套国自然模板实测）
#     · 渐变（模板 27 个定义，我们此前为 0）
#     · 带表头小卡片（模板内容区的主力形态）
#     · 装饰件（模板 6/7 套图片里 71–85% 是 <3% 面积的小件）
# ══════════════════════════════════════════════════════════

#: 渐变 id —— 与 defs() 对应；页面里用 `fill="url(#gBand)"` 引用
GID_BAND = "gBand"   # 垂直：主色 opacity 0 → 1（色带"长出来"）
GID_WASH = "gWash"   # 横向：主色 opacity 0.10 → 0（极淡色晕）


def defs():
    """渐变定义。由 `slide()` 自动注入，**页面里不要重复写**。

    两类型都取自模板实测（`3深蓝白色系` 全 19 页 27 个渐变定义）：
      · `gBand` 色带淡出 —— 让色带不出现硬边
      · `gWash` 极淡色晕 —— opacity 0.10→0，几乎看不见但给页面纵深
    """
    m = C["main"]
    return "\n".join([
        "  <defs>",
        f'    <linearGradient id="{GID_BAND}" x1="0.5" y1="0" x2="0.5" y2="1">',
        f'      <stop offset="0" stop-color="{m}" stop-opacity="0"/>',
        f'      <stop offset="1" stop-color="{m}" stop-opacity="1"/>',
        "    </linearGradient>",
        f'    <linearGradient id="{GID_WASH}" x1="0" y1="0.5" x2="1" y2="0.5">',
        f'      <stop offset="0" stop-color="{m}" stop-opacity="0.10"/>',
        f'      <stop offset="1" stop-color="{m}" stop-opacity="0"/>',
        "    </linearGradient>",
        "  </defs>",
    ])


def grad_band(x, y, w, h, horizontal=False):
    """⭐ 色带淡出：从透明渐变到主色。用于标题栏 / 结论条。

    **不要**用纯色 rect 代替——模板的色带"长出来"靠的就是渐变层。
    """
    gid = GID_BAND
    return f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#{gid})"/>'


def wash(x, y, w, h):
    """⭐ 极淡色晕：主色 opacity 0.10 → 0 的横向渐变。

    **用途**：不想放硬色块、又需要页面有纵深时用。模板靠它让白底页"不空"。
    """
    return f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#{GID_WASH})"/>'


def cardhead(x, y, w, h, title, lines=(), headh=None, headfill=None,
             bodyfill=None, edge=None, tcol="#FFFFFF", fs=None, lead=None):
    """⭐ **带表头的小卡片** —— 模板内容区的主力形态（`5绿色系` 每页 2–4 个）。

    ```
    ┌─ 表头（主色底 + 白字）──────────┐
    ├──────────────────────────────────┤   ← 细边框（C["edge"]）
    │  内容行                          │
    │  内容行                          │
    └──────────────────────────────────┘
    ```

    ⚠️ **不要拿它拼成一个"大表格"** —— 它的价值在于**把一个表格拆成 2–4 块**，
    把表格拆成 2–4 块并留间距，是模板与"一个表格到底"的核心差别，也是元素密度的来源。
    """
    fs = fs or PX["body"]
    lead = lead or fs * 1.55
    headh = headh or int(fs * 1.9)
    eb = edge or C["edge"]
    parts = [
        # 表头
        rect(x, y, w, headh, fill=headfill or C["main"]),
        txt(x + 18, y + headh * 0.68, esc(title), size=fs, fill=tcol, weight=700),
        # 卡身
        f'  <rect x="{x}" y="{y + headh}" width="{w}" height="{h - headh}" '
        f'fill="{bodyfill or "#FFFFFF"}" stroke="{eb}" stroke-width="1.2"/>',
    ]
    # 只画放得下的行 —— 溢出会被 ppt_check 判越界，宁可少一行也不要出框
    fit = max(0, int((h - headh - fs * 0.5) // lead))
    for i, ln in enumerate(lines[:fit]):
        parts.append(txt(x + 18, y + headh + lead * (1.0 + i), esc(ln),
                         size=fs, fill=C["txt"]))
    return "\n".join(parts)


def cards_row(y, h, items, gap=22, x0=None, x1=None):
    """把 N 个 `cardhead` 横向排开（**等宽等距**）。

    `items` = [(标题, [正文行…]), …]
    """
    x0 = M if x0 is None else x0
    x1 = (W - M) if x1 is None else x1
    n = len(items)
    w = (x1 - x0 - gap * (n - 1)) / n
    out = []
    for i, (t, lines) in enumerate(items):
        out.append(cardhead(x0 + i * (w + gap), y, w, h, t, lines))
    return "\n".join(out)


def table(x, y, w, h, cells, fs=None, headfill=None, tcol="#FFFFFF",
          striped=True, edge=None):
    """数据表：表头一行主色底白字，表体隔行浅底，每格居中。

    `cells` = 二维列表，**第一行当表头**。列宽行高等分，不按内容自适应。

    ⚠️ **2026-10-15 补**：此前 `ppt_kit` 没有画表格的函数。
    模板里 19 处 `graphicFrame` 全是表，拆解能认出「这一页有表」，
    但画不出来——配方 4 / 5 / 6（表格 + …）因此一直没法填。
    """
    if not cells or not cells[0]:
        return ""
    fs = fs or PX["caption"]
    eb = edge or C["edge"]
    rows, cols = len(cells), len(cells[0])
    cw, rh = w / cols, h / rows
    out = []
    for ri, row in enumerate(cells):
        for ci in range(cols):
            cx, cy = x + ci * cw, y + ri * rh
            cell = str(row[ci]) if ci < len(row) else ""
            if ri == 0:
                out.append(rect(cx, cy, cw, rh, fill=headfill or C["main"]))
                col, weight = tcol, 700
            else:
                if striped and ri % 2 == 0:
                    out.append(rect(cx, cy, cw, rh, fill=C["gray"]))
                col, weight = C["txt"], None
            out.append(f'  <rect x="{cx:.1f}" y="{cy:.1f}" width="{cw:.1f}" '
                       f'height="{rh:.1f}" fill="none" stroke="{eb}" stroke-width="1"/>')
            out.append(txt(cx + cw / 2, cy + rh * 0.68, esc(cell),
                           size=fs, fill=col, weight=weight, anchor="middle"))
    return "\n".join(out)


# ── 装饰件（模板 71–85% 的图是 <3% 面积的小件，等价物）──

def badge(x, y, text, size=None, fill=None):
    """编号角标：方形主色块 + 白字。与 `titlebar` 的编号同源。"""
    size = size or PX["section"] * 1.5
    return "\n".join([
        rect(x, y, size, size, fill=fill or C["main"]),
        txt(x + size / 2, y + size * 0.70, esc(text), size=size * 0.62,
            fill="#FFFFFF", weight=700, anchor="middle"),
    ])


def dot(x, y, r=6, fill=None):
    """色点：列表前缀 / 图例。**色点是"细节密度"最便宜的一种。**"""
    return f'  <circle cx="{x}" cy="{y}" r="{r}" fill="{fill or C["red"]}"/>'


def rule(x, y, w=None, thick=4, fill=None):
    """装饰短线：标题下方 / 区块分隔。模板 6红色系 的"红字标题 + 横线"就靠它。"""
    return (f'  <rect x="{x}" y="{y}" width="{w or 64}" height="{thick}" '
            f'fill="{fill or C["main"]}"/>')


def rulenum(x, y, n, lead=None, gap=18, fill=None):
    """带色点的编号列表 —— 把"多行文字"变成"多个小元素"。"""
    lead = lead or PX["body"] * 1.6
    out = []
    for i, s in enumerate(n):
        yy = y + i * lead
        out.append(dot(x + 6, yy - 5, r=5, fill=fill or C["red"]))
        out.append(txt(x + gap, yy, esc(s), size=PX["body"], fill=C["txt"]))
    return "\n".join(out)


def iconslot(x, y, w, h, label="图标"):
    """图标位：浅底方块 + 虚线内框 + 小字。

    ⚠️ 模板的图标是**真实图片**；本函数给的是**占位**，交付前应换成 `<image>`。
    但放一个图标位也比什么都没有强——它提供模板的"细节密度"。
    """
    return "\n".join([
        rect(x, y, w, h, fill=C["gray"]),
        f'  <rect x="{x + 6}" y="{y + 6}" width="{w - 12}" height="{h - 12}" '
        f'fill="none" stroke="{C["weak"]}" stroke-width="1.2" stroke-dasharray="5,4"/>',
        txt(x + w / 2, y + h / 2 + 5, esc(label), size=PX["caption"],
            fill=C["weak"], anchor="middle"),
    ])


def image(x, y, w, h, href):
    """⭐ 真图片：`<image>` 按框等比缩放，不裁切不变形。

    `preserveAspectRatio="xMidYMid meet"` 是**必须的** —— 图位是固定比例的框，
    图片比例不同时按最长边缩放到框内并居中；换成 `slice` 会裁掉边上的内容，
    而不写这个属性时 SVG 默认 `xMidYMid meet`，看起来一样但导出器未必同样处理。

    ⚠️ `href` 用**相对项目 `images/` 的路径**（`../images/xxx.png`），
    `render_svg.py` 会绝对化。绝对路径与 `file://` 在换机器时全废。
    """
    return (f'  <image href="{href}" x="{x}" y="{y}" width="{w}" height="{h}" '
            f'preserveAspectRatio="xMidYMid meet"/>')


def imgslot(x, y, w, h, hint="图位"):
    """⭐ **图位**：灰底 + 虚线内框 + 用途提示。放图时整段换成 `image()`。

    ⚠️ 2026-10-16 补。此前图位与文字占位框 `ph()` 画的是同一种虚线框，
    看不出「这里该放图」，也看不出放图之后是裁切还是缩放。
    """
    size = PX["caption"]
    lines = wrap_text(hint, max(w - 32, size * 2), size)[:2]
    top = y + h / 2 - 4 - (len(lines) - 1) * size * 0.7
    parts = [
        rect(x, y, w, h, fill=C["gray"]),
        f'  <rect x="{x + 8}" y="{y + 8}" width="{w - 16}" height="{h - 16}" '
        f'fill="none" stroke="{C["weak"]}" stroke-width="1.4" stroke-dasharray="7,5"/>',
        txt(x + w / 2, top, "【图位】", size=size, fill=C["weak"], anchor="middle"),
    ]
    for i, ln in enumerate(lines):
        parts.append(txt(x + w / 2, top + 30 + i * size * 1.25, esc(ln),
                         size=size, fill=C["weak"], anchor="middle"))
    return "\n".join(parts)


def statement(text, sub=None):
    """⭐ 结尾页大标语（`PX["statement"]` = 147px，模板最大档）。

    模板实测：**结尾页字号（117@1280）比封面（97@1280）还大**——
    用最大字号收场。此前我们的 `PT` 表**没有大标语档**。
    """
    out = [txt(W / 2, H / 2 + 10, esc(text), size=PX["statement"],
               fill=C["main"], weight=700, anchor="middle")]
    if sub:
        out.append(txt(W / 2, H / 2 + 96, esc(sub), size=PX["section"],
                       fill=C["txt"], anchor="middle"))
    return "\n".join(out)


# ══════════════════════════════════════════════════════════
#  整页外壳
# ══════════════════════════════════════════════════════════
def slide(title, body, num="01", page="00", note="", footer_left=None,
          cover=False, head="bar"):
    """整页 SVG：HTML 注释（规格说明）+ 白底 + 标题栏 + 内容 + 页脚"""
    comment = (note + "\n     " if note else "") + (
        f"画布 {W}×{H} ｜ 边距 {M} ｜ 标题栏高 {BAR}（页高 {BAR/H*100:.0f}%）\n"
        f"     字号(px)：大标语 {PX['statement']} ｜ 封面 {PX['cover']} ｜ 标题 {PX['title']}"
        f" ｜ 小标题 {PX['section']} ｜ 正文 {PX['body']} ｜ 图注·页脚 {PX['caption']}\n"
        f"     ⚠️ 字重只有 2 档（常规/粗）——PPTX 端 font-weight 折成布尔，见 ppt_style.WEIGHT\n"
        f"     换主色：改 ppt_style.py 的 C['main']，然后重生成\n"
        f"     交付前：grep \"{PLACEHOLDER_TAG}\" 应清零")
    # 封面 / 结尾页：不要标题栏与页脚，且内容居中 —— 写 NO_CHROME_TAG 让 ppt_check 放行
    chrome = "" if cover else "\n".join(
        x for x in (headbar(title, num, head), logo(),
                    footer(page, footer_left)) if x)
    if cover:
        comment = NO_CHROME_TAG + "（封面/结尾页）：不设标题栏与页脚，内容居中\n     " + comment
    return f'''<!-- {comment}
-->
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">
{rect(0, 0, W, H, fill=C["page"])}
{defs()}
{chrome}
{body}
</svg>
'''


if __name__ == "__main__":
    demo = slide("组件自检", "\n".join([
        f"<!-- 第 1 行：老组件 -->",
        band(M, 100, 400, "A1 色带表头"),
        card(M, 180, 400, 130, "标准卡片", ["正文行一", "正文行二"]),
        tintbox(M + 430, 180, 190, 110, "标签", "2.5 cm³"),
        capsule(M + 650, 180, 160, 56, "胶囊节点"),
        bigstat(M + 840, 180, 190, 110, "10⁹×", "开关比"),
        arrow(M + 1060, 235, M + 1180, 235),

        f"<!-- 第 2 行：新增 —— 带表头小卡片（cards_row） -->",
        cards_row(360, 200, [
            ("表头一", ["内容行", "内容行"]),
            ("表头二", ["内容行", "内容行"]),
            ("表头三", ["内容行", "内容行"]),
        ]),

        f"<!-- 第 3 行：新增 —— 渐变与装饰件 -->",
        wash(M, 600, 460, 150),
        grad_band(M, 640, 300, 46),
        txt(M + 18, 670, "色带淡出 grad_band", size=PX["body"], fill="#FFFFFF", weight=700),
        badge(M + 400, 640, "03"),
        rule(M + 480, 660, 64, 4),
        dot(M + 580, 668, r=6),
        dot(M + 602, 668, r=6, fill=C["main"]),
        iconslot(M + 630, 630, 80, 80, "图标位"),
        rulenum(M + 740, 660, ["要点一", "要点二", "要点三"]),
    ]), page="99", note="ppt_kit 组件自检页（含 2026-09-22 新增组件）")
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_work", "_组件自检.svg")
    out = os.path.normpath(out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(demo)
    print("✅", out)
