# -*- coding: utf-8 -*-
"""deploy_to_vault.py —— D:\\Github 的 skill ↔ Obsidian 库里的运行副本

【管哪几套副本】
    `sync_skill_scripts.py` 管**一台仓内**的脚本副本（正本 → 各 skill）。
    还有**第三套副本**：观测库 `.claude/skills/` 下被 agent 加载的目录。
    它们靠手工 robocopy / 手敲 python 同步，没有机制保证与正本一致。

【它怎么找配对】
    扫 `--repo-root`（默认 `D:/Github`）下每个含 `SKILL.md` 的目录，
    拿目录名去两个库的 `.claude/skills/` 里找同名目录。
    找着就比；找不着就报「未部署」，不猜。

【默认只校验】
    python deploy_to_vault.py                # 报告差异，有差异退出码 1
    python deploy_to_vault.py --write        # 把差异覆盖过去（以仓为准）

【写到哪】
    ① 各库的 `.claude/skills/`（项目级）；
    ② 科研助手的私有 `.claude/skills/`（agent 级）。
    ⚠️ **两处同名时旧的那份可能先被读到**——只同步一处等于没部署。
    个人助手（a04fe676）默认不同步，需要时加 --agent-dir。

⚠️ **方向是仓 → 库**。库里的目录**不回流到仓**——改了库里的副本不会自动回去。
   改内容请改仓，再跑本脚本。
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
#    不排掉它会永远报一条假差异，掩盖真差异。
SKIP_NAMES = {".DS_Store", ".gitignore", ".gitattributes"}

DEFAULT_REPO_ROOT = "D:/Github"
# 库根 → 其 .claude/skills 子目录。环境变量优先。
VAULT_ENVS = [
    ("CHEN_VAULT_RESEARCH", "D:/obsidian/2026/5/科研"),
    ("CHEN_VAULT_PRIVATE", "D:/obsidian/2026/5/私人"),
]
# Agent 私有 skill 目录。Cherry Studio 每个 agent 各有一份，与库里的项目级目录并存。
# ⚠️ **同名时旧的那份可能先被读到**——不一起同步，就等于没部署。
# 只放科研助手。个人助手（a04fe676）的 skill 是另一套，需要时用 --agent-dir 显式加。
DEFAULT_AGENT_SKILLS = [
    "C:/Users/Chen Chen/AppData/Roaming/CherryStudio/Data/Agents/pubmed-zotero/.claude/skills",
]


def vault_skill_dirs():
    out = []
    for env, fallback in VAULT_ENVS:
        root = pathlib.Path(os.environ.get(env) or fallback)
        d = root / ".claude" / "skills"
        if d.is_dir():
            out.append(d)
    return out


def agent_skill_dirs(extra=None):
    """Agent 私有目录。环境变量 CHEN_AGENT_SKILLS（多值用 ; 分隔）优先。"""
    out = []
    cands = []
    env = os.environ.get("CHEN_AGENT_SKILLS")
    if env:
        cands += [p for p in env.split(";") if p.strip()]
    cands += DEFAULT_AGENT_SKILLS
    cands += list(extra or [])
    for c in cands:
        d = pathlib.Path(c)
        if d.is_dir() and d not in out:
            out.append(d)
    return out


def label_of(target):
    """科研/.claude/skills/X 或 Agents/pubmed-zotero/.claude/skills/X → 上层名字。"""
    return target.parent.parent.parent.name


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


def skill_dirs(root):
    """找到所有 skill 目录。

    ① 库根下的**直接子目录**里带 SKILL.md 的；
    ② 各仓 `skills/<名字>/` 里的——**总仓内嵌的 skill 包**。
    ⚠️ **只下探一层**——再深就分不清「skill 包」与「skill 里引用的示例目录」。
    """
    out = []
    for p in sorted(root.iterdir()):
        if not p.is_dir():
            continue
        if (p / "SKILL.md").is_file():
            # 一个仓可以既是可安装的 skill，又带内嵌包——两边都算
            out.append(p)
        pack = p / "skills"
        if pack.is_dir():
            out += [q for q in sorted(pack.iterdir())
                    if q.is_dir() and (q / "SKILL.md").is_file()]
    return out


def main():
    ap = argparse.ArgumentParser(description="仓 → 库与 agent 的 skill 副本同步")
    ap.add_argument("--repo-root", default=DEFAULT_REPO_ROOT)
    ap.add_argument("--write", action="store_true", help="把差异覆盖到库与 agent 目录")
    ap.add_argument("--only", default=None, help="只处理某个 skill（目录名）")
    ap.add_argument("--agent-dir", action="append", default=None,
                    help="额外或替代的 agent skill 目录，可重复")
    a = ap.parse_args()

    repo_root = pathlib.Path(a.repo_root)
    if not repo_root.is_dir():
        raise SystemExit(f"找不到 {repo_root}")
    vaults = vault_skill_dirs()
    agents = agent_skill_dirs(a.agent_dir)
    if not vaults and not agents:
        raise SystemExit("找不到任何 .claude/skills（查了 CHEN_VAULT_RESEARCH / "
                         "CHEN_VAULT_PRIVATE / CHEN_AGENT_SKILLS 与默认路径）")

    repos = skill_dirs(repo_root)
    if a.only:
        repos = [d for d in repos if d.name == a.only]

    targets = vaults + agents
    print(f"deploy_to_vault · 仓 {repo_root} · 目标 {len(vaults)} 个库 + "
          f"{len(agents)} 个 agent")
    dirty = undeployed = 0
    for src in repos:
        found = [(d / src.name) for d in targets if (d / src.name).is_dir()]
        if not found:
            print(f"  · {src.name:<22} 未部署到任何目标（跳过）")
            undeployed += 1
            continue
        for target in found:
            lab = label_of(target)
            only_src, only_dst, changed = diff_one(src, target)
            if not (only_src or only_dst or changed):
                print(f"  ✅ {src.name:<22} 一致 → {lab}")
                continue
            dirty += 1
            print(f"  ⚠️ {src.name:<22} 与 {lab} 不一致")
            for r in only_src:
                print(f"       仓有副本无：{r}")
            for r in only_dst:
                print(f"       副本有仓无：{r}")
            for r in changed:
                print(f"       内容不同：{r}")
            if a.write:
                copy_tree(src, target)
                print("       ✍️ 已覆盖")

    print()
    if dirty == 0:
        print(f"✅ 全部一致（{len(repos) - undeployed} 个已部署 skill × {len(targets)} 处）")
        return 0
    if a.write:
        print(f"✍️ 已覆盖 {dirty} 处")
        return 0
    print(f"❌ {dirty} 处不一致——加 --write 覆盖（方向：仓 → 副本）")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
