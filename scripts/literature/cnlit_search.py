#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
cnlit_search.py —— **中文文献库检索**（维普 / 万方）

【背景】
    英文库有 PubMed / Europe PMC / OpenAlex / CrossRef 四条直连路径，
    **中文库没有**。中文课题用「屏状核」「氯氮平」这类表述时，英文库收不到。
    本脚本补这个缺口。

【浏览器要求】
    维普/万方/CNKI 都有反爬。实测（2026-09-22）：
      · `requests` / `curl` 直连 → 维普 403、CNKI 302 到「安全验证」
      · DrissionPage + **真实浏览器 + 持久 profile** → 维普正常出结果
    ⚠️ **必须固定 profile**：冷 profile 每次都被拦；热 profile 才放行。
    ⚠️ **不要用无头**：CNKI 官方 MCP 项目也注明「无头会触发额外安全验证」。

【用法】
    python cnlit_search.py vip "M=屏状核"
    python cnlit_search.py vip --query 'M=(屏状核) AND M=(氯氮平 OR 抗精神病)' -o out.json
    python cnlit_search.py vip "M=屏状核" --pages 3 --pagesize 50
    python cnlit_search.py vip "M=屏状核" --dump      # 存 HTML 看结构

【⭐ 维普检索语法 —— 字段前缀不能省】
    U=  任意字段   ｜ M=  题名或关键词 ｜ T=  题名 ｜ K=  关键词
    A=  作者       ｜ R=  摘要

【🔴 维普的四个问题（全部实测复现，2026-09-22）】

  ① **裸词静默失效**（最常见）
     `key=屏状核`（无前缀）→ 返回**与检索词完全无关的通用最新列表**，不报错。
     实测：裸词 → 0 篇相关；`U=屏状核` → 124 篇；`M=屏状核` → 31 篇。
     → 字段前缀不能省。**静默返回无关结果比报错更危险。**

  ② **检索式含空格 → WAF 403**
     `M=(屏状核) AND M=(氯氮平)` → 403 Forbidden（空格被拦）。
     去掉空格能通过，但会掉进 ③。

  ③ **复合式解析错误 → 静默假阳性**（最危险）
     `M=(屏状核)AND M=(氯氮平)` 虽通过，但命中 3 条**全部不含「屏状核」**——
     实际匹配的是关键词里的字面「M胆碱受体」。
     **UI 搜索框提交同一式子，得到同样的 3 条假阳性** → 是维普布尔解析器
     不认 `M=` 前缀，不是 URL 编码问题。
     → ⭐ **结论：维普的 URL/搜索框布尔检索式不可用。**
       正确做法 = **单概念式全量取回（`M=屏状核`）→ 本地筛查求交**，
       并在文档里写明「本轮只查了 X 库、Y 字段」。
     → ⭐ **纪律：「不报错」不等于「检索式生效」。任何检索式都要配对照组**
       （单概念命中数）验证它确实被解析了。

  ④ **翻页只能点击，URL 参数无效**
     `&page=2` / `&p=2` **都返回第 1 页**。本脚本改用点击 `.layui-laypage-next`。
     先用 `--pagesize 50` 把页数压到最少，能少发请求就少发。

【结果质量提醒】
    中文库噪声大：科普、新闻、社会新闻、同栏目重复著录都会进结果。
    实测某轮 31 条里 4 条为科普/新闻、5 条为同一文字重复著录 → **真正研究性文献约 20 篇**。

【⭐ 质量过滤：用维普自己的「期刊级别」，不要外挂期刊名单】
    维普结果页左侧自带一组收录/级别筛选项，每个链接带计数，本脚本默认打印：
        核心刊 / 普通刊           ← 综合二分，最实用
        bdhx      北大核心期刊
        zgkjhx    中国科技核心期刊
        cscd      中国科学引文数据库
        scopus / rccse / jst / cas / ic / pubmed
    加 `--core` 只保留核心刊（剔除科普与大众刊物）。

    ⚠️ **不要去找一份外挂的中文期刊分级表**：实测拿过 gleaner 的
       `cnki_journal_tiers.json`（340 种）与 `intl_journal_tiers.json`（96 种），
       两者都是**经管/人文**学科定向的（国际表 meta 明写 `ASJC(14/20)` = 商业管理+经济金融），
       **与中文医学期刊 0 交集**（本项目的 22 种刊均不在表里）。
       维普自带的分级反而覆盖完整、且与记录同源。

    ⚠️ 与翻页同理：筛选项**只能点击**，URL 加 `&QK=bdhx` **无效**。

【依赖】
    venv：见文末「环境现状」——**原 `<旧机器路径>` 是老机器路径，本机不存在**
    DrissionPage **必须 ≥5.0.0b1**（4.1.1.4 与 Chrome 153 的 WebSocket 握手 404）

【环境现状（2026-09-24 换机后）】
    · 浏览器路径改为**运行时探测**（`_find_browser()`），可用环境变量 `BROWSER_PATH` 覆盖
      —— 老机器 Chrome 在**用户级** `AppData\\Local`，本机在**系统级** `Program Files`，写死必挂
    · profile 根改为 `~/.cdp_profiles/<name>`（`_profile()`），随用户目录走
    · venv 与知网 cookie 均需在本机重建
      详见 `科研/_系统/迁移检查_新机器产出物同步核对_20260924.md` 及其「盘符语义更正」节
"""
import argparse
import io
import json
import os
import re
import sys
import time
from urllib.parse import quote

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from DrissionPage import Chromium, ChromiumOptions

# ── 环境 ──────────────────────────────────────────────
# ── 2026-09-24 路径修正：跨机器探测，勿写死用户名/盘符 ──────────
def _find_browser():
    """按序探测浏览器；可用环境变量 BROWSER_PATH 覆盖。"""
    for _p in (os.environ.get("BROWSER_PATH"),
               os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Google\Chrome\Application\chrome.exe"),
               r"C:\Program Files\Google\Chrome\Application\chrome.exe",
               r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
               r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
               r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"):
        if _p and os.path.isfile(_p):
            return _p
    raise FileNotFoundError("未找到 Chrome/Edge；可设环境变量 BROWSER_PATH")


def _profile(_name):
    """持久 profile 根：~/.cdp_profiles/<name>"""
    return os.path.join(os.path.expanduser("~"), ".cdp_profiles", _name)
# ────────────────────────────────────────────────────────────

CHROME = _find_browser()
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

# ⭐ 固定 profile，**不要删**：冷 profile 必被拦（实测 403）。
#    `cnki` 是已用热的 profile（73MB）；换新 profile 需先手动开一次目标站点。
PROFILE = os.environ.get("CNLIT_PROFILE", _profile("cnki"))
PORT = int(os.environ.get("CNLIT_PORT", "9430"))

SITES = {
    'vip': {
        'name': '维普',
        'url': 'https://qikan.cqvip.com/Qikan/Search/Index?key={q}',
        'home': 'https://www.cqvip.com/',
    },
    'cnki': {
        'name': '中国知网',
        'url': 'https://kns.cnki.net/kns8s/defaultresult/index',
        'home': 'https://www.cnki.net/',
        # ⚠️ 知网是 UI 驱动（AJAX 不改 URL），见 search_cnki()
        'ui': True,
    },
    'wanfang': {
        'name': '万方',
        'url': 'https://s.wanfangdata.com.cn/paper?q={q}',
        'home': 'https://www.wanfangdata.com.cn/',
    },
}


def make_browser(attach=None):
    """attach=<端口> 时接管一个**已打开的**浏览器（不新建、退出时也不关它）。
    用途：CNKI 的人工验证会话——人工过一次滑块后，接管同一个浏览器。"""
    if attach:
        return Chromium(f'127.0.0.1:{attach}')
    co = ChromiumOptions()
    co.set_browser_path(CHROME if os.path.exists(CHROME) else EDGE)
    co.set_local_port(PORT)
    co.set_user_data_path(PROFILE)
    co.set_argument('--disable-blink-features=AutomationControlled')
    co.set_argument('--no-first-run')
    co.set_argument('--no-default-browser-check')
    co.set_argument('--window-size=1500,950')
    # ⚠️ 不加 --headless
    return Chromium(co)


# ── 维普解析 ──────────────────────────────────────────
# 一条结果 = 一个 <dl>，含 <dt>标题链接 + <dd>作者/刊名/卷期 + <dd>摘要 + <dd>关键词
# ⚠️ 每条在 DOM 里**出现两次**（响应式双份），必须按 article id 去重
DL_RE = re.compile(r'<dl\b[^>]*>(.*?)</dl>', re.S)
TITLE_RE = re.compile(
    r'<dt>.*?href="/Qikan/Article/Detail\?id=(\d+)[^"]*"[^>]*>(.*?)</a>', re.S)
TOTAL_RE = re.compile(r'hidShowTotalCount"[^>]*value="(\d+)"')
FROM_RE = re.compile(r'class="from">(.*?)</span>\s*<span class="vol">(.*?)</span>', re.S)
ABSTRACT_RE = re.compile(r'class="abstract">(.*?)</span>\s*</span>', re.S)
SUBJECT_RE = re.compile(r'class="subject">(.*?)</span>\s*</dd>', re.S)
TAG_TITLE_RE = re.compile(r'title="([^"]*)"')


def _txt(s):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', s or '')).strip()


def parse_vip(html):
    out, seen = [], set()
    for seg in DL_RE.findall(html):
        m = TITLE_RE.search(seg)
        if not m:
            continue
        aid, title = m.group(1), _txt(m.group(2))
        if not title or aid in seen:
            continue
        seen.add(aid)

        rec = {'id': aid, 'title': title,
               'url': f'https://qikan.cqvip.com/Qikan/Article/Detail?id={aid}'}

        # 作者：<span class="author"> 下的全部 <a title="姓名">
        a = re.search(r'class="author">(.*?)</span>\s*(?:<span class="from">|</dd>)', seg, re.S)
        if a:
            rec['authors'] = TAG_TITLE_RE.findall(a.group(1))

        # 刊名 + 卷期页码
        f = FROM_RE.search(seg)
        if f:
            rec['source'] = TAG_TITLE_RE.findall(f.group(1))[:1]
            rec['source'] = rec['source'][0] if rec['source'] else _txt(f.group(1))
            rec['vol'] = _txt(f.group(2))

        # 摘要：同一 dd 内有两个 span（截断版 + display:none 全文），取较长者
        ab = ABSTRACT_RE.search(seg)
        if ab:
            cands = [_txt(x) for x in re.findall(r'<span[^>]*>(.*?)</span>', ab.group(1), re.S)]
            cands = [c for c in cands if len(c) > 20]
            if cands:
                rec['abstract'] = max(cands, key=len)

        # 关键词
        s = SUBJECT_RE.search(seg)
        if s:
            rec['keywords'] = TAG_TITLE_RE.findall(s.group(1))

        # 年份（从卷期串里取）
        y = re.search(r'(19|20)\d{2}', rec.get('vol', ''))
        if y:
            rec['year'] = y.group(0)

        out.append(rec)
    return out


def count_hits_vip(html):
    m = TOTAL_RE.search(html)
    return m.group(1) if m else None


# ── 知网解析 ────────────────────────────────────────────
# ⚠️ 知网是 **UI 驱动**：检索走 AJAX（POST /kns8s/brief/grid），URL 不变。
#    所以必须先 #txt_search 输入 + 回车，再读 DOM。
#    行结构（kns8s 新版，2026-09 实测）：
#      <tr><td class="seq">…<td class="name"><a href="…/kcms2/article/abstract?v=…">题名</a>
#          <td class="author"><a>作者</a>;…<td class="source"><p><a>刊名</a></p>
#          <td class="date">2026-09-05 11:31<td class="data"><span>期刊</span>
#          <td class="quote">被引<td class="download"><a class="downloadCnt">29</a>
CNKI_TOTAL_RE = re.compile(r'共找到\s*</span>\s*<em>([\d,]+)</em>')
CNKI_PAGE_RE = re.compile(r'countPageMark"[^>]*data-pagenum="(\d+)"')
CNKI_TR_RE = re.compile(r'<tr\b.*?</tr>', re.S)
# ⚠️ 题名单元格有**两种写法**（2026-09 实测，漏了会静默丢 1/3 结果）：
#     A 期刊行：<td class="name"><a class="fz14 inline" target="_blank" href="…">
#     B 报纸/会议行：<td class="name"><div><div><a class="fz14 inline" href="…">
#   故必须容忍中间的 <div> 包裹，且不能假定 href/target 的先后顺序。
CNKI_NAME_RE = re.compile(
    r'<td class="name">\s*(?:<div[^>]*>\s*)*<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', re.S)
CNKI_AUTH_RE = re.compile(r'<td class="author">(.*?)</td>', re.S)
CNKI_SRC_RE = re.compile(r'<td class="source">.*?</?p?>\s*<a[^>]*>(.*?)</a>', re.S)
CNKI_DATE_RE = re.compile(r'<td class="date">(.*?)</td>', re.S)
CNKI_DB_RE = re.compile(r'<td class="data">.*?<span>(.*?)</span>', re.S)
CNKI_CITE_RE = re.compile(r'<td class="quote">(.*?)</td>', re.S)
CNKI_DL_RE = re.compile(r'<td class="download">.*?<a[^>]*>([\d]*)</a>', re.S)
CNKI_A_RE = re.compile(r'<a[^>]*>(.*?)</a>', re.S)


def count_hits_cnki(html):
    m = CNKI_TOTAL_RE.search(html)
    return m.group(1) if m else None


def parse_cnki(html):
    """从知网结果页提取条目（按 detail URL 去重）"""
    out, seen = [], set()
    for tr in CNKI_TR_RE.findall(html):
        m = CNKI_NAME_RE.search(tr)
        if not m:
            continue
        url, title = m.group(1), _txt(m.group(2))
        if not title or url in seen:
            continue
        seen.add(url)

        rec = {'title': title, 'url': url}
        a = CNKI_AUTH_RE.search(tr)
        if a:
            rec['authors'] = [_txt(x) for x in CNKI_A_RE.findall(a.group(1))]
        s = CNKI_SRC_RE.search(tr)
        if s:
            rec['source'] = _txt(s.group(1))
        d = CNKI_DATE_RE.search(tr)
        if d:
            rec['date'] = _txt(d.group(1))
            y = re.search(r'(19|20)\d{2}', rec['date'])
            if y:
                rec['year'] = y.group(0)
        db = CNKI_DB_RE.search(tr)
        if db:
            rec['dbtype'] = _txt(db.group(1))
        c = CNKI_CITE_RE.search(tr)
        if c and _txt(c.group(1)):
            rec['cited'] = _txt(c.group(1))
        dl = CNKI_DL_RE.search(tr)
        if dl and _txt(dl.group(1)):
            rec['download'] = _txt(dl.group(1))
        if 'marktip' in tr:
            rec['note'] = '网络首发'
        out.append(rec)
    return out


# ── 维普「期刊级别」facet ────────────────────────────────
# 结果页左侧带一组期刊收录/级别筛选项，每个链接自带计数：
#   <a data-search="QK=bdhx#北大核心期刊" title="北大核心期刊">…<tt>14</tt></a>
# ⭐ 这是**维普自己的分级**，与记录同源、覆盖它全部收录，
#   比外挂一份期刊名单更好（外挂名单往往只覆盖某几个学科）。
# ⚠️ 代码含义（2026-09-22 实测反解）：
#     bdhx    北大核心期刊      zgkjhx  中国科技核心期刊
#     cscd    中国科学引文数据库  scopus  Scopus
#     rccse   武大RCCSE核心期刊   pubmed  生物医学检索系统(PubMed)
#     jst     日本科技振兴机构    cas     化学文摘  ic  哥白尼索引
#     核心刊 / 普通刊            综合二分（最实用的一档）
FACET_RE = re.compile(
    r'data-search="QK=([^#"&]+)#([^"]*)"[^>]*>(?:<i[^>]*></i>)?([^<]*)<tt>(\d+)</tt>')


def parse_tiers(html):
    """返回 [(代码, 中文标签, 命中数), …]，按命中数降序"""
    out, seen = [], set()
    for m in FACET_RE.finditer(html):
        code, title, text, n = m.group(1), m.group(2), m.group(3).strip(), int(m.group(4))
        if code in seen:
            continue
        seen.add(code)
        out.append((code, title or text, n))
    return sorted(out, key=lambda x: -x[2])


# ── 知网检索（UI 驱动）──────────────────────────────────
def run_cnki(tab, q, a, site):
    """知网必须走 UI：#txt_search 输入 → 回车 → 读 DOM → 点 #Page_next_top 翻页。

    ⚠️ 首次使用要先过「安全验证」（滑块）。做法：
        ① 跑 `_work/cnki_launch.py` 起一个带调试端口的有头浏览器
        ② 人工拖滑块过关
        ③ 再用本脚本 `--attach <端口>` 接管（cookie 已在 profile 里）
    """
    print('  知网为 UI 驱动，正在打开检索页 …')
    tab.get(site['url']); tab.wait(7)

    if 'verify' in (tab.url or '') or '安全验证' in (tab.title or ''):
        print('  ❌ 仍在「安全验证」页。请先人工过一次滑块：')
        print('     1) 运行 _work/cnki_launch.py 起浏览器')
        print('     2) 拖滑块过关')
        print('     3) 本脚本加 --attach <端口> 重跑')
        return 4

    box = None
    for sel in ('css:#txt_search', 'css:input[id*=search]', 'css:input[placeholder*=检索]'):
        try:
            e = tab.ele(sel, timeout=3)
        except Exception:
            e = None
        if e:
            box = e
            break
    if not box:
        print('  ❌ 未找到检索框（#txt_search）——知网可能改版，用 --dump 看结构')
        return 5

    print(f'  输入「{q}」→ 回车')
    box.clear()
    try:
        box.click()
    except Exception:
        pass
    box.input(q); tab.wait(1)
    box.input('\n')                      # ⚠️ 回车提交；点「检索」按钮行为不同
    tab.wait(11)

    html = tab.html or ''
    total = count_hits_cnki(html)
    print(f'  命中：{total or "未解析到"} 条')
    open(os.path.abspath(f'_cnlit_dump_cnki.html'), 'w', encoding='utf-8').write(html)

    # 调到每页 50，减少翻页
    if a.pagesize == 50:
        try:
            tab.ele('css:#perPageDiv', timeout=3).click(); tab.wait(2)
            el = tab.ele('css:#perPageDiv li[data-val="50"]', timeout=3)
            if el:
                el.click(); tab.wait(9)
                html = tab.html or ''
                total = count_hits_cnki(html)
                print(f'  已切到每页 50 条（命中 {total}）')
        except Exception:
            print('  （每页 50 条切换失败，按 20 条/页继续）')

    recs = parse_cnki(html)
    print(f'  第 1 页解析 {len(recs)} 条')

    for pg in range(2, a.pages + 1):
        nxt = None
        try:
            nxt = tab.ele('css:#Page_next_top', timeout=3)
        except Exception:
            nxt = None
        if not nxt:
            print(f'  已是最后一页（共 {pg-1} 页）')
            break
        time.sleep(a.sleep)
        try:
            nxt.click()
        except Exception as e:
            print(f'  翻页失败：{type(e).__name__}')
            break
        tab.wait(10)
        batch = parse_cnki(tab.html or '')
        print(f'  第 {pg} 页解析 {len(batch)} 条')
        if not batch:
            break
        recs += batch

    seen, uniq = set(), []
    for r in recs:
        if r['url'] not in seen:
            seen.add(r['url']); uniq.append(r)

    print(f'\n✅ 共 {len(uniq)} 条（去重后；库里标称 {total or "?"} 条）')
    for r in uniq[:20]:
        print(f'  · [{r.get("year","----")}] {r["title"][:58]}  —— {r.get("source","")[:20]}')
    if len(uniq) > 20:
        print(f'  … 其余 {len(uniq)-20} 条见输出文件')

    if a.out:
        json.dump({'site': 'cnki', 'query': q, 'total': total, 'records': uniq},
                  open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print(f'\n已写 {a.out}')
    return 0


# ── 主流程 ────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description='中文文献库检索（维普/万方）')
    ap.add_argument('site', choices=list(SITES), help='检索哪个库')
    ap.add_argument('query', nargs='?', help='检索词 / 检索式（维普记得带 U= / M= 前缀）')
    ap.add_argument('--query', dest='q2', help='同上（长检索式用这个）')
    ap.add_argument('-o', '--out', help='结果写入 JSON')
    ap.add_argument('--pages', type=int, default=2, help='最多翻几页（默认 2）')
    ap.add_argument('--pagesize', type=int, default=50, choices=[20, 50],
                    help='每页条数（默认 50，能少发请求）')
    ap.add_argument('--sleep', type=float, default=4.0, help='翻页间隔秒（默认 4，别调太小）')
    ap.add_argument('--core', nargs='?', const='bdhx', default=None, metavar='CODE',
                    help='只保留核心刊（默认 bdhx=北大核心；可给 zgkjhx=中国科技核心、'
                         'cscd、scopus、rccse、pubmed 等，见 --list-tiers）')
    ap.add_argument('--list-tiers', action='store_true',
                    help='只打印期刊级别分布后退出（不落盘）')
    ap.add_argument('--dump', action='store_true', help='把首页 HTML 存下来看结构')
    ap.add_argument('--force', action='store_true',
                    help='跳过布尔检索式的拦截（⚠️ 结果不可信，除非你已自行核对）')
    ap.add_argument('--attach', type=int, metavar='PORT',
                    help='接管已打开的浏览器（如 CNKI 人工验证过的实例），不新建也不关闭')
    a = ap.parse_args()

    q = a.q2 or a.query
    if not q:
        print('❌ 需要检索词，例：cnlit_search.py vip "M=屏状核"'); return 1
    site = SITES[a.site]

    print(f'▶ {site["name"]} 检索：{q}')
    print(f'  profile {PROFILE}')

    # ── 检索式体检（维普特有的两种静默失效，必须拦在最前面）──
    if a.site == 'vip':
        if not re.match(r'\s*[UMTKAR]\s*=', q):
            print('  ⚠️ 检索式没有字段前缀（U=/M=/T=/K=/A=/R=）。')
            print('     维普会**静默忽略检索词**、返回无关的通用列表——不报错，但结果无关。')
        if re.search(r'\b(AND|OR|NOT)\b', q, re.I) and not a.force:
            print('\n⛔ 已拦截：维普的布尔检索式**解析不可靠**，会静默返回假阳性。')
            print('   实测：`M=(屏状核)AND M=(氯氮平)` 命中 3 条，**全部不含「屏状核」**——')
            print('   实际匹配的是关键词里的字面「M胆碱受体」。UI 搜索框同样如此。')
            print('\n   ✅ 正确做法：**单概念式全量取回 → 本地筛查求交**。')
            print('      例：cnlit_search.py vip "M=屏状核" --pagesize 50 -o a.json')
            print('          再对 a.json 的 title/abstract/keywords 做本地关键词筛查。')
            print('\n   确认要强行执行请加 --force（结果须逐条人工核对）。')
            return 3

    browser = None
    try:
        browser = make_browser(a.attach)
        tab = browser.latest_tab

        # ── 知网：UI 驱动（AJAX 检索，URL 不变；且必须先过安全验证）──
        if site.get('ui'):
            return run_cnki(tab, q, a, site)

        # ⭐ 预热
        print(f'  预热 {site["home"]}')
        tab.get(site['home']); tab.wait(4)

        # 首页
        url = site['url'].format(q=quote(q))
        print(f'  → {url[:100]}')
        tab.get(url); tab.wait(9)
        html = tab.html or ''
        if len(html) < 3000:
            print(f'  ❌ 页面异常（{len(html)} 字符）——多半被拦。检查 profile 是否固定。')
            return 2

        total = count_hits_vip(html) if a.site == 'vip' else None
        print(f'  命中：{total or "未解析到"} 篇')

        if a.dump:
            p = os.path.abspath(f'_cnlit_dump_{a.site}.html')
            open(p, 'w', encoding='utf-8').write(html)
            print(f'  HTML 已存 {p}（{len(html)//1024} KB）')

        # ⭐ 期刊级别分布（维普自带分级，用于质量过滤）
        tiers = []
        if a.site == 'vip':
            tiers = parse_tiers(html)
            if tiers:
                print('  期刊级别分布：')
                for code, label, n in tiers:
                    print(f'      {label:<24} {n:>4}   [{code}]')
            else:
                print('  ⚠️ 未解析到期刊级别 facet（维普可能改版，用 --dump 看结构）')

        if a.list_tiers:
            return 0

        # --core：只保留核心刊（⚠️ 与翻页一样，只能点，URL 加 &QK= 无效）
        if a.site == 'vip' and a.core:
            el = None
            try:
                el = tab.ele(f'css:a[data-search^="QK={a.core}"]', timeout=4)
            except Exception:
                el = None
            if not el:
                print(f'  ⚠️ 未找到「{a.core}」筛选项，未筛选（用 --list-tiers 看可用代码）')
            else:
                print(f'  → 筛选「{el.attr("title") or el.text.strip()[:14]}」')
                el.click(); tab.wait(9)
                html = tab.html or ''
                total = count_hits_vip(html)
                print(f'  筛选后命中：{total} 篇')

        # 调每页条数（维普：点 .page-view 里的 data-count）
        if a.site == 'vip' and a.pagesize != 20:
            try:
                el = tab.ele(f'css:.page-view a[data-count="{a.pagesize}"]', timeout=3)
                if el:
                    el.click(); tab.wait(8)
                    html = tab.html or ''
                    print(f'  已切到每页 {a.pagesize} 条')
            except Exception:
                pass

        recs = parse_vip(html) if a.site == 'vip' else []
        print(f'  第 1 页解析 {len(recs)} 条')

        # ⚠️ 翻页只能点：URL 加 &page=N 无效（实测返回第 1 页）
        for pg in range(2, a.pages + 1):
            nxt = None
            try:
                nxt = tab.ele('css:a.layui-laypage-next', timeout=3)
            except Exception:
                pass
            if not nxt:
                print(f'  已是最后一页（共 {pg-1} 页）')
                break
            time.sleep(a.sleep)
            try:
                nxt.click()
            except Exception as e:
                print(f'  翻页失败：{type(e).__name__}'); break
            tab.wait(9)
            batch = parse_vip(tab.html or '')
            print(f'  第 {pg} 页解析 {len(batch)} 条')
            if not batch:
                break
            recs += batch

        # 全局去重（跨页防重）
        seen, uniq = set(), []
        for r in recs:
            if r['id'] not in seen:
                seen.add(r['id']); uniq.append(r)

        print(f'\n✅ 共 {len(uniq)} 条（去重后；库里标称 {total or "?"} 篇）')
        for r in uniq[:20]:
            src = r.get('source', '')
            src = src[0] if isinstance(src, list) else src
            print(f'  · [{r.get("year","----")}] {r["title"][:62]}  —— {src[:22]}')
        if len(uniq) > 20:
            print(f'  … 其余 {len(uniq)-20} 条见输出文件')

        if a.out:
            json.dump({'site': a.site, 'query': q, 'total': total,
                       'core_only': a.core,
                       'tiers': [{'code': c, 'label': l, 'count': n} for c, l, n in tiers],
                       'records': uniq},
                      open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
            print(f'\n已写 {a.out}')
        return 0
    finally:
        # ⚠️ --attach 时**绝不能 quit()**——浏览器是用户手动验证过的，关掉就得重新过验证
        if a.attach:
            print('（--attach 模式：浏览器保持打开）')
        else:
            try:
                if browser:
                    browser.quit()
            except Exception:
                pass


if __name__ == '__main__':
    sys.exit(main())
