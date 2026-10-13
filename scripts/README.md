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

## 依赖

**大部分脚本只用标准库。** 需要额外依赖的都写在下面。

| 依赖 | 用于 | 类型 |
|---|---|---|
| `openpyxl` | `build_evtab.py` · `build_daily_ref.py` | pip |
| `DrissionPage` | `cnlit_search.py`（浏览器自动化） | pip |
| `Pillow` | `ppt_check.py` · `render_and_qa_pptx.py` · `render_templates.py` | pip |
| `PyMuPDF`（`fitz`） | `check_metadata_leak.py` 读 PDF | pip |
| `pywin32`（`win32com`） | `render_and_qa_pptx.py` —— **需 Windows + 已安装 PowerPoint** | pip |

```bash
# 只装你要用的那一组
pip install openpyxl            # 证据表
pip install DrissionPage        # 中文库取数
pip install Pillow PyMuPDF      # PPT 质检 / 元数据体检
```

### ⚠️ 外部依赖：`ppt_build.py` 需要一个不在本仓的工具

`ppt_build.py` 的最后一步（SVG → PPTX 合并）调用 **`ppt-master` 的 `svg_to_pptx.py`**——
那是**不可替代的合并层**，本仓不包含。

它按以下顺序查找：

1. 环境变量 `PPT_MASTER`（指向 `svg_to_pptx.py`）
2. 两个已知的技能目录

**找不到会明确报错并给出可操作提示**，不会静默失败。

> 只跑 `--only check` 或 `--only svg` 不需要它。

### 需要网络的脚本

`cnlit_search` · `fetch_abstracts_compare` · `pubmed_meta_fetch` · `quality_screen` · `verify_pmid_doi`

其余脚本**完全离线**。`check_metadata_leak` 尤其适合离线环境——它处理的是本地文件。

---

## 通用约定

1. **脚本只做能自动化的那一半**——每个脚本的 docstring 里写清了它**不查什么**
2. **覆盖要说出来**——报 `N → M → K`
3. **静默失败比报错危险**——替换 / 改名 / 批量操作后要回读验证
4. **同目录 import 自带 path bootstrap**——`ppt/` 下的脚本互相引用时，靠 `sys.path.insert(0, HERE)`，不依赖调用方式

---

## 测试

```bash
uv run --with pytest python -m pytest tests/ -q
```

测试覆盖**可客观验证的判据**（排他性断言必须有出处、编号解析的边界）。
启发式的判据（如身份匹配）**只测结构与选择器**——它们的最后一关永远是人。
