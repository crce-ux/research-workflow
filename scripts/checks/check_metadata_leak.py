# -*- coding: utf-8 -*-
"""
check_metadata_leak.py —— 文档隐藏信息体检（匿名泄露面）

【用途】
    查 Office / PDF 文件里**看不见但带得走**的信息：
    文档属性里的真实姓名、机构、备注页、隐藏页。
    文档属性里的真实姓名、机构、备注页、隐藏页在**逐页看内容时完全查不出来**，但盲审、投稿、外部汇报时会泄露身份。

【适用场景】
    三个真实场景：
      ① **做审稿人** —— 稿件若含可识别信息，需要主动识别并回避
      ② **自己投稿** —— 盲审稿件须自查泄露面
      ③ **组会/外报 PPT 含未发表数据** —— 文档属性、备注页、隐藏页
         可能带出不该带的信息（如禁运期内的试验数据）

【用法】
    python check_metadata_leak.py 汇报.pptx
    python check_metadata_leak.py 04_组会汇报/PPTX/          # 目录：递归找 Office/PDF
    python check_metadata_leak.py 稿件.docx --scene blind     # 盲审场景（判据更严）
    python check_metadata_leak.py --dir <目录> --quiet

    退出码 = 命中项数（盲审场景下任一命中即 >0），可用于门禁。

【检查项】
    Office(.pptx/.docx/.xlsx)：
      • 核心属性  creator / lastModifiedBy / title / created / modified
      • 应用属性  Company / Manager / Application / Revision
      • PPTX 额外  备注页数量 · 隐藏页数量 · 批注
    PDF：
      • Author / Creator / Producer / Title（需 PyMuPDF，缺失则显式标注未检查）

【对应流程】
    `出稿检查总表.md` C 侧 · 交付 —— 匿名与隐藏元数据检查
    借鉴 Research-OS-Studio `paper-talk/references/talk-audit.md` §E（MIT）的检查面

【依赖】
    标准库（zipfile / xml / argparse）。PDF 需 PyMuPDF（`pip install pymupdf`），
    缺失时**逐文件标注"未检查"**，不静默跳过。

【踩坑教训】
    • ⚠️ **本脚本只报不改。** 改元数据可能破坏文档，且删除后未必不可恢复，
      由人决定怎么处理
    • Office 文件就是 zip，直接 zipfile 读 docProps/，不需要装 python-pptx
    • 属性存在不一定是问题：**单机自用改名不影响**；
      只有对外场景（盲审/投稿/外报）才构成泄露
"""
import argparse
import re
import sys
import zipfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

OFFICE_EXT = {".pptx", ".docx", ".xlsx", ".pptm", ".docm", ".xlsm"}
PDF_EXT = {".pdf"}
TARGET_EXT = OFFICE_EXT | PDF_EXT

# 核心属性里需要关注的字段（命名空间无关，按 localname 取）
CORE_FIELDS = ("creator", "lastModifiedBy", "title", "subject", "description",
               "keywords", "category", "contentStatus")
APP_FIELDS = ("Company", "Manager", "Application", "AppVersion",
              "TotalTime", "Template")

# 这些字段"有值"才算命中（其余只作展示）
RISKY_CORE = ("creator", "lastModifiedBy")
RISKY_APP = ("Company", "Manager")


def localname(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_props(xml_bytes: bytes) -> dict:
    """把 docProps/*.xml 解析成 {localname: text}，避免依赖命名空间前缀。"""
    from xml.etree import ElementTree as ET
    out = {}
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return out
    for el in root.iter():
        name = localname(el.tag)
        if el.text and el.text.strip():
            out[name] = el.text.strip()
    return out


def inspect_office(path: Path):
    """返回 (props_core, props_app, extra) —— extra 为 PPTX 专有发现。"""
    core, app, extra = {}, {}, {}
    try:
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            for member, target in (("docProps/core.xml", core),
                                   ("docProps/app.xml", app)):
                if member in names:
                    target.update(parse_props(z.read(member)))

            # PPTX 专有：备注页 / 隐藏页
            if path.suffix.lower() in (".pptx", ".pptm"):
                notes = [n for n in names
                         if re.match(r"ppt/notesSlides/notesSlide\d+\.xml$", n)]
                with_text = []
                for n in notes:
                    body = z.read(n).decode("utf-8", "replace")
                    # 去掉标签后看是否还有实质文字
                    plain = re.sub(r"<[^>]+>", "", body).strip()
                    if len(plain) > 20:
                        with_text.append(n)
                extra["备注页总数"] = len(notes)
                extra["备注页有内容"] = len(with_text)

                hidden = []
                for n in sorted(n for n in names
                                if re.match(r"ppt/slides/slide\d+\.xml$", n)):
                    head = z.read(n)[:2000].decode("utf-8", "replace")
                    if re.search(r'show="0"', head):
                        hidden.append(Path(n).stem)
                extra["隐藏页"] = hidden

                comments = [n for n in names if "comment" in n.lower()
                            and n.endswith(".xml")]
                extra["批注文件"] = len(comments)
    except zipfile.BadZipFile:
        extra["错误"] = "不是有效的 Office 文件（zip 解析失败）"
    except Exception as e:
        extra["错误"] = f"读取失败：{e}"
    return core, app, extra


def inspect_pdf(path: Path):
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return None, {"未检查": "未安装 PyMuPDF —— PDF 元数据**未检查**"}
    try:
        doc = fitz.open(str(path))
        md = doc.metadata or {}
        doc.close()
        core = {k: v for k, v in md.items() if v}
        return core, {"页数": ""}
    except Exception as e:
        return {}, {"错误": f"读取失败：{e}"}


def analyze(path: Path, scene: str):
    """返回 (命中列表, 展示字典)。命中 = 需要人工处置的项。"""
    hits, show = [], {}

    if path.suffix.lower() in OFFICE_EXT:
        core, app, extra = inspect_office(path)
        show["核心属性"] = {k: core.get(k) for k in CORE_FIELDS if core.get(k)}
        show["应用属性"] = {k: app.get(k) for k in APP_FIELDS if app.get(k)}
        show["结构"] = extra

        for f in RISKY_CORE:
            if core.get(f):
                hits.append(f"核心属性 {f} = 「{core[f]}」")
        for f in RISKY_APP:
            if app.get(f):
                hits.append(f"应用属性 {f} = 「{app[f]}」")
        if extra.get("备注页有内容"):
            hits.append(f"备注页有内容 {extra['备注页有内容']} 页"
                        f"（讲稿备注会随文件外发）")
        if extra.get("隐藏页"):
            hits.append(f"隐藏页 {len(extra['隐藏页'])} 页："
                        f"{', '.join(extra['隐藏页'][:6])}")
        if extra.get("批注文件"):
            hits.append(f"批注文件 {extra['批注文件']} 个")

    else:  # PDF
        core, extra = inspect_pdf(path)
        if core is None:
            show["未检查"] = extra["未检查"]
            return [], show
        show["PDF 元数据"] = {k: v for k, v in core.items()
                              if k in ("author", "creator", "producer",
                                       "title", "subject", "keywords")}
        if core.get("author"):
            hits.append(f"PDF author = 「{core['author']}」")
        if core.get("creator") and scene == "blind":
            hits.append(f"PDF creator = 「{core['creator']}」")

    if scene == "blind" and not hits:
        pass
    return hits, show


def main():
    ap = argparse.ArgumentParser(
        description="文档隐藏信息体检（匿名泄露面：文档属性/备注页/隐藏页）")
    ap.add_argument("paths", nargs="*", help="文件或目录（目录则递归找 Office/PDF）")
    ap.add_argument("--dir", help="等价于给一个目录")
    ap.add_argument("--scene", default="external",
                    choices=["external", "blind"],
                    help="场景：external 对外汇报（默认）/ blind 盲审投稿（判据更严）")
    ap.add_argument("--quiet", action="store_true", help="只列命中项")
    args = ap.parse_args()

    targets = []
    for raw in list(args.paths) + ([args.dir] if args.dir else []):
        p = Path(raw)
        if p.is_dir():
            targets += sorted(q for q in p.rglob("*")
                              if q.suffix.lower() in TARGET_EXT)
        elif p.exists():
            targets.append(p)
        else:
            print(f"⚠️  路径不存在，已跳过：{raw}")

    if not targets:
        print("未找到 Office / PDF 文件。")
        print("用法：python check_metadata_leak.py <文件或目录> [--scene blind]")
        return 0

    total = 0
    print(f"场景：{'盲审投稿' if args.scene == 'blind' else '对外汇报'}"
          f" ｜ 待检 {len(targets)} 个文件\n" + "=" * 52)

    for f in targets:
        hits, show = analyze(f, args.scene)
        total += len(hits)
        mark = "❌" if hits else "✅"
        print(f"\n{mark} {f.name}")
        if not args.quiet:
            for group, kv in show.items():
                if isinstance(kv, dict) and kv:
                    body = " · ".join(f"{k}={v}" for k, v in kv.items())
                    print(f"     {group}：{body}")
        for h in hits:
            print(f"   ⚠️  {h}")

    print("\n" + "=" * 52)
    if total == 0:
        print("✅ 未发现元数据泄露项")
    else:
        print(f"⚠️  共 {total} 个命中项，需人工确认是否对外可接受")
        print("   ⚠️ 本脚本只报不改——改元数据可能破坏文档，由人决定")
    return total


if __name__ == "__main__":
    sys.exit(main())
