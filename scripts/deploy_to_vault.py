# -*- coding: utf-8 -*-
"""deploy_to_vault.py —— D:\\Github 的 skill ↔ Obsidian 库里的运行副本

【为什么有它】
    `sync_skill_scripts.py` 管的是**一台仓内**的脚本副本（正本 → 各 skill）。
    但还有**第三套副本**：观测库 `.claude/skills/` 下那些真正被 agent 加载的目录。
    它们靠手工 robocopy / 手敲 python 同步——和当初 `check_skill_structure.py`
    散成 13 份是同一个病：**复制了，但没有机制保证一致。**

【它怎么找配对】
    扫 `--repo-root`（默认 `D:/Github`）下每个含 `SKILL.md` 的目录，
    拿目录名去两个库的 `.claude/skills/` 里找同名目录。
    找着就比；找不着就报「未部署」，不猜。

【默认只校验】
    python deploy_to_vault.py                # 报告差异，有差异退出码 1
    python deploy_to_vault.py --write        # 把差异覆盖过去（以仓为准）

⚠️ **方向是仓 → 库**。库里的目录**不回流到仓**——改了库里的副本不会自动回去，
   这正是要防的漂移。改内容请改仓，再跑这个。
"""
import argparse
import filecmp
import os
import pathlib
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 跳过这些东西：它们与「agent 加载什么」无关
SKIP_DIRS = {".git", ".github", "__pycache__", ".pytest_cache", ".venv"}
# ⚠️ `.gitignore` 是**仓的元数据**，不是 skill 内容——库里的副本不需要它。
#    不排掉它会永远报一条假差异，把真信号淹掉。
SKIP_NAMES = {".DS_Store", ".gitignore", ".gitattributes"}

DEFAULT_REPO_ROOT = "D:/Github"
# 库根 → 其 .claude/skills 子目录。环境变量优先。
VAULT_ENVS = [
    ("CHEN_VAULT_RESEARCH", "D:/obsidian/2026/5/科研"),
    ("CHEN_VAULT_PRIVATE", "D:/obsidian/2026/5/私人"),
]


def vault_skill_dirs():
    out = []
    for env, fallback in VAULT_ENVS:
        root = pathlib.Path(os.environ.get(env) or fallback)
        d = root / ".claude" / "skills"
        if d.is_dir():
            out.append(d)
    return out


def iter_files(root):
    """仓/库目录里参与比对的相对路径集合。"""
    got = {}
    for p in root.rglob("*"):
        rel = p.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if p.name in SKIP_NAMES:
            continue
        if p.is_file():
            got[str(rel).replace("\\", "/")] = p
    return got


def diff_one(src, dst):
    """返回 (仅仓里有, 仅库里有, 内容不同)。"""
    a, b = iter_files(src), iter_files(dst)
    only_src = sorted(set(a) - set(b))
    only_dst = sorted(set(b) - set(a))
    changed = sorted(r for r in set(a) & set(b)
                     if not filecmp.cmp(a[r], b[r], shallow=False))
    return only_src, only_dst, changed


def copy_tree(src, dst):
    for rel, p in iter_files(src).items():
        q = dst / rel
        q.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, q)


def main():
    ap = argparse.ArgumentParser(description="仓 → 库 的 skill 副本同步")
    ap.add_argument("--repo-root", default=DEFAULT_REPO_ROOT)
    ap.add_argument("--write", action="store_true", help="把差异覆盖到库里")
    ap.add_argument("--only", default=None, help="只处理某个 skill（目录名）")
    a = ap.parse_args()

    repo_root = pathlib.Path(a.repo_root)
    if not repo_root.is_dir():
        raise SystemExit(f"找不到 {repo_root}")
    vaults = vault_skill_dirs()
    if not vaults:
        raise SystemExit("找不到任何库的 .claude/skills（查了 CHEN_VAULT_RESEARCH / "
                         "CHEN_VAULT_PRIVATE 与默认路径）")

    repos = sorted(d for d in repo_root.iterdir()
                   if d.is_dir() and (d / "SKILL.md").is_file())
    if a.only:
        repos = [d for d in repos if d.name == a.only]

    print(f"deploy_to_vault · 仓 {repo_root} · 库 {len(vaults)} 处")
    dirty = undeployed = 0
    for src in repos:
        target = next((v / src.name for v in vaults if (v / src.name).is_dir()), None)
        if target is None:
            print(f"  · {src.name:<22} 未部署到任何库（跳过）")
            undeployed += 1
            continue
        only_src, only_dst, changed = diff_one(src, target)
        if not (only_src or only_dst or changed):
            print(f"  ✅ {src.name:<22} 一致 → {target.parent.parent.parent.name}库")
            continue
        dirty += 1
        print(f"  ⚠️ {src.name:<22} 与库不一致 → {target}")
        for r in only_src:
            print(f"       仓有库无：{r}")
        for r in only_dst:
            print(f"       库有仓无：{r}")
        for r in changed:
            print(f"       内容不同：{r}")
        if a.write:
            copy_tree(src, target)
            print("       ✍️ 已覆盖")

    print()
    if dirty == 0:
        print(f"✅ 全部一致（{len(repos) - undeployed} 个已部署 skill）")
        return 0
    if a.write:
        print(f"✍️ 已覆盖 {dirty} 个")
        return 0
    print(f"❌ {dirty} 个不一致——加 --write 覆盖（方向：仓 → 库）")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
