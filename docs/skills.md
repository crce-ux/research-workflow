# 工序 × skill 对照图

> **本文回答一个问题：流程走到某一步，该用谁。**
>
> 流程本身在 [`pipeline.md`](pipeline.md)（P → A → B → C → D → E，含五门与六轴）。
> **从任务出发的入口表**在 [`README.md`](README.md)。
> **外部同类项目的许可与运行足迹**在 [`external-skills.md`](external-skills.md)——**复制前先看其许可列**。
> 本文把**自研 skill** 与**已装的外部 skill** 挂到同一张对照表上——
> 顺便标出**哪些工序没有自研 skill 承载**。
>
> ⚠️ **「有外部 skill」不等于「缺口填上了」**：外部 skill 不背本库的纪律
> （覆盖声明、三态标签、保真界限…）。
>
> | 标记 | 意思 |
> |---|---|
> | ✅ | 有自研 skill 承载 |
> | ⚪ | **主动决定留外部**——外部够用、不建；**且已在对应自研 skill 里挂了调用指针** |
> | 🔴 | 没有自研 skill，也没挂指针（**2026-10-14 起为 0**） |

---

## 〇、全图速览

```
P  日常精读      ✅ paper-reading
A  文献侧        ✅ literature-pipeline（检索 · 取数 · 证据表）
B  内容侧        ✅ ai-academic-writing（表达/内容）· academic-slides（制作稿）
C  交付侧        ✅ academic-slides（出片/体检/快照）· ai-academic-writing（元数据）
D  课题设计      ✅ study-design
E  执行产出      ✅ data-pipeline（E1–E4）· ai-academic-writing（E5）· submission（E6/E7）
────────────────────────────────────────────────
独立支线         国自然 ✅ grant-diagnosis · 审稿 ✅ peer-review · 专利/实验记录 ⚪ 外部够用（指针已挂）
全局             证据核查 ✅ · 自查协议 ✅ text-self-review（横向）
```

**跨段的交接物**——工序连着不等于数据连着。实际递出去的东西是这几个：

| 交接物 | 从 | 到 | 内容 |
|---|---|---|---|
| 精读笔记 | `paper-reading` | `literature-pipeline` | 15 列，含证据标签与定位方式；回填时对齐证据表 |
| **证据表** | `literature-pipeline` | `ai-academic-writing` | 12 列，成文时每个数字指回对应行 |
| **内容稿** | `ai-academic-writing` | `academic-slides` | 要讲什么（⚠️ 推定） |
| 终稿 | `ai-academic-writing` | `submission` | 选刊与成果台账 |
| 制作稿 · 讲稿 · PPTX | `academic-slides` | （交付） | C4 快照后存档 |

> ⚠️ **补记（2026-10-15）**：这张表原先不存在，跨段接口只靠人记。
> 两处曾是断的——`literature-pipeline` 的 SKILL.md 对另外两个 skill 零提及；
> 「内容稿」在 `academic-slides` 里只写了「一份内容稿」，没说由谁产出。
> 现已在三个 skill 各加一节「上下游接口」，本表与之对齐。
>
> ⚠️ **另有跨段的一道工序**：**C3 隐藏元数据**属交付侧，却落在 `ai-academic-writing` 而不是
> `academic-slides`。交付时不要漏。
>
> ✅ **2026-10-15 铺开**：十个自研 skill 全部补齐「上下游接口」一节，格式统一为
> 「上游给我什么 / 我给下游什么 / 什么状态算交出去了 / 不交接的」。
> 并加了机检：`check_assets` **第 7 类 · 接口声明**（硬门禁）——
> 自研 skill 的 SKILL.md 缺这一节就报错；第三方仓自动排除。

**剩下三个缺口都属「外部够用」，且各自在对应自研 skill 里挂了指针。**

> ⚪ **为什么不把它们并进来**（2026-10-14 决定）：
> ① **许可证**——`nature-figure` / `nature-paper-to-patent` **未声明 license**，不能复制进本仓公开分发；
> ② **维护**——`nature-figure` 34M / 114 文件，上游在更新，fork 完就是自己扛；
> ③ **它们已经装好**——科研助手 `pubmed-zotero` 有 32 个 skill，全套都在。
> **一句话：调用 > 复制。** 指针只写「什么时候调谁」，不复制一行内容。

---

## 一、P · 日常精读

| 工序 | 自研 | 外部（已装） |
|---|---|---|
| 选文 / 精读 / 笔记 | ✅ `paper-reading` | `nature-reader`（中英对照）· `nature-paper-card`（16 模块卡）· `literature-review` |

> **自研补的是**：证据标签五态（归属轴）· 定位方式三态 · 15 列回填对齐证据表。

---

## 二、A · 文献侧

| 工序 | 自研 | 外部（已装） |
|---|---|---|
| A1 检索 | ✅ `literature-pipeline` **§〇 是唯一步骤入口** | 见其 §〇：常轨走本库脚本 · 重装按需启用 · ⛔ 标注已弃用 · `nature-literature-pipeline`（外部发现管线：多源检索→六维打分→精读→归档） |
| 全文下载 | — | `nature-downloader` |
| **G0** 质控四项 | ✅ `literature-pipeline`（覆盖声明 + 四项硬性） | `nature-ref-verifier` |
| A2 证据表 | ✅ `literature-pipeline`（12 列口径） | — |
| **G1** 入库 | ✅ `literature-pipeline`（PMID ↔ DOI） | — |
| 取数·专项 | ✅ `literature-pipeline`（中文库 + 政务 / 产业库） | — |
| 综述成文 | ✅ `ai-academic-writing`「文体分叉：论文 / 综述」（名头与配置自洽 · 定论点 · 选结构 · 排证据） | `citation-reviewer`（**私人库**，管成文**之后**：引用审查 / 删改 / 去 AI 味 / 配图 / 格式收尾） |

> **自研补的是**：覆盖声明 `N → M → K` · 影响力归一化（裸被引会筛掉最好的新文）· 证据表列口径。

---

## 三、B · 内容侧（汇报用）

| 工序 | 自研 | 外部（已装） |
|---|---|---|
| B2 自检 | ✅ `ai-academic-writing` ⑤⑥ | `writing-anti-ai` · `humanizer` · `zh-humanizer` · `ai-writing-detection` · `ai-check` |
| **G2** 内容门禁 | ✅（排他性断言 = 0） | — |
| B3 去 AI 味 | ✅ `academic-slides` | `humanizer` |
| B3.5 理解确认 | ✅ `academic-slides` ② | — |
| **G3** 理解门禁 | ✅（逐页一句话 / 磕巴判据） | — |
| B4 制作稿七项 | ✅ `academic-slides` ③ | `nature-polishing` |

> **自研补的是**：表达层四轴 + 内容层四查 · **待核清零** · **理解确认门禁**（外部只做文字，不管讲的人懂没懂）。

---

## 四、C · 交付侧

| 工序 | 自研 | 外部（已装） |
|---|---|---|
| C1 生成出片 | ✅ `academic-slides` ④⑤（含本地工具链 10 个） | `ppt-master`（合并层）· `pptx-generator` · `nature-paper2ppt` |
| C2 视觉验证 | ✅ `academic-slides` ⑥（源体检 + 像素体检） | — |
| **G4** 交付门禁 | ✅ | — |
| C3 隐藏元数据 | ✅ `ai-academic-writing` ⑧ | — |
| C4 快照 | ✅ `academic-slides` ⑨ | — |

> ⚠️ `ppt_build.py` 的合并层调 `ppt-master`——**本库不含，跑 `setup.sh` 拉**。

---

## 五、D · 课题设计

| 工序 | 自研 | 外部（已装） |
|---|---|---|
| D1 子假设落地 | ✅ `study-design` | `scientific-brainstorming`（找 gap） |
| D2 样本量 | ✅ | — |
| D3 入排与分组 | ✅ | — |
| D4 可行性 | ✅ | — |
| D5 伦理与数据管理 | ✅ | — |
| **D6 混杂与偏倚复核** | ✅ | — |
| 依据审计 | ✅（`check_consistency.py`） | — |

> **自研补的是四条规则**：没有证伪条件就不是科学假设 · 效应量不可照搬文献 ·
> 分组阈值必须写出处（**分五类**，含「软件默认值」） · 可行性必须数字对比 + **砍到最小可行版本**。
> **外加 D6 混杂与偏倚复核**（变量角色分类：混杂控、**中介与对撞不控**）**与裁决四档**。
>
> ⚠️ **D1 含终点定义**（七件事：事件/时点/原点/复合/裁定/删失/可捕获）——
> 只给阈值不给操作，是最常见的半成品。

---

## 六、E · 执行产出 ⚠️ **原先缺口最多的一段**

| 工序 | 自研 | 外部（已装） |
|---|---|---|
| E1 数据（变量字典 / 缺失码） | ✅ `data-pipeline` | `nature-statistics` · `nature-data` |
| E2 缺失处理 | ✅ | — |
| E3 SAP 执行 / 偏离记录 | ✅ | — |
| E4 结果报告 | ✅ | — |
| **E5 论文** | ✅ `ai-academic-writing` ①②③④ | `paper-spine` · `nature-writing` · `academic-paper` · `academic-pipeline` · `academic-writing` |
| 图表 | ⚪ **外部够用，不建**（**指针已挂**：`ai-academic-writing` / `academic-slides` 各有「→ `nature-figure`」一节） | `nature-figure` · `scipilot-figure-skill` · `scientific-schematics` · `scientific-svg-figures` · `scientific-visualization` · `svg-figure` |
| E6 投稿选刊 | ✅ `submission`（含 `journal_match.py` 硬过滤） | — |
| E7 归档（成果台账） | ✅ `submission`（含 `check_credit.py` 署名自洽） | — |

> ✅ **E1–E4 已补**（`data-pipeline`）。原先缺的是纪律成文：
> 变量字典四类缺失码、缺失率先报再处理、SAP 偏离必须记录（**偏离要记录，偏离本身不算错误**）。

---

## 七、独立支线

| 支线 | 自研 | 外部（已装） |
|---|---|---|
| **国自然** | ✅ `grant-diagnosis` | `nature-proposal-writer` |
| **审稿** | ✅ `peer-review` | `nature-reviewer` · `academic-paper-reviewer` · `nature-response` |
| 专利 | ⚪ **外部够用，不建**（**指针已挂**：`submission` 「专利是另一种成果」） | `nature-paper-to-patent` |
| 实验记录 | ⚪ **外部够用，不建**（**指针已挂**：`data-pipeline` 「上游的实验记录」） | `nature-experiment-log` |

> ⚠️ **国自然的 AI 边界和论文不同**：论文可大幅 AI 辅助，**标书明文不得直接生成正文**。
> 标书的 AI 边界由 `grant-diagnosis` 的「AI 边界」一节承载（**此前只写在手册和模板里**）。

### ⚠️ 实验记录：结论是「暂不并、暂不建」（2026-10-14）

三处外部里，只有它的决策当时**没给结论**。现在给：

| | |
|---|---|
| **为什么不并进来** | `nature-experiment-log` 虽是 MIT（法律上可以复制），但它是**写 Obsidian + YAML frontmatter** 的——而它**不知道本库的约定**（工作日志字段、AI 声明、命名规则）。搬进来也要适配才能用。 |
| **为什么不现在自研** | 队列 **10-15 才开始**收数据。**现在定格式 = 猜**；等看清主队列的访视流程、收过第一例，才知道记录该有哪些字段。 |
| **结论** | **暂不并、暂不建**。先在 `data-pipeline` 挂指针（已挂）。 |
| **触发条件** | **收第一例之后**——届时回来定格式，或直接适配 `nature-experiment-log`。 |

---

## 八、全局

| 管什么 | 自研 | 挂在哪 |
|---|---|---|
| **证据层核查**（来源 / 定量 / 承压） | ✅ `ai-academic-writing` ⑦ | 挂 D · E5 · 审稿三处 |
| **自查协议**（换维度迭代） | ✅ `text-self-review` | **横向**——套在任何一份产出上 |
| 知识管理 | — | `obsidian-*` · `med-kb-organizer` |

> `text-self-review` **不属于任何一段**——它是方法层的，不是内容层的。
> 凡是「有一份源文件可回查」的文本都能跑（纯创意写作不适用）。

---

## 九、缺口清单

**原本 7 处「没有自研 skill 承载」的工序，2026-10-14 全部收口：**

| # | 原缺口 | 处置 |
|---|---|---|
| 1 | E6 投稿选刊（148 行） | ✅ `submission` |
| 2 | 取数·专项（中文库 / 政务库，243 行） | ✅ 全部并入 `literature-pipeline` |
| 3 | E7 归档（成果台账 134 行） | ✅ `submission` |
| 4 | C4 快照 | ✅ 并入 `academic-slides` ⑨ |
| 5 | 图表生成 | ⚪ 外部够用，**不建** → 指针在 `ai-academic-writing` / `academic-slides` |
| 6 | 专利 | ⚪ 外部够用，**不建** → 指针在 `submission` |
| 7 | 实验记录 | ⚪ 外部够用，**不建** → 指针在 `data-pipeline` |

**约 525 行手册已落到自研 skill；剩下 3 处是主动决定留外部。**

### ⚠️ 收口时又发现一处，已补（2026-10-14）

| # | 缺口 | 处置 |
|---|---|---|
| 8 | **综述成文**（A 段末） | 原先记作「🟡 部分」——**名不副实**：只有 `citation-reviewer`（**私人库**）承载，而它只管成文**之后**（引用审查 / 删改 / 去 AI 味 / 配图 / 格式）。**「怎么写一篇综述」从来没人管**——`ai-academic-writing` 是给论文（IMRaD）的。 → ✅ **已并入 `ai-academic-writing`**（综述与论文的 ④–⑨ 步完全共用，只有 ①–③ 不同） |

> **教训**：`🟡 部分` 是个含糊标记，掩盖了「一半有人管、一半没人管」。
> **要么写清谁管哪一半，要么就标 🔴。**

> ⚪ ≠ 没人管——外部 skill 能顶上，只是**不背本库纪律**。
> **三处指针已挂进对应自研 skill**（图表 → 写作/幻灯片/综述；专利 → 成果台账；实验记录 → 数据管线），
> 所以 agent 走到对应步骤时会**自己看到该调谁**，不必先去翻本文件。
> 需要哪一条纪律时，回到对应手册（`manuals/`）。

---

## 十、自研 10 个补的是什么

外部 skill 覆盖了「怎么做」，自研的 10 个补的是**外部未覆盖的部分**：

| skill | 段 | 补什么 |
|---|---|---|
| `paper-reading` | P | **证据标签五态**（归属轴）· 定位方式三态 · 精读笔记回填口径 |
| `literature-pipeline` | A | **覆盖声明** · 影响力归一化 · 证据表口径 · **中文库与政务库取数**（含已证伪通路） |
| `ai-academic-writing` | B/E5 | **表达层四轴 + 内容层四查** · 本文核查链 · **AI 边界** · **论文与综述两种文体** |
| `academic-slides` | B/C | **待核清零** · **理解确认门禁** · 讲稿规格 · 本地出片工具链 · 交付快照 |
| `study-design` | D | **四条规则** · 裁决四档 |
| `data-pipeline` | E1–E4 | **四类缺失码** · 缺失先报再处理 · **SAP 偏离必留痕** |
| `submission` | E6/E7 | **相关度是门槛 / IF 只排序** · **成果台账署名自洽**（共同一作不能写成第一） |
| `grant-diagnosis` | 支线 | **标书章节职责归位** · 四层去机器味 · **标书 AI 边界** |
| `peer-review` | 支线 | **五层领域核查轴**（给生成法，不给固定清单）· 伦理边界 |
| `text-self-review` | 横向 | **换维度迭代** + 收敛判据（横向协议） |

> 共同点：**都管「凭什么说这话站得住」**，不管「这话怎么写好看」。
> 后者交给外部 skill。

---

## 十一、怎么用

1. **找到你当前所处的阶段**（左边）
2. **看自研有没有**——有就用它，它背本库纪律
3. **⚪ 的格子**：外部 skill 顶上（指针已挂在对应自研 skill 里）——**但它不背本库纪律，用完自己过一遍**
4. **产出的文本要交出去之前** → 挂 `text-self-review` 跑一遍（横向层）
5. **跑完机检** → 发现**落表**；处置（改 / 不改并写理由 / 改规则）**留到改稿任务里做** → 见 §十二

> 各 skill 的安装与用法见其各自 README。正本都在
> [`research-workflow`](https://github.com/crce-ux/research-workflow)。

---

## 十二、机检发现的处置

**已并入 [`pipeline.md`](pipeline.md) §八**——门禁的落点、三个出口（改 / 不改并写理由 / 改规则）、
以及「跑工具 ≠ 改稿」都在 §八。**同一份规矩只留一处。**
