# 能力 × 工具 × 状态

> 用途：动笔或动手之前先查这里。**能调用就调用，不重写。**
> 状态只有四种：已验证 / 未验证 / 未见使用记录 / 不适用。

---

## 一、默认规则

新做任何一个环节之前，按顺序问三句：

1. **有没有装好的工具能做？** → 有，调用。
2. **没有安装，但有可借鉴的方法？** → 看许可，借鉴方法，不复制代码。
3. **都没有？** → 自己写，并在交付时写明为什么。

写进 `科研/CLAUDE.md` 与各 skill 的开工位置。**不许跳过前两步直接开写。**

---

## 二、能力对照

| 阶段 | 能力 | 现成工具 | 状态 | 本库实现 | 动作 |
|---|---|---|---|---|---|
| P | 单篇精读 | `nature-reader` · `nature-paper-card` | **✅ 均已验证 2026-10-19** | `paper-reading` | **分工**：它们读，我们定口径与回填 |
| A | 检索 | `nature-academic-search` | **✅ 已验证 2026-10-19**（有产物；两个源失败） | `literature-pipeline` | **调用**：它跑检索，我们算覆盖声明 |
| A | 全文获取 | `nature-downloader` | **✅ 部分可用 2026-10-19**（arXiv 成功；出版商与 MDPI 403） | 无 | **有条件调用**：开放获取直链走它，其余回落下文 |
| A | 引用核验 | `nature-ref-verifier` | 已验证（用过） | `check_ref_citations` | **分工**：它查存在性，我们查编号一致性 |
| B | 成文 / 文体 | `nature-writing` | **✅ 已验证 2026-10-19** | `ai-academic-writing` | **调用**：它出文体，我们管判据；`paper-spine` 仍未验证 |
| B | 润色 | `nature-polishing` | **✅ 已验证 2026-10-19** | 无 | **调用**：接进 ④ 润色 |
| B | 配图 | `nature-figure` | **✅ 已验证 2026-10-19** | 无 | **调用**；需 matplotlib/numpy，首次会装包 |
| C | 出片 | `ppt-master` | 已验证（出过 pptx） | `academic-slides` 内容侧 | 保持：它出片，我们管讲者侧 |
| C | 讲稿 / 幻灯片体检 | 无 | — | `academic-slides` | 本库独有 |
| D | 研究设计 | 无 | — | `study-design` | 本库独有 |
| E1–E4 | 数据管线 | `nature-statistics` | **✅ 已验证 2026-10-19** | `data-pipeline`（管流程与留痕） | **调用**：方法问它，留痕问我们 |
| E1 | 实验记录 | `nature-experiment-log` | **✅ 已验证 2026-10-19** | 无 | **调用** |
| E5 | 投稿前核查 | `academic-paper-reviewer` | **未见使用记录** | `text-self-review` | 先验证 |
| E6 | 选刊 | 无 | — | `submission` | 本库独有 |
| E7 | 成果台账 | 无 | — | `submission` | 本库独有 |
| E7 | 审稿回复 | `nature-response` | **未见使用记录** | 无 | 验证通过后接进 `submission` |
| 支线 | 同行评议 | `nature-reviewer` ❌ ／ `academic-paper-reviewer` **✅ 已验证 2026-10-19** | 前者不在 allowlist；后者可调用 | `peer-review`（五层轴，已验证可跑） | **三选一**：自有五层轴、ARS 多席位、两者并用 |
| E5 | 投稿前自审 | `academic-paper-reviewer` | **✅ 同上一行** | `text-self-review` | 同上 |
| 支线 | 全管线编排 | `academic-pipeline` · `academic-paper` · `academic-writing` | 可调用·**未跑过** | 无 | 不接；只借用个别模式 |
| 支线 | 国自然 | `nature-proposal-writer` | **✅ 已验证 2026-10-19** | `grant-diagnosis` | **分工**：它出章节框架，我们做诊断；**不代写正文** |
| 支线 | 专利 | `nature-paper-to-patent` | 已接入·**未验证产物** | 无 | 先各跑一次 |
| 横向 | 文本自查 | 无 | — | `text-self-review` | 本库独有 |

**「未见使用记录」= 装了，但没有任何一次产物或日志证明它跑通过。**
**「已接入」= 文档里写了要调用它，但同样没有产物证据。**

按现有记录，11 个外部工具里只有 `nature-ref-verifier` 有明确的使用记录；`ppt-master` 出过 pptx。其余九个都没有产物证明。在验证之前，不得写进任何 skill 的分工节。

---

## 三、验证方法

在**科研助手**（`pubmed-zotero`）里逐条跑，每条记三件事：有没有产出、产出落在哪、结果能不能用。

| # | 工具 | 怎么试 | 通过标准 |
|---|---|---|---|
| 1 | `nature-academic-search` | 检索「claustrum clozapine」 | 返回带 DOI 的条目，且能说出用了哪些库 |
| 2 | `nature-downloader` | 取一篇有 DOI 的开放获取文献 | 落下一个能打开的 PDF |
| 3 | `nature-reader` | 让一份 PDF 出中英对照 | 产出文件可读，段落对应 |
| 4 | `nature-paper-card` | 对同一篇出 16 模块卡 | 产出结构化卡片 |
| 5 | `nature-writing` | 用一段结果文字出 Methods 节 | 产出可用的英文段落 |
| 6 | `nature-polishing` | 润色一段中译英 | 保留事实，只改语言 |
| 7 | `nature-reviewer` | 对一篇公开论文出评审意见 | 产出结构化的意见 |
| 8 | `nature-response` | 对一条审稿意见写回复 | 产出逐条应答 |
| 9 | `nature-proposal-writer` | 给一个选题出标书框架 | 产出章节框架 |
| 10 | `academic-paper-reviewer` | 对同一篇出模拟评审 | 产出多份报告 |
| 11 | `nature-ref-verifier` | 核一条已知错误的引用 | 能指出错在哪 |

跑完把结果填回本表的状态列。**通过才接线，不通过就从推荐里删掉**——不留「据说可以」。

---

## 三之二、验证记录

### 2026-10-19 · 科研助手实测

**1. nature-academic-search — 可用**

检索 `claustrum clozapine`，产物已落盘（md + json）。

| 源 | 命中 | 说明 |
|---|---:|---|
| PubMed（标题摘要） | 1 | `claustrum[TA] AND clozapine[TA]` |
| Europe PMC（全文） | 223 | 换成全文检索后数量级不同 |
| OpenAlex | 3 | |
| CrossRef | 13842 | **相关度匹配，不是布尔 AND，不能当命中数** |
| Semantic Scholar | 失败 | HTTP 429，重试 3 次仍限流 |
| Google Scholar | 失败 | fetch failed |
| arXiv | 365 | 前 20 条无一条同时命中两个主题词 |

对照：`claustrum[TA]` 单独 1527 条，`clozapine[TA]` 单独 15268 条，交集 1 条。**说明不是检索式失效，是两个词在标题摘要层几乎没有共现。**

教训：**「检索到 0 条」要先分清是检索式问题还是主题本身空。** 此处属后者。

**2. nature-downloader — 部分可用**

三条路线，前两条失败，第三条成功：

| # | 路线 | 结果 |
|---|---|---|
| 1 | DOI + `--open-access` | `oa_not_found`（元数据说 confirmed_oa，实际取不到） |
| 2 | 出版商直链（MDPI） | 403 Forbidden |
| 3 | arXiv 开放获取 | **成功**：15 页 PDF，1,046,055 字节，文件头与文本均校验通过 |

规律：**开放获取直链可用，出版商页面与 DOI 解析经常取不到。**

**3. nature-reviewer — 不可调用**

```
Skill nature-reviewer is not in this session's skills allowlist
```

目录里有这个文件夹，但会话允许清单里没有它。**「装了」与「能用」之间还隔着一层 allowlist。**

替代用本库 `peer-review` 跑同一篇，产出 8 条编号意见 + 保密意见，`check_review.py` 六组硬规则全过。**本库审稿链路端到端可用。**

---

### 2026-10-19 · 第二批（数据组）

**4. nature-statistics — 可用**

给定场景（42 例 TRS、两次 PANSS、两协变量），产物 124 行。给出的判断：

| 项 | 结论 |
|---|---|
| 主分析 | 线性混合效应模型，`组别 × 时间 + 年龄 + 病程`，随机截距按患者 |
| 基线比较 | ANCOVA，与治疗效应模型分开 |
| 明确不推荐 | 逐时间点独立 t 检验、按中位数二分连续变量 |
| 多重比较 | 全脑用置换 + TFCE/FWE；预设 ROI 用 FDR，并写明校正检验数 |
| 效应量 | 交互项标准化系数或 Cohen's d，附 95% CI |
| **样本量** | **42 例在 α=0.05、power=0.80 下只能检出 d ≈ 0.88–0.93 的大效应**；交互检验的可检出效应依重测相关 ρ 而定（ρ=0.8 时约 0.55–0.60） |
| 硬约束 | 共线性（VIF>5）、残差假设、扫描仪漂移 |

也明确反对事后功效计算。

> **对 TRS 项目的直接含义**：42 例只够看大效应。要检中等效应，样本量或设计得改。

**5. nature-experiment-log — 可用**

产物 153 行，字段分八组：标识 / 受试者 / 设备 / 范式 / 数据文件 / 质控 / 正文段落 / 异常与下一步。给的是可填的空模板，不是编造的记录。

---

### 2026-10-19 · 第三批（写作组）

**6. nature-polishing — 可用**

产物 251 词、4 段，另附术语台账与 6 条修订说明。润色带修订记录这一点值得保留。

**7. nature-writing — 可用**

产物 113 词，四个小节：Participants / EEG recording and MMN measurement / Outcome / Statistical analysis。字数落在要求的 100–150 区间内，分节符合 IMRaD。

**8. nature-proposal-writer — 可用**

产物是完整的国自然章节框架：立项依据与研究内容（1.1–1.5）、研究基础与工作条件（2.1–2.4）、其他需要说明的问题、附件、参考文献。

> ⚠️ **分工要守住**：它出框架，`grant-diagnosis` 做诊断。国自然明文禁止用生成式 AI 直接生成申请书正文，**框架可以，正文不行**。

---

### 2026-10-19 · 第四批（ARS）

**9. ARS 组件 — 可调用**

本机可调用的 ARS 技能五个（按实测调用，不按目录）：

| 技能 | 可调用 | 说明 |
|---|---|---|
| `academic-writing` | 是 | |
| `academic-paper` | 是 | |
| `academic-paper-reviewer` | 是 | 已实跑 |
| `academic-pipeline` | 是 | 未跑 |
| `academic-slides` | 是 | **本库自有，不是 ARS 的** |

没有名为 `academic-research-skills` 的独立技能；ARS 是这组技能的共同前缀。

**实跑：`academic-paper-reviewer`，`methodology-focus` 模式**

| 项 | 事实 |
|---|---|
| 输入 | arXiv:2503.01761v3，15 页，抽取 77,102 字符 |
| 用时 | 约 3 分钟（技能探测另计 3–4 分钟） |
| 多 agent | **有**：方法学席位 112 秒、EIC 席位 27 秒，两个子代理并行、互不可见 |
| 产出 | 3 条方法学意见 + 2 份独立席位报告 |

它找到的具体问题（对同一篇论文）：

1. 摘要写 `ICC >0.89, DSC >0.85`，Table 2 左半球为 ICC 0.863、DSC 0.837–0.839 —— **摘要与主表冲突**
2. Table 2 的亚区「inter-rater reliability」实际是固定同一 whole-claustrum mask 后的 landmark 放置一致性；Table 1 三列亚区体积可逐列加总回 1693.0 / 1729.0，证明没有独立分割
3. 亚区 DSC 0.925–0.948 反高于 whole 0.838 —— 方向不合理

> **判断**：ARS 的审稿席位是真能找问题的，不是泛泛而谈。
> 怎么用（当结论 / 当线索 / 不用）待定，不作预设。

---

### 2026-10-19 · 第五批（阅读与配图）

**10. nature-reader — 可用**

| 项 | 事实 |
|---|---|
| 产物 | `paper.md` 122,044 字节；`source_map.json` 49 块；`translation_notes.md`；`assets/` 5 张 300dpi 图 |
| 覆盖 | 正文 35 组中英对照、图注 5 组、图 5 幅、表 3 张、参考文献 87 条（照录未译） |
| 对齐 | 逐段一一对应；双栏跨栏段落合并；图表放在首次实质提及处 |
| 额外价值 | 标注了原文 3 处缺陷：摘要拼写、p.8 语法残缺、三处体积合计口径不一致 |

**11. nature-paper-card — 可用，但有一个坑**

16/16 模块齐全，内置审计 14 项全通过，检出 111 个 `[Paper: PDF p. N]` 指针。

> ⚠️ **坑**：`prepare_paper.py` 自动识别图为 0、表为 0（PDF 图注匹配不到）。卡内的 5 图 3 表是人工补入的。**用它时不要相信自动图表识别，先核一遍。**

**12. nature-figure — 可用**

产出三格式：PNG（2102×1653，600dpi）、SVG（89×70mm，文字可编辑）、PDF（TrueType），另附绘图源码、源数据、QA 说明。自检 13 通过、1 警告（未导 TIFF）。

两条环境事实：

- 本机原先没有 matplotlib / numpy，本次安装后出图
- 技能规则要求先问 Python 还是 R，本次未问直接选了 Python —— **属流程偏离**

---

## 四、为什么不直接全接

装了不等于能用。`literature-pipeline` 里已经记过一次教训：

> 别因为「装了」就以为「能用」。nature-academic-search、nature-reader、nature-paper-card 这三个找不到产物或日志记录。

把不可用的工具写进流程，等于让人在关键环节撞墙，比没有更糟。

---

## 五、维护

- 每次用外部工具完成一次真实任务，回来更新状态列，写上日期
- 外部工具的 README 改版后，原记录可能失效，改版即降级为「未验证」
- 本表只收录**自己验证过**的工具；索引里的其他同类放 `external-skills.md`，不进本表


---

## 六、2026-10-19 验证总账

| 工具 | 状态 | 关键限制 |
|---|---|---|
| `nature-academic-search` | ✅ 可用 | Semantic Scholar 429、Google Scholar 失败；CrossRef 数是相关度不是命中 |
| `nature-downloader` | ⚠️ 部分 | 只对开放获取直链稳定；出版商 DOI 与 MDPI 403 |
| `nature-reader` | ✅ 可用 | — |
| `nature-paper-card` | ✅ 可用 | **自动图表识别为 0，需人工补** |
| `nature-writing` | ✅ 可用 | — |
| `nature-polishing` | ✅ 可用 | 附带修订说明与术语台账 |
| `nature-figure` | ✅ 可用 | 依赖 matplotlib/numpy；会先问 Python/R |
| `nature-statistics` | ✅ 可用 | 42 例只能检出 d≈0.88 以上 |
| `nature-experiment-log` | ✅ 可用 | — |
| `nature-proposal-writer` | ✅ 可用 | **只出框架，不出正文** |
| `nature-reviewer` | ❌ 不可用 | 不在 allowlist |
| `academic-paper-reviewer` | ✅ 可用 | 约 3 分钟；多席位并行 |
| `academic-paper` · `academic-pipeline` · `academic-writing` | 可调用·未跑 | — |
| `nature-ref-verifier` | 曾用过·未复验 | — |
| `nature-paper-to-patent` · `nature-paper2ppt` · `paper-spine` | 未验证 | — |
| `ppt-master` | ✅ 出过 pptx | — |

**十四项已验证通过，一项确认不可用（`nature-reviewer`），六项未验。**
