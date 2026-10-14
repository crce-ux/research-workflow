# -*- coding: utf-8 -*-
"""pick_layout.py —— 制作稿 → 版式配方的匹配

【为什么要这一步】
    本库把 7 套模板扫读成 32 个版式配方（`references/layout-recipes.md`），
    并给出可复制的整页骨架（`assets/skeletons/`）。但从「制作稿」到「配方」
    一直是人工目视挑选——翻预览图，挑一个看着像的。
    后果：配方库不参与流程，模块化白做。

    本脚本把匹配变成一条命令，三个方向：
      正向  读制作稿本页的内容字段 → 按内容形态给候选配方
      核对  制作稿自己写的「版式建议」，与内容形态给出的候选对不对得上
      反向  指定一个配方 → 回查这一页缺什么素材

【只读内容字段，不读版式建议】
    特征只从「标题 / 页面文字 / 表格数据 / 图表说明」抽。
    「版式建议」是作者自己写的答案，拿它当输入就成了自问自答。
    它另有用途：与候选比对，看想用的版式与内容形态是否一致。

【数据源】
    `recipes.json`（与脚本同目录）。默认按顺序找：
      ① `--recipes` 指定  ② 脚本同目录  ③ 当前目录
    用 JSON 而不是 YAML：本库脚本一律零依赖，不引入 pyyaml。
    找不到就打印「本次未评」并退出 2 —— 不静默通过。

【用法】
    python pick_layout.py 制作稿.md                 # 全篇逐页给候选
    python pick_layout.py 制作稿.md --page S3       # 只看 S3 页
    python pick_layout.py 制作稿.md --page S3 --recipe 17   # 反向：查配方 17 缺什么
    python pick_layout.py --audit                   # 配方表自检（表 ↔ 文档 ↔ 骨架）

【退出码】
    0  正常
    1  反向模式发现缺料，或版式建议与候选对不上
    2  找不到配方表 / 找不到指定页（本次未评）

【不查什么】
    只比「内容形态」与「配方要求」。选型的最终判断是人的事——
    候选说明「像不像」，不说明「该不该」。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ── 页面切分：`## S3 · 标题` / `## P03 · 标题` / `## 3.1 标题` ──────
PAGE_RE = re.compile(r"^#{2,3}\s*([A-Za-z]?\d+(?:\.\d+)*)\s*[·、:：\s]\s*(.*)$", re.M)

# ── 制作稿七项：`**③ 页面文字**：` ────────────────────────────────
FIELD_RE = re.compile(r"^\*\*([①②③④⑤⑥⑦])\s*([^*]*?)\*\*\s*[:：]?", re.M)

# 七种字段的别名表只有一份，在 `check_talk.py` 里——别处不要再抄。
# 本脚本在正本仓位于 `scripts/ppt/`，在 skill 包内与 `check_talk.py` 同目录，两处都要能找到。
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "checks"))
try:
    from check_talk import FIELD_ALIASES, CONTENT_KINDS, classify_field  # noqa: F401
except ImportError as exc:  # pragma: no cover
    print(f"读不到 check_talk 的字段别名表（{exc}）—— 本次未评（不是查过了通过）")
    raise SystemExit(2)

# ── 并列项：引用行 / 无序 / 有序 ─────────────────────────────────
ITEM_RE = re.compile(r"^\s*(?:>\s*)?(?:[-*•]|\d+[.)、]|[①②③④⑤⑥⑦⑧⑨⑩])\s*\S")
# ── 图 / 截图 ───────────────────────────────────────────────────
FIG_RE = re.compile(r"截图|配图|附图|示意图|组图|图\s*\d|[Ff]igure\s*\d|\.(?:png|jpe?g|svg)\b")
# ── 表格 ───────────────────────────────────────────────────────
PIPE_RE = re.compile(r"^\s*\|.*\|.*\|\s*$", re.M)
# ── 数字：带单位或百分号，排除 19xx / 20xx 年份 ──────────────────
NUM_RE = re.compile(r"\d+(?:[.,]\d+)?\s*(?:%|％|例|篇|条|倍|人|次|万|亿|个|项|分|秒|分钟)")
YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")
# ── 版式建议里写到的配方号 ─────────────────────────────────────
RECIPE_RE = re.compile(r"配方\s*(\d+)")

# ── 关系词：决定用哪种连接件 ────────────────────────────────────
RELATIONS = {
    "因果": ["因此", "所以", "导致", "从而", "得出结论", "推论", "可见"],
    "并列": ["分别", "并列", "三方面", "几方面", "横排", "并排"],
    "对照": ["对照", "对比", "相比", "已完成", "拟开展", "现状", "与目标"],
    "汇聚": ["共同", "汇聚", "汇总", "多个因素", "一起"],
    "流程": ["步骤", "流程", "技术路线", "先", "随后", "然后"],
    "时间": ["里程碑", "进展", "历程", "时间轴", "年表"],
    "分解": ["分解", "拆成", "子目标", "若干条", "分为"],
}


# ── 找配方表 ────────────────────────────────────────────────────
def find_recipes(explicit: str | None = None) -> pathlib.Path | None:
    if explicit:
        p = pathlib.Path(explicit)
        return p if p.is_file() else None
    here = pathlib.Path(__file__).resolve().parent
    for c in (here / "recipes.json", pathlib.Path.cwd() / "recipes.json"):
        if c.is_file():
            return c
    return None


def load_recipes(path: pathlib.Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8")).get("recipes", [])


def find_asset(rel: str, is_dir: bool = False) -> pathlib.Path | None:
    """找 `references/layout-recipes.md`、`assets/skeletons` 这类 skill 包内的资产。

    正本仓（research-workflow）与 skill 包（academic-slides）是两棵目录树，
    同一份资产的相对位置不同，所以按几处候选依次找：
      ① skill 包内：`scripts/` 的上一级
      ② 兄弟仓：`<仓根>/academic-slides/`（正本仓跑 audit 时走这条）
      ③ 当前目录
    """
    here = pathlib.Path(__file__).resolve().parent          # …/scripts/ppt 或 …/scripts
    cands = []
    for base in (here.parent, here.parent.parent, here.parent.parent.parent):
        cands.append(base / rel)                            # skill 包内 / 仓内
        cands.append(base / "academic-slides" / rel)        # 兄弟仓（正本仓跑 audit 走这条）
    cands.append(pathlib.Path.cwd() / rel)
    for c in cands:
        if (c.is_dir() if is_dir else c.is_file()):
            return c
    return None


# ── 制作稿解析 ──────────────────────────────────────────────────
def split_pages(text: str) -> list[tuple[str, str, str]]:
    hits = list(PAGE_RE.finditer(text))
    if not hits:
        return [("(全篇)", "", text)]
    out = []
    for i, m in enumerate(hits):
        end = hits[i + 1].start() if i + 1 < len(hits) else len(text)
        out.append((m.group(1), m.group(2).strip(), text[m.end():end]))
    return out


def parse_fields(body: str) -> dict[str, str]:
    """→ {字段种类: 内容}。认不出的标签直接跳过（check_talk 会把它们报出来）。"""
    out: dict[str, str] = {}
    hits = list(FIELD_RE.finditer(body))
    for i, m in enumerate(hits):
        kind = classify_field(m.group(2))
        if kind is None:
            continue
        end = hits[i + 1].start() if i + 1 < len(hits) else len(body)
        out[kind] = body[m.end():end].strip()
    return out


def clean(text: str) -> str:
    return "\n".join(re.sub(r"^\s*>\s?", "", ln) for ln in text.splitlines()).strip()


def features(fields: dict[str, str]) -> dict:
    """只从内容字段抽特征。"""
    content = "\n".join(clean(fields.get(k, "")) for k in CONTENT_KINDS)
    body_lines = [ln for ln in clean(fields.get("正文", "")).splitlines() if ln.strip()]
    items = sum(1 for ln in body_lines if ITEM_RE.match(ln)) or len(body_lines)
    tbl_txt = clean(fields.get("表格", ""))
    table = 0 if not tbl_txt or tbl_txt.startswith("无") else 1
    if PIPE_RE.search(content):
        table = 1
    figs = len(FIG_RE.findall(clean(fields.get("图注", ""))))
    nums = len(set(NUM_RE.findall(YEAR_RE.sub("", content))))
    rel = {k: sum(1 for w in ws if w in content) for k, ws in RELATIONS.items()}
    return {"items": items, "tables": table, "figures": figs, "numbers": nums,
            "relations": {k: v for k, v in rel.items() if v},
            "n_chars": len(re.sub(r"\s", "", content))}


# ── 打分 ────────────────────────────────────────────────────────
def _range_fit(value: int, lo: int, hi: int) -> tuple[int, int]:
    if lo <= value <= hi:
        return 2, 0
    if value < lo:
        return -2 * (lo - value), lo - value
    return -1, 0


def score(recipe: dict, feat: dict, content: str) -> tuple[int, list[str], list[str]]:
    why, miss = [], []
    s = 0

    hit = [t for t in recipe.get("triggers", []) if t in content]
    s += 3 * min(len(hit), 3)
    if hit:
        why.append("命中词：" + "、".join(hit[:4]))

    n = recipe.get("needs", {})
    for key, label in (("items", "并列项"), ("figures", "图"), ("numbers", "数字")):
        lo, hi = n.get(key, [0, 0])
        d, m = _range_fit(feat[key], lo, hi)
        s += d
        if m:
            miss.append(f"缺 {m} 个{label}（配方要 ≥{lo}，这页 {feat[key]}）")
        elif d > 0 and lo:
            why.append(f"{label} {feat[key]} 个，在配方区间内")

    if n.get("tables"):
        if feat["tables"]:
            s += 2
            why.append("有表格")
        else:
            s -= 4
            miss.append("配方要有表格，这页没有")

    if feat["relations"]:
        why.append("关系词：" + "、".join(feat["relations"]))
    return s, why, miss


def rank(content: str, feat: dict, recipes: list[dict], top: int):
    scored = [(r, *score(r, feat, content)) for r in recipes]
    scored.sort(key=lambda x: -x[1])
    return scored[:top]


# ── 配方表自检 ──────────────────────────────────────────────────
def audit(recipes: list[dict], doc: pathlib.Path | None, skel_dir: pathlib.Path | None) -> int:
    bad = 0
    ids = [r["id"] for r in recipes]
    print(f"配方表：{len(ids)} 个（{min(ids)}–{max(ids)}）")
    if len(set(ids)) != len(ids):
        print("  ✗ 有重复编号")
        bad += 1

    if doc and doc.is_file():
        in_doc = sorted({int(m) for m in re.findall(r"### 配方 (\d+)｜", doc.read_text(encoding="utf-8"))})
        only_tbl = sorted(set(ids) - set(in_doc))
        only_doc = sorted(set(in_doc) - set(ids))
        if only_tbl or only_doc:
            print(f"  ✗ 配方表与文档不一致：只在表 {only_tbl}｜只在文档 {only_doc}")
            bad += 1
        else:
            print(f"  ✅ 配方表与 {doc.name} 的编号集合一致（{len(in_doc)} 个）")
    else:
        print("  ⚠️ 没找到 layout-recipes.md —— 编号一致性本次未评")
        bad += 1

    if skel_dir and skel_dir.is_dir():
        have = {p.name for p in skel_dir.glob("*.svg")}
        want = {r["skeleton"] for r in recipes if r.get("skeleton")}
        lost = sorted(want - have)
        if lost:
            print(f"  ✗ 配方声明了骨架但文件不在：{lost}")
            bad += 1
        else:
            print(f"  ✅ 配方声明的 {len(want)} 个骨架都在（目录内共 {len(have)} 个）")
    else:
        print("  ⚠️ 没找到 assets/skeletons/ —— 骨架存在性本次未评")

    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="制作稿 → 版式配方匹配")
    ap.add_argument("manuscript", nargs="?", help="制作稿 .md")
    ap.add_argument("--page", help="只看这一页（页号）")
    ap.add_argument("--recipe", type=int, help="反向：指定配方，查这一页缺什么素材")
    ap.add_argument("--top", type=int, default=4, help="候选数（默认 4）")
    ap.add_argument("--recipes", help="recipes.json 路径")
    ap.add_argument("--audit", action="store_true", help="配方表自检")
    a = ap.parse_args()

    path = find_recipes(a.recipes)
    if path is None:
        print("找不到 recipes.json —— 本次未评（不是查过了通过）")
        return 2
    recipes = load_recipes(path)
    by_id = {r["id"]: r for r in recipes}

    if a.audit:
        return audit(recipes, find_asset("references/layout-recipes.md", is_dir=False),
                     find_asset("assets/skeletons", is_dir=True))

    if not a.manuscript:
        ap.error("需要一份制作稿，或用 --audit")
    text = pathlib.Path(a.manuscript).read_text(encoding="utf-8", errors="replace")
    pages = [p for p in split_pages(text) if not a.page or p[0] == a.page]
    if not pages:
        print(f"没找到页 {a.page}（页标题要写成 `## S3 · 标题`）")
        return 2

    rc = 0
    for pid, title, body in pages:
        f = parse_fields(body)
        if not f:
            print(f"\n=== {pid} {title} ===")
            print("  这页没有可识别的七项字段——跳过（不是查过了通过）")
            continue
        feat = features(f)
        content = "\n".join(clean(f.get(k, "")) for k in CONTENT_KINDS)
        print(f"\n=== {pid} {title} ===")
        print(f"  形态：并列项 {feat['items']}｜表 {feat['tables']}｜图 {feat['figures']}"
              f"｜数字 {feat['numbers']}｜{feat['n_chars']} 字")

        if a.recipe:
            r = by_id.get(a.recipe)
            if r is None:
                print(f"  配方 {a.recipe} 不在表里")
                return 2
            _, why, miss = score(r, feat, content)
            print(f"  蓝图：配方 {r['id']} {r['name']}")
            for w in why:
                print(f"    · {w}")
            if miss:
                print("  缺料：")
                for m in miss:
                    print(f"    ✗ {m}")
                rc = 1
            else:
                print("  ✅ 素材齐")
            continue

        cands = rank(content, feat, recipes, a.top)
        for r, s, why, miss in cands:
            print(f"  配方 {r['id']:>2} {r['name']}  分 {s:>3}"
                  + (f"｜{'；'.join(why)}" if why else ""))
            if miss:
                print(f"      缺料：{'；'.join(miss)}")

        # 核对作者自己写的版式建议
        said = sorted({int(x) for x in RECIPE_RE.findall(f.get("版式", ""))})
        if said:
            top_ids = [r["id"] for r, *_ in cands]
            print(f"  版式建议写的是配方 {said}；内容形态前 {len(cands)} 名是 {top_ids}")
            if not set(said) & set(top_ids):
                print("    ⚠️ 对不上——要么版式建议另有理由，要么内容形态与想用的版式不匹配")
                rc = 1
            else:
                print("    ✅ 对得上")

    print("\n候选说明的是「像不像」，不是「该不该」——最终选型看这一页要说什么。")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
