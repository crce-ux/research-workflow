# research-workflow

[![CI](https://github.com/crce-ux/research-workflow/actions/workflows/ci.yml/badge.svg)](https://github.com/crce-ux/research-workflow/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**一套从文献检索到成果交付的科研工作流**——带工具、带门禁、带判据。

不是一份方法论综述，是**实际在跑的系统**：下面的每一步、每一道门、每一个脚本，
都来自真实的科研工作，并在真实的返工里被改过。

---

## 管线地图

```
P  日常精读 ────────────────────────────────────────────┐
                                                        │
A  文献侧   检索 → G0 检索层 → 证据表 → G1 入库          │
                                                        │
B  内容侧   内容稿 → B2 自检 → G2 内容门禁               │
             → B3.5 理解确认 → G3 理解门禁 → 制作稿      │
                                                        │
C  交付侧   生成 → 视觉验证 → G4 交付门禁 → 复核 → 快照  │
                                                        │
D  课题设计 子假设 → 样本量 → 入排 → 可行性 → 伦理       │
                                                        │
E  执行产出 数据 → SAP → 结果 → 论文 → 投稿 → 归档       │
└────────────────────────────────────────────────────────┘
```

**四侧（A/B/C/D）+ 两条贯穿线（P 日常精读、E 执行产出）。**

---

## 五道门禁

门禁是这套系统里最核心的设计——**它们不是建议，是关卡**。

| 门 | 一句话判据 | 不过怎么办 |
|---|---|---|
| **G0** 检索层 | 去重 / 存在性 / 元数据完整 / 版本，**四项全过** | 不进表 |
| **G1** 入库 | PMID ↔ DOI 一一匹配 | 回源反查 |
| **G2** 内容 | **排他性断言 = 0** | 补出处 |
| **G3** 理解 | **逐页一句话说得出** | 说不出来就别做 PPT |
| **G4** 交付 | 边缘 / 边距 / 四角 全 0 | 回制作稿改 |

> ⚠️ **唯一的回改回路**：G4 发现问题 → **回制作稿改**，不是直接改成品。
> 否则下次重新生成又会被覆盖。

---

## 六条轴（**别混着查**）

**混着查会互相误报**——同一个词，讲稿里是对的，幻灯片里就是错的。

| # | 轴 | 查什么 |
|---|---|---|
| ① | 措辞的**文体适配** | 口语节拍 vs 口语化 |
| ② | 说法**准不准** | 自足 / 可答 / 有出处 / 不越原文 |
| ③ | 像不像**他**写的 | 术语层 / 引据层 / 立场层 |
| ④ | 像不像**人**写的 | AI 味、套话 |
| ⑤ | **引用与断言** | 自足 · 排他性 · 量词 · 缩写 · 数字口径 |
| ⑥ | **身份匹配**机检 | 保守 / 越级 / 引据 / 回指 / 书面语 / 长句 |

详细判据见 [`docs/gates.md`](docs/gates.md)。

---

## 配套 skill（各自独立仓库）

这套工作流里的**方法**已经沉淀成 6 个可安装的 skill：

| Skill | 管什么 | 最硬的一条 |
|---|---|---|
| [`text-self-review`](https://github.com/crce-ux/text-self-review) | 迭代式文本自查 | 盲区的形状由**当轮采用的维度**决定 |
| [`ai-writing-debug`](https://github.com/crce-ux/ai-writing-debug) | AI 写作痕迹诊断与修复 | 口语节拍 ≠ 口语化 |
| [`literature-pipeline`](https://github.com/crce-ux/literature-pipeline) | 文献调研 | **覆盖声明 N→M→K** + 裸被引必须归一 |
| [`talk-readiness`](https://github.com/crce-ux/talk-readiness) | 汇报讲者侧 | 待核清零 + 磕巴判据 |
| [`peer-review`](https://github.com/crce-ux/peer-review) | 同行评议 | TRS / EEG / ML 三份领域专属清单 |
| [`study-design`](https://github.com/crce-ux/study-design) | 课题设计 | 没有证伪条件，就不是科学假设 |

🔌 **工具怎么接** → [`docs/runtime.md`](docs/runtime.md)：能力 → 候选工具对照，以及**为什么不在 skill 里写死工具 ID**。

---

## 目录

```
README.md                    本文件（管线地图 + 门禁 + 轴）
docs/
  pipeline.md                P→A→B→C→D→E 全流程逐步
  gates.md                   五门 + 六轴的完整判据
  skills.md                  6 个 skill 的索引与选择指南
  runtime.md                 运行环境与工具绑定（能力→工具；**不写工具 ID**）
  核查方法/                   来源核验 / 定量断言审计 / 对抗压力测试 / 演讲产物审查
scripts/
  literature/                检索、元数据核验、质量快筛、中文库取数
  evidence/                  证据表生成、日常文献表、一致性核查
  checks/                    语言 / 身份 / 引用 / 资产 / 隐藏元数据
  ppt/                       PPT 生成与质检工具链
manuals/                     49 份流程手册原文（已去敏化）
  workflow/                  各阶段流程手册
  checklists/                出稿清单（含「出稿检查总表」）
  templates/                 骨架与模板
  ppt/                       PPT 工具链
  writing/                   写作质量（含「文本迭代自查」）
  funding/                   基金与投稿
  notes/                     调研与评估记录
  data-sources/              取数手册
templates/
  ppt-skeletons/             整页 SVG 骨架（可直接复制填内容）
```

> 📖 **`docs/` 是骨架，`manuals/` 是细节层。**
> 前者讲「这套系统怎么运转」，后者讲「每一步具体怎么做、当时踩了什么坑」。

---

## 脚本速览

| 脚本 | 一句话 | 依赖 |
|---|---|---|
| `verify_pmid_doi.py` | PMID/DOI 反查核验——防手填错误 | 标准库 |
| `quality_screen.py` | **OpenAlex 归一化指标**快筛（FWCI / 被引百分位） | 标准库 |
| `check_metadata_leak.py` | Office/PDF **隐藏元数据**体检（盲审泄露面） | 标准库 |
| `check_language.py` | 回指 / 排他性断言 / 空泛量词 / 缩写 / 数字口径 | 标准库 |
| `check_persona.py` | 身份匹配机检（只报可疑，不下判决） | 标准库 |
| `build_evtab.py` | 12 列证据表生成（10 列 PICO + 2 列期刊指标） | openpyxl |
| `ppt_build.py` | 讲稿 → 分镜 → 渲染 → 导出 一条命令出片 | 见 `scripts/ppt/` |

---

## 三条设计原则

**1. 脚本只做能自动化的那一半。**
语义判断（这条证据支持这句话吗、这算不算越级）**必须人工过**。
每个脚本的 docstring 里都写清了它**不查什么**。

**2. 命中 ≠ 要改。**
`check_persona.py` 报「可能」不代表要删——
**写证据边界时「可能」是正确用法，写结论时才是逃避。** 脚本分不清，人分得清。

**3. 覆盖要说出来。**
凡是核查，报出 `可识别位置总数 N → 实际核查 M → 未能覆盖 K`。
**只报「已检查」而不报「没检查什么」，等于假装覆盖完整。**

---

## 测试与 CI

```bash
uv run --with pytest python -m pytest tests/ -q     # 43 个测试
```

| 覆盖什么 | 为什么测它 |
|---|---|
| `check_language` 的规则 | 排他性断言必须有出处——**可客观验证**，值得锁死 |
| `check_ref_citations` 的解析 | 编号解析错一位，双向核对就会大面积误报 |
| `check_skill_structure` 本身 | **校验器也必须被校验**，否则它是没人管的裁判 |

**不测什么**：启发式判据（如身份匹配）只测结构与选择器，不断言「某句话必须被抓」——
那会把启发式当成硬规则来维护。

CI 跑 Python 3.9 / 3.12 / 3.13 三个版本。每个配套 skill 仓库另有独立的结构校验 workflow。

> ⚠️ **一个诚实的空白**：同类项目里，真正的 LLM 行为评估（eval）**没有可抄的 CI 实现**。
> 本仓的立场是先把能自动化的锁死，行为评估留在本地人工做——**不假装它进了 CI**。

---

## 来源

这套系统来自作者的实际科研工作（精神医学 / 难治性精神分裂症 / 神经调控方向），
2026 年 8–10 月逐步建立。部分方法借鉴自开源项目，已在各处标注。

## 许可

MIT
