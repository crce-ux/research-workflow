---
类型: 外部工具评估
主题: workbuddy skills 目录全量扫描（8 个包）—— 可加载 / 可借鉴 / 无关
日期: 2026-09-26
扫描路径: <本机路径>
结论: **8 个包，0 个可加载。** 值得借鉴的收敛到 3 条（另有 1 条经核验后划掉——我方已有且更精）。
前置: [[评估_外部PPTskill_ppt-design-master_20260926]]（其中 1 个包已单独评估过）
方法: 分 3 个子代理并读，主会话只收结论（上下文预算纪律）；**关键结论由主会话原文复核**
---

# workbuddy 技能包全量扫描（2026-09-26）

## 〇、一句话结论

**8 个包里没有一个是可加载的。** 其中 1 个触碰许可边界、1 个自带远程静默自更新、
1 个关闭 TLS 校验并含他人 PII、1 个**承诺 6 个脚本而实际一个都没有**。
值得借鉴的东西收敛到 **3 条**，且最有价值的两条来自**交付残缺的包**——只有思想，没有代码。

---

## 一、总表

| 包 | 体量 | 有代码 | **结论** | 一句话理由 |
|---|---|---|---|---|
| `pptx` | 1.3MB / 15 py | ✅ | 🟡 **可借鉴** | **Anthropic 官方 skill 的第三方重打包**；pptxgenjs 路线与本库不同轨；本机 6+ 依赖全缺；**中文字体零处理** |
| `beatra` | 254KB / 3 py | ✅ | ⛔ **无关** | 付费 AI 媒体生成 SaaS；**每 24h 从 CDN 静默自更新覆盖本包**；带遥测 |
| `ppt-generator-skill` | 232KB / 5 | ✅ | 🟡 **可借鉴（弱）** | 本机**跑不起来**；CLI 参数与文档**直接矛盾**；引用的 `templates/` 不存在；输出是硬编码 demo 页 |
| `ppt-pro-max` | 29KB | ❌ | 🟡 **可借鉴（仅思想）** | **文档承诺 6 个脚本 + demo.pptx，包内实际只有 SKILL.md + 图标 + 2 个 meta** |
| `ppt-afp` | 25KB | ❌ | ⛔ **无关** | 🔴 **硬编码他人飞书租户文档链接 + open_id；`NODE_TLS_REJECT_UNAUTHORIZED=0` 关闭 TLS 校验** |
| `ppt-optimizer` | 29KB | ❌ | ⛔ **无关** | 与已评估的 `ppt-design-master` 高度重叠 |
| `ppt__skillhub` | 34KB | ❌ | ⛔ **无关** | 9:16 竖屏 HTML 演示，与 16:9 组会场景不同轨 |
| `ppt-design-master` | 57KB | ❌ | ⛔ 已评估 | 见 [[评估_外部PPTskill_ppt-design-master_20260926]] |

> **许可**：**8 个包中 7 个没有 LICENSE**（仅 `pptx` 有，且不是开源许可）。

---

## 二、⚠️ 先说风险 —— 三条与"好不好用"无关的硬约束

> 这三条**优先级高于任何功能评价**。装进本地环境前必须知道。

### 2.1 🔴 `ppt-afp`：关闭 TLS 校验 + 硬编码他人 PII

主会话原文复核（`ppt-afp__skillhub/SKILL.md`）：

| 行 | 内容 |
|---|---|
| 212、231 | `NODE_TLS_REJECT_UNAUTHORIZED=0 \` —— **明文关闭 TLS 证书校验**，且**未被注释** |
| 62、68 | 硬编码他人**飞书租户文档**地址 `https://sgl0nnj5ev.feishu.cn/docx/...` |
| 243 | 硬编码个人 open_id `ou_74c5a7816fcb78172bfca68a7f7449e8`（已注释） |
| 137 | 硬编码作者本地路径 `~/Desktop/二饼文件夹/openclaw 二饼/` |

**判断**：这是**绑定在作者个人环境**上的包，不是可分发工具。**不建议加载。**

### 2.2 🔴 `beatra`：每 24 小时静默远程自更新

主会话复核（`beatra__skillhub/scripts/mcp_client.py`）：

- L32：`PACKAGE_CDN_BASE_TEMPLATE = "https://cdn.beatra.ai/agent-packages/.../v{version}"`
- L324：更新源校验（限定了 hostname，这点做得对）
- L1227：每次调用注入 `source_package_slug` —— **遥测**

该包 SKILL.md 自述更新**"不另行确认，客户端即可自动安装"**。
→ **一个会在你不知情时覆盖自己代码的包，不应进学术环境。** 与其功能（AI 生图/视频）也无关。

### 2.3 🟡 `pptx`：是 Anthropic 官方 skill 的第三方重打包

主会话原文复核 `pptx/LICENSE.txt`：

```
© 2025 Anthropic, PBC. All rights reserved.
...use is governed by your agreement with Anthropic regarding use of Anthropic's services.
If no separate agreement exists, use is governed by Anthropic's Consumer/Commercial Terms of Service
```

> ⚠️ **本次更正**：子代理初报为「LICENSE 明文**禁止提取/复制/衍生/分发**」——
> **复核后不成立，原文没有这句话。** 准确表述是：
> **「保留所有权利 + 受 Anthropic 服务条款约束」，不是开源许可。**
> 该包在第三方市场以 "zxh" 名义分发，**其再分发的正当性由 Anthropic 的服务条款决定，不是我能判定的**——
> 但**它不是给你自由使用的开源件**，这一点确定。

> 📌 附带一个事实：**我们本身就在 Anthropic 的技能生态里**。
> 需要官方 `pptx` 能力，**正规路径是走 Anthropic 官方渠道**，而不是采用一个来源不明的重打包副本。

---

## 三、"文档承诺 >> 实际交付" —— 这是这批包的共同模式

与上次评估 `ppt-design-master` 时观察到的现象完全一致（无脚本、无模板、只有规范文本），
本次在其余包中**重复出现，且更严重**：

| 包 | 承诺 | 实际（已 `ls`/`find` 实测） |
|---|---|---|
| `ppt-pro-max` | `scripts/run.py` · `layout_check.py` · `auto_fix.py` · `compat_output.py` · `demo_generate.py` · `assets/demo.pptx` | **包内 `*.py` = 0，`*.pptx` = 0**；只有 `SKILL.md` + `_icon.png` + 2 个 meta |
| `ppt-generator-skill` | `node generate.js --topic X --template Y --pages 10`；`templates/` 目录 | `generate.js` **只认 `--title/--palette/--lang/--output`**；`templates/` **不存在** |
| `pptx` | "`pptxgenjs` 已预装" | 无 `node_modules`，`require` 抛错 |

> **判据**：这类包的 README/SKILL.md **不能作为"它能做什么"的依据**。
> 必须先 `ls` 交付物、再读代码、最好实跑一次。
> → 与本库既有纪律同源：**「不报错 ≠ 检索式生效」**（FACT §〇）。

---

## 四、其余质量问题（逐条可核，仅列有实质影响者）

| 包 | 问题 |
|---|---|
| `pptx` | `scripts/validators_base.py:59-63` 的 schema 路径指向 `schemas/ecma/...` 子目录，而 `schemas/` 已被**拍平** → `validate.py` 会对 `[Content_Types].xml`、`docProps/core.xml` 及**每个 `.rels`** 报**假失败**。重打包引入的实锤 bug |
| `pptx` | `scripts/validate.py:146` 引用 `scripts/recalc.py` —— **包内不存在**（从 xlsx 包合并来的残留） |
| `pptx` | `SKILL.md:109,182` 绝对化禁令「NEVER 标题下装饰线/色条」，称其为"AI 痕迹"——**无出处**，且**与本库 `ppt_kit.py` 的标题栏/色带组件直接冲突** |
| `pptx` | `SKILL.md:151`「safe fonts ... ship with Office」只对拉丁字体成立；**全包 grep 中文字体 = 0 命中** |
| `ppt-pro-max` | 三套字号下限**自相矛盾**：L178「最小 6pt」 vs L227「最低 10pt」 vs L334「低于 6pt 阅读困难」 |
| `ppt-pro-max` | L9「零额外依赖」 vs L391 需 pywin32 + python-pptx + Office —— 自相矛盾 |
| `ppt-optimizer` | `color-schemes.md:78`「浅色文字 + 深色背景 ≥4.5:1（演示环境）」—— 深底**放松**对比度，无出处，且与投影需更高对比的常识相悖 |
| `ppt__skillhub` | `SKILL.md:71`「单个 HTML 文件，可直接打开运行」不实 —— `template.html` L9/L12-13 依赖 3 个外部 CDN，**离线即废** |

---

## 五、可借鉴清单（去重后 3 条）

> ⚠️ **第 1 条已被核验划掉** —— 见 5.1。

### ~~1. CJK 文本宽度估算~~ ❌ **划掉：我方已有，且更精**

子代理建议「中文≈2×拉丁、拉丁≈0.55em」加入 `ppt_check.py`。

**复核结果**：`ppt_style.estimate_text_width()`（L125-147）**已经实现了这件事，而且更细**：

```
CJK 1.0 ｜ 空格 0.3 ｜ 宽拉丁(mMwWOQ%) 0.75 ｜ 窄拉丁(iIlj!|) 0.3 ｜ 其余 0.55 ｜ 粗体 ×1.05
```

它已用于 `ppt_check` 的 I 项（文字出框检测）。
> **教训**：子代理是基于**对该包的阅读**给建议，**没有核对我方是否已有**。
> 「借鉴清单」这类产出，**每一条落笔前都必须先查我方现状**，否则会推荐已有之物。
> 本次 4 条建议里，第 1 条即为此类。

### ⭐ 2. 溢出量化 + 自动修复闭环 → `ppt_check.py` 增 `--fix`

- **我方现状**：`ppt_check` 的 I 项**能检出**文字出框（估算宽度 + 容器包含），但**只能报，不能修**。
- **可借鉴**：量化**溢出率**，并按「先缩字号 → 再扩框 → 复检」的顺序**自动修复**，且设**"不可修复"阈值**（超出则交人工）。
- **落地**：`ppt_check.py --fix`，与现有 `--strict` 并列；修复前自动 `.bak`（参照 `renumber_refs.py` 已有做法）。
- **⚠️ 注意**：来源包 `ppt-pro-max` **没有任何代码交付**，这里借的是**思路**，实现要自己写。

### ⭐ 3. 图片化兼容兜底 → 新脚本 `ppt_compat_export.py`

- **痛点**：**中文 WPS / 不同版 Office 打开同一 PPTX，字体与排版会漂**。
  本库的 SVG 字体栈（`Microsoft YaHei` 打头）在别机打开时并不保证一致。
- **可借鉴**：逐页导出位图 → 合成"图片化" PPTX 作**兜底版本**（文字不可编辑，但**保真**）。
- **适用**：**只用于对外发送/存档**，内部编辑仍用原 PPTX。
- **依赖**：需 Office COM（pywin32）或 LibreOffice —— **本机两者都没有**（见 §六）。

### 4.（边际可选）OOXML 打包层校验 → `ppt_build.py` 成品验证

来源 `pptx` 技能。它做的**不是** SVG 层质检（属于我方 `ppt_check` 的工作），
而是**生成的 PPTX 包本身**的检查：XSD 能过、但 PowerPoint 拒开的一类
（堆积柱 `dLblPos` 非法、组合图未声明的 secondary axId、多 master 共用 theme 等）。

- **我方现状**：`render_and_qa_pptx.py` 做**像素级**成品体检，**不做包结构校验**。
- **价值**：属真实空白，但**触发概率低**（我方 PPTX 由 ppt-master 统一生成，不是手改 XML）。
- **结论**：**优先级最低**，暂不建议做。

---

## 六、依赖现状（本机实测）

| 依赖 | 状态 | 卡住谁 |
|---|---|---|
| `defusedxml` / `lxml` / `Pillow` / `markitdown` | ❌ 全缺 | `pptx` 的 validate / thumbnail |
| `pptxgenjs` | ❌ 缺（node v22 在） | `pptx` 建页、`ppt-generator-skill` |
| `soffice` / `pdftoppm` | ❌ 不在 PATH | `pptx` 缩略图 |
| `python-pptx` | ❌ 缺 | `ppt-generator-skill` 全部 4 个脚本 |
| `pywin32` | ❌ 缺 | 借鉴第 3 条（图片化兜底） |

> 即：**这批包在本机一个都跑不起来**（子代理已逐个实测确认，非推测）。

---

## 七、本次评估的方法说明与更正

| 项 | 说明 |
|---|---|
| **分工** | 8 个包按体量分 3 组，交 3 个子代理并读；主会话只收结论 —— **未让 8 个包的全文进入主上下文** |
| **复核** | 3 条高影响结论（LICENSE / TLS+PII / 脚本数）**由主会话原文复核**，不转述子代理 |
| **更正 1** | 🔴 子代理称 `pptx` 的 LICENSE「明文禁止提取/复制/衍生/分发」→ **原文无此句**。准确表述：**保留所有权利 + 受 Anthropic 服务条款约束**（§2.3） |
| **更正 2** | 子代理建议的「CJK 宽度估算」→ **我方已有且更精**，划掉（§5.1） |
| **未复核项** | 各包内部矛盾的具体行号（`ppt-pro-max` 字号下限、`ppt-optimizer` 对比度论断等）**沿用子代理报告**，未逐条回原文。如需据此改动本库，**须先复核** |

---

## 八、结论与建议

1. **8 个包均不建议加载。** 三个无关包各有硬约束（TLS/PII、静默自更新、场景不符）；
   两个"可借鉴"包**本机跑不起来且劣于现有 SVG 管线**。
2. **值得做的只有 2 件**（第 2、3 条）：
   - `ppt_check.py --fix`（溢出自动修复）—— **纯 Python，无新依赖，可立即做**
   - `ppt_compat_export.py`（图片化兜底）—— **需先解决 COM/soffice 依赖**
3. **`pptx` 的 OOXML 包校验项**优先级最低，**暂缓**。
4. ⚠️ **若确需 Anthropic 官方 `pptx` 能力，走官方渠道**，不要用来源不明的重打包副本（§2.3）。

---

## 九、落地结果（同日完成）

| 借鉴项 | 状态 |
|---|---|
| **第 2 条 · `ppt_check.py --fix`** | ✅ **已完成**（2026-09-26）—— 见下 |
| 第 3 条 · `ppt_compat_export.py`（图片化兜底） | ⏸ 待办 —— **卡在依赖**（本机无 pywin32 / soffice） |
| 第 4 条 · OOXML 包校验 | ⏸ 暂缓（优先级最低） |

### `--fix` 的实现取舍（与"借来的思路"的差异）

来源包 `ppt-pro-max` **零代码交付**，借到的只是"量化溢出 + 自动修复 + 复检"这个骨架。
落地时做了两处**主动收紧**，理由如下：

| 项 | 原思路 | 落地做法 | 为什么收紧 |
|---|---|---|---|
| 修复手段 | 缩字号 **+ 扩框** | **只缩字号** | 扩框会与邻元素撞车；脚本**看不到版式意图**，改一个看不出后果的几何比不修更危险 |
| 字号取值 | 未限定 | **只从 `OK_SIZES` 里取** | 造新字号会触发 E 项，且破坏设计系统一致性 |
| 降幅 | 未设上限 | **≤30%**（`FIX_MAX_DROP=0.70`）| **40px→23px 不是修复，是重排**；此时正确答案是改措辞/扩框 |

**测试**（`_work/` 下）：

- `make_fixture.py` —— 造 4 个几何可控样本。**必须造**：本库 21 骨架均无出框，
  干净库上跑 `--fix` 永远是「无需修复」，**证明不了任何事**。
- `test_rollback.py` —— **故障注入**测回滚分支。该分支在正常几何下**跑不到**
  （降字号对宽度单调递减），但**跑不到的分支等于没测过**，安全网必须自己验一次。

**回归**：21 骨架 `ERROR 0 ｜ WARN 22`，与该功能加入前**逐项一致**。

---

*扫描 2026-09-26 ｜ 8 包 0 可加载 ｜ 借鉴清单经去重与核验后为 3 条（原 4 条，划掉 1 条）｜ 第 2 条当日落地*
