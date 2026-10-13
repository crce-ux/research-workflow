# -*- coding: utf-8 -*-
"""
render_templates.py —— 把 7 套国自然模板全部渲染成 PNG，并拼成「联系表」缩略图墙

【为什么】
    目视逐页看 123 页成本太高；用 contact sheet 把一套模板的全部页拼成 1–2 张图，
    一次 Read 就能扫完整套，且能横向比较版式分布。

【用法】
    python render_templates.py            # 渲染 + 拼图
    python render_templates.py --sheetonly  # 只拼图（PNG 已存在时）

【产出】
    _work/tpl_png/<模板名>/slide-XX.png     逐页原图
    _work/tpl_png/_联系表_<模板名>.png       缩略图墙

【踩坑】
    · PowerPoint COM 的 Export 必须用**绝对路径**
    · 某些版本带尺寸参数会报错 → 回退 `Export(dst, "PNG")` 不带尺寸
"""
import os, sys, glob, math, subprocess

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
# ── 2026-09-24 路径修正：跨机器探测，勿写死用户名/盘符 ──────────
def _find_browser():
    """按序探测浏览器；可用环境变量 BROWSER_PATH 覆盖。"""
    for _p in (os.environ.get("BROWSER_PATH"),
               os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Google\Chrome\Application\chrome.exe"),
               r"C:\Program Files\Google\Chrome\Application\chrome.exe",
               r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
               r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
               r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"):
        if _p and os.path.isfile(_p):
            return _p
    raise FileNotFoundError("未找到 Chrome/Edge；可设环境变量 BROWSER_PATH")


def _profile(_name):
    """持久 profile 根：~/.cdp_profiles/<name>"""
    return os.path.join(os.path.expanduser("~"), ".cdp_profiles", _name)
# ────────────────────────────────────────────────────────────

BASE = os.path.join(os.path.expanduser("~"), "Desktop", "医学心理学", "国家自然科学申报PPT")
WORK = r"<vault>\_系统\_流程与工具\_work"
OUT = os.path.join(WORK, "tpl_png")

COLS, THUMB_W = 5, 400   # 联系表：5 列，缩略图宽 400px


def render_one(pptx_path, out_dir):
    """用 PowerPoint COM 导出整份 PPTX 为 PNG"""
    import win32com.client
    os.makedirs(out_dir, exist_ok=True)
    app = win32com.client.Dispatch("PowerPoint.Application")
    pres = app.Presentations.Open(pptx_path, WithWindow=False)
    try:
        n = pres.Slides.Count
        for i in range(1, n + 1):
            pres.Slides(i).Export(os.path.join(out_dir, f"slide-{i:02d}.png"), "PNG")
    finally:
        # ⚠️ app.Quit() 会杀掉用户正在用的 PowerPoint，只关本次打开的文稿
        pres.Close()
    return n


def make_sheet(png_dir, out_path, title):
    from PIL import Image, ImageDraw
    files = sorted(glob.glob(os.path.join(png_dir, "slide-*.png")))
    if not files:
        print("    ⚠️ 无 PNG，跳过"); return
    ims = [Image.open(f).convert("RGB") for f in files]
    ratio = ims[0].height / ims[0].width
    tw, th = THUMB_W, int(THUMB_W * ratio)
    rows = math.ceil(len(ims) / COLS)
    pad, top = 12, 46
    W = COLS * tw + (COLS + 1) * pad
    H = top + rows * (th + pad + 20) + pad
    sheet = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(sheet)
    d.text((pad, 16), title, fill="#111111")
    for i, (f, im) in enumerate(zip(files, ims)):
        r, c = divmod(i, COLS)
        x = pad + c * (tw + pad)
        y = top + r * (th + pad + 20)
        sheet.paste(im.resize((tw, th)), (x, y))
        d.rectangle([x, y, x + tw, y + th], outline="#BBBBBB")
        d.text((x + 2, y + th + 3), os.path.basename(f).replace("slide-", "P").replace(".png", ""),
               fill="#555555")
    sheet.save(out_path)
    print(f"    ✅ {os.path.basename(out_path)}  {len(ims)} 页  {W}×{H}  {os.path.getsize(out_path)//1024} KB")


def main():
    """用法：render_templates.py [模板目录] [--sheetonly]

    模板目录可省略（用 `BASE` 的默认值）。**换到别的模板集时从命令行传**，
    不要改脚本里的常量——那是复用时的坑。
    """
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    base = args[0] if args else BASE
    only_sheet = "--sheetonly" in sys.argv
    if not os.path.isdir(base):
        print(f"❌ 模板目录不存在：{base}")
        print("   用法：render_templates.py <模板目录> [--sheetonly]")
        return
    print(f"模板目录：{base}\n输出目录：{OUT}\n")
    for f in sorted(os.listdir(base)):
        if not f.endswith(".pptx") or f.startswith("~$"):
            continue
        name = f.split("-")[0]
        d = os.path.join(OUT, name)
        if not only_sheet:
            print(f"  ▶ {name}")
            try:
                n = render_one(os.path.join(base, f), d)
                print(f"    导出 {n} 页")
            except Exception as e:
                print(f"    ❌ {type(e).__name__}: {e}")
                continue
        make_sheet(d, os.path.join(OUT, f"_联系表_{name}.png"), name)


if __name__ == "__main__":
    main()
