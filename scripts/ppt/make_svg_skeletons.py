# -*- coding: utf-8 -*-
"""
make_svg_skeletons.py —— 生成版式骨架 SVG（可直接复制改内容）

【定位】
    工具链的**出厂设置**：从 `ppt_style`（数字）+ `ppt_kit`（零件）生成一整套起点页。
    改主色或字号 → 只改 `ppt_style.py` → 重跑本脚本 → 全库同步。

【用法】
    python make_svg_skeletons.py                 # 全部生成
    python make_svg_skeletons.py --only B2       # 只生成名字含 B2 的

【产出】
    `_流程与工具/PPT骨架模板_20260915/` 下 21 个 .svg + README.md
    预览 PNG 由 `ppt_build.py` 或 `render_svg.py` 生成。

【配套】
    `PPT视觉规范_国自然风格_20260915.md` v2（区块 A / 骨架 B / 连接件 C）
    `PPT版式配方库_20260915.md` v2（32 个配方；附录 E 是配方↔骨架的映射表）
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from ppt_style import C, G, PX, estimate_text_width
from ppt_kit import (slide, band, card, tintbox, capsule, bigstat,
                     ph, arrow, brace, leader, titlebar, footer, txt, rect, vtext,
                     cards_row, statement, esc)

W, H, M = G["w"], G["h"], G["margin"]

# ⚠️ 2026-09-22：**所有坐标一律从 M / W 派生，禁止再写死右边界**
#
# 起因：此前 18 个骨架把右边界硬编码成 1560（= W-40），一旦 G["margin"] 由 40 改为 61，
# 会有 12 处越界（1560 > W-61 = 1539）。这正是本工具链要防的「改一处漏一处」。
# 现在改 `ppt_style.G["margin"]` 一处，重跑本脚本即全库同步。
CW = W - 2 * M                  # 内容宽
GAP = 32                        # 栏间距
C2W = (CW - GAP) // 2           # 双栏每栏宽
C3W = (CW - 2 * GAP) // 3       # 三栏每栏宽
C4W = (CW - 3 * GAP) // 4       # 四栏每栏宽

# 输出目录从**脚本自身位置**推导，不写死盘符 —— 换机器 / 换库根都不用改
OUT = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "PPT骨架模板_20260915"))

# ══════════════════════════════════════════════════════════
#  八 个 骨 架 基 座（只有分区，格内自定）
# ══════════════════════════════════════════════════════════
BASES = {
    "B1": ("通栏", "B1 通栏：单列到底。信息少 + 大图时用。",
           ph(M, 100, CW, 700, "单栏内容区：一张大图，或一段长文（≤9 行）")),

    "B2": ("两栏", "B2 两栏：左文右图 / 左图右文。图文衔接的主力骨架。",
           ph(M, 100, C2W, 700, "左栏：文字 / 要点框") + "\n" +
           ph(M + C2W + GAP, 100, C2W, 700, "右栏：图（须紧贴它支持的那一条）")),

    "B3": ("三栏等宽", "B3 三栏等宽：并列三类。三栏之间要有递进关系，不是随便三块。",
           "\n".join(ph(M + i * (C3W + GAP), 100, C3W, 700, f"第 {i+1} 栏") for i in range(3))),

    "B4": ("窄-宽-窄", "B4 窄-宽-窄：主图居中放大，两侧各放辅助信息。",
           ph(M, 100, 280, 700, "左窄栏：辅助说明 / 要点") + "\n" +
           ph(M + 280 + GAP, 100, CW - 2 * 280 - 2 * GAP, 700, "中间主图（占最大宽度）") + "\n" +
           ph(W - M - 280, 100, 280, 700, "右窄栏：结论 / 汇合")),

    "B5": ("左标签+右内容", "B5 左标签栏 + 右内容：左 1/3 色带标签，右 2/3 内容；左栏内可再分上下。",
           rect(M, 100, 400, 700, fill=C["main"]) + "\n" +
           vtext(M + 120, 230, "侧栏标签（竖排）", size=PX["body"], fill="#FFFFFF", weight=700) + "\n" +
           vtext(M + 240, 230, "副标题", size=PX["body"], fill="#FFFFFF", weight=700) + "\n" +
           ph(M + 400 + GAP, 100, CW - 400 - GAP, 340, "右上区") + "\n" +
           ph(M + 400 + GAP, 460, CW - 400 - GAP, 340, "右下区：可与上区不同主题")),

    "B6": ("上下两段", "B6 上下两段：上总下分。先结论后展开。",
           ph(M, 100, CW, 240, "上段：总结 / 导语 / 两组对照三元组") + "\n" +
           ph(M, 370, CW, 430, "下段：展开（可再分栏）")),

    "B7": ("单栏纵向链", "B7 单栏纵向链：A ↓ B ↓ C。连接件可用箭头(C2)或加号(C3)。",
           "\n".join(ph(M, 100 + i * 190, 700, 150, f"步骤 {i+1}") for i in range(3)) + "\n" +
           ph(M + 700 + GAP, 290, CW - 700 - GAP, 340, "右侧分支说明框（不打断主干）")),

    "B8": ("田字格", "B8 2×2 田字格：四条并列。常配浅底强调块(A5)。",
           ph(M, 100, C2W, 335, "左上") + "\n" + ph(M + C2W + GAP, 100, C2W, 335, "右上") + "\n" +
           ph(M, 465, C2W, 335, "左下") + "\n" + ph(M + C2W + GAP, 465, C2W, 335, "右下")),
}

# ══════════════════════════════════════════════════════════
#  十 三 个 高 频 配 方 变 体（已成型的整页起点）
# ══════════════════════════════════════════════════════════
def _v01():   # 配方 1 · 章节过渡页（6/6 deck 采用，最高频）
    rows = ["01　立项背景和研究思路", "02　创新点和主要技术内容", "03　应用推广和经济社会效益"]
    LW = 340
    RX, RW = M + LW + GAP, CW - LW - GAP
    s = [rect(M, 100, LW, 700, fill=C["main"]),
         vtext(M + LW // 2, 260, "汇报提纲", size=PX["section"], fill="#FFFFFF", weight=700),
         rect(RX, 196, RW, 86, fill=C["main"]),
         txt(RX + 40, 252, rows[0], size=PX["section"], fill="#FFFFFF", weight=700)]
    for i, r in enumerate(rows[1:], 1):
        s.append(txt(RX + 40, 252 + i * 90, r, size=PX["section"], fill="#B9C4D2"))
    s.append(ph(RX, 480, RW, 320, "其余章节条目灰字；当前项主色底+白字（唯一高亮）"))
    return "\n".join(s)


def _v02():   # 配方 2 · 左框 →箭头→ 右图
    LW = 700
    RX, RW = M + LW + GAP, CW - LW - GAP
    return "\n".join([
        card(M, 100, LW, 300, "要点框（A6 虚线框亦可）", ["· 要点一", "· 要点二", "· 要点三"]),
        arrow(M + LW + 4, 250, RX - 4, 250),            # 端点咬在框边
        ph(RX, 100, RW, 300, "图：无边框无圆角，紧贴左框"),
        ph(M, 440, CW, 360, "下段：第二条「框 →箭头→ 图」，或换用其他配方"),
    ])


def _v04():   # 配方 4 · 表格 + 引出线标注
    TW = 960                                        # 表格宽
    BX, BW = M + TW + GAP, CW - TW - GAP            # 右侧标注框
    cols = [M, M + TW // 3, M + TW * 2 // 3]
    s = [rect(M, 120, TW, 60, fill=C["main"])]
    for i, cx in enumerate(cols):
        s.append(txt(cx + 24, 160, f"表头{['一','二','三'][i]}", size=PX["body"],
                     fill="#FFFFFF", weight=700))
    for i in range(5):
        y = 180 + i * 64
        s.append(rect(M, y, TW, 64, fill=("#FFFFFF" if i % 2 else C["tint"]),
                      stroke=C["line"], sw=1))
        for j, cx in enumerate(cols):
            s.append(txt(cx + 24, y + 42, f"行 {i+1}" if j == 0 else "—",
                         size=PX["body"], fill=C["txt"]))
    s += [leader(M + TW + 30, 308, BX, 396),
          rect(BX, 366, BW, 60, fill="#FFFFFF", stroke=C["red"], sw=1.8),
          txt(BX + 24, 406, "标注框：连到具体某一格", size=PX["body"], fill=C["red"], weight=700),
          ph(M, 520, CW, 280, "补充说明 / 结论条（配方 6：表格 + 底部结论色带）")]
    return "\n".join(s)


def _v09():   # 配方 9 · 并列 → 汇聚（本项目立论支点）
    BW, BG = 150, 30
    x0 = (W - (4 * BW + 3 * BG)) // 2               # 四块整体居中
    MID = W // 2
    s = []
    for i in range(4):
        x = x0 + i * (BW + BG)
        s += [rect(x, 140, BW, 90, fill=C["tint"], stroke=C["main"]),
              txt(x + BW // 2, 195, f"脑区 {i+1}", size=PX["body"], anchor="middle")]
    for i in range(4):
        x = x0 + i * (BW + BG) + BW // 2
        tgt = MID if i in (0, 3) else x
        s.append(f'  <path d="M{x} 230 L{x} 300 L{tgt} 300" '
                 f'fill="none" stroke="{C["main"]}" stroke-width="3"/>')
    s += [f'  <line x1="{MID}" y1="300" x2="{MID}" y2="368" stroke="{C["main"]}" stroke-width="3"/>',
          arrow(MID, 340, MID, 400),
          rect(MID - 300, 400, 600, 110, fill=C["main"]),
          txt(MID, 468, "唯一交集：屏状核", size=PX["section"], fill="#FFFFFF",
              weight=700, anchor="middle"),
          ph(M, 570, CW, 230, "支撑证据 / 检索命中数（可配配方 18 的数据库截图）")]
    return "\n".join(s)


def _v10():   # 配方 10 · 三栏等宽 + 色带表头
    s = []
    for i in range(3):
        x = M + i * (C3W + GAP)
        s += [band(x, 110, C3W, f"0{i+1}　栏目名", h=56),
              ph(x, 166, C3W, 540, f"第 {i+1} 栏内容")]
    s += [txt(W // 2, 790, "底部红字收口：一句话结论", size=PX["body"],
              fill=C["red"], anchor="middle")]
    return "\n".join(s)


def _v12():   # 配方 12 · 左右双栏对照
    return "\n".join([
        card(M, 110, C2W, 640, "说法", ["① 说法一", "② 说法二", "③ 说法三"]),
        card(M + C2W + GAP, 110, C2W, 640, "反证",
             ["① 反证一", "② 反证二", "③ 反证三"],
             fill=C["tint"], stroke=C["red"], tcol=C["red"]),
    ])


def _v17():   # 配方 17 · 数据卡片（6/6 deck 采用）
    return "\n".join(
        [bigstat(M + i * (C4W + GAP), 140, C4W, 150, "00.0%", "标签") for i in range(4)] +
        [ph(M, 340, CW, 460,
            "承接内容：数据卡片把关键数字从段落里提出来，一眼可读")])


def _v18():   # 配方 18 · 数据库截图 + 红框 + 大数字（本项目 P17）
    BIG = int(PX["big"] * 2)          # 大数字：靠颜色+字重+孤立抓眼，不必更大
    SW = 900                          # 左：截图区
    RX, RW = M + SW + GAP, CW - SW - GAP
    return "\n".join([
        ph(M, 110, SW, 620, "PubMed / ClinicalTrials.gov 检索界面【真实截图】"),
        rect(M + 60, 210, 460, 90, stroke=C["red"], sw=3.4),
        txt(RX, 290, "0", size=BIG, fill=C["red"], weight=700),
        txt(RX, 344, "TITLE 级命中", size=PX["body"]),
        txt(RX, 470, "1", size=BIG, fill=C["red"], weight=700),
        txt(RX, 524, "TIAB 级命中", size=PX["body"]),
        leader(RX - 12, 250, M + 560, 250), arrow(M + 580, 250, M + SW - 12, 250),
        ph(RX, 580, RW, 150, "口径提醒：写明检索式与检索日期"),
    ])


def _v25():   # 配方 25 · 胶囊节点 + 花括号 + ▸ 列表
    return "\n".join([
        capsule(M, 200, 300, 90, "研究目标"),
        brace(M + 332, 232, 424, span=26),             # 跨住右侧三条
        *[txt(M + 430, 272 + i * 74, f"▸ 子目标 {i+1}（须带证伪条件）",
              size=PX["body"]) for i in range(3)],
        ph(M, 400, CW, 400, "下方：证据 / 检索结果 / 计划"),
    ])


def _v28():   # 配方 28 · 结论色带 →大箭头→ 结论色带
    MID = W // 2
    return "\n".join([
        band(M, 120, CW, "证据：数据结论（措辞不得超出数据支持范围）", h=140),
        arrow(MID, 275, MID, 424),
        txt(MID + 24, 350, "所以", size=PX["body"], fill=C["weak"]),
        band(M, 440, CW, "推论：因此……（须与证据分级，不可写成事实）", h=140, fill=C["red"]),
        ph(M, 620, CW, 180, "证伪条件 / 待验证事项"),
    ])


def _v29():   # ⭐ 新 · 配方 30｜带表头小卡片（配方 5 的实现形态；模板内容区主力）
    return "\n".join([
        txt(M, 108, "把一个「大表格」拆成 2–4 个带表头的小卡片——",
            size=PX["body"], fill=C["weak"]),
        cards_row(140, 300, [
            ("表头一", ["内容行一", "内容行二", "内容行三"]),
            ("表头二", ["内容行一", "内容行二", "内容行三"]),
            ("表头三", ["内容行一", "内容行二", "内容行三"]),
        ]),
        cards_row(470, 300, [
            ("表头四", ["内容行一", "内容行二", "内容行三"]),
            ("表头五", ["内容行一", "内容行二", "内容行三"]),
        ]),
    ])


def _v30():   # ⭐ 新 · 配方 31｜结尾页大标语（PX["statement"] = 147px，模板最大档）
    return statement("感谢各位专家", "请批评指正")


def _v32():   # ⭐ 新 · 配方 32｜目录页（开篇导航）
    """左侧主色块竖排「目录」+ 右侧条目行（序号方块 / 章节名 / 一句话 + 右侧页码）。

    与配方 1 的分工：
      · **配方 1 章节过渡页** = 每次过场**重播**整份提纲，只点亮当前位置
      · **本配方** = 开篇**一次性总览**，4 条同级并列，无当前位置高亮

    设计约束（有意为之，勿误改）：
      · 章节名用 `main`（8.71:1）、说明用 `txt`（12.63:1）——
        **不用 `weak`**：`weak #7A8698` 在白底仅 3.69:1，`ppt_check` 第 J 项会报。
      · 层次靠**字号 40/23 + 颜色 main/txt**做，不靠字重
        （PPTX 端字重只有 2 档，见 `ppt_style.WEIGHT`）。
    """
    LW = 300                                   # 左侧主色块宽
    RW = CW - LW - GAP                         # 右侧条目区宽
    RX = M + LW + GAP
    items = [
        ("01", "研究背景与立论依据", "问题从哪来、为什么值得做", "03"),
        ("02", "证据基础与检索口径", "查了什么、查到什么、边界在哪", "07"),
        ("03", "研究设计与主要结果", "怎么做、得到什么", "12"),
        ("04", "局限、待验证与下一步", "哪些还不能下结论", "16"),
    ]
    ROWH = 660 // len(items)                   # 每行等分（4 行 → 165）
    LEAD_END = W - M - 60                      # 引线右端（给页码留出空间）
    s = [rect(M, 110, LW, 660, fill=C["main"]),
         vtext(M + LW // 2, 368, "目　录", size=PX["section"],
               fill="#FFFFFF", weight=700)]
    for i, (num, name, desc, pg) in enumerate(items):
        y = 110 + i * ROWH
        cy = y + ROWH // 2                     # 行垂直中心
        # 目录引线起点：**紧接章节名末尾**（按实测字宽算，不写死）
        # ⚠️ 起点写死时，引线看起来像一段孤立装饰，而不是「连接标题与页码」。
        #    各行标题不等长 → 起点本就该不同，这正是 TOC 的惯例。
        lx = RX + 100 + estimate_text_width(name, PX["section"], 700) + 20
        s += [rect(RX, cy - 32, 64, 64, fill=C["main"]),
              txt(RX + 32, cy + 12, num, size=PX["body"], fill="#FFFFFF",
                  weight=700, anchor="middle"),
              txt(RX + 100, cy - 4, esc(name), size=PX["section"],
                  fill=C["main"], weight=700),
              txt(RX + 100, cy + 38, esc(desc), size=PX["caption"], fill=C["txt"]),
              rect(lx, cy - 12, LEAD_END - lx, 1.2, fill=C["edge"]),
              txt(W - M, cy + 12, pg, size=PX["body"], fill=C["main"],
                  weight=700, anchor="end")]
        if i:                                  # 行间细分隔线（首行不画）
            s.append(rect(RX, y, RW, 1.5, fill=C["edge"]))
    return "\n".join(s)


VARIANTS = {
    "配方01_章节过渡页":   ("（当前章节名）", "配方 1｜章节过渡页：每次过场重播整份提纲，只点亮当前位置。6/6 deck 采用。", _v01()),
    "配方02_左框箭头右图": ("屏状核：位置、体积与连接", "配方 2｜左框 →箭头→ 右图。箭头端点咬在框边；图紧贴它支持的那一条。", _v02()),
    "配方04_表格引出线":   ("各脑区受体分布", "配方 4｜表格 + 引出线标注。引出线落在具体单元格边界，被标注格文字同时变红。", _v04()),
    "配方09_并列汇聚":     ("按脑区分析 · 屏状核上直接测到", "配方 9｜并列 → 汇聚。上游横排=同层级，箭头=汇聚，下游用实心色块加重。", _v09()),
    "配方10_三栏色带表头": ("三条路线对比", "配方 10｜三栏等宽 + 色带表头 + 递进线。三栏之间要有递进关系。", _v10()),
    "配方12_左右对照":     ("四种说法与反证", "配方 12｜左右双栏对照。两栏结构完全对称，只换内容——差异自己跳出来。", _v12()),
    "配方17_数据卡片":     ("关键数值", "配方 17｜数据卡片。6/6 deck 采用。大号彩色数值 + 小号深灰标签，常 2×2 或 1×4。", _v17()),
    "配方18_数据库截图":   ("交叉空白的规模与唯一的交集证据", "配方 18｜数据库截图 + 红框 + 大数字。把「我确实查过」升级为一手证据。", _v18()),
    "配方25_胶囊花括号":   ("切入点与一个可证伪的假设", "配方 25｜胶囊节点 + 花括号 + ▸ 列表。把总目标分解成若干条。", _v25()),
    "配方28_证据到推论":   ("从证据到推论", "配方 28｜色带 →大箭头→ 色带。左=证据，箭头=「所以」，右=推论。措辞必须分级。", _v28()),

    # ⭐ 2026-09-22 新增两页（依 7 套模板实测）—— 编号接配方库现有 1–29 之后
    "配方30_带表头卡片":   ("带表头小卡片", "配方 30｜⭐ 把「一个大表格」拆成 2–4 个带表头小卡片。模板内容区的主力形态，"
                                        "也是元素密度的来源（模板 6/7 套图片里 71–85% 是 <3% 面积的小件）。", _v29()),
    "配方31_结尾页标语":   ("（结尾页）", "配方 31｜⭐ 结尾页大标语。模板实测**结尾页字号比封面还大**"
                                        "（117@1280 > 97@1280 = 146px@1600），此前本库无此档。", _v30()),

    # ⭐ 2026-09-26 新增（补长期缺口：全库既无目录页配方、也无目录页骨架）
    "配方32_目录页":       ("目录", "配方 32｜⭐ 目录页（开篇一次性总览）。"
                                  "与配方 1 的分工：配方 1 是**每次过场重播**提纲+高亮当前位置，"
                                  "本配方是**开篇总览**、无当前位置。右侧页码须按实际页序改。", _v32()),
}

#: 不要标题栏与页脚的整页骨架（封面 / 结尾页）
NO_CHROME = {"配方31_结尾页标语"}


def build(only=None):
    """生成骨架。

    ⚠️ **2026-09-26 修**：此前 `only` 只用在**返回值**的过滤上，
    写入循环照样跑满 —— 于是 `--only 配方32` 会**静默重写全部 21 个骨架**，
    与"只生成含该串的"这句承诺不符。**一个不照字面执行的开关比没有开关更危险**
    （有人以为安全地跑了一次局部生成，实际全库被覆盖）。
    现在 `only` 在**写入前**就跳过，不再写不该写的文件。
    """
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(os.path.join(OUT, "_归档"), exist_ok=True)
    made = []
    for k, (name, note, body) in BASES.items():
        fn = f"骨架_{k}_{name}.svg"
        if only and only not in fn:
            continue
        open(os.path.join(OUT, fn), "w", encoding="utf-8").write(slide(name, body, num=k, note=note))
        made.append((f"基座 {k}", fn))
    for base, (title, note, body) in VARIANTS.items():
        fn = f"{base}.svg"
        if only and only not in fn:
            continue
        open(os.path.join(OUT, fn), "w", encoding="utf-8").write(
            slide(title, body, note=note, cover=base in NO_CHROME))
        made.append((base.split("_")[0], fn))
    return made


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="只生成文件名含该串的")
    a = ap.parse_args()
    items = build(a.only)
    print(f"✅ 生成 {len(items)} 个骨架 → {OUT}\n")
    for tag, fn in items:
        print(f"  {tag:<10} {fn}")
