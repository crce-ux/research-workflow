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
| P | 单篇精读 | `nature-reader` · `nature-paper-card` | **未见使用记录** | `paper-reading` | 先验证；不可用则只用本库五态 |
| A | 检索 | `nature-academic-search` · `deep-research` | **未见使用记录** | `literature-pipeline` | 先验证；不可用则用本库的 PubMed/OpenAlex/CNKI 组合 |
| A | 全文获取 | `nature-downloader` | **未验证** | 无 | 验证通过后写成分工 |
| A | 引用核验 | `nature-ref-verifier` | 已验证（用过） | `check_ref_citations` | **分工**：它查存在性，我们查编号一致性 |
| B | 成文 / 文体 | `nature-writing` · `paper-spine` | **未见使用记录** | `ai-academic-writing` | 先验证；可用则它管文体，我们管判据 |
| B | 润色 | `nature-polishing` | **未见使用记录** | 无 | 验证通过后接进 ④ 润色 |
| B | 配图 | `nature-figure` | 已接入 | 无 | 保持 |
| C | 出片 | `ppt-master` | 已接入 | `academic-slides` 内容侧 | 保持：它出片，我们管讲者侧 |
| C | 讲稿 / 幻灯片体检 | 无 | — | `academic-slides` | 本库独有 |
| D | 研究设计 | 无 | — | `study-design` | 本库独有 |
| E1–E4 | 数据管线 | `nature-statistics`（只管方法） | 已接入 | `data-pipeline`（管流程与留痕） | 保持分工 |
| E1 | 实验记录 | `nature-experiment-log` | 已接入 | 无 | 保持 |
| E5 | 投稿前核查 | `academic-paper-reviewer` | **未见使用记录** | `text-self-review` | 先验证 |
| E6 | 选刊 | 无 | — | `submission` | 本库独有 |
| E7 | 成果台账 | 无 | — | `submission` | 本库独有 |
| E7 | 审稿回复 | `nature-response` | **未见使用记录** | 无 | 验证通过后接进 `submission` |
| 支线 | 同行评议 | `nature-reviewer` · `academic-paper-reviewer` | **未见使用记录** | `peer-review`（五层轴） | 先验证；可用则分工 |
| 支线 | 国自然 | `nature-proposal-writer` | **未见使用记录** | `grant-diagnosis` | 先验证；可用则它出结构，我们诊断 |
| 支线 | 专利 | `nature-paper-to-patent` | 已接入 | 无 | 保持 |
| 横向 | 文本自查 | 无 | — | `text-self-review` | 本库独有 |

**「未见使用记录」= 装了，但没有任何一次产物或日志证明它跑通过。** 在验证之前，不得写进任何 skill 的分工节。

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

## 四、为什么不直接全接

装了不等于能用。`literature-pipeline` 里已经记过一次教训：

> 别因为「装了」就以为「能用」。nature-academic-search、nature-reader、nature-paper-card 这三个找不到产物或日志记录。

把不可用的工具写进流程，等于让人在关键环节撞墙，比没有更糟。

---

## 五、维护

- 每次用外部工具完成一次真实任务，回来更新状态列，写上日期
- 外部工具的 README 改版后，原记录可能失效，改版即降级为「未验证」
- 本表只收录**自己验证过**的工具；索引里的其他同类放 `external-skills.md`，不进本表
