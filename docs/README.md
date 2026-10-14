# docs/ · 从哪读起

**本文件只回答两个问题：某项任务用哪个 skill；以及，出问题看哪份文档。**

---

## 一、从任务出发

| 我想…… | 用 | 再读 |
|---|---|---|
| 读一篇新文献、做精读笔记 | `paper-reading` | — |
| 查一批文献、建证据表、去重 | `literature-pipeline` | — |
| 从政务 / 产业库取数（NMPA / 医保 / 巨潮…） | `literature-pipeline` §非常规数据源 | — |
| 把一个想法落成可立项的研究方案 | `study-design` | 规则见 `D` 段 |
| 算样本量、核可行性数字 | `study-design` + `scripts/design/sample_flow.py` | — |
| 数据收上来了，算到能报的结果 | `data-pipeline` + `scripts/data/missing_report.py` | — |
| 写论文 / 写综述 / 去 AI 味 | `ai-academic-writing` | **改写必附保真审计** |
| 做组会 PPT、汇报、出片 | `academic-slides` | — |
| 写国自然标书 / 诊断一份标书 | `grant-diagnosis` | — |
| 投哪本刊 / 登记成果台账 | `submission` | — |
| 审别人的稿 / 判断一篇稿子站不站得住 | `peer-review` | — |
| **交出去之前再查一遍** | `text-self-review` | 横向，套在任何一份产出上 |
| 本仓工具本身怎么维护 | **本文 §四** + `scripts/doctor.py` | — |

> ⚠️ **两件事别混**：拿真稿跑检查器是**验收工具**（看它报得准不准），不是改稿。
> 两者的完成标准不同——见 `pipeline.md` §八。

---

## 二、四份文档各管什么

| 文件 | 回答 |
|---|---|
| [`pipeline.md`](pipeline.md) | **流程走到哪、该过哪道门**——P→A→B→C→D→E + 五门 + 六轴 + 闭环 |
| [`skills.md`](skills.md) | **该用谁**——自研 10 个 × 已装外部，以及哪里还空着 |
| [`external-skills.md`](external-skills.md) | **外部同类项目的许可与运行足迹**——复制前先看许可列 |
| [`runtime.md`](runtime.md) | **工具怎么接**——能力 → 候选工具；以及为什么不写死工具 ID |

---

## 三、写在 skill 里的三条通用约定

1. **脚本只做可自动化的部分**——每个脚本的 docstring 里写清它**不查什么**
2. **覆盖要说出来**——报 `N → M → K`，K 逐条列原因
3. **静默失败比报错危险**——规则整条跳过时必须打印「本次未评」；替换 / 改名后要回读验证

---

## 四、维护本仓工具

```bash
python scripts/doctor.py                 # 一条命令跑完五项体检（结构 / 资产 / 两套副本 / 单测）
python scripts/doctor.py --full          # 连原始输出一起看
python scripts/doctor.py --no-tests
```

doctor 跑的五项：

| 项 | 工具 | 查什么 |
|---|---|---|
| 结构 | `checks/check_skill_structure.py --root D:/Github` | 官方 Agent Skills 规范 + **声明落地** |
| 资产 | `checks/check_assets.py --root .` | 死链 / 脚本总数 / 索引覆盖 / **skill 数对账** |
| 副本① 仓内 | `sync_skill_scripts.py --root D:/Github` | 正本 → 各 skill 的 `scripts/`（**按内容反查**，不维护登记表） |
| 副本② 观测库 | `deploy_to_vault.py` | 仓 → 观测库 `.claude/skills/`（**只增改不删**） |
| 单测 | `pytest tests/` | 304 项 |

```bash
python scripts/sync_skill_scripts.py --root D:/Github --write   # 把副本刷成正本
python scripts/deploy_to_vault.py --write                       # 把库里的刷成仓里的
python scripts/run_checks.py --target <稿子> --ledger <待修清单>  # 跑检查器并把发现落表
```

> **三套副本，两个同步器。** 复制了就要有机制保证一致，
> 否则会出现「改了总仓、副本还是旧的」而不被发现。
