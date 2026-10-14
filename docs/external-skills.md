# 外部同类项目 · 许可与运行足迹

> **用途一句话：调用 > 复制；**真要复制，先看许可列。
>
> 本库对 **外部** skill 的一贯主张是「调用 > 复制」——
> 它们的许可、维护、依赖都不是我们的。本清单只做两件事：
> **① 记许可与运行足迹；② 记我们能从中借鉴什么。**
>
> ⚠️ **许可信息来自第三方索引**（`O0000-code/awesome-academic-skills`，CC0 · ★见其仓库），
> **复制或分发前请自行核对上游 `LICENSE`**——索引也会过期。

## 图例

| 标记 | 意思 |
|---|---|
| `net` | 需要联网（API / 抓取） |
| `hooks` | 会安装钩子 / 需要放宽权限 |
| 无标记 | 纯文本，读文件与写文件 |

| 许可 | 能不能复制进本仓 |
|---|---|
| MIT / Apache-2.0 | ✅ 可以（**仍须署名**） |
| CC BY-NC | ⚠️ **非商业**——本库发布在公开仓，按不相容处理 |
| GPL-3.0 | ⚠️ 传染性——**只取方法，不取代码** |
| 无 license / NOASSERTION | 🔴 **不能复制**。只读方法，自己重写 |

---

## 一、文献检索与取数

| 项目 | 许可 | 足迹 | 一句话 |
|---|---|---|---|
| `dsebastien/ai-skill-scholar` | MIT | | 三个可组合的 OpenAlex skill（venue 检索 / 引文图遍历 / 综述编排）——**纯标准库、无 key** |
| `cookjohn/cnki-skills` | 🔴 无 | `net` | 走 Chrome DevTools MCP 驱动知网：检索 / 浏览 / 引文分析 / 下载 / 导出 |
| `cookjohn/gs-skills` | MIT | `net` | Google Scholar 工具集——**抓 DOM，Scholar 一改版就坏** |
| `yorkeccak/scientific-skills` | MIT | `net` | 13 个源的自然语言检索（含 PubMed / 预印本 / 试验 / 专利）；**依赖 Valyu API，不自足** |

> **能借鉴的**：`ai-skill-scholar` 的「**可组合**」——三个 skill 各做一件事，串起来是流程。
> 本库的 `literature-pipeline` 是单体，但 §〇 已按步骤分段入口，方向一致。

---

## 二、精读与证据评级

| 项目 | 许可 | 足迹 | 一句话 |
|---|---|---|---|
| `diogenes-project/diogenes` | ⚠️ GPL-3.0 | `net` `hooks` | **反谄媚的证据方法论**：ICD 203 + GRADE + PRISMA + Cochrane RoB，做成 **14 步评级** |
| `keemanxp/slr-prisma` | 🔴 NOASSERTION | | PRISMA 2020 脚手架（方案 / 检索 / 筛选 / 流程图 / 综合）——**流程指导，不做自动检索** |

> **能借鉴的**：`diogenes` 把 **ICD 203**（美国情报界分析标准）搬进证据评级。
> ICD 203 的核心是**结构化分析技术**——关键假设核查、竞争性假设分析、指标与路标。
> ICD 203 的结构化分析技术与本库 `peer-review` 的「五层生成轴」同向（**给生成法，不给固定清单**），
> 但补上一件我们没写的东西：**把「前提层」的追问固定成一组动作**。

---

## 三、写作与去 AI 味

| 项目 | 许可 | 足迹 | 一句话 |
|---|---|---|---|
| `kangning-huang/science_narrative_skills` | 🔴 无 | `net` | 用 **ABT（And–But–Therefore）** 叙事框架判一篇论文的论证是不是一条故事线 |
| `matsuikentaro1/humanizer_academic` | MIT | | 医学稿去味，**做的是反向动作**——把 LLM 一律抹平的正式术语**补回来** |
| `conorbronsdon/avoid-ai-writing` | MIT | | 引假阳性研究，并坚持自己的标记是「**信号，不是证据**」 |
| `blader/humanizer` | MIT | `net` | 去 AI 腔的事实标准（破折号滥用 / 三项排比 / 填充词 / 否定式排比） |
| `stephenturner/skill-deslop` | MIT | | 科研版去味，**放过 Methods 的被动语态**等学科惯例 |
| `hardikpandya/stop-slop` | MIT | | 八条硬规则；**通用文体，不看假阳性** |
| `houlaisan/deai-academic-zh` | MIT | | 中文三遍法（措辞 → 突发度 → 重构）+ **零编造规则** |

> **能借鉴的三条**：
> ① **ABT 叙事弧**——本库的表达层四轴查「词/句/段/章有没有机器腔」，
>    **不查「这段论证有没有转折与落点」**。ABT 正好补上该缺口（已落进 `ai-academic-writing`）。
> ② **反向动作**——去味不只有「删」，还有「把被抹平的正式术语补回来」。
>    医学稿尤其明显：LLM 会把 `adherence` 写成 `how well patients followed the plan`。
> ③ **「信号，不是证据」**——与本库的 B 类纪律同构，值得直接引用为外部佐证。

---

## 四、设计与统计

| 项目 | 许可 | 足迹 | 一句话 |
|---|---|---|---|
| `aipoch/medical-research-skills` | MIT | | 550+ skill，含 `Protocol Design/` 83 个 |
| `wei-ai-lab/clinical-trial-design` | Apache-2.0 | | R 引擎 + 9 个 MCP 工具，288 个 R 测试 |
| `anthropics/healthcare` `clinical-trial-protocol` | 🔴 无 | | 方案模板 |

> **已吸收**：D6 混杂与偏倚复核 · 终点定义操作化 · 最小可行研究 · 出处分五类。
> ⚠️ 均为**按本库 D 段流程改写**，未复制原文。详见 `study-design`。

---

## 五、汇报与出片

| 项目 | 许可 | 足迹 | 一句话 |
|---|---|---|---|
| `openraiser/paperfit` | MIT | `net` | LaTeX 排版套件：编译 → **渲染成图** → 看图诊断并修版式（溢出框 / 浮动位置 / 间距） |
| `Noi1r/beamer-skill` | MIT | | 学术 Beamer，有主张：**不用 overlay、密度上限、视觉溢出检测** |
| `zouchenzhen/thesis-defense-pptx-skill` | Apache-2.0 | | 从论文 PDF/LaTeX 出答辩稿，**严格复用学校 PPTX 模板**，**清点被引图**并查版式溢出 |
| `noi1r/powerpoint-skill` | MIT | | 原生 OMML 公式的 PPTX 生成 |

> **能借鉴的两条**：
> ① **vision-in-the-loop**——不是「渲染完体检一次」，而是「渲染 → 看图 → 改 → 再渲染」的闭环。
>    本库有 `render_and_qa_pptx.py`（成品像素体检），但**没写明 vision-in-the-loop 闭环**（已落进 `academic-slides`）。
> ② **被引图清点**——版面里有几张图，正文引用了几张，**两张清单对不上就是漏**。
>    被引图清点与本库「覆盖声明 N→M→K」是同一个动作换了对象。

---

## 六、审稿与回复

| 项目 | 许可 | 足迹 | 一句话 |
|---|---|---|---|
| `cmertdalli/polisci-review` | MIT | | 预投稿审查 9 模块，**带目标刊 persona 与 8 份核实过的期刊政策档案** |
| `alexwortega/ai-peer-review-skill` | MIT | | 丢一个 PDF，出 N 份独立评审 + 一份综述 + 一份问题矩阵 CSV |
| `xz-liu/mean-reviewer-skill` | 🔴 无 | | 扮演最坏情况的敌意审稿人：堆弱点、攻框架、分数钉死在拒稿 |
| `pengkangzhen/academic-review-skill` | MIT | | 把批评**故意写成提问**，避免误杀真发现 |
| `claesbackman/AI-research-feedback` | MIT | | 只针对 AER/QJE/JF 档经济学期刊的预审模拟 |

> **能借鉴的两条**：
> ① **期刊政策感知**——审稿前先握目标刊的政策（统计报告要求 / 数据共享 / AI 声明 / 字数），
>    再按它核。本库 `submission` 管选刊、`peer-review` 管审稿，**两边都没把「目标刊政策」落成一张表**。
> ② **「批评写成提问」**——与本库「只批评不给方向 = 违规」互补：
>    有依据但不确定时，**提问比断言更不容易误杀**。

---

## 七、投稿与格式

| 项目 | 许可 | 足迹 | 一句话 |
|---|---|---|---|
| `maxwell2732/my-submission-formatting-agent` | 🔴 无 | `hooks` | 按新刊作者须知**重排定稿**，**绝不碰结果**——专为拒稿后改投 |
| `junhahyung/claude-skill-overleaf` | MIT | | 走 Overleaf git bridge 读写项目 |
| `lovstudio/any2pdf` | MIT | | Markdown → PDF，**真本事是 CJK 渲染**（Pandoc / wkhtmltopdf 在 CJK 渲染上会崩） |
| `gostyan/docx-skill-4-cn-paper` | MIT | | 中文论文 Word 版式（字体 / 字号 / 页边距 / 图表编号 / 参考文献） |
| `7tocr/paper2patent` | MIT | | 论文 → 中国发明专利申请稿 |

> **能借鉴的一条**：**「按目标刊格式重排」是 E6 的一个独立子步骤**——
> 只动版式不动结果，且有明确的界限（**never touching the results**）。
> 本库 `submission` 原先只写「选刊 → 投出去 → 登记回来」，缺「按目标刊格式重排」（已补）。

---

## 八、索引与生态图

| 项目 | 许可 | 一句话 |
|---|---|---|
| `O0000-code/awesome-academic-skills` | CC0 | 223 skill / 14 类的中英双语索引，**每条记许可与运行足迹**——本文格式即取自它 |
| `Yila-AI/awesome-research-skills` | 见其 LICENSE | 「从任务出发」的入口表 + 完整生命周期图 |
| `Anplus/academic-research-skills` | ⚠️ CC BY-NC 4.0 | 10 阶段管线：自适应检查点（FULL/SLIM/MANDATORY）· 材料护照 · 14 场景路由 |

> **能借鉴的两条**：
> ① **「从任务出发」的入口表**——本库的 `skills.md` 按**流程阶段**组织，
>    而人往往是带着任务来的（「我要把稿子变成汇报」）。已补进 `docs/README.md`。
> ② **检查点分档**（FULL / SLIM / MANDATORY）——本库的门禁是二值的（过 / 不过）。
>    ⚠️ **暂不引入**：分档需要先有「风险 × 阶段」的判据，否则只是给同一条门禁换个名字。

---

## ⚠️ 三处**不借鉴**

| 项目类型 | 为什么不 |
|---|---|
| **AIGC 检测规避**（`aigc-down-skill` / `anti-aigc-zh` 等一批） | 目标是**压低检测率**，不是把文本写好。与本库 `text-self-review` 的边界一致：**找出真实的写作问题是合理的；把 AIGC 率压到某个阈值以下是另一回事** |
| **0–100 质量评分档**（多处） | 给了数就有人当真。**没有真值的评分是假精确**——本库的立场是给**可判定的判据**，不给分 |
| **多 persona 模拟审稿当结论** | 一份稿子模拟出 5 份意见，很容易被当成「5 个人都这么看」。它不是证据，只是**另一双眼睛的提问** |
