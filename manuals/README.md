# 手册库

**49 份流程手册原文**——[`docs/`](../docs/) 是这套工作流的骨架，这里是它的**细节层**：
每一步具体怎么执行、判据是什么、踩过哪些坑。

> ⚠️ **已去敏化**：所有真实人名、机构、稿件编号、绝对路径、可指认的未发表数据已替换。
> 项目代号（如 TRS、EEG）保留，因为它们描述的是研究领域，不构成识别。

---

## 分类

| 目录 | 份数 | 内容 |
|---|---|---|
| [`workflow/`](workflow/) | 6 | 各阶段流程手册——文献调研 / 汇报 / 论文 / 统计 / 课题设计 / 精读 |
| [`checklists/`](checklists/) | 4 | 出稿前的清单——禁用词 / 内容自检 / 去味 / **出稿检查总表** |
| [`templates/`](templates/) | 5 | 骨架与模板——新项目 / 工作日志 / 会话交接 / AI 声明 / 理解确认 |
| [`ppt/`](ppt/) | 12 | PPT 工具链——手册 / 速查 / 视觉规范 / 版式配方库 / 底层规则 / 实测记录 |
| [`writing/`](writing/) | 7 | 写作质量——反防御性写作 / 去机器味 / 身份匹配 / **文本迭代自查** |
| [`funding/`](funding/) | 6 | 基金与投稿——国自然标书诊断 / 规则取用 / 选题规划 / 选刊 |
| [`notes/`](notes/) | 7 | 调研与评估记录——第三方库评估 / 工具选型 / 成本估算 |
| [`data-sources/`](data-sources/) | 2 | 取数手册——中文文献库 / 监管政务数据库 |

---

## 从哪开始读

**如果你只读三份：**

1. [`docs/pipeline.md`](../docs/pipeline.md) —— 整套流程的地图（P→A→B→C→D→E）
2. [`checklists/出稿检查总表.md`](checklists/) —— 「现在该跑什么、判据是什么」的唯一入口
3. [`writing/文本迭代自查流程.md`](writing/) —— 迭代式自查的完整方法（已沉淀为 [text-self-review](https://github.com/crce-ux/text-self-review)）

**如果你要做汇报：**
`ppt/PPT工具链手册` → `checklists/PPT文稿去味清单` → `checklists/出稿检查总表`

**如果你要写标书：**
`funding/国自然标书_诊断与架构手册` → `writing/标书去机器味_四层扫描法` → `templates/AI使用情况声明模板`

---

## 这些手册与 skill 的关系

手册是**原始材料**，skill 是**提炼后的可执行版本**：

| 段 | 手册 | 沉淀成的 skill |
|---|---|---|
| P | `workflow/日常精读手册` | [paper-reading](https://github.com/crce-ux/paper-reading) |
| A | `workflow/文献调研流程手册` | [literature-pipeline](https://github.com/crce-ux/literature-pipeline) |
| A | `data-sources/手册_中文文献库取数`（中文库部分已并入 literature-pipeline §五）<br>`data-sources/手册_监管政务数据库取数` + `notes/调研_中文文献库通路_现成工具_20260922` | [data-sources](https://github.com/crce-ux/data-sources) |
| A | （**无对应手册**——综述成文此前无人承载，2026-10-14 新建） | [review-writing](https://github.com/crce-ux/review-writing) |
| B/E5 | `workflow/论文撰写流程` + `writing/反防御性写作` + `writing/标书去机器味` + `checklists/写作禁用词与句式清单` + `writing/代笔身份匹配` | [ai-academic-writing](https://github.com/crce-ux/ai-academic-writing) |
| B/C | `workflow/汇报PPT产出流程手册` + `ppt/`（12 份）+ `checklists/出稿检查总表` | [academic-slides](https://github.com/crce-ux/academic-slides) |
| D | `workflow/课题设计流程手册` | [study-design](https://github.com/crce-ux/study-design) |
| E1–E4 | `workflow/数据与统计分析流程` | [data-pipeline](https://github.com/crce-ux/data-pipeline) |
| E6/E7 | `funding/SCI投稿_选刊流程`（+ 成果台账规范，手册另存） | [submission](https://github.com/crce-ux/submission) |
| 支线 | `funding/国自然标书_诊断与架构手册` + `funding/国自然标书_医学口补充` + `funding/国自然_规则取用指引` | [grant-diagnosis](https://github.com/crce-ux/grant-diagnosis) |
| 支线 | （审稿方法指南，另存） | [peer-review](https://github.com/crce-ux/peer-review) |
| 横向 | `writing/文本迭代自查流程` | [text-self-review](https://github.com/crce-ux/text-self-review) |

> **共 12 个 skill。** 完整工序对照（含缺口与外部工具指针）见
> [`docs/skills.md`](../docs/skills.md)。

**手册保留了 skill 里放不下的东西**：具体的命令、实测数据、踩坑记录、以及与具体项目绑定的案例。
两者互补——skill 管「怎么做」，手册管「为什么这么做、当时踩了什么坑」。

---

## 说明

- 手册中的**脚本路径**已改为相对形式（如 `scripts/checks/check_language.py`），对应总仓的 [`scripts/`](../scripts/)
- 手册中的**项目名与案例**保留为通用表述（如「本项目」「某文献」）
- 部分手册引用了未随本仓发布的内部文件（如具体的证据表、项目索引），**不影响方法本身的可读性**

---

## 逐份索引

> ⚠️ 各手册里提到的《**文献调研与汇报_全流程总纲**》是内部总纲，**未随本仓发布**；
> 其等效内容见 [`docs/pipeline.md`](../docs/pipeline.md)（P→A→B→C→D→E）与 [`docs/gates.md`](../docs/gates.md)。

> 49 份的完整清单。**加粗的**是建议优先读的。

### 流程手册 · `workflow/`（6 份）

| 文件 | 讲什么 |
|---|---|
| `数据与统计分析流程.md` | 实测过的失分点： |
| **`文献调研流程手册.md`** | 文献调研流程手册（证据表→讲解→综述→PPT） |
| `日常精读手册.md` | 日常精读手册（P 段） |
| `汇报PPT产出流程手册.md` | 先把内容写完再碰排版：汇报稿 / 提纲 / 精简报告。 |
| `论文撰写流程.md` | 【上游】数据与统计分析流程 |
| **`课题设计流程手册.md`** | 课题设计流程手册（D 段） |

### 出稿清单 · `checklists/`（4 份）

| 文件 | 讲什么 |
|---|---|
| `PPT文稿去味清单.md` | 实测数据：把 skill 的规则跑在 组会汇报PPT制作稿20260912.md上——20 个内容层触发词命中 … |
| **`内容自检清单.md`** | 两张清单的分工： |
| `写作禁用词与句式清单.md` | 写作禁用词与句式清单 |
| **`出稿检查总表.md`** | 出稿检查总表 |

### 骨架与模板 · `templates/`（5 份）

| 文件 | 讲什么 |
|---|---|
| `AI使用情况声明模板.md` | AI 使用情况声明 · 模板 |
| `会话交接模板.md` | <项目> 对接（新会话专用）— <YYYY-MM-DD> |
| `工作日志模板.md` | <项目名> 工作日志 |
| `新项目骨架.md` | 新项目骨架模板 |
| **`理解确认清单模板.md`** | 如果我自己不懂，就判断不出内容对不对。 |

### PPT 工具链 · `ppt/`（12 份）

| 文件 | 讲什么 |
|---|---|
| `pptx_to_svg_全7套终版结论_20260922.md` | 全 7 套 · 终版结论 |
| `pptx_to_svg_跨模板验证_20260922.md` | 跨模板验证：哪些能改，哪些不能 |
| `pptx_to_svg试跑_3深蓝白色系_20260922.md` | pptxtosvg 试跑：3深蓝白色系 |
| `pptx_to_svg试跑_排版与设计层_20260922.md` | pptxtosvg：排版层与设计层 |
| `PPT工具链手册.md` | python scripts/pptinit.py 我的汇报 \ |
| `PPT工具链速查_20260915.md` | PPT 工具链速查 |
| `PPT文稿去AI味_skill调研与落地方案_20260912.md` | PPT 文稿去 AI 味：skill 调研与落地方案 |
| `PPT版式配方库_20260915.md` | PPT 版式配方库 |
| `PPT视觉规范_国自然风格_20260915.md` | PPT 视觉规范 · 国自然风格 |
| `手册_PPT底层_ppt-master规则与反解.md` | 手册 · PPT 底层（ppt-master 原始规则 与 PPTX 反解） |
| `评估_外部PPTskill_ppt-design-master_20260926.md` | 外部 PPT skill 评估：ppt-design-master v1.1.0 |
| `诊断_画面单调的成因与解法_20260922.md` | 逐页统计色值用量： |

### 写作质量 · `writing/`（7 份）

| 文件 | 讲什么 |
|---|---|
| `Obsidian标注回写_插件与skill调研.md` | 〇、先定判据（决定了 80% 的结论） |
| `Obsidian标注改稿_应用向规则与可复制块.md` | Obsidian 标注改稿 · 应用向规则与可复制块 |
| `PPT与讲稿_身份匹配约束.md` | PPT 文字与讲稿 · 身份匹配约束 |
| `代笔身份匹配_可复制块.md` | 代笔身份匹配 · 可复制块 |
| **`反防御性写作_发布会原则.md`** | 反防御性写作（Anti-Defensive Writing）· 发布会原则 |
| **`文本迭代自查流程.md`** | 文本迭代自查流程（RCAI 循环） |
| `标书去机器味_四层扫描法.md` | 标书去机器味 · 四层扫描法 |

### 基金与投稿 · `funding/`（6 份）

| 文件 | 讲什么 |
|---|---|
| `SCI投稿_选刊流程.md` | SCI 投稿 · 选刊流程 |
| `国自然_规则取用指引.md` | 国自然 · 规则取用指引 |
| `国自然与SCI写作_外部框架调研_20260919.md` | 国自然与 SCI 写作 · 外部框架调研 |
| `国自然与SCI写作_板块规划_20260919.md` | 国自然与 SCI 写作 · 板块规划 |
| `国自然标书_医学口补充.md` | 国自然标书 · 医学口补充 |
| `国自然标书_诊断与架构手册.md` | 国自然标书 · 诊断与架构手册 |

### 调研与评估记录 · `notes/`（7 份）

| 文件 | 讲什么 |
|---|---|
| `AI科研配图_路线选择与实测记录_20260915.md` | AI 科研配图 — 路线选择与实测记录 |
| `Token消耗估算_20260919.md` | 工作流 Token 消耗估算 |
| `工作流整体评估_20260919.md` | 科研工作流 · 整体评估 |
| `第三方库评估_ChineseResearchLaTeX_20260919.md` | 评估：huangwb8/ChineseResearchLaTeX |
| `第三方技能库_可借鉴项与升级清单_20260919.md` | Research-OS-Studio 可借鉴项与升级清单 |
| `评估_workbuddy技能包全量扫描_20260926.md` | workbuddy 技能包全量扫描（2026-09-26） |
| `调研_中文文献库通路_现成工具_20260922.md` | 中文文献库通路：现成工具盘点 |

### 取数手册 · `data-sources/`（2 份）

| 文件 | 讲什么 |
|---|---|
| `手册_中文文献库取数.md` | 手册 · 中文文献库取数（维普 + 知网） |
| `手册_监管政务数据库取数.md` | 手册 · 监管/政务数据库取数 |
