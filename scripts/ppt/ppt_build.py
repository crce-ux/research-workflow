# -*- coding: utf-8 -*-
"""
ppt_build.py —— PPT 制作**总管线**（一条命令跑完 渲染 → 体检 → 合 PPTX → 验证）

【背景】
    以前做一册 PPT 要手动串 4 步、记 4 个命令、路径各写一遍：
        render_svg.py（逐页）→ ppt_check（无）→ svg_to_pptx.py <project> → render_and_qa_pptx.py
    本脚本把这条链固定下来，**输入一个目录，输出 PPTX + 报告**。

【目录约定】
    <项目>/
      svg/             ← 你把页放这里（.svg，按文件名排序 = 页序）
      images/          ← 页面里 <image href="../images/..."> 指向这里
      out/             ← 本脚本生成：preview/ · pptx/ · render/ · 报告.md
      build.md         ← 可选：本册的说明（标题、页码起始、备注）

【用法】
    python ppt_build.py <项目目录>              # 全流程
    python ppt_build.py <项目目录> --only check # 只体检（秒级，不渲染）
    python ppt_build.py <项目目录> --only svg   # 只渲染逐页预览
    python ppt_build.py <项目目录> --only pptx  # 只合 PPTX
    python ppt_build.py <项目目录> --only qa    # 只对成品做像素体检

【依赖】
    render_svg.py（本目录）· ppt_check.py（本目录）· render_and_qa_pptx.py（本目录）
    ppt-master 的 svg_to_pptx.py（合并 PPTX）
"""
import argparse
import glob
import os
import shutil
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from ppt_style import C, G, PX, FONT

def _find_ppt_master():
    """定位 ppt-master 的 `svg_to_pptx.py`（合并层，**不可替代**）。

    顺序：环境变量 `PPT_MASTER` → 两个已知技能目录 → 报错时给出可操作的提示。
    写成「多候选 + 环境变量」是为了**不再硬编码盘符**——
    换机器、技能换位置时只设一个环境变量即可。
    """
    env = os.environ.get("PPT_MASTER")
    if env and os.path.exists(env):
        return env
    rel = os.path.join("ppt-master", "skills", "ppt-master", "scripts", "svg_to_pptx.py")

    # 仓库本地的 vendor/（由 setup.sh 拉到；从脚本位置逐级向上找）
    d = os.path.dirname(os.path.abspath(__file__))
    for _ in range(4):
        c = os.path.join(d, "vendor", rel)
        if os.path.exists(c):
            return c
        d = os.path.dirname(d)

    cands = [
        os.path.join(os.environ.get("APPDATA", ""), "CherryStudio", "Data", "Skills", rel),
        os.path.join(os.environ.get("APPDATA", ""), "CherryStudio", "Data", "Agents",
                     ".claude", "skills", rel),
    ]
    for c in cands:
        if os.path.exists(c):
            return c
    return None


PPT_MASTER = _find_ppt_master()


def project_cfg(proj):
    """读 `<项目>/ppt.json`（可选）。**项目专有内容放这里，不放共享库。**

    支持的键（都可省）：
        footer     页脚左侧文字
        audience   受众（写进 spec_lock 的 communication 段）
        objective  目标（同上）
        message    核心信息（同上）
    """
    p = os.path.join(proj, "ppt.json")
    if not os.path.exists(p):
        return {}
    try:
        import json
        return json.load(open(p, encoding="utf-8"))
    except Exception as ex:
        print(f"  ⚠️ ppt.json 解析失败（忽略）：{ex}")
        return {}

BAR = "═" * 62


def run(cmd, note=""):
    print(f"  $ {' '.join(os.path.basename(str(c)) if i == 0 else str(c) for i, c in enumerate(cmd))}")
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (r.stdout or "") + (r.stderr or "")
    if r.returncode != 0:
        print(f"    ❌ 退出码 {r.returncode}")
        print("    " + "\n    ".join(out.strip().splitlines()[-12:]))
        return False
    for ln in out.strip().splitlines()[-6:]:
        if ln.strip():
            print(f"    {ln.strip()}")
    return True


def stage_check(proj, strict=False):
    print(f"\n{BAR}\n【1/4】源文件体检（秒级，先查再渲染）\n{BAR}")
    svg = os.path.join(proj, "svg")
    if not os.path.isdir(svg):
        print(f"  ❌ 缺 {svg}"); return False
    cmd = [sys.executable, os.path.join(HERE, "ppt_check.py"), svg]
    if strict:
        cmd.append("--strict")
    r = subprocess.run(cmd, text=True, encoding="utf-8", errors="replace")
    return r.returncode == 0 or not strict


def stage_svg(proj):
    print(f"\n{BAR}\n【2/4】渲染逐页预览\n{BAR}")
    svg = os.path.join(proj, "svg")
    out = os.path.join(proj, "out", "preview")
    os.makedirs(out, exist_ok=True)
    files = sorted(glob.glob(os.path.join(svg, "*.svg")))
    if not files:
        print("  ❌ svg/ 下没有 .svg"); return False
    ok = 0
    for f in files:
        dst = os.path.join(out, os.path.basename(f).replace(".svg", ".png"))
        if run([sys.executable, os.path.join(HERE, "render_svg.py"), f, dst, "--scale", "1"]):
            ok += 1
    print(f"  → 预览 {ok}/{len(files)} 张  {out}")
    return ok == len(files)


SPEC_LOCK = "spec_lock.md"

SPEC_TMPL = """<!-- ppt-master-schema: spec-lock/v1 -->
<!-- 由 ppt_build.py 从 ppt_style.py 自动生成；改样式请改 ppt_style.py 后重跑 -->

# Execution Lock

## canvas
- viewBox: 0 0 {w} {h}
- format: PPT 16:9

## communication
- audience: {audience}
- objective: {objective}
- core_message: {msg}
- consumption_mode: presentation

## mode
- mode: pyramid

## visual_style
- visual_style: {vstyle}

## colors
- background: "{page}"
- secondary_bg: "{tint}"
- primary: "{main}"
- accent: "{red}"
- body_text: "{txt}"
- surface: "{tint}"
- grid: "{line}"

## typography
- font_family: {font}
- title_family: {font}
- body_family: {font}
- title: {f_title}
- page_title: {f_title}
- section: {f_section}
- body: {f_body}
- annotation: {f_caption}

## page_rhythm
{rhythm}

## pptx_structure
- mode: flat

## forbidden
- `mask`, `<style>`, `class`, external CSS, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`, `<set>`, `<script>` / event attributes, `<iframe>`
- HTML named entities in text; write typography as raw Unicode and escape XML reserved characters
"""


def write_spec_lock(proj, svg_files):
    """从 ppt_style 生成 spec_lock.md（缺则建；已存在则只补 pptx_structure.mode）"""
    p = os.path.join(proj, SPEC_LOCK)
    cfg = project_cfg(proj)
    rhythm = "\n".join(f"- P{i+1:02d}: breathing" for i in range(len(svg_files)))
    body = SPEC_TMPL.format(
        w=G["w"], h=G["h"],
        msg=cfg.get("message", "见 build.md 或制作稿"),
        audience=cfg.get("audience", "（未指定——写进 <项目>/ppt.json）"),
        objective=cfg.get("objective", "（未指定——写进 <项目>/ppt.json）"),
        vstyle=cfg.get("visual_style", "国自然风格"),
        font=FONT.replace("'", "").replace(",sans-serif", ", sans-serif").replace(",", ", "),
        f_title=PX["title"], f_section=PX["section"],
        f_body=PX["body"], f_caption=PX["caption"],
        rhythm=rhythm, **{k: C[k] for k in
                         ("page", "tint", "main", "red", "txt", "line")})
    open(p, "w", encoding="utf-8").write(body)
    print(f"    ✍️  已生成 {SPEC_LOCK}（{G['w']}×{G['h']}，{len(svg_files)} 页，mode: flat）")
    return True


def stage_pptx(proj):
    print(f"\n{BAR}\n【3/4】合并 PPTX\n{BAR}")
    if not PPT_MASTER:
        print("  ❌ 找不到 ppt-master 的 svg_to_pptx.py（合并层，不可替代）")
        print("     三个办法（任选）：")
        print("       ① 设环境变量：set PPT_MASTER=<...>\\svg_to_pptx.py")
        print("       ② 确认 ppt-master skill 已安装（Settings → Skills）")
        print("       ③ 检查它是否被移动/改名")
        return False
    svg_files = sorted(glob.glob(os.path.join(proj, "svg", "*.svg")))
    if not svg_files:
        print("  ❌ svg/ 下没有 .svg"); return False
    write_spec_lock(proj, svg_files)

    out = os.path.join(proj, "out", "pptx")
    os.makedirs(out, exist_ok=True)
    name = os.path.basename(os.path.normpath(proj)) + ".pptx"
    # svg_to_pptx 约定读 <project>/svg_output/
    link = os.path.join(proj, "svg_output")
    if not os.path.exists(link):
        try:
            os.symlink(os.path.join(proj, "svg"), link, target_is_directory=True)
        except Exception:
            shutil.copytree(os.path.join(proj, "svg"), link, dirs_exist_ok=True)
    return run([sys.executable, PPT_MASTER, proj, "-o", os.path.join(out, name)])


def stage_qa(proj):
    print(f"\n{BAR}\n【4/4】成品像素体检\n{BAR}")
    pp = glob.glob(os.path.join(proj, "out", "pptx", "*.pptx"))
    if not pp:
        print("  ⚠️ 没有 PPTX，跳过"); return True
    return run([sys.executable, os.path.join(HERE, "render_and_qa_pptx.py"),
                pp[0], os.path.join(proj, "out", "render")])


#: 会被 `--apply-footer` 替换掉的页脚占位串。
#: ⚠️ **只放中性占位**——共享库不含任何项目专有串。
#: 若某项目历史上用过别的占位文字，在它自己的 `ppt.json` 里加 `"legacy_footers": […]`。
_PLACEHOLDER_DEFAULT = ("（项目名）· 汇报",)


def apply_footer(proj, dry=True):
    """把页脚占位文字换成 `<项目>/ppt.json` 的 `footer`。

    骨架是共享模板，页脚是占位；复制到项目后若忘了改，
    交付出去就是一行"（项目名）· 汇报"。
    本函数只替换**恰好等于占位串**的位置，不碰用户已改过的页脚。

    `dry=True` 只报告不改（`ppt_build` 默认行为）。
    """
    cfg = project_cfg(proj)
    want = cfg.get("footer")
    if not want:
        return 0, []
    phs = tuple(cfg.get("legacy_footers", ())) + _PLACEHOLDER_DEFAULT
    svg_dir = os.path.join(proj, "svg")
    hits = []
    for f in sorted(glob.glob(os.path.join(svg_dir, "*.svg"))):
        t = open(f, encoding="utf-8").read()
        n = sum(t.count(p) for p in phs)
        if n:
            hits.append((f, n))
            if not dry:
                for p in phs:
                    t = t.replace(p, want)
                open(f, "w", encoding="utf-8").write(t)
    return sum(n for _, n in hits), hits


def main():
    ap = argparse.ArgumentParser(description="PPT 制作总管线")
    ap.add_argument("project", help="项目目录（需含 svg/）")
    ap.add_argument("--only", choices=["check", "svg", "pptx", "qa"], help="只跑某一阶段")
    ap.add_argument("--strict", action="store_true", help="体检查出 ERROR 就停")
    ap.add_argument("--apply-footer", action="store_true",
                    help="把骨架占位页脚换成 ppt.json 里的 footer（改写 svg/，慎用）")
    a = ap.parse_args()

    proj = os.path.abspath(a.project)
    if not os.path.isdir(proj):
        print(f"❌ 目录不存在：{proj}"); return 1
    print(f"▶ PPT 构建：{proj}")

    # 页脚占位检查 / 替换（在体检之前，这样后面的检查看的是最终文本）
    n_ph, hits = apply_footer(proj, dry=not a.apply_footer)
    if n_ph:
        if a.apply_footer:
            print(f"  ✍️  已把 {n_ph} 处占位页脚换成 ppt.json 的 footer（{len(hits)} 个文件）")
        else:
            print(f"  ⚠️  {n_ph} 处页脚仍是占位（{len(hits)} 个文件）——"
                  f"交付前必须处理")
            print(f"      一键替换：ppt_build.py \"{proj}\" --apply-footer")
            print(f"      或手动改成 ppt.json 里的 footer")

    stages = {"check": stage_check, "svg": stage_svg, "pptx": stage_pptx, "qa": stage_qa}
    seq = [a.only] if a.only else ["check", "svg", "pptx", "qa"]
    failed = []
    for s in seq:
        # check 需要 strict 参数，其余不需要
        ok = stages[s](proj, a.strict) if s == "check" else stages[s](proj)
        if not ok:
            failed.append(s)
            # 阶段失败一律停：后续阶段依赖前一步产物，硬跑只会产出"看起来成功"的残次品
            print(f"\n❌ 阶段「{s}」失败，已停止（后续阶段依赖它的产物）")
            if s == "pptx":
                print("   常见原因：某个 SVG 用了导出器不支持的属性。"
                      "先跑 `ppt_check.py <svg目录>`（它会直接指出是哪一页哪个属性）")
            return 1
    print(f"\n{BAR}\n✅ 全部 4 阶段通过 → {os.path.join(proj, 'out')}\n{BAR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
