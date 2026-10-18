# 运行环境与工具绑定

**本文回答一个问题：流程走到某一步，该找哪个工具。**

---

## 🔴 先讲一条：本文件不写工具 ID

MCP 工具的完整名是 `mcp__<服务器ID>__<工具名>`。**服务器 ID 由客户端生成，重装或换机就变**
——同一台服务器，换机器前可能叫 `MAcOg5uCwF7W8c0l_ymBz` 这样的可读串，换机器后成了一串 UUID。

| ❌ 不要 | ✅ 要 |
|---|---|
| 把 `mcp__a1b2c3…__search_pubmed` 写进 skill、文档或脚本 | 只写**能力** + **服务器显示名**（"simple-pubmed 的 PubMed 检索"） |

写死 ID 的代价：**换机后失效，别人拿到也失效。** 运行时按名字自动解析，**用的人不需要知道 ID**。

---

## 能力 → 候选工具

| 能力 | 候选（按显示名） | 说明 |
|---|---|---|
| 多源学术检索 | `academic-search`（`search_papers` / `search_by_doi`） | 跨库；`get_citations` 可做他引判定 |
| PubMed 检索与全文 | `simple-pubmed`（`search_pubmed` / `get_paper_fulltext`） | 复杂布尔查询易超时 → 先简后繁，或 `[Title]` 限定 |
| Google 补充（中文 / 预印本） | `google-search` | 实测常比内置联网搜索稳，中文查询尤甚 |
| Zotero **写**（建/改条目、进合集、打标签） | `zotero-manager` | 乐观锁，**禁止并行写** |
| Zotero **读**（查库、读 note / PDF 正文） | `zoteroMCP` | 只读，不会误写 |
| 读图（独立第二意见） | `vision-bridge` | 主模型原生视觉够用时不必调 |

> ⚠️ **两台 Zotero 最容易拿错**：**写找 `zotero-manager`，读找 `zoteroMCP`**。
> 二者并存且工具名不同，混用会一次误写或一次多余往返。

---

## 两条路：脚本 vs MCP

同一件事常常两条路都能走。**默认走脚本**：

| | 仓库自带脚本 `scripts/` | MCP |
|---|---|---|
| 连接方式 | `urllib` 直连 E-utilities / Crossref / OpenAlex | 客户端中间层 |
| 可复现 | ✅ 命令行可重跑、结果可存档 | ❌ 会话内，不易复现 |
| 可进 CI | ✅ | ❌ |
| 适合 | **流程里要留痕的确定性步骤** | **探索性检索、Zotero 读写** |

**重叠时优先脚本。** 例：取 PubMed 元数据——`scripts/literature/pubmed_meta_fetch.py`
一次给全卷/期/页/DOI，且结果可直接进证据表与检查表；逐条走 MCP 调用则不易留痕、无法复现。

脚本各自的依赖见 [`scripts/README.md`](../scripts/README.md)。

---

## skill 为什么保持工具无关

**11 个**配套 skill 是可独立安装的件（10 个方法 skill 为 MIT 开源）。它们的正文只写方法与能力，
**不绑定任何具体 MCP**——所以换机器、换客户端、换人来用，都还成立。

本机实际挂了哪些服务器、各叫什么名、什么 ID，属于**环境事实**，
记在使用者自己的记忆 / 配置层，**不进 skill**，所以本文件只出现"显示名"。
