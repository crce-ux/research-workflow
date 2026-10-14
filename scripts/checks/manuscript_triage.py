# -*- coding: utf-8 -*-
"""manuscript_triage.py —— 审稿前的报告条目体检

【背景】
    peer-review 三遍阅读法的第 2 遍（方法学深度审查，2–4 h）是审稿的主要工作量。
    其中一部分时间花在确认某件事写没写上：分配隐藏有没有说、样本量怎么定的、
    分析集是哪个——这些是存在性问题，翻一遍就能答。

    先把「写了没有」一次列出来，人再去看「写得对不对」。

【它查什么】
    按研究设计核对该设计的核心报告条目在不在（CONSORT / STROBE / STARD / TRIPOD）。
    上表里每一条都是**存在性**：「有没有写」。
    ⚠️ 「未采用盲法」算写到了——报告状态本身就是要求。

【它不查什么】
    ⭐ 「对不对」和「有没有写」是两件事。
    这个脚本只做后者。缺一项不等于缺陷（可能写在补充材料里），
    查到了也不等于对（方法可能写得完整但做错了）。

用法：
    python manuscript_triage.py <manuscript.md> [--type rct|observational|diagnostic|prediction]
    不给 --type 就按信号词猜，并打印猜的是哪个。

退出码恒为 0——它是**读稿工具，不是门禁**。
"""
import argparse
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 每项 = (显示名, 正则)。正则命中 = 「写到了」。
# ⚠️ 只放进**核心**条目。放太多会把工具变成噪声源。
ITEMS = {
    "rct": [
        ("随机序列生成方法", r"随机(化)?(序列|号码|数字表|区组|分层|方法|方案)|(区组|分层|计算机(生成|产生)|中心|中央)随机"
                          r"|sequence generation|random(ly)? (assign|allocat)"),
        ("分配隐藏", r"分配隐藏|分配隐蔽|密封信封|不透光信封|中心随机|中央随机|allocation concealment|central(ized)? random"),
        ("盲法（写明采用或未采用）", r"盲法|双盲|单盲|设盲|盲态|blinding|blinded|masked"),
        ("样本量依据（效能 / 效应量）", r"样本量(估算|计算|估计)|检验效能|把握度|power (calculat|analys)|effect size"),
        ("主要终点预先设定", r"主要终点|主要结局|primary (outcome|endpoint)"),
        ("受试者流程（入组 / 失访）", r"入组|筛选|流程图|失访|脱落|flow ?(chart|diagram)|CONSORT"),
        ("分析集（ITT / mITT / 全分析集）", r"ITT|意向性分析|意向治疗|全分析集|mITT|per.?protocol|符合方案集"),
        ("缺失数据处理", r"缺失(数据|值)|失访的处置|multiple imputation|多重插补|LOCF|末次观测"),
        ("注册号与注册时点", r"注册号|试验注册|ChiCTR|NCT\d|ISRCTN|ClinicalTrials\.gov|预注册"),
        ("不良事件 / 安全性", r"不良事件|安全性|AE\b|adverse event|safety"),
    ],
    "observational": [
        ("研究设计类型写明", r"队列研究|病例对照|横断面|巢式|cross.?sectional|cohort|case.?control"),
        ("纳排标准", r"纳入标准|排除标准|inclusion criteria|exclusion criteria"),
        ("暴露 / 结局的操作定义", r"暴露(定义|评估|测量)|结局(定义|判定|评估)|operational definition|ascertain"),
        ("样本量依据", r"样本量(估算|计算|估计)|效能|把握度|power (calculat|analys)"),
        ("混杂因素（预设 + 如何控制）", r"混杂|confound|协变量|调整|adjust(ed|ment) for"),
        ("缺失数据处理", r"缺失(数据|值)|multiple imputation|多重插补|complete.?case"),
        ("偏倚讨论", r"偏倚|偏奇|bias|选择性偏倚|回忆偏倚|selection bias|recall bias"),
        ("敏感性分析", r"敏感性分析|sensitivity analys"),
    ],
    "diagnostic": [
        ("待评价试验的操作定义", r"待评价(试验|检查|指标)|index test|被测(试验|指标)"),
        ("金标准", r"金标准|参考标准|reference standard|gold standard"),
        ("判读盲法", r"盲法|设盲|blinding|blinded|不知晓"),
        ("阳性阈值（预先设定）", r"阈值|界值|cut.?off|threshold|阳性判断标准"),
        ("不确定 / 无法判读结果的处置", r"不确定(结果|病例)|无法判读|uninterpretable|indeterminate|excluded from analysis"),
        ("灵敏度 / 特异度 + 95%CI", r"灵敏度|敏感度|特异度|sensitivity|specificity"),
        ("目标人群与转诊路径", r"转诊|就诊人群|连续入组|consecutive (patients|enrol)|spectrum"),
    ],
    "prediction": [
        ("目标人群与结局定义", r"目标人群|研究人群|结局(定义|判定)|outcome (definition|ascertain)"),
        ("事件数 / 每变量事件（EPV）", r"事件数|EPV|events per variable|每(个)?变量"),
        ("缺失数据处理", r"缺失(数据|值)|imputation|插补"),
        ("变量选择方法", r"变量(选择|筛选)|特征(选择|筛选)|LASSO|stepwise|逐步回归|feature selection"),
        ("过拟合与内部验证", r"内部验证|交叉验证|bootstrap|Bootstrap|过拟合|overfit|calibration ?plot"),
        ("区分度", r"区分度|AUC|C.?statistic|ROC"),
        ("校准", r"校准|calibration|Hosmer|Brier"),
    ],
}

# 猜类型用的信号词（按优先级）
SIGNALS = [
    ("rct", r"随机对照|RCT|randomi[sz]ed controlled|双盲|安慰剂对照|分配隐藏"),
    ("diagnostic", r"灵敏度|特异度|ROC|金标准|参考标准|诊断准确性|sensitivity and specificity"),
    ("prediction", r"预测模型|列线图|nomogram|AUC|校准曲线|风险评分|prediction model"),
    ("observational", r"队列|病例对照|横断面|cohort|case.?control|cross.?sectional|回顾性"),
]


def guess_type(text):
    scores = []
    for name, pat in SIGNALS:
        scores.append((len(re.findall(pat, text, re.I)), name))
    scores.sort(reverse=True)
    return scores[0][1] if scores and scores[0][0] else None, scores


def triage(text, kind):
    missing = []
    for label, pat in ITEMS[kind]:
        if not re.search(pat, text, re.I):
            missing.append(label)
    return missing


def main():
    ap = argparse.ArgumentParser(description="审稿前的报告条目体检")
    ap.add_argument("manuscript")
    ap.add_argument("--type", choices=sorted(ITEMS), default=None)
    a = ap.parse_args()

    p = pathlib.Path(a.manuscript)
    text = p.read_text(encoding="utf-8", errors="replace")

    if a.type:
        kind, how = a.type, "指定"
    else:
        kind, scores = guess_type(text)
        how = "推断"
        if not kind:
            raise SystemExit(
                "猜不出研究设计。请给 --type："
                + " / ".join(sorted(ITEMS))
                + "\n（或先把稿子的标题与摘要贴进来）")

    items = ITEMS[kind]
    missing = triage(text, kind)
    n_ok = len(items) - len(missing)

    print(f"manuscript_triage · {p.name} · {how}类型：{kind}")
    print(f"  核心报告条目：报告了 {n_ok} / {len(items)} 项")
    if missing:
        print("\n  没找到（⚠️ 只是「正文里没找到」，可能写在补充材料）：")
        for m in missing:
            print(f"    · {m}")
    else:
        print("\n  ✅ 核心条目都在正文里出现了")

    print("\n  ⚠️ 只查「有没有写」，不查「写得对不对」。"
          "\n     缺一项不等于缺陷，但意见里问一句是合理的。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
