# 脚本索引

**脚本 59 个（Python 58 个 + `ppt/setup.sh` 1 个），按阶段分组。** 多数只用标准库，可直接跑。

> ⚠️ `literature/` 的 `journal_match.py` / `fetch_journal_metrics.py` 需要 `scripts/_journal_data/` 下三份 CSV
> （中科院分区 / JCR / 预警名单）——**授权数据，本仓不分发**，缺它会直接报出该放哪三份。

> 📌 **`scripts/` 是正本。**
> 其中一部分已随包分发到各 skill 的 `scripts/`（`ai-academic-writing` / `literature-pipeline` / `academic-slides` / `text-self-review` / `peer-review` / `study-design` / `data-pipeline` / `paper-reading` / `grant-diagnosis` / `submission`），
> 各 skill 里的副本是**运行版**。**改脚本改 `scripts/`，再同步过去**——不要只改副本，两边会岔。
>
> 🔴 同步跑 `python scripts/sync_skill_scripts.py --root D:/Github`：
>
> ```bash
> python scripts/sync_skill_scripts.py --root D:/Github           # 校验（默认，进退出码）
> python scripts/sync_skill_scripts.py --root D:/Github --write   # 把不一致的覆盖为正本
> ```
>
> 它**按内容反查**，不维护「谁装了谁」的登记表（登记表自己会漂）：
> 扫每个 skill 的 `scripts/`，拿文件名去正本索引里找，找得到就比对。
> 当前基线：**71 份运行版副本，0 不一致**。
>
> ⚠️ **一个正本都对不上的仓 = 不参与分发**（如第三方的 `video-talkcraft`），整仓跳过——
> 否则它自带的脚本会被逐条误报成「无正本」，掩盖真差异。
>
> ⚠️ `ppt/` 里的 `ppt_build.py` 依赖第三方的 `ppt-master`（**不在本仓**，Hugo He，MIT）。
> 先跑一次 `bash scripts/ppt/setup.sh` 把它拉到 `vendor/`（不进 git）。

---

## 根目录 · 仓库自身的维护工具

| 脚本 | 干什么 |
|---|---|
| `doctor.py` | **一条命令跑完五项体检**：结构 / 资产 / 副本①仓内 / 副本②观测库 / 单测。全绿，或指出哪条没过。`--full` 看原始输出 |
| `sync_skill_scripts.py` | **正本 → 各 skill 的分发校验 / 同步**（见上「📌 `scripts/` 是正本」）。`--root <含各 skill 的目录>`，默认只校验、`--write` 覆盖 |
| `deploy_to_vault.py` | **仓 → 观测库 `.claude/skills/` 的第三套副本同步**。默认只校验、`--write` 覆盖。**只增改不删**——库里多出来的由人判断 |
| `run_checks.py` | **跑一批检查器，把发现写进「待修清单」**。`--target <文件或目录> --ledger <清单.md>` |
| `audit.py` | **一条命令跑完一份稿件的检查**：识别文档类型 → 跑对应检查器 → 输出「位置 / 检查项 / 问题 / 依据」四列。`--json`、`--only`、`--strict` |
| `confirm.py` | **网页点选收集输入**：`--spec spec.json --out answers.json`。起本地服务、打印带 token 的地址，用户提交后写成 JSON。只绑 `127.0.0.1`；超时退出码 2 |

> ⚠️ `deploy_to_vault.py` 面对的是**第三套副本**：`sync_skill_scripts.py` 管仓内各 skill 的
> `scripts/`，`deploy_to_vault.py` 管**被 agent 加载的目录**。此前它们靠手敲同步。
> ⚠️ `.gitignore` 不参与比对——它是**仓的元数据**，不是 skill 内容。

> ⚠️ 各 skill 的检查器此前一直在复制：`check_skill_structure.py` 一度有 **13 份**副本，全靠手工重灌。
> 复制了就得有机制保证一致。

> ⚠️ `run_checks.py` **试跑每一个检查器**（收不了单一路径参数的自动跳过），**不维护登记表**。
> 它**不把发现拆成「文件 / 说明」两列**——各检查器格式不同，硬拆会解析错（`check_metadata_leak`
> 的格式就与多数不同）。**整行原文照存**。
> **AUTO 区按目标分段**：跑目标 B 不会冲掉目标 A 的发现。

---

## literature/ · 检索与核验

| 脚本 | 一句话 | 依赖 |
|---|---|---|
| `verify_pmid_doi.py` | PMID/DOI 反查核验——**防手填错误** | 标准库 |
| `quality_screen.py` | **OpenAlex 归一化指标**快筛（FWCI / 被引百分位） | 标准库 |
| `pubmed_meta_fetch.py` | 批量拉元数据（PMID 优先用 esummary） | 标准库 |
| `dedupe_refs.py` | **文献列表去重**（DOI → PMID → 归一化标题）；标题太短宁可不合 | 标准库 |
| `cnlit_search.py` | 中文文献库（知网 / 万方 / 维普）取数 → 分发到 `literature-pipeline` | DrissionPage |
| `fetch_abstracts_compare.py` | 摘要抓取与比对 | 标准库 |
| `journal_match.py` | **期刊匹配（投稿选刊）** → 分发到 `submission` | 标准库 |
| `fetch_journal_metrics.py` | 期刊指标拉取 → 分发到 `submission` + `literature-pipeline`（**两处部署**） | 标准库 |

> ⚠️ `cnlit_search.py` 需本机重建 venv 与知网 cookie。
> ⚠️ `journal_match.py` / `fetch_journal_metrics.py` 需 `_journal_data/` 三份 CSV（授权数据，不分发）。

---

## data/ · 数据管线

| 脚本 | 一句话 | 依赖 |
|---|---|---|
| `missing_report.py` | **逐变量逐时点缺失率**，按四类缺失码拆开；每列给**粗缺失率**与**真缺失率**（后者摘除「不适用」）。**报告工具，退出码恒为 0** | 标准库 |

> 🔴 `missing_report.py` 只摆两个率，不替你选——用粗的还是真的，看 SAP 怎么写。
> ⚠️ 「不适用」不是缺失：逻辑上不存在的取值（男性问月经、未服药问副作用）算进缺失率会虚高，
> 还会让插补用错人。

---

## design/ · 研究设计

| 脚本 | 一句话 | 依赖 |
|---|---|---|
| `sample_flow.py` | **样本量 → 需招募 → 可招募**，三段数字摆出来。按脱落率给乐观/预期/保守三套，按分组比拆每组；可招募数不够时退出码 1 | 标准库 |

> ⭐ 只做「**拿到主分析样本量之后**」的换算——**样本量本身怎么来**（效应量、效能、检验方法）不在本脚本。
> ⚠️ D4 的可行性判据是「可招募数 ≥ 样本量需求」，缺哪一半都不算算过。

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
| `check_phrases.py` | 措辞九组：自我削弱 / 套话 / 抽象标签 / 演义媒体化 / 自问自答 / 伪对立 / 名词化 / 越级引用 / 连接词堆砌 | 启发式，按文体门控 |
| `check_persona.py` | 身份匹配（保守 / 越级 / 引据 / 回指 / 书面语 / 长句） | 全部启发式 |
| `check_talk.py` | 讲者侧硬规则：待核清零 / 洗白词 / 每页 200–500 字 / 加粗 ≤3 / 总字数↔时长 / 制作稿七项 / 讲稿六样 | **可判定** |
| `check_lit.py` | 证据表 12 列 / 对照列 NA / 同作者同年 a-b / IF 与分区须带年份版本 / 分区标题；覆盖声明 N→M→K 齐且相加对 | 硬；E6 为软 |
| `check_vault.py` | **科研库命名与结构**：精读笔记 / 终稿不带日期 / ADR 命名 · 工作日志字段+倒序 · AI 声明 · 理解确认清单 | 硬；按**文件名**触发 |
| `check_review.py` | **审稿意见结构**：四档审稿建议 / 摘要段 / 编号 3–8 条 / 每条带位置与要求 / 不端指控不得给作者看 / 密评须标「不向作者展示」 | 硬；草稿·密评·非审稿意见自动跳过并报因 |
| `manuscript_triage.py` | **审稿前的报告条目体检**：按设计类型（RCT / 观察性 / 诊断 / 预测）核对核心报告条目在不在。只查「有没有写」，不查「写得对不对」 | 读稿工具，退出码恒为 0 |
| `negation_diff.py` | **改写前后的否定比对**——抽否定短语求差集；「原文有、改写后没有」单列。数字变了看得见，**否定丢了几乎看不见** | 辅助，不是判据 |
| `number_diff.py` | **跨版本数字比对**（维度 D15）：两版文本（中英 / md↔docx / 初稿↔终稿）的数字集合求差集，连上下文一起列 | 辅助，不是判据 |
| `check_token_diff.py` | **改写前后的受保护 token 比对**（LaTeX / 引用 key / 数字与单位 / 状态 token / 路径 URL）——丢失的必须逐个解释 | 硬 |
| `check_data.py` | **数据管线口径（E1–E4）**：变量字典七列 + **缺失码四类** / SAP 偏离七列 + **偏离行原因与批准人不得为空** / 结果报告 p 与 95%CI | 硬；按**文件名**触发 |
| `check_note.py` | **精读笔记口径**：必备信息 / 标注使用 / **定位方式与引用形式一致**（标了「仅摘要」却引用 Table = 在编） | 硬；N4 为软 |
| `ledger_to_cv.py` | **成果台账 → NSFC 简历用成果清单**：按表头认表、近 N 年筛（年份缺失单列待补）、论文只导已发表/已接收、按署名优先级排序 | 硬（只读不判） |
| `check_credit.py` | **成果台账署名自洽**：署名情况 ↔ 位次（如「共同第一作者」却写位次 3）/ 六种署名枚举 / **三数字齐** / 状态四态 | 硬；全占位行时报「本次未评」 |
| `check_review_article.py` | **综述自称与配置自洽**：标题（或摘要**自我描述**）自称「系统综述 / 荟萃分析 / 范围综述」→ 必须有方法学要素；未定项计数 | 硬 R1 + 软 R2；**不扫摘要里的「荟萃分析」**（此处多指引用别人，实测 20 篇误报 3 篇） |
| `check_design.py` | **研究设计书结构**：假设节证伪条件 / 乐观·保守两套 / 脱落率 / 风险四列表 / 伦理与预注册 | 硬；缺节时报「本次未评」 |
| `check_ref_citations.py` | 正文 `[n]` ↔ 文末编号表 双向对应 | 硬 |
| `check_grant_rules.py` | **指导类文档里有没有写死年度性数值**（篇幅/年龄/申请代码/经费/资助期限）；只在文件名含 指南/规则/清单/申报/SKILL 的文档上触发 | 硬；非指导类自动跳过并报因 |
| `convergence_log.py` | **自查轮次记录 → 能否判收敛**（C1a/C1b/C2/C3）；回流>0 的轮作废、自动摘出序列；满 6 轮报止损 | 硬（只读不判） |
| `check_assets.py` | 死链 / 路径 / 索引覆盖 | 分档 |
| `check_metadata_leak.py` | **Office/PDF 隐藏元数据**（盲审泄露面） | 硬（对外场景） |
| `check_skill_structure.py` | **Agent Skill 结构校验**（frontmatter / name / 正文长度 / 深链） | 硬（静态） |
| `skill_selfcheck.py` | **skill 自检入口**（分发到各 skill 时改名为 selfcheck.py）：结构 + 语法 + 依赖 | 硬（静态） |
| `renumber_refs.py` | 参考文献重新编号 | — |

### `check_skill_structure.py` —— 唯一可完全 CI 化的层

按[官方 Agent Skills 规范](https://agentskills.io/specification)做**静态校验**：零依赖、不调模型、只读。

```bash
python scripts/checks/check_skill_structure.py --root <含多个 skill 的目录>
python scripts/checks/check_skill_structure.py <单个skill目录> --strict
```

查：`name` 的格式/长度/与目录一致/不含保留词 · `description` 长度 ·
frontmatter 白名单字段 · 正文 < 500 行 · 引用只走一层 · 是否有可判定的 `Anti-Patterns`。

> `check_skill_structure.py` 是同类项目里唯一被多个仓库验证过、能完全进 CI 的一层。
> 真正的 LLM 行为评估（eval）目前没有可抄的 CI 实现——见下文。

> ⚠️ **脚本只做可自动化的部分。** 语义判断必须人工过。
> **命中不等于要改**——证据边界里「可能」是正确用法，结论里用它则是回避。

---

## ppt/ · PPT 工具链

| 脚本 | 一句话 |
|---|---|
| `ppt_init.py` | 新项目初始化 |
| `ppt_style.py` | **样式真相源**（改本文件，全库统一） |
| `ppt_kit.py` | 组件库 |
| `ppt_build.py` | **一条命令出片**（讲稿→分镜→渲染→导出） |
| `ppt_check.py` | 源体检（ERROR=0 才导出） |
| `render_svg.py` / `render_templates.py` | 渲染 |
| `render_and_qa_pptx.py` | 成品像素体检 |
| `make_notes.py` | 讲稿 → PPT 备注 |
| `slide_fit.py` | **画之前的版面算术**：容量、带高预算、**配图可读性**（图内字号 × 显示宽 ÷ 图宽 < 9px 即不可读） |
| `pptx_shapes.py` | **pptx 形状级读取**：zipfile + ElementTree 直读 OOXML；组变换、主题色、占位符帧继承。独立工具，当前无自动调用方 |

> ⚠️ **做 PPT 走全链路**——见 [`academic-slides`](https://github.com/crce-ux/academic-slides)。

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
# 只装需要的一组
pip install openpyxl            # 证据表
pip install DrissionPage        # 中文库取数
pip install Pillow PyMuPDF      # PPT 质检 / 元数据体检
```

### ⚠️ 外部依赖：`ppt_build.py` 需要一个不在本仓的工具

`ppt_build.py` 的最后一步（SVG → PPTX 合并）调用 **`ppt-master` 的 `svg_to_pptx.py`**——
不可替代的合并层，本仓不包含。

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

1. **脚本只做可自动化的部分**——每个脚本的 docstring 里写清了它**不查什么**
2. **覆盖要说出来**——报 `N → M → K`
3. **静默失败比报错危险**——替换 / 改名 / 批量操作后要回读验证
4. **同目录 import 自带 path bootstrap**——`ppt/` 下的脚本互相引用时，靠 `sys.path.insert(0, HERE)`，不依赖调用方式

---

## 测试

```bash
uv run --with pytest python -m pytest tests/ -q
```

**有一条测试要额外装库才跑**——`test_pptx_shapes.py` 与 `python-pptx` 的交叉验证：

```bash
uv run --with pytest --with python-pptx python -m pytest tests/test_pptx_shapes.py -q
```

`python-pptx` 是另一份对同一套 OOXML 的读取实现。两边逐形状比几何与文字，对得上才说明
`pptx_shapes.py` 读对了。**只在测试里用，不进运行时依赖**——常规那一轮会把它 skip 掉。

测试覆盖**可客观验证的判据**（排他性断言必须有出处、编号解析的边界、结构校验规则）。
启发式的判据（如身份匹配）**只测结构与选择器**——最后一关由人判断。

**测试本身也有要求**：校验器要能被校验。`test_check_skill_structure.py` 用临时目录
造出合规与不合规的 skill，断言规则确实生效。

### 一个已知的空白

同类项目里，**真正的 LLM 行为评估（eval）没有可抄的 CI 实现**——
见到的都是结构校验、脚本单测、安全扫描。行为评估目前只能本地跑。

本仓的立场：**先把能自动化的锁死（结构 + 单测），行为评估留在本地人工做**，
不假装它进了 CI。
