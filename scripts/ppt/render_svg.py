# -*- coding: utf-8 -*-
"""
render_svg.py —— SVG → PNG 预览（**支持中文**）

【用途】
    把自制 SVG 示意图渲染成 PNG，供**视觉验证**与 PPT 嵌入。
    补 `_work/render_svg.py` 的缺口——它用 svglib，**不渲染 CJK，中文会变方框**，
    只能校验几何，不能做视觉验证。

【渲染方式】
    Edge/Chrome 的 headless 模式用系统字体引擎，**中文渲染正确**，
    且支持 CSS 字体栈、tspan、透明度等 SVG 特性。
    实测（2026-09-14）：屏状核局部环路示意图，中英文与 tspan 加粗全部正确。

【对应流程】
    `汇报PPT产出流程手册.md` §三 视觉验证 T1（SVG 初稿后）
    `文献调研与汇报_全流程总纲.md` —— 自制示意图的验证环节

【用法】
    python render_svg.py <输入.svg> [输出.png] [--scale 2] [--width 1200] [--height 512]

    默认参数从 SVG 的 width/height 属性读取；--scale 建议 2（看细节）。

【依赖】
    Microsoft Edge 或 Google Chrome（自动探测常见安装路径）。
    纯标准库 + subprocess，无需 pip 包。

【踩坑教训】
    · **必须先把 SVG 复制到纯 ASCII 路径**——浏览器对 file:// 的中文路径处理不稳，
      直接指中文路径会静默截出空白图。本脚本内部自动复制到临时目录。
    · Edge 会打印 QQBrowser / task_manager 的报错，**是噪声不是失败**，
      判据是输出文件是否生成且非空。脚本已按此判断。
    · `--force-device-scale-factor` 才是真正的缩放；只改 `--window-size` 会裁切而非缩放。
    · svglib / cairosvg **都不适合中文**；cairosvg 还常缺 cairo 运行库。

【冒烟测试】
    2026-09-14 于 `屏状核_氯氮平/04_组会汇报/素材_示意图/屏状核局部抑制环路_示意图.svg`
    通过；2× 输出 2400×1024，中文与 tspan 加粗渲染正确。
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

#: ⚠️ 顺序有讲究 —— 优先用**专用 headless 二进制**，最后才用系统浏览器。
#:
#: 【教训 2026-09-15】此前只探测 Edge 与 Chrome 的 Program Files 路径，
#: 结果**用户 Edge 开着时，headless 调用被转发给已有实例后直接 rc=0 退出**，
#: 不渲染、不报错、不产出文件 —— 表现为「未生成输出」。
#: 排查花了很久，因为脚本当时把浏览器 stderr 吞掉了（现已保留）。
#:
#: Playwright 的 `chrome-headless-shell` 是**独立的 headless 二进制**，
#: 不与任何正在运行的浏览器争抢实例，是最稳的选择。
_BROWSER_CANDIDATES = [
    # Playwright 专用 headless shell（最佳）
    (r"C:\Users\{u}\AppData\Local\ms-playwright", r"chromium_headless_shell-*\chrome-headless-shell-win64\chrome-headless-shell.exe"),
    # Playwright 完整 chromium
    (r"C:\Users\{u}\AppData\Local\ms-playwright", r"chromium-*\chrome-win64\chrome.exe"),
    # 用户级安装的 Chrome（Program Files 之外，之前漏了这里）
    (r"C:\Users\{u}\AppData\Local\Google\Chrome\Application", "chrome.exe"),
    # 系统浏览器（有"被已有实例吞掉"的风险，故排在最后）
    (r"C:\Program Files\Google\Chrome\Application", "chrome.exe"),
    (r"C:\Program Files (x86)\Microsoft\Edge\Application", "msedge.exe"),
    (r"C:\Program Files\Microsoft\Edge\Application", "msedge.exe"),
]


def find_browser():
    """返回第一个可用的浏览器可执行文件路径（优先 headless 专用二进制）"""
    import glob as _glob
    user = os.environ.get("USERNAME") or os.path.basename(os.path.expanduser("~"))
    for base, pat in _BROWSER_CANDIDATES:
        hits = sorted(_glob.glob(os.path.join(base.format(u=user), pat)))
        if hits:
            return hits[-1]          # 取版本最新的一个
    return None


def svg_size(path):
    """从 SVG 根元素的 width/height 读尺寸（无单位像素）"""
    head = open(path, encoding="utf-8").read(2000)
    w = re.search(r'width="(\d+(?:\.\d+)?)', head)
    h = re.search(r'height="(\d+(?:\.\d+)?)', head)
    return (int(float(w.group(1))) if w else 1200,
            int(float(h.group(1))) if h else 800)


def absolutize_hrefs(svg_text, svg_dir):
    """把 SVG 里的**相对路径 href 改写成绝对 file:// URL**。

    【背景】
        本脚本会把 SVG 复制到**纯 ASCII 临时目录**再交给浏览器（见下方"踩坑教训"）。
        复制之后，原 SVG 里 `../素材/xxx.png` 这类**相对路径全部失效** ——
        表现为：图片区域渲染成空白或错图，但 SVG 本身没有任何报错。
        实测（2026-09-15）：一页 2×2 图片网格，四张图全渲染成同一块模糊色斑，
        像素体检还显示"非白占比 88%"（像是成功了），只有肉眼能看出错。

    【改写范围】只动 **相对路径**；`http(s)://` / `data:` / `#锚点` / 已是绝对路径的一律不碰。
    """
    def repl(m):
        attr, url = m.group(1), m.group(2)
        if re.match(r'^(https?:|data:|#|/|[A-Za-z]:)', url):
            return m.group(0)
        abs_path = os.path.normpath(os.path.join(svg_dir, url.replace("/", os.sep)))
        return f'{attr}="file:///{abs_path.replace(os.sep, "/")}"'

    return re.sub(r'((?:xlink:)?href)="([^"]+)"', repl, svg_text)


def main():
    ap = argparse.ArgumentParser(description="SVG → PNG（支持中文）")
    ap.add_argument("src", nargs="?", help="输入 SVG")
    ap.add_argument("out", nargs="?", help="输出 PNG（默认与输入同名）")
    ap.add_argument("--which", action="store_true", help="只打印当前选中的浏览器，不渲染")
    ap.add_argument("--scale", type=float, default=2.0, help="缩放倍数（默认 2）")
    ap.add_argument("--width", type=int, help="覆盖宽度")
    ap.add_argument("--height", type=int, help="覆盖高度")
    args = ap.parse_args()

    if args.which:
        b = find_browser()
        print(f"选中的浏览器：{b}" if b else "❌ 未找到任何浏览器")
        return 0 if b else 1

    if not args.src:
        ap.error("需要给出输入 SVG（或用 --which 查看浏览器）")
    if not os.path.isfile(args.src):
        print(f"❌ 找不到：{args.src}")
        return 1

    browser = find_browser()
    if not browser:
        print("❌ 未找到可用的浏览器（Edge / Chrome / Playwright chromium 均未探测到）")
        return 1

    sw, sh = svg_size(args.src)
    w, h = args.width or sw, args.height or sh
    out = args.out or (os.path.splitext(args.src)[0] + ".png")

    # ⚠️ 复制到纯 ASCII 临时路径——浏览器对 file:// 中文路径处理不稳
    #    ⚠️ 复制前必须把相对 href 绝对化，否则 SVG 里的图片全部失效（见 absolutize_hrefs）
    tmpdir = tempfile.mkdtemp(prefix="svgrender_")
    tmp_svg = os.path.join(tmpdir, "in.svg")
    tmp_png = os.path.join(tmpdir, "out.png")
    src_dir = os.path.dirname(os.path.abspath(args.src))
    svg_text = open(args.src, encoding="utf-8").read()
    n_abs = len(re.findall(r'(?:xlink:)?href="(?!https?:|data:|#|/|[A-Za-z]:)', svg_text))
    open(tmp_svg, "w", encoding="utf-8").write(absolutize_hrefs(svg_text, src_dir))
    if n_abs:
        print(f"   （已把 {n_abs} 个相对图片路径改写为绝对路径）")

    # ⚠️ 必须给独立的 user-data-dir —— 否则 headless 会用**默认 profile**，
    #    而默认 profile 常被用户正开着的浏览器锁住 → 静默渲染失败（实测 2026-09-15）：
    #    表现是"未生成输出"，且不报任何错。这也解释了"为什么有时候能跑、有时候不能"。
    profile = os.path.join(tmpdir, "profile")
    cmd = [
        browser, "--headless=new", "--disable-gpu", "--hide-scrollbars",
        f"--user-data-dir={profile}",
        "--no-first-run", "--no-default-browser-check",
        f"--force-device-scale-factor={args.scale}",
        f"--window-size={w},{h}",
        f"--screenshot={tmp_png}",
        "file:///" + tmp_svg.replace("\\", "/"),
    ]
    r = subprocess.run(cmd, capture_output=True, timeout=120)

    if not os.path.isfile(tmp_png) or os.path.getsize(tmp_png) == 0:
        # ⚠️ 不要把浏览器输出吞掉 —— 这次排查慢就是因为它静默失败（2026-09-15）
        print("❌ 渲染失败（未生成输出）")
        print(f"   浏览器：{browser}")
        err = (r.stderr or b"").decode("utf-8", "ignore").strip()
        out = (r.stdout or b"").decode("utf-8", "ignore").strip()
        if err:
            print("   stderr：" + err[:600].replace("\n", "\n           "))
        if out:
            print("   stdout：" + out[:300].replace("\n", "\n           "))
        if not err and not out:
            print("   浏览器无任何输出（rc=%d）—— 常见原因：该浏览器正被占用，"
                  "调用被转发给已有实例后直接退出。\n"
                  "   处置：确认 python 能找到一个**专用 headless 二进制**；"
                  "跑 `render_svg.py --which` 看当前选中的是哪个。" % r.returncode)
        shutil.rmtree(tmpdir, ignore_errors=True)
        return 1

    shutil.copyfile(tmp_png, out)
    size = os.path.getsize(out)
    print(f"✅ {os.path.basename(out)}  "
          f"{int(w * args.scale)}×{int(h * args.scale)}  {size // 1024} KB")
    shutil.rmtree(tmpdir, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
