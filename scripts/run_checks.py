# -*- coding: utf-8 -*-
"""run_checks.py —— 跑一批检查器，把发现写进「待修清单」

【为什么有它】
    闭环缺的最后一环：检查器跑完，发现**只留在终端里**，要人手工抄进待修清单。
    实测：10 条发现是我手工捞进去的。下次谁记得抄？

【怎么不破坏「工具无关」】
    检查器自己**不该知道库路径**——那会让它们没法单独安装。
    所以由**这个驱动脚本**接：它跑检查器、收输出、写文件。检查器一行不改。

【怎么挑检查器】
    🔴 **试跑，不查登记表**（设计纪律 5：按信息找）。扫 `checks/check_*.py`，
    每个跑一次；**收不了单一路径参数的**（argparse 报 usage）自动跳过。
    以后新增检查器不用回来改这里。

【AUTO 区按**目标**分段】
    ⚠️ 不能整块重写——否则跑目标 B 会把目标 A 的发现冲掉。
    每个目标一段，脚本只重写**本次目标**那一段，其余原样保留。

【用法】
    python run_checks.py --target <文件或目录> --ledger <待修清单.md>
    python run_checks.py --target ... --dry-run          # 只打印，不写
"""
import argparse
import datetime
import os
import pathlib
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = pathlib.Path(__file__).resolve().parent
CHECKS_DIR = HERE / "checks"

BEGIN = "<!-- AUTO:BEGIN"
END = "<!-- AUTO:END -->"
FINDING = re.compile(r"^\s*(?:❌|○)\s+(.*)$")
SECTION = re.compile(r"^## 目标：(.+)$", re.M)
TIMEOUT = 180


def discover():
    return sorted(CHECKS_DIR.glob("check_*.py"))


def run_one(script, target):
    """跑一个检查器。返回 (findings, status)。status ∈ ok / skip / error。"""
    try:
        # ⚠️ 必须给子进程 UTF-8——Windows 下子进程默认按 GBK 写 stdout，
        #    中文与 ❌/○ 会变成乱码，**发现就抓不到了**（静默丢结果）。
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        r = subprocess.run([sys.executable, str(script), str(target)],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=TIMEOUT, cwd=str(CHECKS_DIR),
                           env=env)
    except subprocess.TimeoutExpired:
        return [], "error"
    err = r.stderr or ""
    if r.returncode == 2 and ("usage:" in err or "unrecognized arguments" in err):
        return [], "skip"

    # ⚠️ **不拆「文件 / 发现」两列**——各检查器格式不同：
    #    `❌ <文>: <说明>`（多数）  vs  `❌ <目录>：<文件>` + 缩进续行（check_metadata_leak）。
    #    硬拆会把后者解析错。**整行原文照存**，格式无关、不会误读。
    seen, out = set(), []
    for line in (r.stdout or "").splitlines():
        m = FINDING.match(line)
        if not m:
            continue
        body = m.group(1).strip()
        if body and body not in seen:
            seen.add(body)
            out.append(body)
    return out, "ok"


def parse_auto(text):
    """把 AUTO 区解析成 {目标: 该段原文}。"""
    m = re.search(re.escape(BEGIN) + r".*?" + re.escape(END), text, re.S)
    if not m:
        return {}
    inner = m.group(0)
    parts = SECTION.split(inner)
    sections = {}
    # parts = [前言, 目标1, 段1, 目标2, 段2, ...]
    for i in range(1, len(parts) - 1, 2):
        sections[parts[i].strip()] = parts[i + 1]
    return sections


def parse_rows(section_text):
    """从某目标的段里取出已有条目（用于算「本次未复现」）。"""
    rows = set()
    for line in section_text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[0] not in ("检查器", "") \
                and not set(cells[0] + cells[1]) <= set("-: "):
            rows.add((cells[0].strip("`"), cells[1]))
    return rows


def render_section(target, findings, gone, skipped, stamp):
    esc = str(target).replace("|", "\\|")
    out = [f"## 目标：{esc}", "",
           f"_最近一次运行：{stamp} · 发现 {len(findings)} 条_", ""]
    if findings:
        out += ["| 检查器 | 发现 | 状态 |", "|---|---|---|"]
        for chk, body in findings:
            out.append(f"| `{chk}` | {body.replace('|', '\\|')} | ☐ |")
    else:
        out.append("_本次没有报出任何发现。_")
    if gone:
        out += ["", "**本次未复现**（上次有、这次没有）——**消失 ≠ 已处置**：",
                "确认后请挪到「已处置」并写明是改了稿、还是判据变了。", ""]
        for chk, body in sorted(gone):
            out.append(f"- `{chk}` ｜ {body}")
    if skipped:
        out += ["", f"_未跑：{'、'.join('`' + s + '`' for s in skipped)}"
                    f"（不收单一路径参数）_"]
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description="跑检查器并把发现写进待修清单")
    ap.add_argument("--target", required=True, help="文件或目录")
    ap.add_argument("--ledger", required=True, help="待修清单 .md（须含 AUTO 标记）")
    ap.add_argument("--dry-run", action="store_true", help="只打印，不写")
    a = ap.parse_args()

    target = pathlib.Path(a.target).resolve()
    if not target.exists():
        print(f"❌ 目标不存在：{target}")
        return 2
    ledger = pathlib.Path(a.ledger)
    if not ledger.is_file():
        print(f"❌ 找不到待修清单：{ledger}")
        return 2
    text = ledger.read_text(encoding="utf-8", errors="replace")
    if BEGIN not in text or END not in text:
        print(f"❌ 清单里没有 {BEGIN} … {END} 标记——先加上，避免覆盖手写内容")
        return 2

    findings, skipped, errored = [], [], []
    scripts = discover()
    print(f"run_checks · 目标 {target} · 检查器 {len(scripts)} 个")
    for s in scripts:
        fs, status = run_one(s, target)
        if status == "skip":
            skipped.append(s.stem)
        elif status == "error":
            errored.append(s.stem)
        else:
            findings += [(s.stem, b) for b in fs]

    key = str(target)
    sections = parse_auto(text)
    prev = parse_rows(sections.get(key, ""))
    cur = set(findings)
    gone = prev - cur

    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    sections[key] = render_section(target, findings, gone, skipped, stamp)

    block = (f"{BEGIN} · 由 scripts/run_checks.py 生成 · **手工编辑会被覆盖** -->\n"
             + "\n".join(sections[k].rstrip() + "\n" for k in sorted(sections))
             + END)

    print(f"  跑通 {len(scripts) - len(skipped) - len(errored)} · "
          f"跳过 {len(skipped)} · 出错 {len(errored)}"
          + (f"（{'、'.join(errored)}）" if errored else ""))
    print(f"  目标「{target.name}」：发现 {len(cur)} 条 · 未复现 {len(gone)} 条"
          f" · 清单共 {len(sections)} 个目标")

    if a.dry_run:
        print("\n" + sections[key])
        return 0

    # ⚠️ 替换串里全是 Windows 反斜杠路径——用 re.sub 的字符串替换会把 `\O` 当转义
    #    （`bad escape \O`）。**必须传函数**，函数返回值按字面处理。
    new = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END),
                 lambda _m: block, text, flags=re.S)
    ledger.write_text(new, encoding="utf-8")
    print(f"\n  ✍️ 已写入 {ledger}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
