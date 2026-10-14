# scripts/

**本目录是运行版。正本在 [`research-workflow`](https://github.com/crce-ux/research-workflow) 的 `scripts/`**——开发与测试都在总仓。

改脚本请改总仓，再同步过来；**不要只改本目录**。

| 脚本 | 干什么 | 服务于 |
|---|---|---|
| `pubmed_meta_fetch.py` | 按 PMID 批量拉卷 / 期 / 页 / DOI（走 esummary） | G0 元数据完整 |
| `verify_pmid_doi.py` | PMID / DOI 反查，确认文献真实存在 | G0 存在性 |
| `fetch_abstracts_compare.py` | 批量拉摘要，与证据表「关键结果」列逐篇比对 | Step 2 |
| `quality_screen.py` | OpenAlex 归一化指标快筛（FWCI / 被引百分位） | 规则 2 |
| `fetch_journal_metrics.py` | 期刊 IF / 分区（含年份口径） | 证据表列口径 |
| `cnlit_search.py` | 中文库取数（维普 / 知网） | Step 0 |
| `dedupe_refs.py` | **文献列表去重**：DOI → PMID → 归一化标题；标题太短宁可不合 | Step 0 → 覆盖声明 |
| `build_evtab.py` | 12 列证据表生成 | Step 1 |
| `build_daily_ref.py` | 日常文献表生成 | Step 0 |
| `check_consistency.py` | 证据表 ↔ 讲解 ↔ 综述 ↔ PPT 一致性核对 | 单一数据源 |
| `check_lit.py` | 证据表列级口径 + 覆盖声明 N→M→K（见下） | **A 类规则** |

### `check_lit.py` 用法

```bash
python check_lit.py --evtab 证据表_思路A.md     # 12 列 / 对照 NA / a-b / IF 与分区带年份 / 分区标题
python check_lit.py --coverage 调研报告.md     # 覆盖声明 N→M→K 齐、且相加对
```

**硬失败会进退出码；E6（关键结果里有没有数字）是软提示，不进**——机制类文献本来就可能没有效应量。

## 依赖

| 脚本 | 依赖 |
|---|---|
| 多数 | 标准库 |
| `build_evtab.py` | `openpyxl` |
| `cnlit_search.py` | 浏览器（**不要用无头**，会触发额外验证） |
| `quality_screen.py` / `fetch_journal_metrics.py` | 联网 |
| `check_skill_structure.py` | 结构校验（官方 Agent Skills 规范）：name / description / 正文长度 / 深链 / **声明落地** |
| `selfcheck.py` | **一条命令自检**：结构 + 语法 + 依赖。见下 |

## 边界

**脚本只做可自动化的部分。**

- 脚本能核「这条引文存在吗」「这两个数一致吗」
- **核不了「这条证据真的支持这句话吗」**——必须人工过

## 自检

```bash
python scripts/selfcheck.py            # 结构 + 语法 + 依赖
python scripts/selfcheck.py --strict   # 结构警告也算失败（CI 用这个）
```

查三样：**结构**（官方规范）· **语法**（逐个编译 `scripts/*.py`）· **依赖**（哪些脚本要装第三方库，只报不判）。
下载本 skill 后想确认「东西是齐的、没坏的」，跑 `selfcheck.py` 就够。
