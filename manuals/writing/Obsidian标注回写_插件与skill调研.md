# Obsidian 标注 → Agent 回写：插件与 Skill 调研

> 需求（用户 2026-10-12）：在 Obsidian 库的 markdown 文件里对需要修改的地方做标注，
> agent 同步识别标注并执行修改。
> 检索：GitHub 仓库搜索 8 组查询，核录 README + SKILL.md 原文。

---

## 〇、先定判据（决定了 80% 的结论）

**不是所有"标注"agent 都读得到。** 按存储位置分三类：

| 存储位置 | agent 读 .md 时可见？ | 代表 |
|---|---|---|
| **① 正文内联标记** | ✅ 直接可见，零解析成本 | CriticMarkup |
| **② 文件内独立数据块**（末尾 fenced block / JSON） | ✅ 可见，需按格式解析 | Tandem Comments |
| **③ 插件数据库 / 独立 sidecar 文件** | ❌ 读原文什么都看不到 | side-note、annotation-marker |

> **判据一句话：标注必须落在文件里，不能只落在插件的库里。**
> 很多"批注插件"看着功能齐全，但正文一个字符都不改——对 agent 是**黑箱**。
> 选型时**先看它把数据存哪儿**，再看功能表。

---

## 一、方案 A：CriticMarkup（首选）

### 语法（行业标准，非某插件私有）

| 写法 | 含义 |
|---|---|
| `{++新增文字++}` | 建议增加 |
| `{--删除文字--}` | 建议删除 |
| `{~~原文~>改后~~}` | 建议替换 |
| `{==高亮的原文==}` | 高亮（只指示，不提改法） |
| `{>>这里是批注<<}` | 批注/意见 |

带署名与日期的扩展前缀（可选，写在 `{` 与标记符之间）：

```
{author="Chen" date="2026-10-12"~~旧~>新~~}
{author="Chen">>这段要改，见组会意见<<}
```

约束：值必须**双引号**包裹、键**小写**、`{` 后**无空格**、值内**不得含 `"` `{` `}` 或换行**。

### 首选理由

- **纯文本**：就是文件正文，`Read` 直接看到，无需 MCP、无需 API
- **双向**：人写给人看，agent 也写给人看，同一套语法
- **可 diff**：进 git 就是普通文本变更
- **有既有实现兜底**：Obsidian 渲染/审阅、Pandoc `--track-changes` 都能处理

### 插件

| 插件 | ★ | 角色 | 备注 |
|---|---|---|---|
| **philphilphil/obsidian-track-changes** | 14 | **审阅面板（主力）** | 社区商店搜 "Track Changes" 直接装。侧栏逐条 accept/reject/reply、多作者配色、**支持人工留标**（右键菜单 / 命令面板）、*Finalize for publish* 一次清空。**⚠️ 核心：内置 [`docs/SKILL.md`](https://github.com/philphilphil/obsidian-track-changes/blob/main/docs/SKILL.md) 可直接交给 agent** |
| Fevol/obsidian-criticmarkup | 260 | **渲染器（star 最高）** | 支持建议模式 / 批注模式 / 库级索引。**⚠️ README 自述仍是 beta，明确写「不要在主力库使用」，有丢文本的非零风险** |
| ShotaShirai1719/obsidian-review-comments | 5 | Notion 式批注，存为 CriticMarkup | 2026-09 新 |
| gcailly/obsidian-side-comments | 0 | 把 CriticMarkup 批注显示到侧栏 | 轻量 |
| EliasSchlie/obsidian-criticmarkup | 0 | 内联渲染 + accept/reject 按钮 | 轻量 |

> ⚠️ **方向陷阱**：track-changes 自带的 SKILL.md 是**评审向**——它的硬规则写着
> "**Never rewrite, rephrase, or generate text**"，agent 只加标注、绝不改原文。
> **track-changes 的评审向规则与我们的需求正好相反**（我们要 agent 读标注→执行修改）。
> 可以拿它的**语法规范**用，但**规则要反过来写**，见 §四。

---

## 二、方案 B：Tandem Comments（正文零污染）

`leonpawelzik/obsidian-tandem-comments`（34★，2026-09-29，社区商店可装）

- 批注存**文件末尾一个 fenced code block**，内容是**纯 JSON**；正文一个字符都不动
- 引用锚定（quote-anchored），非内联位置标记
- README 原话：**"AI assistants can read, write, and act on them with nothing but file access"**
- 设置页**可导出 skill 文件**，直接教 Claude Code 该格式

**取舍**：正文干净、JSON 好解析；代价是锚点靠引文而非位置，且需要额外的解析层。
适合"批注量大、不想污染正文"的场景；对"就地改一句话"这类需求不如 CriticMarkup 直接。

---

## 三、❌ 明确排除的两个（看似可用，实际对 agent 是黑箱）

| 插件 | ★ | 为什么排除 |
|---|---|---|
| `uuq007/obsidian-annotation-marker` | 62 | 自述存储方式为「**标注数据存储在独立的标注文件中，不修改原始 Markdown 文件**」→ **原文里什么都没有** |
| `mofukuru/side-note` | 30 | 位置以 **CodeMirror 绝对字符偏移**存储，走 `ChangeSet.mapPos()` 实时映射 → 数据在插件侧，文件里读不到 |

> annotation-marker 与 side-note 这两个功能都不弱（side-note 锚点跟随编辑做得很好），**但它们是为"人在 Obsidian 里看"设计的，不是为"agent 读文件"设计的**。
> 若要勉强打通，得让 agent 去解析 sidecar 文件或插件 data.json——**不值得**，除非有别的理由必须用它们。

---

## 四、Agent 侧：已具备的能力

**关键认识**：本会话工作目录就是库根 `D:\Obsidian\2026\5\`。
`Read` / `Edit` / `Write` **直接作用于库内 .md 文件**——**不需要 MCP，不需要 Local REST API**。

已装技能：`obsidian-cli`、`obsidian-markdown`（后者正是 CriticMarkup 类语法的编辑规范）。

**缺的只有一份「应用向」规则文件**。它与现成的评审向 SKILL.md 的差别：

| | 评审向（track-changes 自带） | **应用向（我们要的）** |
|---|---|---|
| 谁写标注 | agent | **人（作者）** |
| 谁执行 | 人 | **agent** |
| agent 的动作 | 只加标记，**绝不改原文** | **按标记改原文，然后清掉标记** |
| 产出 | 带标注的文件 | 干净的改后文件 + 变更说明 |

应用向 skill 该管的四件事：

1. **解析**：识别五种标记（含 `author=` / `date=` 前缀）
2. **执行**：`++` 插入 · `--` 删除 · `~~a~>b~~` 替换 · `==` 仅定位（找就近的 `>>` 取意图）
3. **清理**：改完**移除全部标记外壳**，正文不留 `{++` 之类的残渣
4. **留痕**：逐条列出「原文 → 改后 → 依据哪条标注」，**改了什么必须能对上**（与项目既有「有意删除要留一行说明」一致）

**边界**（与 Agent 系统提示词一致）：
- 标注含义不明 → **不猜**，保留标记并列入「待人工确认」
- 标注要求与证据冲突（如要求删掉真实局限）→ **不执行**，提请复核
- 涉及批量删除/合并 → **先确认**

### 备选：真要装 MCP 才走的通道

若日后要脱离本工作目录、或在手机端操作，可考虑：
`MarkusPfundstein/mcp-obsidian`（4471★，配 `coddingtonbear/obsidian-local-rest-api` 3019★）·
`bitbonsai/mcpvault`（1684★）· `jacksteamdev/obsidian-mcp-tools`（829★，含语义检索）。
**当前场景不需要**——直读文件更简单、更快、更可控。

---

## 五、建议

**装 `obsidian-track-changes`（商店可搜 "Track Changes"）+ 写一份应用向 skill。**

理由：CriticMarkup 是纯文本、双向、可 diff，与「结果落盘、变更可追溯」的项目习惯天然一致；
而 track-changes 提供了**人工留标的顺手的 UI**（右键菜单直接标）和**审阅面板**，
避免手工敲 `{~~旧~>新~~}`。

**不要**用 Fevol 的渲染器做主渲染——README 自己承认 beta 且有丢文本风险。

> ⚠️ 待办：应用向 skill 尚未编写。需要时按 §四 的四项职责 + 三条边界产出。

---

## 更新日志

- **2026-10-12** 建立。GitHub 检索 8 组查询（criticmarkup / comments plugin / annotation markdown /
  obsidian mcp / ai edit notes / track changes / criticmarkup skill / review-gated edits），
  核录 README 与 SKILL.md 原文，未做改写。存储位置判据为主线。
