# -*- coding: utf-8 -*-
"""confirm.py：spec 校验、token 门禁、提交落盘。"""
import json
import urllib.error
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
