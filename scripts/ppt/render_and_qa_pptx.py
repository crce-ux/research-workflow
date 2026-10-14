# -*- coding: utf-8 -*-
"""
PPTX 渲染 + 客观版式体检（配合 AI 视觉复核使用）

用法:
    python render_and_qa_pptx.py <pptx路径> [输出目录] [--width 1600]

作用:
    1) 用 PowerPoint COM 把 PPTX 逐页导出为 PNG（视觉复核的原料）
    2) 对每页做像素级客观体检：边缘污染 / 内容包围盒 / 边距一致性 / 大块留白
    3) 打印体检报告（AI 再结合 PNG 做语义判断：溢出、错位、缺字、口径错误）

依赖: pywin32 (win32com)、Pillow   环境: Windows + 已安装 PowerPoint
注意: Export 带尺寸参数在部分版本会报错，本脚本自动回退为不带尺寸导出（实测可用）。
"""
import os, sys, shutil, argparse

sys.stdout.reconfigure(encoding='utf-8')


def render(src, out, width=1600):
    # PowerPoint Export 要求绝对路径，必须 abspath
    src = os.path.abspath(src)
    out = os.path.abspath(out)
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(out, exist_ok=True)
    import win32com.client
    app = win32com.client.Dispatch("PowerPoint.Application")
    try:
        try:
            app.Visible = True
        except Exception:
            pass
        pres = app.Presentations.Open(os.path.abspath(src), ReadOnly=True, WithWindow=True)
        n = pres.Slides.Count

        # 【教训 2026-10-07】原来写 Export(dst, "PNG", width, -1)，
        # 误以为 -1 是「按比例算高」。实测 PowerPoint 会把宽缩到 width、
        # 却把高留在**默认导出高度的 1350**，于是 16:9 的画面被**纵向拉伸 1.5 倍**
        # （应 900），且**不报错、不产出异常文件**。后果：像素体检量出的
        # 边缘/边距/四角全部失真（纵向数字虚高 50%），而肉眼又看不出明显问题。
        #   实测对照：Export(dst,"PNG",1600,-1) -> 1600×1350 (1.185) ❌
        #             Export(dst,"PNG",1600,900) -> 1600×900  (1.778) ✅
        #             Export(dst,"PNG")          -> 2400×1350 (1.778) ✅ 但尺寸不受控
        # 改为**按页面实际宽高比显式算高**，不再依赖 -1。
        _sw, _sh = pres.PageSetup.SlideWidth, pres.PageSetup.SlideHeight
        _h = int(round(width * _sh / _sw)) if _sw else int(round(width * 9 / 16))

        for i in range(1, n + 1):
            dst = os.path.join(out, f"slide_{i:02d}.png")
            try:
                pres.Slides(i).Export(dst, "PNG", width, _h)      # 方式A：显式给出宽与高
            except Exception:
                pass
            if not (os.path.exists(dst) and os.path.getsize(dst) > 0):
                pres.Slides(i).Export(dst, "PNG")                 # 方式B：原始尺寸（回退）
        pres.Close()
    finally:
        try:
            app.Quit()
        except Exception:
            pass
    return sorted(f for f in os.listdir(out) if f.lower().endswith('.png'))


def qa(png_dir, files):
    from PIL import Image
    print("\n" + "=" * 78)
    print("客观版式体检")
    print("=" * 78)
    for f in files:
        p = os.path.join(png_dir, f)
        im = Image.open(p).convert("RGB")
        W, H = im.size
        px = im.load()

        def avg(c):
            return sum(c) / 3

        # 边缘采样（避开四角，取边中部）
        L = [px[1, int(H * r)] for r in (0.15, 0.35, 0.5, 0.65, 0.85)]
        R = [px[W - 2, int(H * r)] for r in (0.15, 0.35, 0.5, 0.65, 0.85)]
        T = [px[int(W * r), 1] for r in (0.25, 0.5, 0.75)]
        B = [px[int(W * r), H - 2] for r in (0.25, 0.5, 0.75)]
        corners = {"左上": px[2, 2], "右上": px[W - 2, 2], "左下": px[2, H - 2], "右下": px[W - 2, H - 2]}

        # 内容包围盒（背景阈值：三通道均 >235 视为空）
        def is_bg(c):
            return all(v > 235 for v in c)

        minx, maxx, miny, maxy = W, 0, H, 0
        for y in range(0, H, 3):
            for x in range(0, W, 3):
                if not is_bg(px[x, y]):
                    minx = min(minx, x); maxx = max(maxx, x)
                    miny = min(miny, y); maxy = max(maxy, y)

        # 背景主色
        from collections import Counter
        cnt = Counter(px[x, y] for y in range(0, H, 4) for x in range(0, W, 4))
        bg_main = cnt.most_common(1)[0]

        flags = []
        if sum(1 for c in L if avg(c) < 200) >= 3:
            flags.append("⚠ 左边缘偏暗/有底色泄漏")
        if sum(1 for c in R if avg(c) < 200) >= 3:
            flags.append("⚠ 右边缘偏暗/有底色泄漏")
        if minx > int(W * 0.08):
            flags.append(f"⚠ 左侧留白偏大({minx}px)")
        if (W - maxx) > int(W * 0.08):
            flags.append(f"⚠ 右侧留白偏大({W - maxx}px)")

        print(f"\n{f}  ({W}×{H})")
        print(f"  边距  左{minx:>4}  右{W - maxx:>4}  上{miny:>4}  下{H - maxy:>4}   (px)")
        print(f"  主色  {bg_main[0]} 占 {bg_main[1] * 100 // (W * H // 16)}%")
        print(f"  四角  " + "  ".join(f"{k}{v}" for k, v in corners.items()))
        print(f"  边带  左{avg(L[2]):.0f} 右{avg(R[2]):.0f} 上{avg(T[1]):.0f} 下{avg(B[1]):.0f}  (亮度均值)")
        print(f"  → {' ; '.join(flags) if flags else '✅ 边缘/边距未见异常'}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pptx")
    ap.add_argument("outdir", nargs="?", default=None)
    ap.add_argument("--width", type=int, default=1600)
    a = ap.parse_args()
    outdir = a.outdir or (os.path.splitext(os.path.basename(a.pptx))[0] + "_png")
    print("渲染中…", a.pptx)
    files = render(a.pptx, outdir, a.width)
    print(f"导出 {len(files)} 页 → {os.path.abspath(outdir)}")
    qa(outdir, files)
