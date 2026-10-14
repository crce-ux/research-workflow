#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ppt_init.py —— **建一个新的 PPT 项目目录**（工具链的入口）

【背景】
    在此之前，起一个新汇报要手动 mkdir、手写 ppt.json、记目录约定，
    而且**很容易漏掉 images/ 或 ppt.json** —— 漏了要到合并阶段才报错。
    本脚本把「新项目 5 步」的第 1 步做成一条命令。

【用法】
    python ppt_init.py <项目目录> --title "汇报标题" --footer "页脚文字"
    python ppt_init.py ../我的汇报                      # 全部取默认（中性占位）

【它建什么】
    <项目>/
      svg/          页面放这里（文件名排序 = 页序）        【你维护】
      images/       图片资源                              【你维护】
      ppt.json      项目配置（页脚 / 受众 / 目标）         【可改】
      build.md      本册说明（标题、页码范围）              【可改】
      README.md     项目内速查（指向工具链手册）            【只读提示】

【建完之后】
    从 `PPT骨架模板_*/` 复制一个 .svg 到 `svg/01_xxx.svg`，填内容，
    然后 `python ppt_build.py <项目目录>`。
"""
import argparse
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from ppt_style import G, PX, C, FOOTER_TEXT  # noqa: E402


SKELETON_HINT = """# 本册说明

- **标题**：（填）
- **页序**：文件名排序 = 页序，用 `01_` `02_` 前缀
- **页码范围**：从 01 起

## 逐页要点

| 页 | 文件 | 讲什么 | 备注 |
|---|---|---|---|
| 01 | `svg/01_xxx.svg` | （填） | |

> 本文件供 `ppt_build.py` 与人工查阅；**不是必填**，但不写的话
> `spec_lock.md` 的 core_message 会显示"见 build.md 或制作稿"。
"""

README_TMPL = """# {title}

> 用**自建 PPT 工具链**做的汇报项目。手册见
> `_系统/_流程与工具/PPT工具链手册.md`。

## 目录约定

| 位置 | 谁维护 | 说明 |
|---|---|---|
| `svg/` | **你** | 页面 SVG，**文件名排序 = 页序** |
| `images/` | **你** | 图片；页面里用 `<image href="../images/xxx.png">` |
| `ppt.json` | 可改 | 项目配置（页脚 / 受众 / 目标） |
| `build.md` | 可改 | 本册说明 |
| `out/` | 自动 | 预览 PNG · PPTX · 成品渲染图 |

## 三条命令

```bash
# 1. 起页：从骨架库复制（骨架库在 _系统/_流程与工具/PPT骨架模板_*/）
cp "../_系统/_流程与工具/PPT骨架模板_20260915/配方30_带表头卡片.svg" svg/01_xxx.svg

# 2. 填内容后出成品（体检 → 预览 → PPTX → 成品验证）
python "../_系统/_流程与工具/_scripts/ppt_build.py" .

# 3. 单步重跑（改了一页想快点看）
python "../_系统/_流程与工具/_scripts/ppt_build.py" . --only check   # 只体检，秒级
```

## 交付前必过

- [ ] `ppt_check.py` 的 **占位残留清零**（`【说明】` 全删）
- [ ] 页脚文字与 `ppt.json` 一致（骨架默认是 `{footer}`）
- [ ] 图片确实放了（删图测试：把图删掉，图旁的说明文字是否还说得通）
"""

PPT_JSON_TMPL = {
    "footer": FOOTER_TEXT,
    "audience": "（填：谁看这场汇报）",
    "objective": "（填：这场汇报要达成什么）",
    "message": "（填：一句话核心信息）",
}


def main():
    ap = argparse.ArgumentParser(description="建一个新的 PPT 项目目录")
    ap.add_argument("project", help="项目目录（不存在则创建）")
    ap.add_argument("--title", default="", help="汇报标题（写进 README）")
    ap.add_argument("--footer", default="", help="页脚左侧文字（写进 ppt.json）")
    ap.add_argument("--force", action="store_true", help="已存在时仍写入模板文件")
    a = ap.parse_args()

    proj = os.path.abspath(a.project)
    if os.path.exists(proj) and os.listdir(proj) and not a.force:
        print(f"⚠️  目录已存在且非空：{proj}")
        print("    要覆盖模板文件（不删已有页面）请加 --force")
        return 1

    os.makedirs(os.path.join(proj, "svg"), exist_ok=True)
    os.makedirs(os.path.join(proj, "images"), exist_ok=True)

    footer = a.footer or FOOTER_TEXT
    title = a.title or os.path.basename(proj)

    cfg = dict(PPT_JSON_TMPL)
    cfg["footer"] = footer
    p = os.path.join(proj, "ppt.json")
    if not os.path.exists(p) or a.force:
        json.dump(cfg, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"  ✍️  ppt.json        （页脚：{footer}）")
    else:
        print("  ⏭  ppt.json         已存在，保留")

    for fn, body in [("build.md", SKELETON_HINT),
                     ("README.md", README_TMPL.format(title=title, footer=footer))]:
        p = os.path.join(proj, fn)
        if not os.path.exists(p) or a.force:
            open(p, "w", encoding="utf-8").write(body)
            print(f"  ✍️  {fn}")
        else:
            print(f"  ⏭  {fn}         已存在，保留")

    print(f"\n✅ 项目已建：{proj}")
    print(f"   画布 {G['w']}×{G['h']} ｜ 边距 {G['margin']} ｜ 主色 {C['main']}")
    print(f"   字号(px) 大标语 {PX['statement']} / 封面 {PX['cover']} / 标题 {PX['title']}"
          f" / 正文 {PX['body']} / 图注 {PX['caption']}")
    print()
    print("   下一步：从骨架库复制一个 .svg 到 svg/ 填内容，然后")
    print(f"     python {os.path.join(HERE, 'ppt_build.py')} \"{proj}\"")
    return 0


if __name__ == "__main__":
    sys.exit(main())
