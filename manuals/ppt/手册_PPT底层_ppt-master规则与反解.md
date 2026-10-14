# 手册 · PPT 底层（ppt-master 原始规则 与 PPTX 反解）

> **定位**：`PPT工具链手册.md` 的**底层补充**——本文收录三块手册正文没写的东西：
> ① ppt-master 自身的原始使用规则（我们的自建管线只替代了它的「写作层」）
> ② PPTX 反解回 SVG（`pptx_to_svg`）——反解参考模板、提取设计参数
> ③ PPT 完整流程与视觉验证的固化口径
> **来源**：2026-09-24 自 Agent `FACT.md` §五 Stage 7 与 §七 迁出（**原文照搬，未改写**）。
> **何时读**：直接用 ppt-master 原始管线时；要反解别人的 PPTX 模板时；改 PPT 验证流程时。
> **日常做组会 PPT 只需读 `PPT工具链手册.md` + `PPT工具链速查_20260915.md`。**

---

## 一、ppt-master 原始使用规则（背景知识）

- 管线：7 步；**Step 4 Strategist 强制且不可跳过**，唯一用户确认门
- 导出：`python <skills>/ppt-master/skills/ppt-master/scripts/svg_to_pptx.py <project> --pptx-structure flat -o <out.pptx>`
- ⚠️ **解释器**：原记录用 `E:/python/python.exe`（默认 python 3.11 缺 flask 与 python-pptx）
  → 🔴 **本机无此目录**。⚠️ 原因是**盘符语义随机器变**，不是「本机没有 E 盘」：
  **老机器**＝内置 `E:` + 移动硬盘 `F:`；**本机**＝无内置 E，**移动硬盘占 `E:`**（且 E: 有内容）。
  本机解释器用 `D:\Python313\python.exe`（3.13.14）；缺依赖时按需补装。详见 `FACT.md` §十三「🔴 盘符映射」
- ⚠️ **编码**：`export PYTHONIOENCODING=utf-8`，否则报 GBK 错
- ⚠️ **脚本坑**：抽页/重编号时 `extract` 出的 block 未写回文件会静默丢失

> 与自建管线的关系见 `PPT工具链手册.md` §八。
> **合并层仍靠 ppt-master**，其 `svg_to_pptx.py` 三个位置均已确认在位。

## 二、⭐ PPT 完整流程（2026-09-11 固化）

```
① 内容稿定稿 → ② PPT制作稿 → ③ 生成PPTX → ④ 视觉验证 → ⑤ 成品复核 → ⑥ 迭代
```

- **② PPT制作稿是关键中间产物**：逐页七项素材——**把内容与排版解耦**（实战曾迭代到 v7）
- 规则：数字以制作稿为准不凭记忆；单位与文献编号 `[n]` 必须保留

## 三、⭐ PPT 视觉验证（2026-09-12）

- **渲染路径**：PowerPoint COM（win32com）导出 PNG。**Export 必须用绝对路径**
- **可复用脚本**：`科研/scripts/render_and_qa_pptx.py <pptx> [outdir]`
- **双轨验证**：客观像素体检 + 语义判读（原生视觉读 PNG）
- **已验证能抓到的缺陷**：背景图边缘泄漏（逐像素暗带，文字复核完全无法发现）
- ⚠️ **依赖**：`pywin32`（本机迁移后未装，见迁移检查文件）

**SVG 手写规则**：禁 Python -c 传参（中文丢失）；背景统一 `#FFFFFF`；用 Write 工具写；
嵌入图用 `<image href=...>`；无图占位用虚线 rect

> 导出器支持边界的**完整清单**见 `PPT工具链手册.md` §七（什么能写、什么会炸），本文不重复。

---

## 四、⭐⭐ 反解参考模板：`pptx_to_svg`（2026-09-22 首次使用）

用于**反解别人的 PPTX 模板**，提取配色/字号/边距/几何等设计参数。

```bash
<解释器> <skills>/ppt-master/skills/ppt-master/scripts/pptx_to_svg.py \
  <模板.pptx> -o <输出目录>
```

- **纯标准库**（zipfile + ElementTree），秒级，**不要 PowerPoint、不要 python-pptx**
- 输出：`svg/`（masters/layouts/slides **三层**）· `svg-flat/`（自包含）· `assets/` · `conversion-report.json`
- 保真度：目视与原页几乎一致
- **能提取**：边距/栅格/对齐线（坐标精确）· 字号/字重/字体族/对齐 · 装饰件形状几何 · 图片尺寸与位置 · 调色板与用量占比
- **不能提取**：**阴影（`outerShdw` 丢失）** · 斜向渐变填充 · 动画转场 · 字体本身

### ⚠️ 指标必须人工验证定义（实测两次踩坑）

① 「小图占比」被**整页背景图**污染（2亮蓝白/7紫 每页都有一张 99.9% 的背景图）
② 「顶部通栏带」把**整页色域**误判成顶部带（测出 166.8% > 100%）

→ **异常值是指标定义有问题的信号，不是发现** → 须改用视觉复核。

### 本次反解产出（7 套国自然模板）

- `pptx_to_svg_全7套终版结论_20260922.md`
- `pptx_to_svg_跨模板验证_20260922.md`
- `pptx_to_svg试跑_3深蓝白色系_20260922.md`
- `pptx_to_svg试跑_排版与设计层_20260922.md`

→ 结论已落进 `PPT工具链手册.md` §10.2（视觉改版）与 `PPT视觉规范_国自然风格_20260915.md`。
