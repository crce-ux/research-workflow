# -*- coding: utf-8 -*-
"""check_phrases.py —— 措辞层与防御性写作的词表 / 句式机检

【它管什么】
    `ai-academic-writing` 里的**词表与句式**规则——自我削弱、套话、抽象标签、
    演义媒体化、降智解释、自问自答、伪对立、名词化、越级引用、连接词堆砌，
    以及防御性写作 D1–D7、辩驳腔、主次、提示语冒号、翻译腔、元叙事、
    工作日志、杜撰标签、主张强度。这些词表与句式规则是纯匹配，不需要判断；
    原先只写在 references/ 里，每轮靠模型重读。

【它不管什么（避免重复）】
    · 口语动词 / 程度词 / 第一人称 / 指示代词 / 口头连接词 → `check_persona.py` 的 **C8**
    · 引用自足 / 排他性断言 / 数字口径 → `check_language.py`
    · 「这句话像不像人写的」整体判断 → 人工
    **混着查会互相误报**——本脚本只做上表列出的二十七组。

【词表来源】
    `manuals/checklists/写作禁用词与句式清单.md`（权威）+ `references/` 各轴。
    组 10–23 的中文词条参考 junbolian/Academic-Humanizer（MIT）的
    `references/lexicon.txt` 与 `references/chinese.md`，译文与合并见
    `ai-academic-writing/references/lexicon-zh.md`。
    改词表请改手册与 lexicon-zh.md，再同步本脚本。

用法：
    python check_phrases.py 文稿.md [--kind 幻灯片|讲稿|论文|标书] [--only 3,4]

退出码 = 命中组数（0 = 全过）
"""
import argparse
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# (组号, 组名, 适用范围, [正则…], 一句话)
GROUPS = [
    (1, "自我削弱", {"论文", "标书", "讲稿"},
     [r"遗憾的是", r"仍明显落后", r"效果有限", r"存在严重不足", r"未能超过",
      r"本文(只是|仅是|仅仅是|只不过是)", r"(初步|粗浅|浅显|肤浅)的?(尝试|探索|思考)",
      r"抛砖引玉", r"笔者水平有限", r"不足之处(敬请)?(批评|指正)?", r"难免(存在|有)"],
     "说得比证据弱——等于替审稿人备好反驳点"),
    # ⚠️ 手册原表里还有单字「仅」，但它在本项目文稿里是正常用词，命中率极高会掩盖真问题，故不收。
    (2, "套话", {"论文", "标书", "幻灯片"},
     [r"随着社会的发展", r"越来越受到广泛关注", r"日益受到(学界)?关注",
      r"近年来", r"随着[^。\n]{0,12}(快速|迅速|飞速|不断|蓬勃|持续|日益)(发展|进步|普及|兴起)",
      r"(受到|引起|得到)了?[^。\n]{0,8}(越来越多|广泛|日益|高度|极大|普遍)的?(关注|重视)",
      r"说白了", r"说穿了", r"先说结论"],
     "开场套话——删掉不影响任何信息"),
    (3, "抽象标签", {"论文", "标书", "讲稿"},
     [r"具有重要(的)?理论意义", r"(本研究|本文)的关键抓手", r"具有重要意义",
      r"填补了[^。\n]{0,8}(空白|不足)", r"提供了?(新的|重要的|有益的|有效的|全新的)?(思路|视角|参考|借鉴|启示|决策支持)",
      r"奠定了?[^。\n]{0,6}基础", r"开辟了?[^。\n]{0,6}(新路径|新方向|新领域)"],
     "有标签无动作——还原成原文已有的动作"),
    (4, "演义媒体化与喻体", {"幻灯片", "讲稿", "论文", "标书"},
     [r"双雄", r"大军", r"混战", r"领跑", r"抢跑", r"洗牌", r"跳水", r"封神", r"神仙打架",
      r"赋能", r"底层逻辑", r"顶层设计", r"痛点", r"打通", r"护城河", r"双刃剑", r"组合拳",
      r"助力", r"打造", r"深耕", r"破局", r"基石", r"蓝图", r"全方位", r"多维度", r"深度融合",
      r"(新|全新)的?(范式|格局|赛道)",
      r"(像|相当于|如同|好比|堪称|宛如)(一位|一个|一名|位|个)[^，。！？\n]{0,10}"
      r"(导师|秘书|助手|顾问|管家|审查员|实习生|伙伴|向导|老师|专家|大脑|侦探)"],
     "戏谑化比喻与拟人喻体——判据：能否出现在药监局公告里；"
     "「闭环」「链路」「引擎」等在部分领域是术语，见 references/lexicon-zh.md 的待核对类"),
    (5, "自问自答", {"幻灯片", "讲稿"},
     [r"[？?]\s*[—\-]{1,2}\s*", r"那么[，,]?\s*[^。？?]{0,20}(是什么|有哪些)[？?]"],
     "不设问——把答案直接写出来"),
    (6, "伪对立", {"论文", "标书", "讲稿"},
     [r"不是[^。]{1,30}?而是", r"不只是[^。]{1,30}?更是", r"并非[^。]{1,30}?而是",
      r"与其说[^。\n]{1,20}不如说", r"(看似|表面上?)[^。\n]{1,20}(实则|实际上|其实)",
      r"你以为[^。\n]{1,30}其实", r"说到底"],
     "「不是 A 而是 B」多数是修辞——它替读者预设了一个误解再否定；真实纠错才用。"
     "「是 A，不是 B」式的必要区分不在此列"),
    (7, "名词化", {"论文", "标书"},
     [r"进行了[^。，]{0,6}(分析|研究|探讨|比较)", r"对[^。，]{1,16}进行(了)?(分析|研究|评估)",
      r"加以(分析|研究|说明|解决|讨论|改进|验证)", r"(做|作)出了?[^。\n]{0,4}贡献"],
     "还原为动词：「进行了分析」→「分析」"),
    (8, "越级引用", {"期刊审稿", "回导师"},
     [r"§\s*\d", r"第\s*\d+\s*条", r"\b(CONSORT|SPIRIT|STROBE|PRISMA|STARD|TRIPOD|ARRIVE|CARE)\b"],
     "身份界限——学生/首次审稿人不引章节号、不点报告规范名"),
    (9, "连接词堆砌", {"论文", "标书", "幻灯片"},
     [r"首先[^。]{0,60}其次[^。]{0,60}(最后|再次)", r"因此[^。]{0,40}从而[^。]{0,40}进而"],
     "连接词成串出现——靠结构表达顺序，不靠连接词"),
    # ── 防御性写作（2026-10-25 吸收自 MIT 项目 anti-defensive-writing 与
    #    academic-defensive-writing-auditor 的 D1–D9 分类；只收可判定的句式）
    (10, "面向审稿人的预辩护（D1）", {"论文", "标书"},
     [r"(?i)We (?:emphasize|note|stress|highlight) that",
      r"(?i)It (?:should|must) be (?:noted|emphasized|stressed) that",
      r"(?i)To (?:avoid|prevent) (?:misunderstanding|confusion)",
      r"(?i)(?:One|A reader) might (?:argue|counter|object)",
      r"(?i)A (?:potential|likely) (?:concern|objection) is",
      r"(?:需要|值得)(?:指出|强调|说明|澄清)的是", r"为避免(?:误解|混淆)",
      r"可能有人会(?:说|问)", r"一个(?:可能|潜在)的质疑是",
      r"常被问(?:到)?的一个问题", r"有人(?:会)?问", r"这里(?:要|需要)(?:强调|说明)"],
     "面向想象中的审稿人先辩一句——直接陈述事实即可"),
    (11, "否认式声明（D2）", {"论文", "标书"},
     [r"(?i)We (?:do not|make no) claim",
      r"(?i)(?:should|must) not be (?:interpreted|construed|read) as",
      r"(?i)does not (?:establish|imply|prove|demonstrate)",
      r"本文不(?:主张|声称)", r"不应(?:被)?(?:理解为|解读为)", r"并不能(?:说明|证明|推出)", r"不代表"],
     "用「不主张」替代「主张」——正面写一次范围，不重复否认"),
    (12, "为省略辩护（D5）", {"论文", "标书"},
     [r"(?i)We (?:did not|do not) (?:include|report|compare)[^.]{0,30}because",
      r"(?i)(?:is|are) (?:unnecessary|not needed) because",
      r"(?i)would be (?:unfair|biased)",
      r"(?:未|没有)(?:纳入|报告|比较|设置)[^。]{0,20}因为", r"没有(?:必要|理由)[^。]{0,12}因为", r"这样的比较不公平"],
     "为「没做什么」辩护——要么写成一次限制，要么直接描述评价方案"),
    (13, "公平性自我辩护（D6）", {"论文", "标书"},
     [r"(?i)For a fair comparison", r"(?i)To (?:ensure|maintain) fairness", r"(?i)provides? a fair (?:setting|comparison)",
      r"为(?:保证|确保)公平", r"为了公平(?:比较)?", r"公平起见"],
     "直接写控制了什么变量，不解释「为什么这样才公平」"),
    # ── 主次（2026-10-26）：正面内容承担叙述，否定与限定落在次要位置
    (17, "句内后置否定（主次）", {"论文", "标书", "讲稿", "幻灯片"},
     [r"[，,；;]\s*\*{0,2}\s*(?:不是|并非|而非|而不是)"],
     "正面主张说完，同一句的后半又用否定占去等量篇幅。主句只写正面内容，"
     "限定另起一句，或移到页末边界段；同一限制全文只说一次"),
    (26, "转折词", {"论文", "标书", "讲稿", "幻灯片"},
     [r"(?<!不)但(?!凡)"],
     "正面说完又用「但」把话收回——重要就直接说，不重要就删；"
     "关系改用分号、句号或冒号承担"),
    # ── 2026-10-26 吸收自 junbolian/Academic-Humanizer（MIT）的中文规则
    (18, "提示语冒号", {"论文", "标书", "讲稿"},
     [r"(一句话(总结|说|概括)|简单说|小结|结论|核心(是|在于|观点)?|关键(是|在于)?|重点(是)?|"
      r"原因(如下|有|在于)?|答案(是)?|本质(是|上)?|换句话说|也就是说|我的(观点|判断|结论))[：:]"],
     "提示语不承担信息——删掉提示语，把后面的话直接说出来；"
     "引出原话、定义、公式的冒号不在此列"),
    (19, "翻译腔", {"论文", "标书", "讲稿"},
     [r"对于[^，。！？\n]{2,15}来说", r"对[^，。！？\n]{2,15}而言", r"就[^，。！？\n]{2,15}而言",
      r"在[^，。！？\n]{2,12}方面", r"这意味着", r"这表明", r"这说明",
      r"(一个|一种|一套)[^，。、；：！？\n]{15,}的[一-鿿]{2,5}"],
     "中文里不这样起句——对象直接放到主语位置，长定语拆成两句话；"
     "表示数学条件的「当…时」不在此列"),
    (20, "元叙事", {"论文", "标书", "讲稿", "幻灯片"},
     [r"本(节|章|部分|小节)(将|主要|首先|拟)?(介绍|讨论|阐述|给出|分析|说明|回顾|概述)",
      r"下面(我们)?(将|来)?(介绍|讨论|分析|说明|给出)",
      r"接下来(我们)?(将|会)?(介绍|讨论|分析|说明|给出)",
      r"如前(所述|文所述)", r"前文(已经)?(提到|指出|述及|讨论)",
      r"(本文|全文)(的)?(结构|章节|内容)?安排如下", r"其余部分(安排|组织)如下",
      r"本(节|章)小结", r"小结一下"],
     "只谈文本自身、没有内容——删掉，或只留它包着的实质结论；"
     "全文结论部分的小结不在此列"),
    (21, "工作日志", {"论文", "标书"},
     [r"(健全性|合理性|完整性)(检查|校验)", r"流水线", r"管线", r"审计",
      r"(验证|核验|认证|评估|计算)(协议|流程|环节)", r"认证(的)?(上界|下界|界|结果|解)",
      r"护栏", r"兜底", r"回退机制", r"重试", r"(从未|没有|未被|未曾)(被)?触发",
      r"随机(数)?种子", r"种子(数|号|值)", r"容差", r"迭代(上限|次数上限)", r"时间上限",
      r"残差(为|小于|低于|不超过|在)", r"(抖动项|正则化(项|参数|系数)?)(取|为|设为|设置为)",
      r"数值(验证|检验|核验|确认)", r"经(过)?数值(验证|检验)"],
     "把跑代码的过程写进方法与证明——写成方法、结果和论证；"
     "报告结果所依赖的取值保留"),
]


# ── 需要计数的两类（不是单句正则）──────────────────────────
HEDGE_EN = re.compile(
    r"\b(?:although|while|whereas|despite|may|might|could|potentially|possibly|"
    r"perhaps|arguably|somewhat)\b", re.I)
HEDGE_ZH = re.compile(r"可能|或许|也许|似乎|一定程度上|某种程度上")
#: 辩驳腔：全篇「不是」的最低计数量。达到即提示，不计对错。
NEG_CONTRAST = re.compile(r"不是")
CONTRAST_MIN = 3
PRELIM = re.compile(
    r"\b(?:preliminary|initial|initially|suggestive|exploratory|proof[- ]of[- ]concept|"
    r"indicative)\b|初步|探索性|提示性|概念验证", re.I)


def _special(text, only):
    """D3 限定词堆叠、D7 初步标签重复——按句或按篇计数，不是单点正则。"""
    out = []
    if not only or 14 in only:
        found = []
        for i, line in enumerate(text.splitlines(), 1):
            for sent in re.split(r"(?<=[。！？!?])\s*", line):
                n = len(HEDGE_EN.findall(sent)) + len(HEDGE_ZH.findall(sent))
                if n >= 3:
                    found.append((i, f"限定词 {n} 个：{sent.strip()[:26]}"))
        if found:
            out.append((14, "限定词堆叠（D3）", {"论文", "标书", "讲稿"},
                        "一句里叠三层以上限定，断言强度被稀释", found[:8]))
    if not only or 15 in only:
        ms = list(PRELIM.finditer(text))
        if len(ms) >= 3:
            found = [(text[:m.start()].count("\n") + 1, m.group(0)) for m in ms]
            out.append((15, "初步标签重复（D7）", {"论文", "标书"},
                        "同一标签用三次以上，读者会认为全部结论都待定", found[:8]))
    if not only or 16 in only:
        n = len(NEG_CONTRAST.findall(text))
        if n >= CONTRAST_MIN:
            density = n / max(1, len(text)) * 1000
            out.append((16, "辩驳腔（全篇「不是」计数）", {"论文", "标书", "讲稿", "幻灯片"},
                        "全篇「不是」过密时，每句都在否定一个不在场的人；"
                        "改为一次说清：陈述是什么，边界另起一句",
                        [(0, f"全篇「不是」{n} 次（{density:.1f} 次/千字）")]))
    if not only or 22 in only:
        out += _coined_labels(text)
    if not only or 23 in only:
        out += _claim_strength(text)
    if not only or 24 in only:
        out += _novelty_words(text)
    if not only or 25 in only:
        out += _rhythm(text)
    if not only or 27 in only:
        out += _short_sentences(text)
    return out


# ── 短句（组 27）────────────────────────────────────────
SHORT_MAX = 10        # 汉字数上限
SHORT_RATE = 0.05     # 短句率提示线（2026-10-26 由 8% 收紧到 5%）
SHORT_SKIP = ("#", "|", "-", "*", "`")
#: 只有取值的字段行（**可行性：高。**）是结构，不是散文；
#: 「**表述**：……正文……」是散文，照常计
SHORT_FIELD = re.compile(r"^\*\*[^*]{2,14}[：:][^*]*\*\*\s*$")
#: 批注行（🔴 ⚠️ ❌ ✅）是说明，不是散文
SHORT_MARK = ("🔴", "⚠️", "❌", "✅", "📖", "🔌")


def _short_sentences(text):
    """散文里的短句占比。表格、列表、标题、纪律块不算。"""
    raw = text.splitlines()
    if raw and raw[0].strip() == "---":          # 跳过 YAML frontmatter
        for j in range(1, len(raw)):
            if raw[j].strip() == "---":
                raw = [""] * (j + 1) + raw[j + 1:]
                break
    sents = []
    for i, line in enumerate(raw, 1):
        s = re.sub(r"^>\s?", "", line.strip())
        if not s or "本页纪律" in s or SHORT_FIELD.match(s) or s.startswith(SHORT_MARK):
            continue
        if s.startswith(("#", "|", "-", "`")):
            continue
        if s.startswith("*") and not s.startswith("**"):     # * 列表项，非加粗
            continue
        s = s.replace("**", "")
        for part in re.split(r"(?<=[。！？])", s):
            part = part.strip()
            n = len(re.findall(r"[一-鿿]", part))
            if n:
                sents.append((i, n, part))
    if not sents:
        return []
    short = [x for x in sents if x[1] <= SHORT_MAX]
    rate = len(short) / len(sents)
    if rate <= SHORT_RATE:
        return []
    found = [(ln, f"{n} 字：{s[:26]}") for ln, n, s in short[:8]]
    found.append((0, f"全篇短句 {len(short)} / {len(sents)} 句"
                     f"（{rate * 100:.0f}%，上限 {SHORT_RATE * 100:.0f}%）"))
    return [(27, "短句过密", {"论文", "标书", "讲稿", "幻灯片"},
             "短句连成串时，读起来一顿一顿；把能并的并回主句，"
             "用逗号或分号承接，只保留确实需要停顿的", found)]


# ── 句子节奏（组 25）────────────────────────────────────
RHY_LONG = 90        # 单句汉字上限
RHY_PAIR_MIN = 15    # 相邻句同款的最短句长
RHY_PAIR_TOL = 0.20  # 相邻两句的长度容差
#: 序数编号开头的并列条款
ENUM_HEAD = re.compile(r"^(?:第[一二三四五六七八九十]+[，、．.]|[一二三四五六七八九十]+、|[①②③④⑤⑥⑦⑧⑨⑩]|[（(]\d+[)）])")


def _rhythm(text):
    """相邻句同款、分号过密、长句——看的是句子与段落，不是词。"""
    out = []
    raw = text.splitlines()
    if raw and raw[0].strip() == "---":          # 跳过 YAML frontmatter
        for j in range(1, len(raw)):
            if raw[j].strip() == "---":
                raw = [""] * (j + 1) + raw[j + 1:]
                break
    plain = [re.sub(r"^\s*>\s?", "", l).replace("**", "") for l in raw]
    plain = [re.sub(r"^\s*[-*+•]\s+", "", l) for l in plain]
    sents = []
    for i, line in enumerate(plain, 1):
        for s in re.split(r"(?<=[。！？])", line):
            s = s.strip()
            if s:
                sents.append((i, s))

    pairs = []
    for (la, a), (lb, b) in zip(sents, sents[1:]):
        ca, cb = a.count("，"), b.count("，")
        x, y = len(a), len(b)
        if ca != cb or ca < 1 or min(x, y) < RHY_PAIR_MIN:
            continue
        if abs(x - y) / max(x, y) >= RHY_PAIR_TOL:
            continue
        # 「妄想：Cascella 2011…」这类条目式并列是数据，不是同款句
        if re.match(r"^[^：，。]{2,20}：", a) and re.match(r"^[^：，。]{2,20}：", b):
            continue
        # 序数编号的并列条款是结构，不是同款句
        if ENUM_HEAD.match(a) and ENUM_HEAD.match(b):
            continue
        pairs.append((la, f"第 {la} / {lb} 行：{a[:16]}… ｜ {b[:16]}…"))
    if pairs:
        out.append((25, "相邻句同款", {"论文", "标书", "讲稿", "幻灯片"},
                    "相邻两句结构一样、长度接近，读起来像填表；"
                    "改其中一句的句法：合并、拆分、换语序", pairs[:6]))

    semi, pos = [], 0
    for block in re.split(r"(\n\s*\n)", text):
        if not block.strip():
            pos += len(block)
            continue
        n = block.count("；") + block.count(";")
        if n >= 2:
            ln = text[:pos].count("\n") + 1
            semi.append((ln, f"第 {ln} 段 {n} 个分号"))
        pos += len(block)
    if semi:
        out.append((25, "分号过密", {"论文", "标书", "讲稿"},
                    "一段两个以上分号，说明句子该拆；拆成完整句子", semi[:6]))

    longs = [(ln, f"{len(re.findall('[一-鿿]', s))} 字：{s[:26]}…")
             for ln, s in sents if len(re.findall("[一-鿿]", s)) > RHY_LONG]
    if longs:
        out.append((25, "长句", {"论文", "标书", "讲稿"},
                    f"单句超过 {RHY_LONG} 个汉字，拆成两句，拆完仍要衔接", longs[:6]))
    return out


# ── 杜撰标签（组 22）──────────────────────────────────────
#: 抽象修饰语 + 系统名词。修饰语取 2–6 个汉字，贪心取最长。
LABEL_HEAD = re.compile(
    r"((?:(?![的了是在有不也都就而与和或])[一-鿿]){2,6})"
    r"(机制|体系|框架|范式|闭环|协议|架构|护栏|底座|中台|飞轮|管线|流水线)")
#: 修饰语是普通形容词或指代时，说的是通用名词，不是自造的名字。
LABEL_MOD_BAD = re.compile(
    r"^(?:主要|核心|基本|关键|重要|一般|通用|标准|统一|现有|现成|目前|当前|这篇|一个|一种|这个|该|本|其|难|不|无|有)"
    r"|[到把被让给做作说写看问讲提用由从向对于能会可要应必已尚将未]")
#: 领域内已有定义的组合，跳过。
LABEL_OK = re.compile(
    r"(注意力|门控|定价|分配|拍卖|激励|匹配|投票|选择|传导|作用|形成|反应|病理|生理|药理|"
    r"神经|分子|免疫|代偿|防御|调节|奖赏|多巴胺|胆碱能|补偿|奖惩|疗效|发病|致病)机制"
    r"|(理论|概念|分析|研究|贝叶斯|监管|法律|建模|评价指标|指标|标准|知识|学科|课程|诊疗|医疗|"
    r"卫生|监测)体系"
    r"|(理论|概念|分析|研究|贝叶斯|监管|法律|建模)框架"
    r"|(网络|模型|系统|软件|计算)架构"
    r"|(通信|加密|网络|共识|实验|临床|访谈|调查|治疗|知情同意|随机|采集|分割|扫描|成像|重建|配准)协议"
    r"|(控制|反馈)闭环|(研究|计算|科学|实验)范式"
    r"|(数据|处理|分析|影像|生信)管线")
LABEL_DEF = re.compile(r"称为|定义为|是指|指的是|由.{1,20}组成|简称")


def _coined_labels(text):
    """文中既没定义也没引用的自造名词——只出现一两次，却写得像读者早该知道。"""
    lines = text.splitlines()
    seen = {}
    for m in LABEL_HEAD.finditer(text):
        phrase, head = m.group(0), m.group(2)
        if LABEL_OK.search(phrase) or LABEL_MOD_BAD.search(m.group(1)):
            continue
        ln = text[:m.start()].count("\n") + 1
        seen.setdefault(phrase, []).append(ln)
    found = []
    for phrase, lns in seen.items():
        if len(lns) > 2:
            continue                     # 反复使用，按本文定义过的概念处理
        first = lns[0]
        ctx = lines[first - 1] if 0 < first <= len(lines) else ""
        if LABEL_DEF.search(ctx):
            continue                     # 同句给过定义
        found.append((first, f"{phrase}（{len(lns)} 次）"))
    if not found:
        return []
    found.sort()
    return [(22, "杜撰标签", {"论文", "标书", "讲稿"},
             "自造名词写得像读者早该知道——文中没定义也没引用时，改成它做了什么；"
             "领域术语与本文定义过的名称不在此列", found[:8])]


# ── 主张强度（组 23）─────────────────────────────────────
SIG_WORD = re.compile(r"显著(?!性)")
TEST_WORD = re.compile(
    r"检验|检验统计量|[pP]\s*[<>=≤≥]|[pP]\s*值|置信区间|\bCI\b|方差分析|秩和|卡方|"
    r"[tTF]\s*检验|效应量|Bonferroni|FDR|多重比较|校正")
OPT_WORD = re.compile(r"最优|最佳|最优解")
OPT_COND = re.compile(r"命题|定理|引理|假设|在[^。]{0,12}(条件下|范围内|情形下)")


def _claim_strength(text):
    """「显著」必须交代检验；「最优」必须交代条件。看段落，不看单句。"""
    sig, opt = [], []
    pos = 0
    for para in re.split(r"(\n\s*\n)", text):
        if not para.strip():
            pos += len(para)
            continue
        ln = text[:pos].count("\n") + 1
        has_test = bool(TEST_WORD.search(para))
        has_cond = bool(OPT_COND.search(para))
        for sent in re.split(r"(?<=[。！？])", para):
            if SIG_WORD.search(sent) and not has_test:
                sig.append((ln, ("显著无检验：" + sent.strip())[:46]))
            if OPT_WORD.search(sent) and not has_cond:
                opt.append((ln, ("最优无条件：" + sent.strip())[:46]))
        pos += len(para)
    out = []
    if sig:
        out.append((23, "显著无检验", {"论文", "标书"},
                    "「显著」要有统计检验；没有检验就给差值并删去这个词", sig[:8]))
    if opt:
        out.append((23, "最优无条件", {"论文", "标书"},
                    "「最优」要与命题条件核对；复述结果时带上假设与适用范围", opt[:8]))
    return out


# ── 首创词（组 24）──────────────────────────────────────
NOVELTY = re.compile(r"首次|首创|国内外首次|尚属首次")
NOVELTY_MAX = 3


def _novelty_words(text):
    ms = list(NOVELTY.finditer(text))
    if len(ms) < NOVELTY_MAX:
        return []
    found = [(text[:m.start()].count("\n") + 1, m.group(0)) for m in ms]
    return [(24, "首创词重复", {"论文", "标书", "讲稿"},
             "「首次」全篇至多一次，且要有文献检索支撑；反复出现时读者会认为每条都要打折",
             found[:8])]


def scan(text, only=None):
    hits = []
    for num, name, kinds, pats, note in GROUPS:
        if only and num not in only:
            continue
        found = []
        for p in pats:
            for m in re.finditer(p, text):
                ln = text[:m.start()].count("\n") + 1
                found.append((ln, m.group(0)[:30]))
        if found:
            hits.append((num, name, kinds, note, found))
    hits += _special(text, only)
    return hits


def main():
    ap = argparse.ArgumentParser(description="措辞层词表/句式机检")
    ap.add_argument("doc")
    ap.add_argument("--kind", default=None,
                    choices=["幻灯片", "讲稿", "论文", "标书", "期刊审稿", "回导师"])
    ap.add_argument("--only", default=None, help="只查指定组，如 3,4")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    text = open(a.doc, encoding="utf-8", errors="replace").read()
    only = {int(x) for x in a.only.split(",")} if a.only else None
    hits = scan(text, only)

    # 文体门控：不属于本文体的组只提示、不计入退出码
    inscope, outscope = [], []
    for h in hits:
        (inscope if (a.kind is None or a.kind in h[2]) else outscope).append(h)

    print(f"check_phrases · {a.doc} · 文体={a.kind or '未指定（全部按适用计）'}")
    if not hits:
        print("  ✅ 全过（二十七组词表/句式）")
        return 0
    for num, name, kinds, note, found in inscope:
        print(f"  ❌ {num} {name}：{len(found)} 处 — {note}")
        for ln, s in found[:6]:
            where = "全篇" if ln == 0 else f"第 {ln} 行"
            print(f"        {where}：{s}")
    for num, name, kinds, note, _f in outscope:
        print(f"  ○  {num} {name}：不属本文体（{'/'.join(sorted(kinds))}），未计")
    if inscope:
        print(f"\n  共 {len(inscope)} 组命中。⚠️ 命中不等于要改——「仅」「也就是说」这类有合法用法，仍由人判断。")
    return len(inscope)


if __name__ == "__main__":
    raise SystemExit(main())
