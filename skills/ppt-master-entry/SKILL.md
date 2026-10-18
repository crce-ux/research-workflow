---
name: ppt-master-entry
description: 做汇报 PPT、把内容稿做成 pptx、按模板出片时用。本机已装 ppt-master，本 skill 只给入口与四步流程，不复制它的规则。
compatibility: 需要 ppt-master 已装在 Cherry 全局 skill 池。
---

# ppt-master 入口

本机的 ppt-master 装在：

```
C:\Users\Chen Chen\AppData\Roaming\CherryStudio\Data\Skills\ppt-master\skills\ppt-master
```

PPT 一律走 ppt-master。**不自建模板、不用自建骨架与配方。**

## 读什么

- 模板契约与生成流程 → ppt-master 的 SKILL.md 与 workflows/generate-pptx.md
- 模板库 → ppt-master/templates 下四类 *_index.json
- 质量门 → ppt-master 的 svg_quality_checker.py --template-mode

## 四步

```
① 读内容稿，定每页说什么
② 选模板   templates/decks 等目录的 index → 开 design_spec 判断适用场景
③ 装模板   scripts/apply_template.py <项目> --root <模板根>
④ 出片     scripts/svg_to_pptx.py <项目> --quick-generate
```

## 三条硬约束

- **镜像模板（`replication_mode: mirror`）不能装新内容**——框按原文长度定死。换内容用 `fidelity` / `standard`。
- **版式跟着信息结构走**——表格页要表格版式，不能把表压成方框。
- **导出后用 PowerPoint 渲染逐页看**——Chrome 渲 SVG 不反映换行，会误判。

## 上下游接口

- **上游给我什么**：内容稿与每页要点（来自 ai-academic-writing）、讲稿与制作稿（来自 academic-slides）
- **我给下游什么**：一份 pptx，落在项目目录下
- **什么状态算交出去了**：导出成功；`svg_quality_checker --template-mode` 退出码 0；PowerPoint 逐页渲染看过
- **不交接的**：不做内容改写，不写讲稿
