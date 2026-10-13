# 脚本索引

**26 个脚本，按阶段分组。** 多数只用标准库，可直接跑。

---

## literature/ · 检索与核验

| 脚本 | 一句话 | 依赖 |
|---|---|---|
| `verify_pmid_doi.py` | PMID/DOI 反查核验——**防手填错误** | 标准库 |
| `quality_screen.py` | **OpenAlex 归一化指标**快筛（FWCI / 被引百分位） | 标准库 |
| `pubmed_meta_fetch.py` | 批量拉元数据（PMID 优先用 esummary） | 标准库 |
| `cnlit_search.py` | 中文文献库（知网 / 万方 / 维普）取数 | DrissionPage |
| `fetch_abstracts_compare.py` | 摘要抓取与比对 | 标准库 |
| `journal_match.py` | 期刊匹配（投稿选刊） | 标准库 |
| `fetch_journal_metrics.py` | 期刊指标拉取 | 标准库 |

> ⚠️ `cnlit_search.py` 需本机重建 venv 与知网 cookie。

---

## evidence/ · 证据表

| 脚本 | 一句话 | 依赖 |
|---|---|---|
| `build_evtab.py` | 12 列证据表生成（10 PICO + 2 期刊指标） | openpyxl |
| `build_daily_ref.py` | 日常精读文献表 | openpyxl |
| `check_consistency.py` | 跨文档一致性（数字 / 篇数 / 编号） | 标准库 |

---

## checks/ · 门禁检查

| 脚本 | 查什么 | 性质 |
|---|---|---|
| `check_language.py` | 回指 / **排他性断言** / 空泛量词 / 缩写 / 数字口径 | ② 硬，其余启发式 |
| `check_persona.py` | 身份匹配（保守 / 越级 / 引据 / 回指 / 书面语 / 长句） | 全部启发式 |
| `check_ref_citations.py` | 正文 `[n]` ↔ 文末编号表 双向对应 | 硬 |
| `check_assets.py` | 死链 / 路径 / 索引覆盖 | 分档 |
| `check_metadata_leak.py` | **Office/PDF 隐藏元数据**（盲审泄露面） | 硬（对外场景） |
| `renumber_refs.py` | 参考文献重新编号 | — |

> ⚠️ **脚本只做能自动化的那一半。** 语义判断必须人工过。
> **命中 ≠ 要改**——写证据边界时「可能」是正确用法，写结论时才是逃避。

---

## ppt/ · PPT 工具链

| 脚本 | 一句话 |
|---|---|
| `ppt_init.py` | 新项目初始化 |
| `ppt_style.py` | **样式真相源**（改这里，全库统一） |
| `ppt_kit.py` | 组件库 |
| `make_svg_skeletons.py` | 生成 SVG 骨架 |
| `ppt_build.py` | **一条命令出片**（讲稿→分镜→渲染→导出） |
| `ppt_check.py` | 源体检（ERROR=0 才导出） |
| `render_svg.py` / `render_templates.py` | 渲染 |
| `render_and_qa_pptx.py` | 成品像素体检 |
| `make_notes.py` | 讲稿 → PPT 备注 |

> ⚠️ **做 PPT 之前先过讲者侧那关**——见 [`talk-readiness`](https://github.com/crce-ux/talk-readiness)。
> PPT 做得再好，讲的人没内化，一样会当场卡住。

---

## 通用约定

1. **脚本只做能自动化的那一半**——每个脚本的 docstring 里写清了它**不查什么**
2. **覆盖要说出来**——报 `N → M → K`
3. **静默失败比报错危险**——替换 / 改名 / 批量操作后要回读验证
