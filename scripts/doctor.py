# -*- coding: utf-8 -*-
"""doctor.py —— 一条命令跑完本仓的全部体检

【跑哪几项】
    本仓有四个检查项，各有一个工具，跑一次要点四条命令：

        结构   check_skill_structure.py --root D:/Github
        资产   check_assets.py --root .
        副本①  sync_skill_scripts.py --root D:/Github     （仓内各 skill 的 scripts/）
        副本②  deploy_to_vault.py                          （观测库 .claude/skills/）
        单测   pytest tests/

    收成一条命令：全绿，或指出哪条没过。

用法：
    python scripts/doctor.py [--repo-root D:/Github] [--no-tests] [--full]

    --full  连原始输出一起打（默认只打每项的结论行）

退出码 = 失败项数（0 = 全绿）。
"""
import argparse
import os
import pathlib
import re
import shutil
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}

# 结论行的识别：各工具都打印 ✅ / ❌ / ⚠️ 开头的汇总行
SUMMARY = re.compile(r"^\s*(✅|❌|⚠️|🛑|汇总|不一致|✍️|全部|本次未评)")


def run(label, argv, summary_filter=None):
    """跑一条命令（argv 是完整命令），返回 (label, ok, 结论行, 原始输出)。"""
    try:
        p = subprocess.run(argv, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=ENV, cwd=str(ROOT))
    except FileNotFoundError as e:
        return label, False, [f"起不了进程：{e}"], ""
    out = (p.stdout or "") + (p.stderr or "")
    lines = [ln.rstrip() for ln in out.splitlines() if ln.strip()]
    if summary_filter:
        picked = [ln for ln in lines if summary_filter(ln)] or lines[-1:]
    else:
        picked = [ln for ln in lines if SUMMARY.search(ln)][-4:] or lines[-3:]
    return label, p.returncode == 0, picked, out


def main():
    ap = argparse.ArgumentParser(description="本仓一条命令体检")
    ap.add_argument("--repo-root", default="D:/Github")
    ap.add_argument("--no-tests", action="store_true")
    ap.add_argument("--full", action="store_true", help="连原始输出一起打")
    a = ap.parse_args()

    py = sys.executable
    jobs = [
        ("结构", [py, str(HERE / "checks/check_skill_structure.py"), "--root", a.repo_root], None),
        ("资产", [py, str(HERE / "checks/check_assets.py"), "--root", "."], None),
        ("副本① 仓内", [py, str(HERE / "sync_skill_scripts.py"), "--root", a.repo_root], None),
        ("副本② 观测库", [py, str(HERE / "deploy_to_vault.py"), "--repo-root", a.repo_root], None),
    ]
    if not a.no_tests:
        # ⚠️ 本机系统 python 没装 pytest——跑测试要走 uv。没有 uv 就退回直跑。
        # ⚠️ 不要再加 `-q`：pyproject 的 addopts 已经是 `-q`，
        # 两个叠成 `-qq` 会连「N passed」行也吞掉。
        if shutil.which("uv"):
            tests = ["uv", "run", "--with", "pytest", "python", "-m", "pytest",
                     "tests/", "-p", "no:cacheprovider"]
        else:
            tests = [py, "-m", "pytest", "tests/", "-p", "no:cacheprovider"]
        jobs.append(("单测", tests,
                     lambda ln: re.search(r"\d+ (passed|failed|error)", ln)
                     or "passed" in ln or "failed" in ln))

    print(f"doctor · 仓 {ROOT} · repo-root {a.repo_root}")
    print(f"  {'项':<14}判定")
    failed = []
    for label, argv, filt in jobs:
        name, ok, lines, raw = run(label, argv, filt)
        print(f"  {name:<14}{'✅ 通过' if ok else '❌ 未过'}")
        for ln in lines:
            print(f"        {ln.strip()[:150]}")
        if not ok:
            failed.append((name, raw))
        if a.full and raw:
            print("        ── 原始输出 ──")
            for ln in raw.splitlines():
                print(f"        {ln}")

    print()
    if not failed:
        print("✅ 全绿")
        return 0
    print(f"❌ {len(failed)} 项未过：" + " / ".join(n for n, _ in failed))
    print("   （加 --full 看原始输出）")
    return len(failed)


if __name__ == "__main__":
    raise SystemExit(main())
