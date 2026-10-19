# -*- coding: utf-8 -*-
"""confirm.py：spec 校验、token 门禁、提交落盘。"""
import json
import urllib.error
import urllib.parse
import urllib.request

import pytest

import confirm

SPEC = {
    "title": "测试",
    "intro": "说明",
    "questions": [
        {"id": "a", "type": "radio", "label": "A", "required": True,
         "options": [{"value": "x"}, {"value": "y"}]},
        {"id": "b", "type": "multi", "label": "B",
         "options": [{"value": "p"}, {"value": "q"}]},
        {"id": "c", "type": "text", "label": "C"},
    ],
}


@pytest.fixture()
def srv(tmp_path):
    s = confirm.ConfirmServer(SPEC, tmp_path / "ans.json", 0)
    s.start()
    yield s
    s.shutdown()


def test_validate_ok():
    assert confirm.validate(SPEC) is None


def test_validate_missing_questions():
    assert "questions" in confirm.validate({})


def test_validate_unknown_type():
    bad = {"questions": [{"id": "a", "type": "slider", "label": "A"}]}
    assert "未知题型" in confirm.validate(bad)


def test_validate_duplicate_id():
    bad = {"questions": [
        {"id": "a", "type": "text", "label": "A"},
        {"id": "a", "type": "text", "label": "B"},
    ]}
    assert "重复" in confirm.validate(bad)


def test_page_requires_token(srv):
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(f"http://127.0.0.1:{srv.port}/?k=wrong")
    assert e.value.code == 403


def test_page_renders(srv):
    body = urllib.request.urlopen(srv.url).read().decode("utf-8")
    assert "测试" in body and "提交" in body


def test_submit_writes_answers(srv, tmp_path):
    payload = json.dumps({"k": srv.token,
                          "answers": {"a": "x", "b": ["p", "q"], "c": "hi"}},
                         ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(f"http://127.0.0.1:{srv.port}/submit",
                                 data=payload,
                                 headers={"Content-Type": "application/json"})
    assert json.loads(urllib.request.urlopen(req).read())["ok"] is True
    assert srv.wait(5)
    ans = json.loads((tmp_path / "ans.json").read_text(encoding="utf-8"))
    assert ans == {"a": "x", "b": ["p", "q"], "c": "hi"}


def test_submit_rejects_bad_token(srv):
    payload = json.dumps({"k": "nope", "answers": {}}).encode("utf-8")
    req = urllib.request.Request(f"http://127.0.0.1:{srv.port}/submit",
                                 data=payload,
                                 headers={"Content-Type": "application/json"})
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(req)
    assert e.value.code == 403


def test_submit_rejects_non_utf8(srv):
    req = urllib.request.Request(f"http://127.0.0.1:{srv.port}/submit",
                                 data=b'{"k": "x", "answers": {"a": "\xff\xfe"}}',
                                 headers={"Content-Type": "application/json"})
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(req)
    assert e.value.code == 400


# ── 原料上传 ──────────────────────────────────────────────

def _upload(srv, name, data):
    req = urllib.request.Request(
        f"http://127.0.0.1:{srv.port}/upload", data=data,
        headers={"X-Filename": urllib.parse.quote(name)},
        method="POST")
    return urllib.request.urlopen(req)


@pytest.fixture()
def srv_in(tmp_path):
    s = confirm.ConfirmServer(SPEC, tmp_path / "ans.json", 0, tmp_path / "原料")
    s.start()
    yield s
    s.shutdown()


def test_upload_creates_dir_and_file(srv_in, tmp_path):
    resp = json.loads(_upload(srv_in, "内容稿.md", "正文".encode("utf-8")).read())
    assert resp["saved"] == "内容稿.md"
    p = tmp_path / "原料" / "内容稿.md"
    assert p.read_text(encoding="utf-8") == "正文"


def test_upload_dedupes_names(srv_in):
    _upload(srv_in, "a.txt", b"1")
    r2 = json.loads(_upload(srv_in, "a.txt", b"2").read())
    assert r2["saved"] == "a-1.txt"


def test_upload_strips_paths(srv_in, tmp_path):
    r = json.loads(_upload(srv_in, "../../evil.txt", b"x").read())
    assert "/" not in r["saved"] and ".." not in r["saved"]
    assert not (tmp_path / "evil.txt").exists()
    assert (tmp_path / "原料" / "evil.txt").exists()


def test_upload_rejects_oversize(srv_in, monkeypatch):
    monkeypatch.setattr(confirm, "MAX_BYTES", 4)
    with pytest.raises(urllib.error.HTTPError) as e:
        _upload(srv_in, "big.bin", b"12345")
    assert e.value.code == 413


def test_delete_removes_file(srv_in, tmp_path):
    _upload(srv_in, "x.txt", b"1")
    payload = json.dumps({"k": srv_in.token, "name": "x.txt"}).encode("utf-8")
    req = urllib.request.Request(f"http://127.0.0.1:{srv_in.port}/delete",
                                 data=payload,
                                 headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req)
    assert not (tmp_path / "原料" / "x.txt").exists()


def test_submit_writes_manifest(srv_in, tmp_path):
    _upload(srv_in, "b.png", b"png")
    payload = json.dumps({"k": srv_in.token, "answers": {"a": "x"}}).encode("utf-8")
    req = urllib.request.Request(f"http://127.0.0.1:{srv_in.port}/submit",
                                 data=payload,
                                 headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req)
    assert srv_in.wait(5)
    manifest = json.loads((tmp_path / "原料" / confirm.MANIFEST).read_text(encoding="utf-8"))
    assert [m["name"] for m in manifest] == ["b.png"]


def test_files_lists_uploads(srv_in):
    _upload(srv_in, "c.txt", b"123")
    body = urllib.request.urlopen(
        f"http://127.0.0.1:{srv_in.port}/files?k={srv_in.token}").read()
    files = json.loads(body)
    assert [f["name"] for f in files] == ["c.txt"]
    assert files[0]["size"] == 3


def test_files_requires_token(srv_in):
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(f"http://127.0.0.1:{srv_in.port}/files")
    assert e.value.code == 403
