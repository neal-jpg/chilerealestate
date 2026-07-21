import json

import pytest

from routine.model import (
    build_request, parse_response, make_model_call, make_cli_call,
    resolve_model_call,
)


def test_parse_response_joins_text_blocks():
    payload = {"content": [{"type": "text", "text": "["},
                           {"type": "text", "text": "]"}]}
    assert parse_response(payload) == "[]"


def test_parse_response_ignores_non_text_and_empty():
    assert parse_response({}) == ""
    assert parse_response({"content": [{"type": "tool_use", "id": "x"}]}) == ""
    assert parse_response({"content": None}) == ""


def test_build_request_sets_headers_and_body():
    req = build_request("hi there", "sk-test", model="claude-sonnet-5")
    assert req.method == "POST"
    assert req.full_url.endswith("/v1/messages")
    # urllib capitalizes header keys (x-api-key -> X-api-key).
    assert req.get_header("X-api-key") == "sk-test"
    assert req.get_header("Anthropic-version") == "2023-06-01"
    body = json.loads(req.data.decode("utf-8"))
    assert body["model"] == "claude-sonnet-5"
    assert body["messages"][0]["content"] == "hi there"


class _FakeResp:
    def __init__(self, text):
        self._t = text.encode("utf-8")

    def read(self):
        return self._t

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_make_model_call_uses_opener_and_parses_reply():
    captured = {}

    def opener(req, timeout=None):
        captured["req"] = req
        return _FakeResp(json.dumps({"content": [{"type": "text", "text": "[]"}]}))

    mc = make_model_call(api_key="sk-x", model="claude-sonnet-5", opener=opener)
    assert mc("extract please") == "[]"
    assert captured["req"].get_header("X-api-key") == "sk-x"


def test_make_model_call_requires_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        make_model_call(api_key=None)


class _FakeRun:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_make_cli_call_returns_stdout():
    captured = {}

    def runner(cmd, **kwargs):
        captured["cmd"] = cmd
        return _FakeRun(stdout="[]")

    mc = make_cli_call(runner=runner)
    assert mc("extract this") == "[]"
    assert captured["cmd"] == ["claude", "-p", "extract this"]


def test_make_cli_call_raises_on_failure():
    mc = make_cli_call(runner=lambda cmd, **k: _FakeRun(returncode=1, stderr="boom"))
    with pytest.raises(RuntimeError):
        mc("extract this")


def test_resolve_model_call_prefers_cli():
    mc = resolve_model_call(which=lambda b: "/usr/bin/claude", env={})
    assert mc is not None


def test_resolve_model_call_falls_back_to_api_key():
    mc = resolve_model_call(which=lambda b: None, env={"ANTHROPIC_API_KEY": "sk-x"})
    assert mc is not None


def test_resolve_model_call_none_when_nothing_available():
    assert resolve_model_call(which=lambda b: None, env={}) is None
