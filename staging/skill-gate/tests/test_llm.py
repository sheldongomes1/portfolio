"""The Anthropic wrapper, with the SDK call stubbed: no network."""

from types import SimpleNamespace

import pytest

from skillgate.config import ModelConfig
from skillgate.llm import AnthropicJSONModel, LLMError
from skillgate.util import SkillGateError

CFG = ModelConfig(provider="anthropic", model="claude-opus-5", settings={"effort": "high", "max_tokens": 1000})


def _model(monkeypatch, create):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    m = AnthropicJSONModel(CFG)
    monkeypatch.setattr(m._client.messages, "create", create)
    return m


def _resp(text='{"verdict": "PASS", "reason": "r", "evidence": "e"}', stop="end_turn", model="claude-opus-5"):
    return SimpleNamespace(stop_reason=stop, stop_details=None, model=model,
                           content=[SimpleNamespace(type="text", text=text)],
                           usage=SimpleNamespace(input_tokens=10, output_tokens=5))


def test_missing_key_is_a_clear_error(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(SkillGateError, match="ANTHROPIC_API_KEY is not set"):
        AnthropicJSONModel(CFG)


def test_request_shape_and_result(monkeypatch):
    seen = {}

    def create(**kw):
        seen.update(kw)
        return _resp(model="claude-opus-5")

    r = _model(monkeypatch, create).complete_json(system="s", user="u", schema={"type": "object"})
    assert r.data["verdict"] == "PASS" and r.served_model == "claude-opus-5" and r.input_tokens == 10
    assert seen["model"] == "claude-opus-5" and seen["max_tokens"] == 1000
    assert seen["output_config"] == {"format": {"type": "json_schema", "schema": {"type": "object"}}, "effort": "high"}
    assert "fallbacks" not in seen  # never a silent switch to another model


def test_connection_error_becomes_llm_error(monkeypatch):
    import anthropic
    import httpx2

    def create(**kw):
        raise anthropic.APIConnectionError(request=httpx2.Request("POST", "https://api.anthropic.com/v1/messages"))

    with pytest.raises(LLMError, match="connection error"):
        _model(monkeypatch, create).complete_json(system="s", user="u", schema={})


@pytest.mark.parametrize("stop,match", [("refusal", "declined"), ("max_tokens", "truncated")])
def test_refusal_and_truncation_become_llm_error(monkeypatch, stop, match):
    with pytest.raises(LLMError, match=match):
        _model(monkeypatch, lambda **kw: _resp(stop=stop)).complete_json(system="s", user="u", schema={})


def test_malformed_json_becomes_llm_error(monkeypatch):
    with pytest.raises(LLMError, match="not valid JSON"):
        _model(monkeypatch, lambda **kw: _resp(text="PASS!")).complete_json(system="s", user="u", schema={})
