# -*- coding: utf-8 -*-
"""pptx_shapes.py —— 模板拆解 · pptx 前端（零依赖）

【干什么】
    直接读 `.pptx`（其实是个 zip），出与 `tpl_reader.py` 同一套形状级记录。
    有了本文件，模板拆解不再需要 ppt-master——`zipfile` + `ElementTree` 就够。

【为什么可以自己读】
    模板拆解只要三样：**几何、形状族、颜色角色**。
    ppt-master 转 SVG 时丢掉的阴影、斜向渐变、渐变 stop 顺序、字体文件，本工具一样都用不上。
    反过来，直接从 OOXML 读还能多拿到三样：
      · `a:tailEnd/@type`  箭头端，不用从 SVG 的 `<marker>` 反推
      · `a:prstDash/@val`  虚线样式，不用看 `stroke-dasharray`
      · 表格 / 图表 / SmartArt 分得开，不用都叫 `graphic-frame`

【两处要小心】
    ① 组合 `p:grpSp` 的子形状坐标在组自己的坐标系里，要按 `chOff` / `chExt` 换算。
    ② 没有 `a:xfrm` 的占位符继承母版的帧。本文件**不求继承**——
       母版与版式形状另走一遍，标 `scope=master` / `layout`，
       由 `tpl_reader` 分到 INHERIT 桶。ppt-master 的做法相同。

【单位】
    坐标 `a:off/@x`、`a:ext/@cx` 是 EMU（914400 EMU = 1 英寸）。
    字号 `a:rPr/@sz` 是 1/100 pt。
    线宽 `a:ln/@w` 是 EMU。
    一律折算到本库画布 1600×900：`k = 1600 / sldSz.cx`。
"""
from __future__ import annotations

import os
import posixpath
import re
import sys
import zipfile
from xml.etree import ElementTree as ET

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

W, H = 1600, 900
EMU_PER_PT = 12700

A = "http://schemas.openxmlformats.org/drawingml/2006/main"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
C = "http://schemas.openxmlformats.org/drawingml/2006/chart"
REL = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"a": A, "p": P, "r": R, "c": C}

#: 版式里那些「不是内容」的母版件——页码、日期、页脚
FOOTER_PH = {"sldNum", "dt", "ftr"}


def _q(prefix: str, tag: str) -> str:
    return f"{{{NS[prefix]}}}{tag}"


def _tag(el) -> str:
    t = el.tag
    return t.split("}", 1)[-1] if isinstance(t, str) else ""


def _num(v, default=None):
    if v is None:
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


# ══════════════════════════════════════════════════════════
#  OPC：找部件、走关系
# ══════════════════════════════════════════════════════════
class _Pkg:
    """一个 .pptx 包。按需解析 XML，结果缓存。"""

    def __init__(self, path):
        self.zf = zipfile.ZipFile(path)
        self._xml: dict[str, ET.Element | None] = {}
        self._rels: dict[str, dict[str, str]] = {}

    def close(self):
        self.zf.close()

    def names(self) -> list[str]:
        return self.zf.namelist()

    def xml(self, part: str):
        if part in self._xml:
            return self._xml[part]
        node = None
        try:
            node = ET.fromstring(self.zf.read(part))
        except (KeyError, ET.ParseError):
            node = None
        self._xml[part] = node
        return node

    def rels(self, part: str) -> dict[str, dict]:
        """部件的关系表 → {rId: {"target": 包内路径, "type": 关系类型, "external": bool}}"""
        if part in self._rels:
            return self._rels[part]
        d, f = posixpath.split(part)
        rp = posixpath.join(d, "_rels", f + ".rels")
        out: dict[str, dict] = {}
        node = self.xml(rp)
        if node is not None:
            for rel in list(node):
                if _tag(rel) != "Relationship":
                    continue
                target = rel.get("Target") or ""
                ext = rel.get("TargetMode") == "External"
                out[rel.get("Id")] = {
                    "target": target if ext else _norm(d, target),
                    "type": rel.get("Type") or "",
                    "external": ext,
                }
        self._rels[part] = out
        return out

    def target(self, part: str, rid: str) -> str | None:
        rel = self.rels(part).get(rid)
        return rel["target"] if rel else None

    def rel_by_type(self, part: str, suffix: str) -> str | None:
        """按关系类型的尾段找目标，如 `/slideLayout` / `/slideMaster`。"""
        for rel in self.rels(part).values():
            if rel["type"].endswith(suffix) and not rel["external"]:
                return rel["target"]
        return None


def _norm(base: str, target: str) -> str:
    if target.startswith("/"):
        return target.lstrip("/")
    return posixpath.normpath(posixpath.join(base or "", target))


# ══════════════════════════════════════════════════════════
#  主题色
# ══════════════════════════════════════════════════════════
def _theme_colors(pkg: _Pkg) -> dict[str, str]:
    """`ppt/theme/theme1.xml` 的 `a:clrScheme` → {dk1: #RRGGBB, accent1: …}。

    `dk1` / `lt1` 常写成 `a:sysClr`，颜色在 `@lastClr` 上，不在 `@val` 上。
    """
    for n in pkg.names():
        if not re.fullmatch(r"ppt/theme/theme\d+\.xml", n):
            continue
        node = pkg.xml(n)
        if node is None:
            continue
        scheme = node.find(f".//{_q('a', 'clrScheme')}")
        if scheme is None:
            continue
        out = {}
        for slot in list(scheme):
            name = _tag(slot)
            for c in list(slot):
                if _tag(c) == "srgbClr" and c.get("val"):
                    out[name] = "#" + c.get("val").upper()
                    break
                if _tag(c) == "sysClr" and c.get("lastClr"):
                    out[name] = "#" + c.get("lastClr").upper()
                    break
        if out:
            # ⚠️ `a:schemeClr val="bg1" / "tx1" / "bg2" / "tx2"` **不是色板槽位**，
            #    要走母版 `p:clrMap` 折一层。不解的话这些配色全落成 unresolved
            #    ——学术答辩-01 的 160 个图标填的就是 `bg1`，画出来是空的。
            for m in pkg.names():
                if "slideMaster" not in m or not m.endswith(".xml"):
                    continue
                node = pkg.xml(m)
                if node is None:
                    continue
                cmap = node.find(f".//{_q('p', 'clrMap')}")
                if cmap is not None:
                    for alias in ("bg1", "tx1", "bg2", "tx2"):
                        slot = cmap.get(alias)
                        if slot and slot in out:
                            out[alias] = out[slot]
                    break
            return out
    return {}


def _deck_default_sz(pkg: _Pkg) -> int | None:
    """`p:presentation.xml` 的 `p:defaultTextStyle` 一级字号（1/100 pt）。

    文字没有任何显式字号时，规范让演示文稿级的这套默认样式兜底。
    """
    node = pkg.xml("ppt/presentation.xml")
    if node is None:
        return None
    lvl = node.find(f".//{_q('p', 'defaultTextStyle')}/{_q('a', 'lvl1pPr')}")
    if lvl is None:
        return None
    d = lvl.find(_q("a", "defRPr"))
    return _num(d.get("sz")) if d is not None else None


def _color_holder(holder, theme: dict[str, str], notes: list[str]) -> str | None:
    """从 `a:solidFill` / `a:rPr` / `a:ln` 这类容器里取第一个颜色。

    → `#RRGGBB` / `none`（noFill）/ `gradient`（gradFill）/ `unresolved`（查不到主题色）
    """
    if holder is None:
        return None
    for c in list(holder):
        t = _tag(c)
        if t == "noFill":
            return "none"
        if t == "gradFill":
            return "gradient"
        if t in ("srgbClr", "schemeClr", "sysClr", "prstClr", "scrgbClr"):
            return _one_color(c, theme, notes)
    # 颜色常包在 `a:solidFill` 里，再往下找一层
    solid = holder.find(_q("a", "solidFill"))
    if solid is not None:
        for c in list(solid):
            return _one_color(c, theme, notes)
    return None


def _hsl_of(hex_colour: str) -> tuple:
    h = hex_colour.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    mx, mn = max(r, g, b), min(r, g, b)
    ll = (mx + mn) / 2
    if mx == mn:
        return 0.0, 0.0, ll
    d = mx - mn
    s = d / (2 - mx - mn) if ll > 0.5 else d / (mx + mn)
    if mx == r:
        hh = ((g - b) / d) % 6
    elif mx == g:
        hh = (b - r) / d + 2
    else:
        hh = (r - g) / d + 4
    return hh * 60, s, ll


def _hex_of(h: float, s: float, l: float) -> str:
    if s <= 0:
        v = round(l * 255)
        return f"#{v:02X}{v:02X}{v:02X}"
    q = l * (1 + s) if l < 0.5 else l + s - l * s
    p = 2 * l - q
    out = []
    for t in (h / 360 + 1 / 3, h / 360, h / 360 - 1 / 3):
        t = t % 1.0
        if t < 1 / 6:
            v = p + (q - p) * 6 * t
        elif t < 1 / 2:
            v = q
        elif t < 2 / 3:
            v = p + (q - p) * (2 / 3 - t) * 6
        else:
            v = p
        out.append(round(min(1.0, max(0.0, v)) * 255))
    return "#%02X%02X%02X" % tuple(out)


def _modulate(colour: str, mods, notes: list[str]) -> str:
    """`lumMod` / `lumOff` / `shade` / `tint` → 提亮或压暗后的颜色。

    ⚠️ 这几个修饰符把主题色拉出一族浓淡（深蓝 → 浅蓝底、深蓝 → 更深的条）。
       不读的话每一个浓淡都当成基色。实测 6 份模板：`lumMod` 1444 个、
       `shade` 963 个、`lumOff` 546 个。
       浙大蓝那份结论页的浅蓝底是 `lumMod 20% + lumOff 80%`，
       不读就记成深蓝 `#003F88`，统一配色后整块变成饱和蓝，块上的字读不了。
    """
    h, s, l = _hsl_of(colour)
    for m in mods:
        v = (_num(m.get("val")) or 0) / 100000.0
        t = _tag(m)
        if t in ("lumMod", "shade"):
            l *= v
        elif t == "lumOff":
            l += v
        elif t == "tint":
            l = l * (1 - v) + v
        l = min(1.0, max(0.0, l))
    return _hex_of(h, s, l)


def _one_color(c, theme: dict[str, str], notes: list[str]) -> str:
    t = _tag(c)
    if t == "srgbClr":
        return "#" + (c.get("val") or "").upper()
    if t == "sysClr":
        return "#" + (c.get("lastClr") or c.get("val") or "").upper()
    if t == "schemeClr":
        name = c.get("val") or ""
        mods = [x for x in list(c)
                if _tag(x) in ("lumMod", "lumOff", "shade", "tint")]
        if mods and "color-approx" not in notes:
            notes.append("color-approx")
        if name in theme:
            base = theme[name]
            return _modulate(base, mods, notes) if mods else base
        notes.append("theme-unresolved")
        return "unresolved"
    if t == "prstClr":
        return {"black": "#000000", "white": "#FFFFFF"}.get(c.get("val") or "", "unresolved")
    return "unresolved"


def _grad_stops(gf, theme, notes) -> dict | None:
    """`a:gradFill` → {"stops": [[pos, "#RRGGBB"], …], "ang": 度}。取首末两站。

    `a:lin/@ang` 是 1/60000 度，0 度指向右、顺时针增（OOXML 的约定）。
    """
    if gf is None:
        return None
    stops = []
    for gs in gf.findall(f".//{_q('a', 'gs')}"):
        pos = _num(gs.get("pos"))
        col = _color_holder(gs, theme, notes)
        if pos is not None and col and col.startswith("#"):
            stops.append([pos / 100000.0, col])
    if len(stops) < 2:
        return None
    if len(stops) > 2:
        notes.append("gradient-approximated")
    lin = gf.find(_q("a", "lin"))
    ang = _num(lin.get("ang")) if lin is not None else 0
    return {"stops": [stops[0], stops[-1]], "ang": (ang or 0) / 60000.0}


def _alpha_of(parent, tag: str) -> float:
    """`<tag><…><a:alpha val=…>` → 0–1。没写就 1.0。

    ⚠️ 半透明填充很常见。7 份模板实测 **821 处** `a:alpha`。
       全按不透明画的话，一个 4% 透明度的浅底会画成饱和红——
       国自然6红色 p11 那三张卡片就是这么从「白底红字」变成「红底红字」的，
       整页的轻重完全反过来。
    """
    if parent is None:
        return 1.0
    node = parent.find(_q("a", tag))
    if node is None:
        return 1.0
    a = node.find(f".//{_q('a', 'alpha')}")
    if a is None:
        return 1.0
    v = _num(a.get("val"))
    return 1.0 if v is None else v / 100000.0


def _style_refs(style, theme, notes) -> tuple[str | None, str | None]:
    """`p:style` → (填充色, 描边色)。

    多数 `rect` 没有显式 `a:solidFill`，颜色来自 `a:fillRef` 指的主题色。
    只读显式填充会让这些形状的填充全落成空，随后被 A6 虚线框判据误收。
    """
    if style is None:
        return None, None
    fill = style.find(_q("a", "fillRef"))
    ln = style.find(_q("a", "lnRef"))
    fill_c = _color_holder(fill, theme, notes) if fill is not None else None
    ln_c = _color_holder(ln, theme, notes) if ln is not None else None
    if fill_c or ln_c:
        notes.append("from-style-ref")
    return fill_c, ln_c


# ══════════════════════════════════════════════════════════
#  几何
# ══════════════════════════════════════════════════════════
def _xfrm_el(el, holder_tag: str):
    """找到形状的 `a:xfrm`（或 graphicFrame 的 `p:xfrm`）元素本身。"""
    holder = (el.find(_q("p", holder_tag)) if not holder_tag.startswith("a:")
              else el.find(_q("a", holder_tag)))
    if holder is None:
        holder = el
    xf = holder if _tag(holder) == "xfrm" else holder.find(_q("a", "xfrm"))
    if xf is None:
        xf = holder.find(_q("p", "xfrm"))
    return xf


def _flips_of(el, holder_tag: str) -> tuple:
    """`a:xfrm/@flipH` / `@flipV`。→ (flipH, flipV)

    ⚠️ 翻转要读。折线连接符的方向靠它——`bentConnector3` 的拐点在哪一侧
    完全由 flipH/flipV 决定。不读的话有一半折线会画成镜像。
    预设多边形（人字箭头、旗标、梯形）同理。
    """
    xf = _xfrm_el(el, holder_tag)
    if xf is None:
        return False, False
    return (xf.get("flipH") in ("1", "true"), xf.get("flipV") in ("1", "true"))


def _xfrm_of(el, holder_tag: str):
    """取 `a:xfrm`（或 graphicFrame 的 `p:xfrm`）。→ (x, y, cx, cy, rot) 或 None

    ⚠️ `p:graphicFrame` 的帧**就是** `p:xfrm` 本身，不是它的子元素。
    旧写法找到 `p:xfrm` 后又去里面找 `a:xfrm`，找不到 → 返回 None →
    表格与图表的坐标全落成 `0,0 0×0`，主内容是表格的页连行列都算不出来。
    """
    xf = _xfrm_el(el, holder_tag)
    if xf is None:
        return None
    off = xf.find(_q("a", "off"))
    ext = xf.find(_q("a", "ext"))
    if off is None or ext is None:
        return None
    return (_num(off.get("x"), 0.0), _num(off.get("y"), 0.0),
            _num(ext.get("cx"), 0.0), _num(ext.get("cy"), 0.0),
            _num(xf.get("rot"), 0.0))


def _child_transform(parent, el):
    """组合 → 子形状的坐标变换。

    组在自己的坐标系里有一个矩形 `off` / `ext`，子形状的坐标落在另一个矩形
    `chOff` / `chExt` 里。换算：`X = off + (x - chOff) * ext / chExt`。

    → (fx, fy, sx, sy)：`X = fx + x * sx`
    """
    g = el.find(_q("p", "grpSpPr"))
    if g is None:
        return parent
    xf = g.find(_q("a", "xfrm"))
    if xf is None:
        return parent
    off, ext = xf.find(_q("a", "off")), xf.find(_q("a", "ext"))
    coff, cext = xf.find(_q("a", "chOff")), xf.find(_q("a", "chExt"))
    if None in (off, ext, coff, cext):
        return parent
    ecx, ecy = _num(ext.get("cx"), 0.0), _num(ext.get("cy"), 0.0)
    ccx, ccy = _num(cext.get("cx"), 0.0), _num(cext.get("cy"), 0.0)
    if ccx == 0 or ccy == 0:
        return parent
    gsx, gsy = ecx / ccx, ecy / ccy
    ox, oy = _num(off.get("x"), 0.0), _num(off.get("y"), 0.0)
    cox, coy = _num(coff.get("x"), 0.0), _num(coff.get("y"), 0.0)
    fx, fy, sx, sy = parent
    return (fx + (ox - cox * gsx) * sx, fy + (oy - coy * gsy) * sy, gsx * sx, gsy * sy)


def _apply(t, x, y, w, h):
    fx, fy, sx, sy = t
    return (fx + x * sx, fy + y * sy, w * sx, h * sy)


IDENTITY = (0.0, 0.0, 1.0, 1.0)


# ══════════════════════════════════════════════════════════
#  占位符继承（只求帧，不求样式）
# ══════════════════════════════════════════════════════════
def _ph_key(el):
    """`p:ph` 的分类键。type 默认 `body`，idx 默认 `0`。"""
    ph = el.find(f".//{_q('p', 'ph')}")
    if ph is None:
        return None
    return (ph.get("type") or "body", str(ph.get("idx") or "0"))


def _ph_index(pkg: _Pkg, part: str) -> dict:
    """某个版式 / 母版里所有占位符的帧 → {(type, idx): (x,y,cx,cy,rot)}"""
    out: dict = {}
    node = pkg.xml(part)
    if node is None:
        return out
    tree = node.find(f".//{_q('p', 'spTree')}")
    if tree is None:
        return out
    for sp in tree.iter(_q("p", "sp")):
        key = _ph_key(sp)
        if key is None:
            continue
        fr = _xfrm_of(sp, "spPr")
        if fr is not None:
            out.setdefault(key, fr)
    return out


def _ph_lookup(index: dict, key):
    """按 (type, idx) 查，查不到就退到同 type 的任意一个。"""
    if not index or key is None:
        return None
    if key in index:
        return index[key]
    for (t, _i), fr in index.items():
        if t == key[0]:
            return fr
    return None


# ══════════════════════════════════════════════════════════
#  文字
# ══════════════════════════════════════════════════════════
def _run_props(rPr, theme, notes):
    if rPr is None:
        return None, False, None
    sz = _num(rPr.get("sz"))
    bold = (rPr.get("b") or "") in ("1", "true")
    col = _color_holder(rPr, theme, notes)
    return sz, bold, col


def _para_def_sz(p, lst, deck_sz):
    """一段取不到显式字号时的退路，按 OOXML 的解析顺序。

    ⚠️ 实测（2026-10-15，`模板源/9.开题答辩PPT`）：北大红 25%、北大墨绿 31%
    的文字形状**在 XML 里真的没有字号**——run 没有 `@sz`、没有 `endParaRPr`、
    也没有占位符。字号是继承来的，不是读取器漏读（逐件对过 XML）。

    退路顺序：`a:endParaRPr/@sz` → `a:pPr/a:defRPr/@sz` →
    `a:lstStyle/lvlNpPr/a:defRPr/@sz` → 演示文稿级 `p:defaultTextStyle`。

    ⚠️ **最后一条可能与形状自己的证据冲突**：北大墨绿 p2 目录六项里五项写
    `sz="2400"`、第一项没写；按 deck 默认值会读成 1800，画出来比其余五项小。
    两条线索互相矛盾，本函数按规范取 deck 默认值，**但把来源记进 notes**，
    报告里能逐件查到哪些字号是推出来的。数字不猜，来源不藏。
    """
    end = p.find(_q("a", "endParaRPr"))
    if end is not None and _num(end.get("sz")):
        return _num(end.get("sz")), "size-endpara"
    pPr = p.find(_q("a", "pPr"))
    if pPr is not None:
        d = pPr.find(_q("a", "defRPr"))
        if d is not None and _num(d.get("sz")):
            return _num(d.get("sz")), "size-ppr-defrpr"
        if lst is not None:
            lvl = int(_num(pPr.get("lvl")) or 0) + 1
            node = lst.find(_q("a", f"lvl{lvl}pPr"))
            if node is None:
                node = lst.find(_q("a", "lvl1pPr"))
            if node is not None:
                d = node.find(_q("a", "defRPr"))
                if d is not None and _num(d.get("sz")):
                    return _num(d.get("sz")), "size-lvlstyle"
    if deck_sz:
        return deck_sz, "size-deck-default"
    return None, None


def _text_of(txBody, theme, notes, deck_sz=None):
    """→ (整块文字, runs, 最大字号（1/100 pt）, 对齐)"""
    if txBody is None:
        return "", [], 0.0, None
    runs, sizes, algn = [], [], None
    paras = txBody.findall(_q("a", "p"))
    lst = txBody.find(_q("a", "lstStyle"))
    for p in paras:
        pPr = p.find(_q("a", "pPr"))
        if algn is None and pPr is not None and pPr.get("algn"):
            algn = pPr.get("algn")
        for r in list(p):
            if _tag(r) not in ("r", "fld"):
                continue
            t = r.find(_q("a", "t"))
            s = (t.text or "") if t is not None else ""
            if not s:
                continue
            sz, bold, col = _run_props(r.find(_q("a", "rPr")), theme, notes)
            runs.append({"text": s, "size": sz, "color": col, "bold": bold})
            if sz:
                sizes.append(sz)
    if runs and not sizes:
        for p in paras:
            sz, code = _para_def_sz(p, lst, deck_sz)
            if sz:
                sizes.append(sz)
                if code not in notes:
                    notes.append(code)
                break
    text = "".join(r["text"] for r in runs)
    return text, runs, (max(sizes) if sizes else 0.0), algn


# ══════════════════════════════════════════════════════════
#  一个形状
# ══════════════════════════════════════════════════════════
def _walk(el, ctx, transform, out, gid=None):
    """递归走 spTree。ctx 里带 deck / page / scope / k / theme / stats。"""
    tag = _tag(el)
    theme, notes_all = ctx["theme"], ctx["stats"]

    if tag in ("nvGrpSpPr", "grpSpPr", "nvSpPr", "spPr", "nvPicPr", "blipFill",
               "nvCxnSpPr", "nvGraphicFramePr", "txBody", "style"):
        return

    if tag == "grpSp":
        notes = ["group"]
        ctx["stats"]["group"] += 1
        g = _record(el, ctx, transform, kind="group", notes=notes,
                    holder="grpSpPr", frame_el="grpSpPr")
        out.append(g)
        child = _child_transform(transform, el)
        for c in list(el):
            _walk(c, ctx, child, out, g.get("sid"))
        return

    if tag in ("sp", "cxnSp", "pic"):
        kind = {"sp": "shape", "cxnSp": "connector", "pic": "picture"}[tag]
        _emit_leaf(el, ctx, transform, out, kind, gid)
        return

    if tag == "graphicFrame":
        _emit_graphic_frame(el, ctx, transform, out, gid)
        return

    for c in list(el):
        _walk(c, ctx, transform, out, gid)


def _record(el, ctx, transform, kind, notes, holder="spPr", frame_el=None,
            gid=None) -> dict:
    frame_el = frame_el or holder
    xf = _xfrm_of(el, frame_el)
    inherited = False
    if xf is None:
        # 占位符没有自己的 `a:xfrm` 时，帧写在版式或母版里。只求帧，不求样式。
        fr = _ph_lookup(ctx.get("ph_index") or {}, _ph_key(el))
        if fr is not None:
            xf, inherited = fr, True
    if xf is None:
        ctx["stats"]["no-frame"] += 1
        notes.append("no-frame")
        x, y, w, h, rot = 0.0, 0.0, 0.0, 0.0, 0.0
    else:
        x, y, w, h, rot = xf
    if inherited:
        notes.append("frame-from-layout")
    X, Y, Wd, Hd = _apply(transform, x, y, w, h)
    # ⚠️ **旋转要在这里折掉**，让 x/y/w/h 一律是「画出来占的那块地方」。
    #
    # 起因：国自然那 6 份 deck 里旋转形状是 **0 个**，答辩模板里 6–69 个。
    # 也就是说「没有旋转」是那批提炼成果的隐含前提。
    # 不折的话，一个 90° 的旗标（记 176×459）实际占的是 459×176，
    # 它会横跨两行，把整页的行切分搅成一团。
    #
    # 折掉之后，下游（分格、判据、渲染）都不用再记得这件事；
    # 原始角度仍留在 `rot` 里供参考。
    if rot:
        if round(rot / 60000.0) % 180 == 90:
            cx, cy = X + Wd / 2, Y + Hd / 2
            X, Y, Wd, Hd = cx - Hd / 2, cy - Wd / 2, Hd, Wd
    kx, ky = ctx["kx"], ctx["ky"]
    sh = {}
    sh.update(deck=ctx["deck"], page=ctx["page"], sid=el.get("id"),
              kind=kind, scope=ctx["scope"], name=None, prst=None, rot=rot or None,
              flip=list(_flips_of(el, frame_el)),
              x=X * kx, y=Y * ky, w=Wd * kx, h=Hd * ky,
              av_adj=None, rx=None, fill=None, fill_role=None,
              stroke=None, stroke_role=None, stroke_w=0.0, dash=None, head="none",
              text="", runs=[], size_px=0.0, align=None, anchor=None, media=None,
              from_group=transform != IDENTITY, group_id=gid,
              # ⚠️ 传的是**同一个列表**，不是副本——`_emit_leaf` 之后还会往里
              #    追加 `from-style-ref` / `theme-unresolved` / `gradient` 这类标记。
              #    传副本会让这些标记全部丢掉。
              bucket=None, notes=notes, unsupported=False,
              part=ctx.get("part"), layout_part=ctx.get("layout_part"),
              master_part=ctx.get("master_part"),
              placeholder=_ph_key(el) is not None)
    nv = el.find(f".//{_q('p', 'cNvPr')}")
    if nv is not None:
        sh["sid"] = nv.get("id") or sh["sid"]
        sh["name"] = nv.get("name")
        if kind == "group":
            sh["group_id"] = nv.get("id")
    if abs(transform[2] - 1.0) > 0.02 and "group-scaled" not in notes:
        notes.append("group-scaled")
    return sh


def _cust_geom(holder) -> dict | None:
    """`a:custGeom` → 路径数据（在路径自己的坐标空间里）。

    → {"w": 路径空间宽, "h": 路径空间高, "d": "M… L… C… Z"} 或 None

    坐标空间到形状矩形的换算放在渲染侧做：`x_svg = 形状x + pt.x / w × 形状宽`。
    这里只出路径数据，不折进画布坐标——路径可能被同一形状重复使用。

    ⚠️ 只认 `a:pt` 上的**字面数字**。实测 30 万个坐标点里没有一条写成
    `x="T0"`（引用 `a:gdLst` 的公式），所以不用求值公式。
    `a:arcTo` 在实测样本里没出现过；真碰上就当不支持，记在 notes 里。
    """
    cg = holder.find(_q("a", "custGeom"))
    if cg is None:
        return None
    paths = cg.findall(f".//{_q('a', 'path')}")
    if not paths:
        return None
    # ⚠️ `a:path/@w` 与 `@h` 可以只给一个、甚至一个都不给。
    #    按 ECMA-376，缺省时取**形状自己的 extent**。
    #    不兜这一下，「任意多边形」那类只给 `h` 的直条会被整件丢掉——
    #    实测学术答辩-01 有三件（都是不带 `@w` 的竖线）。
    xf = holder.find(_q("a", "xfrm"))
    ext = xf.find(_q("a", "ext")) if xf is not None else None
    dw = _num(ext.get("cx")) if ext is not None else None
    dh = _num(ext.get("cy")) if ext is not None else None
    pw = _num(paths[0].get("w")) or dw or 0
    ph = _num(paths[0].get("h")) or dh or 0
    if not pw or not ph:
        return None
    segs, unsupported = [], []
    for p in paths:
        for op in list(p):
            tag = _tag(op)
            if tag == "close":
                segs.append("Z")
                continue
            if tag == "arcTo":
                # ⚠️ 认不出来就**出声**，不静默少画一段。
                #    实测 124 份模板里 `a:arcTo` 出现 0 次，所以先不实现；
                #    真碰上会记进 `unsupported`，由调用侧写进 notes。
                unsupported.append("arcTo")
                continue
            pts = [( _num(q.get("x")), _num(q.get("y")) )
                   for q in op.findall(_q("a", "pt"))]
            if tag == "moveTo" and len(pts) == 1:
                segs.append(f"M{pts[0][0]:.1f},{pts[0][1]:.1f}")
            elif tag == "lnTo" and len(pts) == 1:
                segs.append(f"L{pts[0][0]:.1f},{pts[0][1]:.1f}")
            elif tag == "cubicBezTo" and len(pts) == 3:
                segs.append("C" + " ".join(f"{a:.1f},{b:.1f}" for a, b in pts))
            elif tag == "quadBezTo" and len(pts) == 2:
                segs.append("Q" + " ".join(f"{a:.1f},{b:.1f}" for a, b in pts))
    if not segs:
        return None
    out = {"w": pw, "h": ph, "d": " ".join(segs)}
    if unsupported:
        out["unsupported"] = sorted(set(unsupported))
    return out


def _emit_leaf(el, ctx, transform, out, kind, gid=None):
    theme, notes = ctx["theme"], []
    sh = _record(el, ctx, transform, kind, notes, gid=gid)
    holder = el.find(_q("p", "spPr"))
    style = el.find(_q("p", "style"))

    prst = None
    if holder is not None:
        pg = holder.find(_q("a", "prstGeom"))
        if pg is not None:
            prst = pg.get("prst")
            av = pg.find(_q("a", "avLst"))
            if av is not None:
                gd = av.find(_q("a", "gd"))
                if gd is not None:
                    m = re.search(r"val\s+(-?\d+)", gd.get("fmla") or "")
                    if m:
                        sh["av_adj"] = int(m.group(1)) / 100000.0
    sh["prst"] = prst
    if prst is None and holder is not None:
        # ⚠️ 预设几何为空的不都是坏形状——**`a:custGeom` 占非文字内容件的 53%**
        #    （实测 126 份 / 63115 件里 33624 件）。图标、箭头、手绘形全在这一类。
        #    路径命令只用到 moveTo / lnTo / cubicBezTo / close，
        #    30 万个坐标点全是字面数字，没有一条引用 gdLst 的公式。
        sh["path"] = _cust_geom(holder)
        if sh["path"] and sh["path"].get("unsupported"):
            notes.append("custgeom-" + "+".join(sh["path"]["unsupported"]))
    if sh["av_adj"] is not None:
        sh["rx"] = sh["av_adj"] * min(abs(sh["w"]), abs(sh["h"]))

    if kind == "picture":
        blip = el.find(f".//{_q('a', 'blip')}")
        if blip is not None:
            rid = blip.get(_q("r", "embed"))
            tgt = ctx["pkg"].target(ctx["part"], rid) if rid else None
            if tgt:
                sh["media"] = posixpath.basename(tgt)
        sh["fill"] = "none"
        sh["stroke"] = "none"
        out.append(sh)
        return

    fill = _color_holder(holder, theme, notes) if holder is not None else None
    f_alpha = _alpha_of(holder, "solidFill")
    stroke, dash, sw, head = None, None, 0.0, "none"
    s_alpha = 1.0
    if holder is not None:
        ln = holder.find(_q("a", "ln"))
        if ln is not None:
            if ln.find(_q("a", "noFill")) is not None:
                stroke = "none"
            else:
                stroke = _color_holder(ln, theme, notes)
                s_alpha = _alpha_of(ln, "solidFill")
            wemu = _num(ln.get("w"))
            if wemu:
                sw = wemu * ctx["kx"]
            pd = ln.find(_q("a", "prstDash"))
            if pd is not None and pd.get("val") not in (None, "solid"):
                dash = pd.get("val")
            ends = []
            for side, name in (("headEnd", "start"), ("tailEnd", "end")):
                e = ln.find(_q("a", side))
                if e is not None and (e.get("type") or "none") != "none":
                    ends.append(name)
            if ends:
                head = "+".join(ends)
        if holder.find(_q("a", "noFill")) is not None:
            fill = "none"
        elif holder.find(_q("a", "gradFill")) is not None:
            fill = "gradient"
            notes.append("gradient")
            ctx["stats"]["gradient"] += 1
            # ⚠️ 只记首末两站与线性角度。实测渐变占非文字内容件的 8.4%，
            #    其中绝大多数是两站。多站按首末两点近似，并在 notes 里标出来。
            #    不记的话，深色渐变背景画不出来——白底白图标，整页看着是空的。
            g = _grad_stops(holder.find(_q("a", "gradFill")), theme, notes)
            if g:
                sh["grad"] = g

    if fill is None or stroke is None:
        sf, sl = _style_refs(style, theme, notes)
        if fill is None:
            fill = sf
        if stroke is None:
            stroke = sl

    sh["fill"] = fill or "none"
    sh["stroke"] = stroke or "none"
    sh["fill_alpha"] = round(f_alpha, 4)
    sh["stroke_alpha"] = round(s_alpha, 4)
    sh["stroke_w"] = sw
    sh["dash"] = dash
    sh["head"] = head

    tx = el.find(_q("p", "txBody"))
    sh["text"], sh["runs"], sz100, sh["align"] = _text_of(
        tx, theme, notes, ctx.get("deck_sz"))
    if tx is not None:
        bp = tx.find(_q("a", "bodyPr"))
        if bp is not None:
            sh["anchor"] = bp.get("anchor")
            # ⚠️ 文字框的内边距要读。实测 1364 个文字框里 412 个（30%）显式设了，
            #    常见值从 `0` 到 `182840` EMU（画布 24px）。差 24px 就是重放时
            #    文字互相压的原因——按框的左边缘起排，比原页偏出去一截。
            #    OOXML 的默认值：左右 91440 EMU（12px），上下 45720 EMU（6px）。
            l = _num(bp.get("lIns"), 91440.0)
            t = _num(bp.get("tIns"), 45720.0)
            r = _num(bp.get("rIns"), 91440.0)
            b = _num(bp.get("bIns"), 45720.0)
            sh["ins"] = [v * ctx["kx"] * transform[2] for v in (l, t, r, b)]
    # `a:rPr/@sz` 是 1/100 pt；先折成 pt 再折成 px，组内缩放一并乘上
    sh["size_px"] = (sz100 / 100.0) * EMU_PER_PT * ctx["kx"] * transform[2]
    out.append(sh)


def _table_grid(el) -> list[list[str]]:
    """`a:tbl` → 二维字符串。行 × 列，空行不留。"""
    rows = []
    for tr in el.iter(_q("a", "tr")):
        row = []
        for tc in tr.findall(_q("a", "tc")):
            row.append("".join((t.text or "") for t in tc.iter(_q("a", "t"))))
        if row:
            rows.append(row)
    return rows


def _chart_data(pkg: _Pkg, part: str, el) -> dict | None:
    """`a:graphicData/c:chart/@r:id` → 图表部件里的类别与各系列数值。

    只取 `c:cat` 与 `c:val` 的缓存值——够画一版对比图，不做完整图表解析。
    """
    ref = el.find(f".//{_q('c', 'chart')}")
    rid = ref.get(_q("r", "id")) if ref is not None else None
    cpart = pkg.target(part, rid) if rid else None
    if not cpart:
        return None
    node = pkg.xml(cpart)
    if node is None:
        return None
    kind = None
    for t in ("barChart", "lineChart", "pieChart", "scatterChart", "areaChart"):
        if node.find(f".//{_q('c', t)}") is not None:
            kind = t.replace("Chart", "")
            break
    cats, series = [], []
    for s in node.iter(_q("c", "ser")):
        cat = s.find(_q("c", "cat"))
        if cat is not None and not cats:
            cats = [p.find(_q("c", "v")).text or ""
                    for p in cat.iter(_q("c", "pt")) if p.find(_q("c", "v")) is not None]
        val = s.find(_q("c", "val"))
        if val is not None:
            series.append([float(p.find(_q("c", "v")).text or 0)
                           for p in val.iter(_q("c", "pt"))
                           if p.find(_q("c", "v")) is not None
                           and (p.find(_q("c", "v")).text or "").replace(".", "", 1).isdigit()])
    series = [s for s in series if s]      # 空系列丢掉的，是解析残留
    if not series:
        return None
    return {"kind": kind or "bar", "cats": cats, "series": series}


def _emit_graphic_frame(el, ctx, transform, out, gid=None):
    theme, notes = ctx["theme"], []
    sh = _record(el, ctx, transform, "graphic-frame", notes, holder="xfrm",
                 frame_el="xfrm", gid=gid)
    data = el.find(f".//{_q('a', 'graphicData')}")
    sub = None
    if data is not None:
        for c in list(data):
            sub = _tag(c)
            break
    if sub == "tbl":
        sh["notes"].append("tbl")
        sh["cells"] = _table_grid(el)
        if sh["cells"]:
            sh["text"] = "".join(sh["cells"][0])
        # ⚠️ `p:graphicFrame` 自己没有 `txBody`，字号写在每个单元格的
        #    `a:tc/a:txBody` 里。不在这里取一次，表格框的字号会一律留 0
        #    ——实测北大红有 19 个这样的框。取全表最大的一号。
        best = 0.0
        for tb in el.findall(f".//{_q('a', 'tc')}/{_q('a', 'txBody')}"):
            _, _, sz, _ = _text_of(tb, theme, notes, ctx.get("deck_sz"))
            best = max(best, sz)
        if best:
            sh["size_px"] = (best / 100.0) * EMU_PER_PT * ctx["kx"] * transform[2]
    elif sub == "chart":
        sh["notes"].append("chart")
        sh["chart"] = _chart_data(ctx["pkg"], ctx["part"], el)
    elif sub == "relIds":
        sh["notes"].append("smartart")
    else:
        sh["notes"].append("graphic-frame")
    sh["unsupported"] = True
    ctx["stats"]["graphic-frame"] += 1
    out.append(sh)


# ══════════════════════════════════════════════════════════
#  入口
# ══════════════════════════════════════════════════════════
def _parts(pkg: _Pkg) -> tuple[str | None, list[str], str | None, list[str]]:
    """→ (presentation.xml, 幻灯片部件表, slideMaster 部件, slideLayout 部件表)"""
    pres = "ppt/presentation.xml"
    master, layouts = None, []
    for n in pkg.names():
        if re.fullmatch(r"ppt/slideMasters/slideMaster\d+\.xml", n):
            master = master or n
        elif re.fullmatch(r"ppt/slideLayouts/slideLayout\d+\.xml", n):
            layouts.append(n)
    if pkg.xml(pres) is None:
        return None, [], master, sorted(layouts)
    lst = pkg.xml(pres).find(_q("p", "sldIdLst"))
    order = []
    if lst is not None:
        for sid in lst.findall(_q("p", "sldId")):
            rid = sid.get(_q("r", "id"))
            tgt = pkg.target(pres, rid) if rid else None
            if tgt and tgt.endswith(".xml") and tgt not in order:
                order.append(tgt)
    return pres, order, master, sorted(layouts)


def _canvas(pkg: _Pkg, pres: str) -> tuple[float, float]:
    node = pkg.xml(pres)
    if node is None:
        return 12192000.0, 6858000.0        # 13.333in × 7.5in
    sz = node.find(_q("p", "sldSz"))
    if sz is None:
        return 12192000.0, 6858000.0
    return (_num(sz.get("cx"), 12192000.0), _num(sz.get("cy"), 6858000.0))


def _new_stats() -> dict:
    return {k: 0 for k in ("no-frame", "gradient", "graphic-frame", "group",
                           "effect", "non-16x9", "color-other", "pages", "files",
                           "tbl", "chart", "smartart", "unresolved", "theme-missing")}


def read_pptx(path, deck: str | None = None) -> tuple[list[dict], dict]:
    """一个 .pptx → (形状表, 统计)。"""
    path = str(path)
    deck = deck or os.path.splitext(os.path.basename(path))[0]
    pkg = _Pkg(path)
    stats = _new_stats()
    stats["files"] = 1
    out: list[dict] = []
    try:
        pres, slides, master, layouts = _parts(pkg)
        if pres is None:
            raise ValueError("包里没有 ppt/presentation.xml")
        cw, ch = _canvas(pkg, pres)
        kx, ky = W / cw, H / ch
        if abs(ky / kx - 1.0) > 1e-6:
            stats["non-16x9"] += 1
        theme = _theme_colors(pkg)
        if not theme:
            stats["theme-missing"] = 1
        deck_sz = _deck_default_sz(pkg)

        def ctx_for(part, page, scope, store, ph_index=None):
            return {"deck": deck, "page": page, "scope": scope,
                    "kx": kx, "ky": ky, "ph_index": ph_index or {},
                    "theme": theme, "stats": store, "pkg": pkg, "part": part,
                    "deck_sz": deck_sz}

        _ph_cache: dict[str, dict] = {}

        def ph_index_of(part):
            if part and part not in _ph_cache:
                _ph_cache[part] = _ph_index(pkg, part)
            return _ph_cache.get(part) or {}

        slides = slides or sorted(
            n for n in pkg.names() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n))
        for i, part in enumerate(slides, 1):
            node = pkg.xml(part)
            if node is None:
                continue
            tree = node.find(f".//{_q('p', 'spTree')}")
            if tree is None:
                continue
            lay = pkg.rel_by_type(part, "/slideLayout")
            mas = pkg.rel_by_type(lay, "/slideMaster") if lay else None
            idx = dict(ph_index_of(mas))
            idx.update(ph_index_of(lay))          # 版式盖过母版
            c = ctx_for(part, i, "slide", stats, idx)
            # 幻灯片自己用的版式与母版：`page_inherited` 靠这两个值
            # 把版式上的 logo 那类装饰挑出来，别把整册 11 个版式全算上。
            c["layout_part"], c["master_part"] = lay, mas
            for child in list(tree):
                _walk(child, c, IDENTITY, out)
            stats["pages"] += 1

        for part, scope in ([(m, "master") for m in ([master] if master else [])]
                            + [(l, "layout") for l in layouts]):
            node = pkg.xml(part)
            if node is None:
                continue
            tree = node.find(f".//{_q('p', 'spTree')}")
            if tree is None:
                continue
            mas = pkg.rel_by_type(part, "/slideMaster") if scope == "layout" else None
            c = ctx_for(part, 0, scope, stats, ph_index_of(mas))
            for child in list(tree):
                _walk(child, c, IDENTITY, out)
    finally:
        pkg.close()

    # 计数落回 stats，供报告用
    for note, key in (("tbl", "tbl"), ("chart", "chart"), ("smartart", "smartart"),
                      ("theme-unresolved", "unresolved")):
        stats[key] = sum(1 for s in out if note in (s.get("notes") or []))
    return out, stats
