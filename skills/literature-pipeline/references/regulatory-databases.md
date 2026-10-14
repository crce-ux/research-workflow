# 监管 / 政务 / 产业数据库 · 逐站取数

> **管什么**：NMPA · CDE · 国家医保局 · 巨潮资讯 · 港交所披露易 · 卫健委 · ClinicalTrials.gov
> **不管什么**：文献检索（走 `literature-pipeline`）。

---

## 〇、先试直连，再上浏览器

**顺序不可颠倒**：

```
1  curl / requests        —— 政府主页大多失败，但附件、接口常可行
2  官方开放 API           —— ClinicalTrials.gov API v2 等，直连
3  DrissionPage + 真实浏览器 —— 兜底
```

> ⚠️ **浏览器是兜底，不是默认。** 上来就开浏览器，
> 慢且脆，大部分时候并不需要。

---

## 一、NMPA · 药品批准文号

### 难点：瑞数动态令牌

NMPA 站有**瑞数**（Riversafe）反爬：页面内嵌 `api.js`，
运行时生成动态令牌；直接调接口 **HTTP 412**。

### 已证伪的路

```
❌ curl / requests
❌ Playwright 无头
❌ Playwright 有头 + stealth
❌ goto → reload 换 Cookie
❌ 反混淆 api.js（jsjiami 混淆 + 自定义 VM）
```

### 可用：DrissionPage + localStorage 注入 ⭐

**关键观察**：**首页的搜索框驱动不了**（首页搜索框只负责跳转），
但**结果页可以独立访问**——查询条件**持久化在 localStorage 里**。

所以不去点首页搜索框，而是：

```python
# 1. 用 DrissionPage 打开结果页
# 2. 往 localStorage 写查询条件
# 3. reload —— 结果页读 localStorage 渲染
```

条件名与结构**随站点改版会变**，第一次跑时在 DevTools 里看一眼 localStorage 的键。

> 🔴 **常见误判**：以为要「模拟用户在首页输入」。
> 其实**在首页输入这一步是多余的**——结果页 + localStorage 就够了。

---

## 二、CDE · 受理品种

### 通路：UI 驱动，**按回车提交**

```python
# 在搜索框填受理号 / 药品名，然后 —— 按回车
page.ele("input").input("...")
page.actions.key_down("ENTER")   # ⚠️ 必须是回车
```

> 🔴 **点「查询」按钮不触发**。CDE 搜索页绑的是回车键事件，不是按钮 click。

### 不走接口

CDE 的查询接口 URL 带**一次性令牌**（页面加载时生成、随会话失效）。抓到一个，下次就废。
**用 UI 驱动。**

### 结果解析

受理品种列表在 AJAX 返回的 JSON 里——**但 URL 不变**（`POST` 到同一端点）。
用 DrissionPage 监听 network 抓响应，或直接解析渲染后的 DOM。

> ⚠️ 抓到响应后，**别只看第一条**——分页在同一个端点，用参数翻。

---

## 三、国家医保局 · 药品目录

**✅ 可直连。** 最省事的一个。

```
1  curl 下载目录附件（PDF）
2  解析 PDF 文本
3  grep 药名 / 剂型 / 甲乙类
```

> ⚠️ **别把附件当网页抓。** 它是**静态文件**，`curl` 一次拿到，
> 不需要浏览器。

---

## 四、巨潮资讯 · 上市公司公告

**✅ 接口可用。**

```python
# 1. 股票表接口 → 拿 orgId（每家公司一个）
# 2. 公告接口 hisAnnouncement/query
#    参数：stock=<orgId>&searchkey=<关键词>&pageNum=1&pageSize=30
```

返回 JSON，含 `announcementTitle` / `adjunctUrl` / `announcementTime`。

> ⚠️ **`orgId` 是巨潮内部的**，不是股票代码——**先查表**。
> 直接拿股票代码当 orgId 会查空，且不报错。

---

## 五、港交所披露易

**✅ 接口可用。**

```python
# 1. prefix.do → 按股票代码查 stockId
# 2. 拿 stockId 调披露接口
```

> ⚠️ **`stockId` 也要先查**——和巨潮同一个坑：**代码 ≠ 内部 ID**。

---

## 六、卫健委

**❌ 412**——同 NMPA 的反爬。**用 DrissionPage。**

---

## 七、ClinicalTrials.gov

**✅ API v2 直连，不用浏览器。**

```
https://clinicaltrials.gov/api/v2/studies?query.term=...
```

> **别把它当非常规源。** 它是**开放 API**——
> 归在 `literature-pipeline` 的直连类里更准确，
> 本文列出只为**防止**有人对着它开浏览器。

---

## 八、⚠️ 法定披露 ≠ 申报状态（**一条重要的教训**）

### 症状

查「某药是否已申报 / 已受理」时，
去**交易所公告**里找——找不到，就下结论「媒体无据」。

**上市公司公告滞后**：事情可能已经发生，公司还没发公告（早期、金额未达披露线、或还在观望）。

### 实例

> 某药**已在 CDE 受理**（CDE 受理目录里有受理号），
> 而该公司**当时尚未发公告** → **曾因此误判「媒体无据」**。

### 正确做法

| 你想知道 | 该去哪 |
|---|---|
| **事情发生了没有**（受理 / 获批 / 进目录） | **业务主管站的业务目录**（CDE / NMPA / 医保局） |
| **公司说了什么**（公告 / 口径 / 预期） | 交易所披露（巨潮 / 披露易） |

> 🔴 **交易所只记「公司说了什么」，不记「事情发生了没有」。**
> **两者是两条独立的证据链，不能互相证伪。**

---

## 九、本机接线表（换机照此重建）

> 第一次跑通后，**把跑通的参数记在本节接线表里**——
> 下次换机直接照搬，不用重新试错。

| 项 | 值 |
|---|---|
| Python venv | `<待填>`（需 `DrissionPage`） |
| 浏览器可执行文件 | `<本机 Edge / Chrome 路径>` |
| 浏览器 profile 目录 | `<待填>`（登录态存在 profile 目录） |
| 默认超时 | `<待填>` 秒 |
| NMPA localStorage 键名 | `<第一次跑时从 DevTools 抄>` |

```bash
# 重建：装 DrissionPage
uv pip install DrissionPage
# 或
<venv>/Scripts/pip install DrissionPage
```

---

## 十、通用自检（每次取数后问）

1. **对照组过了吗？** 单概念命中数合理吗——还是脚本根本没生效？
2. **解析条数对上「命中 N 条」了吗？** 对不上就是漏解析。
3. **我查的是「事情发生了没有」，还是「公司说了什么」？** 两者不可混用。
4. **能直连的我用浏览器了吗？** 能省则省。
5. **参数（orgId / stockId / 令牌）是新查的吗？** 旧的可能已失效。
