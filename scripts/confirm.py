#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""confirm.py —— 网页点选收集输入，结果写成 JSON。

【用途】
    开工前把「用户说不清、但有穷举可能」的输入一次问完。
    表单只收事实与选项；需要判断的部分仍回对话。

【用法】
    python scripts/confirm.py --spec spec.json --out answers.json [--port 0] [--timeout 900]

    起服务后打印地址（含随机 token），用户提交即写 `answers.json` 并关服。
    超时则不写文件、关服退出，调用方回落到对话提问。

【spec 格式】
    {
      "title": "页标题",
      "intro": "一句话说明",
      "questions": [
        {"id": "occasion", "type": "radio", "label": "场合", "required": true,
         "options": [{"value": "组会汇报", "hint": "每周例会"}]},
        {"id": "audience", "type": "multi", "label": "听众", "options": [...]},
        {"id": "notes", "type": "text", "label": "其他要求", "placeholder": "可留空"}
      ]
    }

    题型三种：`radio` / `multi` / `text`。`required` 为真时，未答不能提交。

【退出码】
    0 已提交 · 2 超时未提交 · 3 spec 或端口有问题

【边界】
    · 只绑 127.0.0.1；地址带一次性随机 token，缺 token 返回 403
    · 不做鉴权、不存历史、不联网
    · 请求体必须是 UTF-8 的 JSON
"""
from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PAGE = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<style>
:root{--ink:#1b1b1f;--mute:#6b6b76;--line:#e3e3e8;--accent:#2c5fd4;--bg:#f6f7f9}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
 font:15px/1.6 -apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif}
.wrap{max-width:760px;margin:0 auto;padding:32px 20px 96px}
h1{font-size:22px;margin:0 0 6px}
.intro{color:var(--mute);margin:0 0 28px}
.q{background:#fff;border:1px solid var(--line);border-radius:12px;padding:18px 18px 14px;margin:0 0 14px}
.q h2{font-size:15px;margin:0 0 10px;font-weight:600}
.opts{display:grid;gap:8px}
label.opt{display:flex;gap:10px;align-items:flex-start;padding:10px 12px;border:1px solid var(--line);
 border-radius:9px;cursor:pointer;transition:.12s}
label.opt:hover{border-color:#c3cee6}
label.opt input{margin:3px 0 0}
label.opt.sel{border-color:var(--accent);background:#f3f6ff}
.val{font-weight:500}
.hint{color:var(--mute);font-size:13px;margin-top:2px}
input[type=text]{width:100%;padding:9px 11px;border:1px solid var(--line);border-radius:9px;font:inherit}
.bar{position:fixed;left:0;right:0;bottom:0;background:#fff;border-top:1px solid var(--line);
 padding:12px 20px;display:flex;gap:12px;align-items:center;justify-content:center}
button{background:var(--accent);color:#fff;border:0;border-radius:9px;padding:11px 26px;
 font:inherit;font-weight:600;cursor:pointer}
button:disabled{opacity:.45;cursor:default}
.ok{color:#1a7f4b;font-weight:600}
</style></head>
<body><div class="wrap">
<h1>__TITLE__</h1><p class="intro">__INTRO__</p>
<div id="qs"></div>
</div>
<div class="bar"><span id="msg"></span><button id="go">提交</button></div>
<script>
const SPEC = __SPEC__;
const ANS = {};
const box = document.getElementById('qs');
SPEC.questions.forEach(function(q){
  const d = document.createElement('div'); d.className='q';
  const h = document.createElement('h2'); h.textContent = q.label; d.appendChild(h);
  if (q.type === 'text') {
    const t = document.createElement('input');
    t.type = 'text'; t.placeholder = q.placeholder || '';
    ANS[q.id] = '';
    t.addEventListener('input', function(){ ANS[q.id] = t.value; });
    d.appendChild(t);
  } else {
    const wrap = document.createElement('div'); wrap.className='opts';
    q.options.forEach(function(o){
      const l = document.createElement('label'); l.className='opt';
      const i = document.createElement('input');
      i.type = q.type === 'multi' ? 'checkbox' : 'radio';
      i.name = q.id; i.value = o.value;
      i.addEventListener('change', function(){
        if (q.type === 'multi') {
          ANS[q.id] = Array.from(document.querySelectorAll('input[name="'+q.id+'"]:checked')).map(x=>x.value);
          i.parentElement.classList.toggle('sel', i.checked);
        } else {
          ANS[q.id] = o.value;
          Array.from(document.querySelectorAll('input[name="'+q.id+'"]')).forEach(function(x){
            x.parentElement.classList.toggle('sel', x.checked);
          });
        }
        refresh();
      });
      const col = document.createElement('div');
      const v = document.createElement('div'); v.className='val'; v.textContent = o.value;
      col.appendChild(v);
      if (o.hint) { const hh = document.createElement('div'); hh.className='hint'; hh.textContent = o.hint; col.appendChild(hh); }
      l.appendChild(i); l.appendChild(col); wrap.appendChild(l);
    });
    d.appendChild(wrap);
  }
  box.appendChild(d);
});
function missing(){
  return SPEC.questions.filter(function(q){
    if (!q.required) return false;
    const v = ANS[q.id];
    return v === undefined || v === '' || (Array.isArray(v) && v.length === 0);
  }).map(function(q){ return q.label; });
}
function refresh(){
  const m = missing();
  document.getElementById('go').disabled = m.length > 0;
  document.getElementById('msg').textContent = m.length ? ('还差：' + m.join('、')) : '';
}
document.getElementById('go').addEventListener('click', function(){
  if (missing().length) return;
  fetch('/submit', {method:'POST', headers:{'Content-Type':'application/json; charset=utf-8'},
    body: JSON.stringify({k: new URLSearchParams(location.search).get('k'), answers: ANS})})
   .then(function(r){ return r.json(); })
   .then(function(){
     document.querySelector('.wrap').innerHTML =
       '<h1>已提交</h1><p class="intro ok">回到对话即可，我会接着做。</p>';
     document.getElementById('go').disabled = true;
     document.getElementById('msg').textContent = '';
   });
});
refresh();
</script></body></html>"""


def validate(spec) -> str | None:
    """返回错误说明；通过则返回 None。"""
    if not isinstance(spec, dict):
        return "spec 必须是对象"
    if not isinstance(spec.get("questions"), list) or not spec["questions"]:
        return "spec 缺 questions"
    ids = set()
    for q in spec["questions"]:
        for key in ("id", "type", "label"):
            if key not in q:
                return f"问题缺 {key}：{q}"
        if q["id"] in ids:
            return f"问题 id 重复：{q['id']}"
        ids.add(q["id"])
        if q["type"] not in ("radio", "multi", "text"):
            return f"未知题型 {q['type']}（{q['id']}）"
        if q["type"] in ("radio", "multi"):
            if not isinstance(q.get("options"), list) or not q["options"]:
                return f"{q['id']} 缺 options"
            for o in q["options"]:
                if "value" not in o:
                    return f"{q['id']} 的选项缺 value"
    return None


class ConfirmServer:
    """一次确认会话：一个 spec，一份答案。"""

    def __init__(self, spec: dict, out: str, port: int = 0):
        self.spec = spec
        self.out = os.path.abspath(out)
        self.token = secrets.token_urlsafe(12)
        self.done = threading.Event()
        self.httpd = ThreadingHTTPServer(("127.0.0.1", port), _handler_for(self))
        self._thread = None

    @property
    def port(self) -> int:
        return self.httpd.server_address[1]

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}/?k={self.token}"

    def start(self) -> None:
        self._thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self._thread.start()

    def wait(self, timeout: float) -> bool:
        return self.done.wait(timeout=timeout)

    def shutdown(self) -> None:
        self.httpd.shutdown()


def _handler_for(srv: ConfirmServer):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, code, body, ctype="text/html; charset=utf-8"):
            data = body.encode("utf-8") if isinstance(body, str) else body
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            u = urlparse(self.path)
            if u.path != "/":
                return self._send(404, "not found", "text/plain; charset=utf-8")
            if parse_qs(u.query).get("k", [""])[0] != srv.token:
                return self._send(403, "token 不对", "text/plain; charset=utf-8")
            page = (PAGE
                    .replace("__TITLE__", srv.spec.get("title", "确认"))
                    .replace("__INTRO__", srv.spec.get("intro", ""))
                    .replace("__SPEC__", json.dumps(srv.spec, ensure_ascii=False)))
            self._send(200, page)

        def do_POST(self):
            if urlparse(self.path).path != "/submit":
                return self._send(404, "not found", "text/plain; charset=utf-8")
            n = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(n) or b"{}"
            try:
                payload = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                return self._send(400, "bad json（请求体必须是 UTF-8）",
                                  "text/plain; charset=utf-8")
            if payload.get("k") != srv.token:
                return self._send(403, "token 不对", "text/plain; charset=utf-8")
            answers = payload.get("answers", {})
            out = {q["id"]: answers.get(q["id"]) for q in srv.spec["questions"]}
            with open(srv.out, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=2)
            self._send(200, '{"ok":true}', "application/json")
            srv.done.set()

    return Handler


def main() -> int:
    ap = argparse.ArgumentParser(description="网页点选收集输入，结果写 JSON")
    ap.add_argument("--spec", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--port", type=int, default=0, help="默认 0 = 由系统分配")
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--no-browser", action="store_true")
    a = ap.parse_args()

    with open(a.spec, encoding="utf-8") as f:
        spec = json.load(f)
    err = validate(spec)
    if err:
        print(f"[错误] {err}")
        return 3

    try:
        srv = ConfirmServer(spec, a.out, a.port)
    except OSError as e:
        print(f"[错误] 端口 {a.port} 起不来：{e}")
        return 3

    srv.start()
    print(f"[confirm] 打开：{srv.url}")
    print(f"[confirm] 结果写入：{srv.out}")
    sys.stdout.flush()
    if not a.no_browser:
        try:
            webbrowser.open(srv.url)
        except Exception:
            pass

    ok = srv.wait(a.timeout)
    srv.shutdown()
    if ok:
        print("[confirm] 已提交")
        return 0
    print(f"[confirm] 超时 {a.timeout}s，未提交")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
