# skill 全景与工序编排

> 回答两个问题：**这一步该用谁**；**什么时候去找外部 skill**。
> 手册去向见 [`manuals.md`](manuals.md)；流程本身见 [`pipeline.md`](pipeline.md)。

---

## 一、装在哪

| 位置 | 数量 | 说明 |
|---|---:|---|
| Cherry 全局池 `Data/Skills/` | 72 | 含 **ppt-master** |
| 本 agent `.claude/skills/` | 20 | 生活/写作类 + `ppt-master-entry` |
| 私人库 `.claude/skills/` | 12 | **全部也在全局池**（重复，未删） |
| 科研库 `.claude/skills/` | 13 | 10 个自研 + 3 个通用 |
| 科研助手 `.claude/skills/` | 32 | 全套 nature-* + ppt-master |

**去重后约 100 个。** 私人库 12 个与全局池完全重复，留着不影响，但别当成两套。

---

## 二、分类

### 核心自研（10 个，本仓维护）

`paper-reading` · `literature-pipeline` · `ai-academic-writing` · `academic-slides` ·
`data-pipeline` · `submission` · `grant-diagnosis` · `peer-review` · `text-self-review` · `study-design`

### 外部可用（已装，不复制）

`nature-*`（科研助手，32 个）· `ppt-master` · `deep-research` · `humanizer` · `llm-writing` ·
`office-transform` · `defuddle` · `obsidian-cli` · `obsidian-markdown` · `find-skills` · `skill-creator`

### 重复

私人库 12 个全部也在全局池：`book-manager` `career-coach` `chen-reflection` `citation-reviewer`
`evening-review` `find-skills` `literature-review` `med-kb-organizer` `morning-briefing`
`python-coach` `skill-creator` `weekly-summary`

### 失效 / 待修

| 项 | 问题 |
|---|---|
| `citation-reviewer` | 脚本路径指向旧机器（`C:/Users/陈晨/...`） |

---

## 三、工序表

| 工序 | 首选（自研） | 备选（已装） | 在哪 | 交接物 |
|---|---|---|---|---|
| 日常精读 | `paper-reading` | `nature-reader`、`nature-paper-card` | 本 agent / 科研助手 | 精读笔记（15 列） |
| 检索取数 | `literature-pipeline` | `nature-academic-search`、`deep-research` | 本 agent / 科研助手 | 证据表（12 列） |
| 成文 | `ai-academic-writing` | `nature-writing`、`llm-writing`、`humanizer` | 本 agent / 科研助手 | 内容稿 |
| 出片 | **`ppt-master`** | `nature-paper2ppt` | 本 agent（入口） | pptx |
| 讲稿 | `academic-slides` | — | 科研库 | 讲稿 · 制作稿 |
| 课题设计 | `study-design` | `scientific-brainstorming` | 科研库 / 科研助手 | 设计书 |
| 执行产出 | `data-pipeline`、`submission` | `nature-statistics`、`nature-figure`、`nature-data` | 本 agent / 科研助手 | 数据 · 台账 |
| 审稿 | `peer-review` | `nature-reviewer`、`academic-paper-reviewer` | 科研库 / 科研助手 | 审稿意见 |
| 横向自查 | `text-self-review` | `ai-check` | 科研库 | 自查报告 |
| 标书 | `grant-diagnosis` | `nature-proposal-writer` | 科研库 / 科研助手 | 诊断报告 |

**交接物是硬的**：精读笔记 → 证据表 → 内容稿 → 终稿 → 制作稿。上一段没交出去，下一段不开始。

### 支线（不在主链上）

| skill | 干什么 |
|---|---|
| `session-handoff` | 会话过长或交付完成后留续接摘要 |
| `obsidian-cli` / `obsidian-markdown` | 读写库、查属性与任务 |
| `book-manager` | 书单 |
| `chen-reflection` | 自我探索对话 |
| `career-coach` / `python-coach` | 职业与技能推进 |
| `writing-principles` / `story-review` / `style-analyzer` / `writing-anti-ai` / `llm-writing` | 写作侧 |
| `office-transform` | 局部抽离或改写 Office 文件 |
| `find-skills` / `skill-creator` | 找 skill / 造 skill |

---

## 四、什么时候去找外部 skill

三条判据，缺一条就不装。

1. **触发**：某工序自研无覆盖，且近 30 天真实出现 ≥2 次。
   一个月用不到两次的需求，不值得装。
2. **先查已装**：100 个条目里搜一遍。多数需求已经被覆盖——PPT 早就装好了，只是没入口。
3. **验收**：许可证可分发、能离线跑、不要新的明文密钥。
   缺一条 → 挂指针，不装。

装之前先看 [`external-skills.md`](external-skills.md) 的许可列。

> ⚠️ 「有外部 skill」不等于「缺口填上了」。外部 skill 不背本库的纪律（覆盖声明、三态标签、保真界限）。
> 自研 skill 管口径，外部 skill 管能力。

---

## 五、ppt-master 的入口

`ppt-master` 装在全局池，但不在本 agent 的可调用列表里。已补 `ppt-master-entry`，只给路径与四步流程，不复制 ppt-master 的规则。

| 位置 | 作用 |
|---|---|
| `research-workflow/skills/ppt-master-entry/` | **源**，随仓版本化 |
| 科研库 `.claude/skills/ppt-master-entry/` | 副本，`deploy_to_vault.py` 同步 |
| 本 agent `.claude/skills/ppt-master-entry/` | 运行时副本，新开会话后可见 |

**PPT 一律走 ppt-master**，不自建模板、不用自建骨架与配方。
