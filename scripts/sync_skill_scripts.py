# -*- coding: utf-8 -*-
"""sync_skill_scripts.py —— 正本 → 各 skill 的分发校验与同步

【为什么有它】
    本库的约定是「正本在 research-workflow，各 skill 的 scripts/ 是运行版」。
    但**没有任何机制保证两边一致**——只靠「改完记得同步」+ `cmp`。
    实测：`check_skill_structure.py` 一度有 **13 份**副本，一场会话里我手工重灌两次。

    ⚠️ 讽刺的是：同一场我对**外部** skill 的主张是「调用 > 复制，fork 完就是自己扛维护」。
    对别人的代码要求「别复制」，对自己的代码却在复制——**这个脚本是把这个双标收掉**。

【怎么找，不靠登记表】
    🔴 不维护一张「谁装了谁」的清单——那种表本身就会漂。
    改为**按内容反查**：扫每个 skill 的 scripts/，拿文件名去正本索引里找；
    找得到就比对，比对不过就报。**按信息找，不按登记表找。**

【用法】
    python sync_skill_scripts.py --root D:/Github            # 只校验（默认）
    python sync_skill_scripts.py --root D:/Github --write    # 把不一致的覆盖为正本

退出码 = 不一致的文件数（--write 后应为 0）
"""
import argparse
import filecmp
import pathlib
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 正本目录（**相对正本仓**，不是相对库根）
CANON_DIRS = ["scripts/checks", "scripts/literature", "scripts/evidence",
              "scripts/data", "scripts/ppt"]
CANON_REPO = "research-workflow"        # 正本所在的仓名

# ⚠️ 唯一一处改名映射：正本 skill_selfcheck.py → 分发名 selfcheck.py
RENAME = {"skill_selfcheck.py": "selfcheck.py"}

# 不做比对的（工具链自带 / 非正本）
SKIP_NAMES = {"setup.sh"}
# 只比对脚本本体——`scripts/README.md` 是**每个 skill 自己的**文档，不是分发物
COMPARE_SUFFIX = {".py", ".sh"}


def build_index(canon):
    """正本索引：分发名 → 正本绝对路径。"""
    index = {}
    for d in CANON_DIRS:
        cd = canon / d
        if not cd.is_dir():
            continue
        for f in sorted(cd.glob("*.py")):
            index[RENAME.get(f.name, f.name)] = f
    return index


def scan(root):
    """所有 skill 仓 = 库根下含 SKILL.md 的目录。"""
    return sorted(p for p in root.iterdir()
                  if p.is_dir() and (p / "SKILL.md").is_file())


def survey(root, canon_repo, index):
    """比对全部运行版。返回 (drift, orphan, copies, skipped)。
    drift 每项 = (skill 名, 文件名, 正本路径, 运行版路径)。"""
    drift, orphan, copies, skipped = [], [], 0, []
    for skill in scan(root):
        if skill.resolve() == canon_repo:
            continue                      # 正本自己不比
        sd = skill / "scripts"
        if not sd.is_dir():
            continue
        files = [f for f in sorted(sd.iterdir())
                 if f.is_file()
                 and f.suffix in COMPARE_SUFFIX
                 and f.name not in SKIP_NAMES]
        matched = [f for f in files if f.name in index]
        # 🔴 一个正本都对不上的 skill = **不参与分发**（如第三方仓自带自己的脚本），整仓跳过。
        #    否则它自己的脚本会被逐条报成「无正本」，淹没真信号。
        if not matched:
            skipped.append(skill.name)
            continue
        for f in files:
            src = index.get(f.name)
            if src is None:
                orphan.append((skill.name, f.name))
                continue
            copies += 1
            if not filecmp.cmp(src, f, shallow=False):
                drift.append((skill.name, f.name, src, f))
    return drift, orphan, copies, skipped


def main():
    ap = argparse.ArgumentParser(description="正本 → 各 skill 分发校验/同步")
    ap.add_argument("--root", default=".", help="含 research-workflow 与各 skill 的目录")
    ap.add_argument("--write", action="store_true", help="把不一致的覆盖为正本（默认只校验）")
    a = ap.parse_args()
    root = pathlib.Path(a.root).resolve()

    canon_repo = (root / CANON_REPO).resolve()
    index = build_index(canon_repo)
    if not index:
        print(f"❌ 在 {canon_repo} 下找不到正本（{', '.join(CANON_DIRS)}）")
        return 1

    print(f"sync_skill_scripts · 正本 {len(index)} 个 · 扫 {a.root}")
    drift, orphan, copies, skipped = survey(root, canon_repo, index)

    print(f"  运行版副本 {copies} 份"
          + (f" · 不参与分发 {len(skipped)} 个（{'、'.join(skipped)}）" if skipped else ""))

    for name, fname, src, dst in drift:
        if a.write:
            shutil.copyfile(src, dst)
        print(f"  {'✍️ ' if a.write else '❌'} {name}/{fname}"
              f"{'  ← 已覆盖为正本' if a.write else '  与正本不一致'}")
    for name, fname in orphan:
        print(f"  ○ {name}/{fname}：正本里没有同名文件——确认是否该收进正本")

    if not drift:
        print("  ✅ 全部副本与正本一致")
    print(f"\n  不一致 {len(drift)} · 无正本 {len(orphan)}"
          + ("（已全部覆盖）" if a.write and drift else ""))
    return 0 if not drift else len(drift)


if __name__ == "__main__":
    raise SystemExit(main())
