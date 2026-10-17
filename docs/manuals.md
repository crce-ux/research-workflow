# 手册 ↔ skill 去向表

> 本表是 `manuals/` 50 份文件的唯一去向结论。**以 skill 为准**，手册只作源材料归档。
> 判定脚本：`python scripts/audit_manuals.py --json out.json`（口径：CJK 二元组重合度，只报候选）。
> 脚本分数只说明用词重合；改写过的章节分数会低，低分不等于没收录。

| 手册 | 节数 | 结论 | 去向 | 备注 |
|---|---:|---|---|---|
| `checklists/PPT文稿去味清单.md` | 11 | 已收 | academic-slides / check_phrases |  |
| `checklists/内容自检清单.md` | 13 | 已收 | ai-academic-writing/references/content-audit.md |  |
| `checklists/写作禁用词与句式清单.md` | 7 | 已收 | 机检 check_phrases |  |
| `checklists/出稿检查总表.md` | 6 | 已收 | ai-academic-writing + 各机检 |  |
| `funding/SCI投稿_选刊流程.md` | 8 | 已收 | submission |  |
| `funding/国自然_规则取用指引.md` | 5 | 已收 | grant-diagnosis |  |
| `funding/国自然与SCI写作_外部框架调研_20260919.md` | 8 | 已收 | grant-diagnosis | 调研部分不收；判据部分在 ten-layers |
| `funding/国自然与SCI写作_板块规划_20260919.md` | 8 | 已收 | grant-diagnosis |  |
| `funding/国自然标书_医学口补充.md` | 6 | 已收 | grant-diagnosis |  |
| `funding/国自然标书_诊断与架构手册.md` | 12 | 已收 | grant-diagnosis |  |
| `notes/AI科研配图_路线选择与实测记录_20260915.md` | 9 | 不收 | — | 一次性调研记录，不是规则 |
| `notes/Token消耗估算_20260919.md` | 9 | 不收 | — | 一次性调研记录，不是规则 |
| `notes/工作流整体评估_20260919.md` | 8 | 不收 | — | 一次性调研记录，不是规则 |
| `notes/第三方库评估_ChineseResearchLaTeX_20260919.md` | 9 | 不收 | — | 一次性调研记录，不是规则 |
| `notes/第三方技能库_可借鉴项与升级清单_20260919.md` | 11 | 不收 | — | 一次性调研记录，不是规则 |
| `notes/评估_workbuddy技能包全量扫描_20260926.md` | 11 | 不收 | — | 一次性调研记录，不是规则 |
| `notes/调研_中文文献库通路_现成工具_20260922.md` | 9 | 不收 | — | 一次性调研记录，不是规则 |
| `ppt/PPT工具链手册.md` | 13 | 不收 | — | 工具链已删大半；保留的部分见 academic-slides/scripts |
| `ppt/PPT工具链速查_20260915.md` | 11 | 不收 | — | 工具链已删大半，速查失效 |
| `ppt/PPT文稿去AI味_skill调研与落地方案_20260912.md` | 8 | 不收 | — | 调研记录；规则已进 ai-academic-writing |
| `ppt/PPT版式配方库_20260915.md` | 16 | 不收 | — | 配方库已删（2026-10-18），路线废弃 |
| `ppt/PPT视觉规范_国自然风格_20260915.md` | 11 | 不收 | — | 国自然风格，PPT 改走 ppt-master |
| `ppt/pptx_to_svg_全7套终版结论_20260922.md` | 9 | 不收 | — | 试跑记录，路线废弃 |
| `ppt/pptx_to_svg_跨模板验证_20260922.md` | 8 | 不收 | — | 试跑记录，路线废弃 |
| `ppt/pptx_to_svg试跑_3深蓝白色系_20260922.md` | 6 | 不收 | — | 试跑记录，路线废弃 |
| `ppt/pptx_to_svg试跑_排版与设计层_20260922.md` | 7 | 不收 | — | 试跑记录，路线废弃 |
| `ppt/手册_PPT底层_ppt-master规则与反解.md` | 5 | 已收 | academic-slides | ppt-master 的规则依据 |
| `ppt/评估_外部PPTskill_ppt-design-master_20260926.md` | 10 | 不收 | — | 外部评估记录 |
| `ppt/诊断_画面单调的成因与解法_20260922.md` | 8 | 不收 | — | 针对自建 SVG 管线；出片改走 ppt-master 后不适用 |
| `templates/AI使用情况声明模板.md` | 11 | 已收 | ai-academic-writing/references/ai-boundary.md |  |
| `templates/会话交接模板.md` | 9 | 已收 | session-handoff |  |
| `templates/工作日志模板.md` | 3 | 已收 | data-pipeline |  |
| `templates/新项目骨架.md` | 5 | 已收 | academic-slides / 项目初始化 |  |
| `templates/理解确认清单模板.md` | 10 | 已收 | academic-slides/references/comprehension-gate.md |  |
| `workflow/数据与统计分析流程.md` | 7 | 已收 | data-pipeline |  |
| `workflow/文献调研流程手册.md` | 15 | 已收 | literature-pipeline | 五节改写后分数偏低，内容在 SKILL.md 与 references/coverage-and-rules.md |
| `workflow/日常精读手册.md` | 10 | 已收 | paper-reading |  |
| `workflow/汇报PPT产出流程手册.md` | 13 | 已收（已改定位） | academic-slides | 出片改走 ppt-master；文件本身的流程已按新定位改写 |
| `workflow/论文撰写流程.md` | 7 | 已收 | ai-academic-writing |  |
| `workflow/课题设计流程手册.md` | 13 | 已收 | study-design |  |
| `writing/Obsidian标注回写_插件与skill调研.md` | 8 | 不收 | — | 工具调研，不是规则；结论是插件选型 |
| `writing/Obsidian标注改稿_应用向规则与可复制块.md` | 10 | 不收 | — | 标注协议，未进 skill；要用于改稿时再单独建 |
| `writing/PPT与讲稿_身份匹配约束.md` | 9 | 已收 | ai-academic-writing / 机检 check_persona |  |
| `writing/代笔身份匹配_可复制块.md` | 7 | 已收 | ai-academic-writing |  |
| `writing/反防御性写作_发布会原则.md` | 9 | 已收 | ai-academic-writing |  |
| `writing/文本迭代自查流程.md` | 11 | 已收 | text-self-review |  |
| `writing/标书去机器味_四层扫描法.md` | 15 | 已收 | ai-academic-writing |  |
| `取数/手册_中文文献库取数.md` | 3 | 已收 | literature-pipeline/references/pitfalls.md | 维普/知网四坑在 pitfalls；标题差异导致分数低 |
| `取数/手册_监管政务数据库取数.md` | 3 | 已收 | literature-pipeline/references/regulatory-databases.md |  |

## 统计

不收 20 份 · 已收 28 份 · 已收（已改定位） 1 份

## 缺口清单

**无未处置的内容缺口。** 审计报出的 21 处「未匹配」全部落在下列三类，已逐条判为不收：

1. `ppt/` 的试跑与评估记录（路线已废弃）
2. `ppt/PPT版式配方库`、`PPT视觉规范_国自然风格`（配料库已删 / 风格不再使用）
3. `notes/` 的调研记录

两处低分是改写造成的，内容确实在 skill 里：

| 手册 | 实际去向 |
|---|---|
| `取数/手册_中文文献库取数.md` | `literature-pipeline/references/pitfalls.md`（维普/知网四坑） |
| `workflow/文献调研流程手册.md` | `literature-pipeline/SKILL.md` 与 `references/coverage-and-rules.md` |

## 维护约定

- 手册更新后跑一次 `audit_manuals.py`，看新节有没有去向。
- 新增手册必须在本表登记，否则 `check_manuals.py` 报错。
