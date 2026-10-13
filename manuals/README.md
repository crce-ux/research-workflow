# 手册库

**49 份流程手册原文**——[`docs/`](../docs/) 是这套工作流的骨架，这里是它的**细节层**：
每一步具体怎么执行、判据是什么、踩过哪些坑。

> ⚠️ **已去敏化**：所有真实人名、机构、稿件编号、绝对路径、可指认的未发表数据已替换。
> 项目代号（如 TRS、EEG）保留，因为它们描述的是研究领域，不构成识别。

---

## 分类

| 目录 | 份数 | 内容 |
|---|---|---|
| [`workflow/`](workflow/) | 7 | 各阶段流程手册——文献调研 / 汇报 / 论文 / 统计 / 课题设计 / 精读 / 全流程总纲 |
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

1. [`workflow/文献调研与汇报_全流程总纲.md`](workflow/) —— 整套流程的地图
2. [`checklists/出稿检查总表.md`](checklists/) —— 「现在该跑什么、判据是什么」的唯一入口
3. [`writing/文本迭代自查流程.md`](writing/) —— 迭代式自查的完整方法（已沉淀为 [text-self-review](https://github.com/crce-ux/text-self-review)）

**如果你要做汇报：**
`ppt/PPT工具链手册` → `checklists/PPT文稿去味清单` → `checklists/出稿检查总表`

**如果你要写标书：**
`funding/国自然标书_诊断与架构手册` → `writing/标书去机器味_四层扫描法` → `templates/AI使用情况声明模板`

---

## 这些手册与 skill 的关系

手册是**原始材料**，skill 是**提炼后的可执行版本**：

| 手册 | 沉淀成的 skill |
|---|---|
| `writing/文本迭代自查流程` | [text-self-review](https://github.com/crce-ux/text-self-review) |
| `writing/反防御性写作` + `标书去机器味` + `写作禁用词清单` + `代笔身份匹配` | [ai-writing-debug](https://github.com/crce-ux/ai-writing-debug) |
| `workflow/文献调研流程手册` | [literature-pipeline](https://github.com/crce-ux/literature-pipeline) |
| `workflow/汇报PPT产出流程手册`（讲者侧那半） | [talk-readiness](https://github.com/crce-ux/talk-readiness) |
| （审稿方法指南，另存） | [peer-review](https://github.com/crce-ux/peer-review) |
| `workflow/课题设计流程手册` | [study-design](https://github.com/crce-ux/study-design) |

**手册保留了 skill 里放不下的东西**：具体的命令、实测数据、踩坑记录、以及与具体项目绑定的案例。
两者互补——skill 管「怎么做」，手册管「为什么这么做、当时踩了什么坑」。

---

## 说明

- 手册中的**脚本路径**已改为相对形式（如 `scripts/checks/check_language.py`），对应总仓的 [`scripts/`](../scripts/)
- 手册中的**项目名与案例**保留为通用表述（如「本项目」「某文献」）
- 部分手册引用了未随本仓发布的内部文件（如具体的证据表、项目索引），**不影响方法本身的可读性**
