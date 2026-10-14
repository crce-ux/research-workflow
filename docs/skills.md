# 工序 × skill 对照图

> **这张图回答一个问题：流程走到某一步，该用谁。**
>
> 流程本身在 [`pipeline.md`](pipeline.md)（P → A → B → C → D → E）。
> 本文把**自研 skill** 与**已装的外部 skill** 挂到同一张骨架上——
> 顺便标出**哪些工序还没有自研 skill**（🔴）。
>
> ⚠️ **「有外部 skill」不等于「这一格填上了」**：外部 skill 不背本库的纪律
> （覆盖声明、三态标签、保真红线…）。🔴 说的是**没有自研 skill 承载**。

---

## 〇、全图速览

```
P  日常精读      ✅ paper-reading
A  文献侧        ✅ literature-pipeline
B  内容侧        ✅ ai-academic-writing（表达/内容）· academic-slides（制作稿）
C  交付侧        ✅ academic-slides（出片/体检）· ai-academic-writing（元数据）
D  课题设计      ✅ study-design
E  执行产出      ✅ data-pipeline（E1–E4）· ai-academic-writing（E5）· E6/E7 🔴
────────────────────────────────────────────────
独立支线         国自然 🔴 · 审稿 ✅ peer-review · 专利 🔴 · 实验记录 🔴
全局             证据核查 ✅ · 自查协议 ✅ text-self-review（横向）
```

**一眼看去：链条在 E 段断了三次，另有国自然那一大块空着。**

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
| A1 检索 | ✅ `literature-pipeline` **§〇 是唯一步骤入口** | 见其 §〇：常轨走本库脚本 · 重装按需启用 · ⛔ 标注已弃用 |
| 全文下载 | — | `nature-downloader` |
| **G0** 质控四项 | ✅ `literature-pipeline`（覆盖声明 + 四项硬性） | `nature-ref-verifier` |
| A2 证据表 | ✅ `literature-pipeline`（12 列口径） | — |
| **G1** 入库 | ✅ `literature-pipeline`（PMID ↔ DOI） | — |
| 取数·专项 | 🔴 **无**（中文库 / 政务库手册 243 行） | — |
| 综述成文 | 🟡 部分 | `citation-reviewer` · `nature-literature-pipeline` |

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
| C4 快照 | 🔴 **无** | — |

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
| 依据审计 | ✅（`check_consistency.py`） | — |

> **自研补的是四条铁律**：没有证伪条件就不是科学假设 · 效应量不可照搬文献 ·
> 分组阈值必须写出处 · 可行性必须数字对比。**外加裁决四档。**

---

## 六、E · 执行产出 ⚠️ **这一段断得最厉害**

| 工序 | 自研 | 外部（已装） |
|---|---|---|
| E1 数据（变量字典 / 缺失码） | ✅ `data-pipeline` | `nature-statistics` · `nature-data` |
| E2 缺失处理 | ✅ | — |
| E3 SAP 执行 / 偏离记录 | ✅ | — |
| E4 结果报告 | ✅ | — |
| **E5 论文** | ✅ `ai-academic-writing` ①②③④ | `paper-spine` · `nature-writing` · `academic-paper` · `academic-pipeline` · `academic-writing` |
| 图表 | 🔴 **无** | `nature-figure` · `scipilot-figure-skill` · `scientific-schematics` · `scientific-svg-figures` · `scientific-visualization` · `svg-figure` |
| E6 投稿选刊 | 🔴 **无**（`journal_match.py` 有，手册 148 行） | — |
| E7 归档（成果台账） | 🔴 **无** | — |

> ✅ **E1–E4 已补**（`data-pipeline`）。原先的拦路虎不是不会做，是**纪律没人替你背**——
> 变量字典四类缺失码、缺失率先报再处理、SAP 偏离必须记录（**偏离本身不致命，不记录才致命**）。

---

## 七、独立支线

| 支线 | 自研 | 外部（已装） |
|---|---|---|
| **国自然** | ✅ `grant-diagnosis` | `nature-proposal-writer` |
| **审稿** | ✅ `peer-review` | `nature-reviewer` · `academic-paper-reviewer` · `nature-response` |
| 专利 | 🔴 **无** | `nature-paper-to-patent` |
| 实验记录 | 🔴 **无** | `nature-experiment-log` |

> ⚠️ **国自然的 AI 边界和论文不同**：论文可大幅 AI 辅助，**标书明文不得直接生成正文**。
> 这一条现在**没有任何 skill 承载**，只写在手册和模板里。

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

## 九、缺口清单（🔴 共 7 处）

| # | 缺口 | 手册行数 | 急不急 |
|---|---|---|---|
| 3 | E6 投稿选刊 | 148 | 🟡 |
| 5 | 取数·专项（中文库 / 政务库） | 243 | 🟢 |
| 6 | 图表生成 | — | 🟢 外部够用 |
| 7 | C4 快照 | — | 🟢 |
| 8 | E7 归档 | — | 🟢 |
| 9 | 专利 | — | 🟢 外部够用 |
| 10 | 实验记录 | — | 🟢 外部够用 |

**合计约 610 行手册没有 skill 承载。**

---

## 十、自研 6 个补的是什么

外部 skill 覆盖了「怎么做」，自研这 6 个补的是**它们不管的那半**：

| skill | 补什么 |
|---|---|
| `literature-pipeline` | **覆盖声明** · 影响力归一化 · 证据表口径 |
| `ai-academic-writing` | **表达层四轴 + 内容层四查** · 本文核查链 · **AI 边界（合规）** |
| `academic-slides` | **待核清零** · **理解确认门禁** · 讲稿规格 · 本地出片工具链 |
| `study-design` | **四条铁律** · 裁决四档 |
| `peer-review` | **五层领域核查轴**（给生成法，不给固定清单）· 伦理边界 |
| `text-self-review` | **换维度迭代** + 收敛判据（横向协议） |

> 共同点：**都管「凭什么说这话站得住」**，不管「这话怎么写好看」。
> 后者交给外部那一堆。

---

## 十一、怎么用

1. **找到你当前那一段**（左边）
2. **看自研有没有**——有就用它，它背本库纪律
3. **🔴 的格子**：先用外部 skill 顶上，**但纪律得自己记**（手册在 `manuals/`）
4. **产出的文本要交出去之前** → 挂 `text-self-review` 跑一遍（横向那一层）

> 各 skill 的安装与用法见其各自 README。正本都在
> [`research-workflow`](https://github.com/crce-ux/research-workflow)。
