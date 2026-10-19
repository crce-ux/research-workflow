---
name: research-workflow
description: 做科研工作流的体检与排障、判断某一步该用哪个 skill、维护本仓工具时用。22 个检查器与 410 项测试，一条命令跑完结构、资产、路由、手册、两套副本与单测。当用户说「跑一下体检」「doctor」「检查器报错」「哪个 skill 管这一步」「工具链怎么维护」「仓库对账」「skill 装在哪」时使用。
compatibility: 需要 uv（跑单测）与 Python 3.11+。
---

# 科研工作流 · 入口与体检

本仓是十个自研 skill 的正本与工具层。skill 本身管方法与判据，本仓管「这些判据有没有被真正执行」。

## 读什么

- 某一步该用哪个 skill → `docs/skills-map.md`
- 全流程与五道门 → `docs/pipeline.md`
- 手册去哪了 → `docs/manuals.md`
- 各 skill 之间的接口 → `docs/skills.md`

## 一条命令

```bash
uv run --with pytest python scripts/doctor.py
```

七项：结构 · 资产 · 路由 · 手册 · 副本①仓内 · 副本②观测库 · 单测。

全绿才算工具链正常。任一项未过，按输出逐条处置。

## 检查器分四组

| 组 | 查什么 | 例子 |
|---|---|---|
| 稿件 | 语言、措辞、引用、证据表、笔记、讲稿 | `check_language.py` `check_ref_citations.py` `check_talk.py` |
| 文档 | 设计书、数据管线、审稿意见、国自然年度值 | `check_design.py` `check_data.py` `check_grant_rules.py` |
| 仓库 | 资产对账、skill 结构、路由节、手册登记、元数据泄漏 | `check_assets.py` `check_routes.py` `check_manuals.py` |
| 比对 | 改写前后受保护 token、数字与否定项 | `check_token_diff.py` `number_diff.py` `negation_diff.py` |

## 上下游接口

- **上游给我什么**：各 skill 的产出物（笔记、证据表、稿件、制作稿）与仓库改动
- **我给下游什么**：体检结论、待修清单、被拦下的交付
- **什么状态算交出去了**：`doctor.py` 退出码 0
- **不交接的**：不改稿、不做内容判断、不上台表达

## Anti-Patterns

- **Never** 把检查器报告当欠账——报出发现是工具可用的证据，不是必须立刻改的清单
- **Never** 在 `doctor.py` 未全绿时说「工具链正常」
- **Never** 只跑单测当完整体检
- **Never** 手改生成物（`_journal_data` 以外的对账文件、索引、副本）
- **Never** 在检查器「本次未评」时说「查过了」——未评不是通过
