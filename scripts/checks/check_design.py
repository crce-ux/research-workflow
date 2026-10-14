# -*- coding: utf-8 -*-
"""check_design.py —— 研究设计书的结构机检（对齐 study-design 的四条规则）

【背景】
    `study-design` 在 SKILL.md 里写了四条规则：证伪条件、效应量两套、阈值出处、
    可行性数字对比。本脚本把其中**能机检**的部分查掉。

【它查什么、不查什么】
    查：该有的东西在不在——证伪条件(G1) / 乐观保守两套(G2) / 脱落率(G3) /
        风险四列(G4) / 伦理与预注册(G6) / **疗效阈值有没有写出处(G7)**。
    不查：出处的标准**对不对**、效应量取得**合不合理**——语义，一律不碰。

    ⚠️ 2026-10-14：此前「阈值出处」整条被归为「语义，不查」——把两件事混为一谈。
    「出处**对不对**」是语义（确实不查）；「**有没有写**出处」是结构，与 G1
    「有没有写证伪条件」同类。结果是：四条规则里只有第 3 条没有机检。

【⚠️ 它会标出你自己的设计书】
    2026-10-14 实测 `TRS_EEG/03_课题申报/02_研究设计书_终稿_20260812.md`：
    2.4 假设节没有证伪条件、3.2 没有乐观/保守两套、也没有脱落率、8.2 风险表只有三列。
    **判据很清楚，是稿子没通过检查**。要不要改稿，你定。

用法：
    python check_design.py <设计书.md>
    python check_design.py <设计书.md> --deliverables <03_课题申报/>

退出码 = 硬命中条数（0 = 全过）
"""
import argparse
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HEAD = re.compile(r"^(#{1,6})\s*(.+)$", re.M)

# 证伪条件：判据是「什么结果算假设不成立」
FALSIFY = re.compile(
    r"若不|若[^。；\n]{0,50}(?:则|即)[^。；\n]{0,50}(?:不成立|被否|不支持|推翻)"
    r"|证伪|否则[^。；\n]{0,40}(?:不成立|不支持)|不成立即|视为不成立")
OPTIMISTIC = re.compile(r"乐观|×\s*0\.7|\*\s*0\.7")
CONSERVATIVE = re.compile(r"保守|×\s*0\.5|\*\s*0\.5")
DROPOUT = re.compile(r"脱落率|失访率|dropout")
RISK_COLS = ("风险", "概率", "影响", "应对")

# ── G7 疗效 / 分组阈值有没有写出处 ────────────────────────────
# 规则 3 说「分组阈值必须写明出处」。此前 docstring 把「阈值出处」归为「语义，不查」——
# 把两件事混了：「出处对不对」是语义（确实不查），但「**有没有写**出处」
# 是结构，与 G1「有没有写证伪条件」同类。
# ⚠️ 触发面必须窄：**只认疗效判定型的百分比阈值**（减分率 / 应答 / 缓解），
#    不认操作阈值（如「有效试次 ≥85%」的质控阈值本就不需要文献出处）——
#    放宽会把操作阈值全报成缺出处。
RESPONSE = re.compile(r"减分率|应答|缓解|疗效判定|界定有效")
THRESHOLD = re.compile(r"(?:≥|>=|>|不低于|至少|超过)\s*\d+(?:\.\d+)?\s*%?")
SOURCED = re.compile(r"\[\d+(?:\s*[,–\-]\s*\d+)*\]|PMID|DOI|指南|共识|标准|依据"
                     r"|Kane|TRRIP|BPRS|CGI")
# 文档**自己已标为待定**的，不再重复报——已知未决，不算漏写。
# （实测：初稿的「待确认事项」清单里就列了这条阈值，被重复报了一次。）
PENDING = re.compile(r"待确认|待定|待讨论|待课题组|待核|TBD")

# 交付物清单（design-steps.md §交付物清单）——按**文书种类**找，不按文件名抠字
DELIVERABLES = {
    "研究设计书": "研究设计书",
    "伦理申请材料": "伦理",
    "预注册登记": "预注册",
    "进度与预算表": "预算",
    "证据依据核对表": "证据依据",
}


def sections(text):
    """切章节：(层级, 标题, 正文)。正文到下一个同级或更高级标题为止。"""
    marks = [(m.start(), len(m.group(1)), m.group(2).strip(), m.end()) for m in HEAD.finditer(text)]
    out = []
    for i, (s, lv, title, e) in enumerate(marks):
        end = len(text)
        for s2, lv2, _t2, _e2 in marks[i + 1:]:
            if lv2 <= lv:
                end = s2
                break
        out.append((lv, title, text[e:end]))
    return out


def find_sec(secs, *keys, level=None):
    """按标题关键词找章节；level 限定层级（None = 任意）。"""
    for lv, title, body in secs:
        if any(k in title for k in keys) and (level is None or lv == level):
            return lv, title, body
    return None


def items_of(body):
    """把章节正文拆成条目：以 `**…**` 或编号开头的块。"""
    parts, cur = [], []
    for line in body.splitlines():
        if re.match(r"^\s*(\*\*[^*]+?\*\*|\d+[.、]\s|\#{3,6}\s)", line) and cur:
            parts.append("\n".join(cur))
            cur = [line]
        else:
            cur.append(line)
    if cur:
        parts.append("\n".join(cur))
    parts = [p for p in (s.strip() for s in parts) if p]
    return parts if len(parts) > 1 else [body]


def check(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    secs = sections(text)
    hits, soft, skipped = [], [], []

    # G1 证伪条件——假设节里每条都要有
    hs = find_sec(secs, "假设")
    if hs:
        items = items_of(hs[2])
        bad = [i for i, it in enumerate(items, 1) if not FALSIFY.search(it)]
        if bad:
            hits.append(f"G1 研究假设节有 {len(bad)}/{len(items)} 条没写证伪条件"
                        f"（第 {'/'.join(map(str, bad))} 条）——"
                        f"没有它，事后无论什么结果都能解释得通")
    else:
        skipped.append("G1 无「假设」节")

    # G2/G3 样本量节：乐观保守两套 + 脱落率
    ss = find_sec(secs, "样本量")
    if ss:
        if not (OPTIMISTIC.search(ss[2]) and CONSERVATIVE.search(ss[2])):
            hits.append("G2 样本量节没给「乐观 / 保守」两套效应量"
                        "（规则：文献值 ×0.7 / ×0.5）——只给一套会低估样本量")
        if not DROPOUT.search(ss[2]):
            hits.append("G3 样本量节没写脱落率——需招募数应按脱落率上浮")
    else:
        skipped.append("G2/G3 无「样本量」节")

    # G4 风险表四列
    for line in text.splitlines():
        if line.lstrip().startswith("|") and "风险" in line and "概率" in line:
            miss = [c for c in RISK_COLS if c not in line]
            if miss:
                hits.append(f"G4 风险表缺列 {'/'.join(miss)}"
                            f"（规则：风险 → 概率 → 影响 → 应对，四件事）")
            break
    else:
        skipped.append("G4 无风险表")

    # G6 伦理审批 + 预注册
    # ⚠️ G6**全篇查**，不按章节查。原因：本库的设计书用 `**（3）预注册与透明度**`
    #    这种**粗体伪标题**，不是 markdown 标题——按章节切会漏掉它，把
    #    「预注册平台：ClinicalTrials.gov / OSF」判成「没写平台」（实测踩过）。
    #    代价：全篇任意位置提到就算过，比逐节严。宁松不误报。
    if "伦理" in text and not re.search(r"批件号|审批号|受理号|补充申请|申请中", text):
        hits.append("G6 未写明伦理批件号，也未标「申请中」")
    if "预注册" in text and not re.search(
            r"ChiCTR|ClinicalTrials|Chinese Clinical Trial|OSF|NCT\s*\d|注册号", text):
        hits.append("G6 提到预注册，但全篇未见注册平台或注册号"
                    "（ChiCTR / ClinicalTrials.gov / OSF）")

    # G7 疗效 / 分组阈值写了没写出处
    for i, line in enumerate(text.splitlines()):
        if not (RESPONSE.search(line) and THRESHOLD.search(line)):
            continue
        window = text.splitlines()[max(0, i - 1):i + 2]      # 本行 ±1
        if any(PENDING.search(w) for w in window):
            continue                                          # 已标待定 → 不重复报
        if not any(SOURCED.search(w) for w in window):
            hits.append(f"G7 第 {i + 1} 行给了疗效阈值，但**没写出处**："
                        f"{line.strip()[:60]}——"
                        f"规则：阈值要能立刻说出依据（哪份指南 / 共识 / 哪篇文献）")

    # G5（软）可行性数字对比
    fs = find_sec(secs, "可行性")
    if fs:
        nums = re.findall(r"\d[\d,]{1,6}", fs[2])
        if len(nums) < 2:
            soft.append("G5 可行性节没看到两个数字——规则要求「可招募数 ≥ 样本量需求」"
                        "摆出来对比，不能只写「预计可满足」")

    # ⚠️ 没评到的规则要说出来。例如「设想稿」没有假设节/样本量节，
    #    四条规则会**全部静默跳过**，屏幕上却显示「全过」——「全过」是假象。
    if skipped:
        soft.insert(0, f"本次未评：{'；'.join(skipped)}（缺对应章节，不算查过通过）")
    return hits, soft


def check_deliverables(d):
    """清单对照——**只报不判**：缺的未必是错，可能还没走到相应步骤。"""
    d = pathlib.Path(d)
    if not d.is_dir():
        return [f"{d}：不是目录"]
    names = [p.name for p in d.rglob("*")]
    return [f"交付物清单：未见「{kind}」（{kw}）——若是还没到这一步，忽略"
            for kind, kw in DELIVERABLES.items()
            if not any(kw in n for n in names)]


def main():
    ap = argparse.ArgumentParser(description="研究设计书结构机检")
    ap.add_argument("path")
    ap.add_argument("--deliverables", default=None, help="另查 03_课题申报/ 的交付物清单")
    a = ap.parse_args()

    p = pathlib.Path(a.path)
    files = [p] if p.is_file() else sorted(p.rglob("*研究设计书*.md"))
    total = 0
    print(f"check_design · {a.path} · 扫 {len(files)} 个文件")
    for f in files:
        hits, soft = check(f)
        for h in hits:
            print(f"  ❌ {f.name}：{h}")
        for s in soft:
            print(f"  ○ {f.name}：{s}")
        total += len(hits)

    if a.deliverables:
        notes = check_deliverables(a.deliverables)
        print("\n  ── 交付物清单对照（只报不判）──")
        for n in notes or ["  五件齐"]:
            print(f"  ○ {n}")

    if not total:
        print("  ✅ 已评的规则全过")
    print(f"\n  共 {total} 处硬命中。⚠️ 只查结构，不查方案科不科学。")
    return total


if __name__ == "__main__":
    raise SystemExit(main())
