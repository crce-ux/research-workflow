# -*- coding: utf-8 -*-
"""slide_fit.py —— 画之前先算：版面够不够，图里的字还看不看得清

【背景】
    academic-slides 的纪律是「不要等渲染出来才发现放不下」。
    本脚本把版面算术做成一条命令。

【两条判据（都来自 script-spec.md）】

    容量 ≈ 内容区面积 × 0.78 ÷ 单字占位        单字占位 = 字号² × 1.35
    带高 = Σ ceil(字数 ÷ 每行字数) × 字号 × 行距

    ⭐ 配图可读性：图内字号 × 显示宽 ÷ 图宽 < 9 px → 不可读
       （一张高清大图缩到版面上，图里的字可能只剩 5 px；
         在编辑器的缩放状态里**看不出来**，只能算。）

用法：
    # 一张文字块放得下吗
    python slide_fit.py --chars 320 --size 20

    # 多块的带高之和 vs 区域高
    python slide_fit.py --blocks "标题:24:12" "要点:20:180" "注释:16:90" --area 1200x525

    # 配图里的字缩到版面上还看得清吗
    python slide_fit.py --image-font 14 --image-width 2000 --display-width 500

退出码 = 问题条数（0 = 全过）。
"""
import argparse
import math
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LOSS = 0.78          # 损耗系数（script-spec.md）
CELL_FACTOR = 1.35   # 单字占位 = 字号² × 1.35——由手册给出的三组数反解出来
MIN_PX = 9           # 配图可读性下限


def capacity(area_w, area_h, size):
    """整页容量（字数）。"""
    return (area_w * area_h) * LOSS / (size * size * CELL_FACTOR)


def block_height(chars, size, area_w, leading=1.5):
    """一个文字块的带高（px）。"""
    per_line = max(1, int(area_w / size))       # 中文 ≈ 1 em 宽
    lines = math.ceil(chars / per_line) if chars else 0
    return lines, lines * size * leading


def main():
    ap = argparse.ArgumentParser(description="版面算术：放得下吗 / 图里字还看得清吗")
    ap.add_argument("--chars", type=int, help="文字块字数")
    ap.add_argument("--size", type=float, help="字号 px")
    ap.add_argument("--blocks", nargs="*", default=None,
                    help="多块，形如 名称:字号:字数")
    ap.add_argument("--area", default="1200x525", help="内容区尺寸，如 1200x525")
    ap.add_argument("--leading", type=float, default=1.5, help="行距倍数（默认 1.5）")
    ap.add_argument("--image-font", type=float, help="配图内字号 px")
    ap.add_argument("--image-width", type=float, help="配图原始宽 px")
    ap.add_argument("--display-width", type=float, help="版面上显示宽 px")
    a = ap.parse_args()

    try:
        area_w, area_h = (float(x) for x in a.area.lower().split("x"))
    except ValueError:
        raise SystemExit(f"--area 要写成 宽x高，如 1200x525；收到 {a.area!r}")

    problems = 0

    # ── 配图模式 ──
    if a.image_font is not None:
        if a.image_width is None or a.display_width is None:
            raise SystemExit("配图模式要同时给 --image-width 与 --display-width")
        shown = a.image_font * a.display_width / a.image_width
        print(f"slide_fit · 配图可读性")
        print(f"  图内字号 {a.image_font:g}px × 显示宽 {a.display_width:g} ÷ 图宽 "
              f"{a.image_width:g} = 版面上 {shown:.1f} px（下限 {MIN_PX}）")
        if shown < MIN_PX:
            problems += 1
            print(f"  ❌ 不可读——图里的字在版面上只剩 {shown:.1f} px。"
                  f"\n     → 裁图 / 拆图 / 把关键数字重打进版面，别指望读者放大")
        else:
            print("  ✅ 可读")
        return problems

    # ── 多块模式 ──
    if a.blocks:
        parsed = []
        for spec in a.blocks:
            try:
                name, size, chars = spec.rsplit(":", 2)
                parsed.append((name, float(size), int(chars)))
            except ValueError:
                raise SystemExit(f"--blocks 每项写成 名称:字号:字数；收到 {spec!r}")
        print(f"slide_fit · 带高预算 · 内容区 {area_w:g}×{area_h:g} · 行距 {a.leading:g}")
        total = 0.0
        for name, size, chars in parsed:
            lines, h = block_height(chars, size, area_w, a.leading)
            total += h
            print(f"  {name:<10} {chars:>4} 字 @{size:g}px → {lines:>2} 行 · 带高 {h:>7.1f} px")
        print(f"  {'合计':<10} {'':>4}    {'':>2}    {'':>2}       {total:>7.1f} px"
              f" / {area_h:g} px")
        if total > area_h:
            problems += 1
            print(f"  ❌ 超 {total - area_h:.1f} px——**画之前就该减**，"
                  f"别等渲染出来再改")
        else:
            print(f"  ✅ 余量 {area_h - total:.1f} px")
        return problems

    # ── 单块模式 ──
    if a.chars is None or a.size is None:
        raise SystemExit("要么给 --chars 与 --size，要么给 --blocks，"
                         "要么给 --image-font 三个参数")
    cap = capacity(area_w, area_h, a.size)
    lines, h = block_height(a.chars, a.size, area_w, a.leading)
    print(f"slide_fit · 容量 · 内容区 {area_w:g}×{area_h:g} · 字号 {a.size:g}px")
    print(f"  整页容量≈ {cap:.0f} 字；本块 {a.chars} 字 → {lines} 行 · 带高 {h:.1f} px")
    if a.chars > cap:
        problems += 1
        print(f"  ❌ 超出整页容量 {a.chars - cap:.0f} 字 → 拆页或减字")
    else:
        print(f"  ✅ 容量内（余 {cap - a.chars:.0f} 字）")
    if h > area_h:
        problems += 1
        print(f"  ❌ 带高超出区域 {h - area_h:.1f} px")
    return problems


if __name__ == "__main__":
    raise SystemExit(main())
