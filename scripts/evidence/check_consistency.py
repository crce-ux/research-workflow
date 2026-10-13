# -*- coding: utf-8 -*-
"""
check_consistency.py —— 交付物一致性校验（质量核查③用）

用途：校验 证据表 / 逐篇讲解 / 综述 / PPT稿 多处篇数与关键数字完全对齐。
对应《文献调研流程手册》Step 7：一致性校验——证据表/讲解/综述/PPT 篇数与数字一致。

用法：
    # 讲解模式（默认）：证据表 vs 逐篇讲解（含标题篇数 + 作者集合比对）
    python check_consistency.py --evtab 证据表_模块X.md --explain 模块X_参考文献逐篇讲解.md [--ppt 模块X_PPT稿.md] [--nums "80%,0.757"]

    # 综述模式：证据表 vs 综述初稿（综述章节标题非作者-年份格式，跳过标题/作者集合比对，改用 PMID 全集比对）
    python check_consistency.py --evtab 证据表_模块X.md --explain 模块X_综述初稿.md --type review [--nums "80%,0.757"]

    # 关键数字自动覆盖（P2-2）：不手动列数字，脚本从证据表"关键结果"列全量提取数值并核对下游
    python check_consistency.py --evtab 证据表_模块X.md --explain 模块X_参考文献逐篇讲解.md --auto-nums

参数：
    --evtab    证据表 md 路径（必填）
    --explain  逐篇讲解 或 综述初稿 md 路径（必填）
    --type     explain（默认）| review；review 模式用于综述（标题为"一、二、"章节，非"### N. 作者"）
    --ppt      PPT 稿 md 路径（可选，比对 PMID）
    --nums     关键数字列表（逗号分隔，可选，双源比对）
    --auto-nums 自动覆盖：提取证据表关键结果列全部数值型结果（百分比/AUC/OR/g/d/r/CI 区间），
                逐项核对下游是否出现（区间类自动拆端点容错 ;/. 写法差异）——比人工 --nums 抽查更彻底

校验项：
    1. 篇数一致（explain：证据表行 vs 讲解标题；review：证据表行 vs 综述 PMID 全集）
    2. 作者-年份集合对称（仅 explain 模式）
    3. 关键数字双源存在（可选的 --nums 列表逐项检查）
    4. PMID 溯源抽查（--ppt 给出时比对）

⚠️ 已知坑：
  - PPT 稿常使用全角括号（如 （PMID 26955358）），本脚本同时匹配半角/全角括号。
  - 综述参考文献条目可能带附注（如"PMID 41124326；在线预发表"），故 PMID 比对用宽松正则（PMID 数字），
    不要求右括号紧邻。
"""
import sys, re, argparse
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 作者名+年份：支持姓氏（拉丁扩展字符、连字符、撇号）与研究组名（ADEPT-2/B-SNIP 带数字连字符）
AUTH_RE = re.compile(r"([A-Za-zÀ-ɏ][A-Za-zÀ-ɏ0-9'\-]* \d{4})")

def extract_pmids(text):
    """匹配 PMID：带 'PMID' 前缀（半角/全角括号）或裸 8 位数字（附录格式）"""
    found = set()
    for pat in [r"\(PMID\s*[:：]?\s*(\d{6,})", r"（PMID\s*[:：]?\s*(\d{6,})",
                r"PMID\s*[:：]?\s*(\d{6,})"]:
        found |= set(re.findall(pat, text))
    # 附录 C 常见格式：作者年份（8位数字）——补充裸 8 位数字（PMID/PMCID 均 8 位）
    found |= set(re.findall(r"（(\d{8})）", text))
    found |= set(re.findall(r"\((\d{8})\)", text))
    return found

def extract_authors(text, from_evtab=False):
    """从证据表数据行或讲解标题提取 作者·年份 集合

    证据表取第 2 列（作者·年份）而非整行——否则第一列 'PMID 40353045' 会被
    AUTH_RE 误匹配成 'PMID 4035'（含数字的作者名如 ADEPT-2 也会被跳过）。
    """
    out = set()
    for line in text.split("\n"):
        if from_evtab:
            if line.startswith("|") and "PMID" in line:
                cells = [c.strip() for c in line.split("|")[1:-1]]
                if len(cells) >= 2:
                    m = AUTH_RE.search(cells[1])
                    if m:
                        out.add(m.group(1))
        else:
            if line.startswith("### ") and "——" in line:
                m = AUTH_RE.search(line)
                if m:
                    out.add(m.group(1))
    return out

# ---- 关键数字自动覆盖（--auto-nums） ----
# 从证据表"关键结果"列提取的数值型结果模式：
#   ① 百分比（80%、46.1%）；② 带前缀的效应量/统计量（AUC=0.757、OR=1.183、g≈0.76、d≈-1.01、r=-0.52）；
#   ③ CI 区间（[0.76;0.83]）；④ 连字符区间（0.76-0.83）。
KEY_NUM_PATTERNS = [
    r"\d+(?:\.\d+)?%",
    r"(?:AUC|OR|g|d|r|P|p|HR|RR)\s*[=≈~]+\s*-?\d+(?:\.\d+)?",
    r"\[\d+(?:\.\d+)?;?\s*\d+(?:\.\d+)?\]",
    r"\d+\.\d+\s*-\s*\d+\.\d+",
]

def extract_key_nums(ev_md):
    """从证据表 md 的'关键结果'列（第 8 列）自动提取数值型结果 token 集合"""
    tokens = set()
    for line in ev_md.split("\n"):
        if not (line.startswith("|") and "PMID" in line):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) < 8:
            continue
        key = cells[7]
        for pat in KEY_NUM_PATTERNS:
            for m in re.findall(pat, key):
                tokens.add(m.replace(" ", ""))
    return tokens

def token_present(token, text):
    """token 在下游是否存在：区间类拆端点数字（容忍 ;/. 写法差异），其余精确子串"""
    if "[" in token or ("-" in token and "." in token):
        nums = re.findall(r"\d+\.\d+", token)
        if nums:
            return all(n in text for n in nums)
    return token in text

def main():
    ap = argparse.ArgumentParser(description="交付物一致性校验")
    ap.add_argument("--evtab", required=True, help="证据表 md 路径")
    ap.add_argument("--explain", required=True, help="逐篇讲解 或 综述初稿 md 路径")
    ap.add_argument("--type", choices=["explain", "review"], default="explain",
                    help="explain=逐篇讲解（默认）；review=综述初稿（章节标题，非作者-年份）")
    ap.add_argument("--ppt", help="PPT 稿 md 路径（可选）")
    ap.add_argument("--nums", help="关键数字列表（逗号分隔，可选，与 --auto-nums 可叠加）")
    ap.add_argument("--auto-nums", action="store_true",
                    help="自动覆盖：从证据表'关键结果'列提取全部数值型结果（百分比/AUC/OR/g/d/r/CI 区间），逐项核对下游是否出现")
    args = ap.parse_args()

    ev = open(args.evtab, encoding="utf-8").read()
    ex = open(args.explain, encoding="utf-8").read()
    ev_rows = [l for l in ev.split("\n") if l.startswith("|") and "PMID" in l]

    if args.type == "review":
        # 综述模式：章节标题非"### N. 作者 ——"，改用 PMID 全集比对篇数，跳过作者集合
        ev_pmids = extract_pmids(ev)
        ex_pmids = extract_pmids(ex)
        missing_pmids = ev_pmids - ex_pmids   # 证据表有/综述参考文献缺
        print(f"证据表数据行：{len(ev_rows)} 篇（PMID {len(ev_pmids)} 个）")
        print(f"综述参考文献 PMID：{len(ex_pmids)} 个")
        print(f"\n证据表有但综述参考文献缺: {sorted(missing_pmids) or '无'}")
        count_ok = len(ev_rows) == len(ex_pmids) and not missing_pmids
        sym_ok = not missing_pmids
        print("（综述模式：篇数以证据表行数 vs 综述参考文献 PMID 全集比对）")
    else:
        # 讲解模式：标题篇数 + 作者集合对称
        ex_titles = [l for l in ex.split("\n") if l.startswith("### ") and "——" in l]
        print(f"证据表数据行：{len(ev_rows)} 篇")
        print(f"逐篇讲解篇数：{len(ex_titles)} 篇")
        count_ok = len(ev_rows) == len(ex_titles)
        # 作者集合对称
        ev_auth = extract_authors(ev, from_evtab=True)
        ex_auth = extract_authors(ex, from_evtab=False)
        missing = ex_auth - ev_auth   # 讲解有/证据表缺
        extra = ev_auth - ex_auth     # 证据表有/讲解缺
        print(f"\n讲解有但证据表缺: {sorted(missing) or '无'}")
        print(f"证据表有但讲解缺: {sorted(extra) or '无'}")
        sym_ok = not missing and not extra

    # 3. 关键数字双源（--nums 人工指定 和/或 --auto-nums 自动覆盖）
    if args.auto_nums:
        auto = extract_key_nums(ev)
        if args.nums:
            auto |= {n.strip() for n in args.nums.split(",") if n.strip()}
        nums = sorted(auto)
        print(f"\n关键数字自动覆盖（--auto-nums：从证据表关键结果列提取 {len(nums)} 项）:")
        num_ok = True
        for kw in nums:
            if not token_present(kw, ex):
                num_ok = False
                print(f"  ⚠️ 证据表有但下游未找到: {kw}（可能为写法差异，人工核对）")
        if num_ok:
            print("  ✅ 证据表全部关键数字均在下游出现")
    elif args.nums:
        nums = [n.strip() for n in args.nums.split(",") if n.strip()]
        print("\n关键数字双源抽查:")
        num_ok = True
        for kw in nums:
            in_ev, in_ex = kw in ev, kw in ex
            if not (in_ev and in_ex):
                num_ok = False
                print(f"  ❌ {kw:10s} 证据表={in_ev} 讲解={in_ex}")
        if num_ok:
            print("  ✅ 全部双源一致")
    else:
        num_ok = True

    # 4. PPT PMID 抽查
    ppt_ok = True
    if args.ppt:
        ppt = open(args.ppt, encoding="utf-8").read()
        ppt_pmids = extract_pmids(ppt)
        ev_pmids = extract_pmids(ev)
        print(f"\nPPT稿 PMID 数：{len(ppt_pmids)}；证据表 PMID 数：{len(ev_pmids)}")
        if len(ppt_pmids) != len(ev_pmids):
            ppt_ok = False
            print(f"  ⚠️ 篇数不一致：PPT={len(ppt_pmids)} vs 证据表={len(ev_pmids)}")
        elif ppt_pmids != ev_pmids:
            ppt_ok = False
            print("  ⚠️ PMID 集合不一致（差集见上）")

    # 结论
    print("\n=== 结论 ===")
    checks = [("篇数一致", count_ok), ("作者集合对称", sym_ok), ("关键数字双源", num_ok), ("PPT PMID 对齐", ppt_ok)]
    for name, ok in checks:
        print(f"  {'✅' if ok else '❌'} {name}")
    print("\n一致性判定:", "✅ 全部通过" if all(ok for _, ok in checks) else "❌ 存在不一致，需人工核对")

if __name__ == "__main__":
    main()
