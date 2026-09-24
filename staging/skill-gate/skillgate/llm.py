"""The model client used by lint, criteria drafting and the judge.

One narrow interface, `complete_json`, so tests substitute a fake and no unit
test ever calls a real API. The Anthropic client:

- requires ANTHROPIC_API_KEY and fails with a clear message when it is missing;
- never falls back to another model (no server-side fallbacks): a refusal, a
  truncated answer or an API failure raises LLMError, which callers record as
  ERROR, never as PASS or FAIL;
- retries connection errors, 408/409/429 and 5xx with the SDK's own
  exponential backoff (`max_retries` in skillgate.yaml);
- reports the model that actually served each call, so a receipt can show it.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Protocol

from skillgate.config import ModelConfig
from skillgate.util import SkillGateError


class LLMError(Exception):
    """A call that could not be completed. Recorded as ERROR."""


@dataclass
class LLMResult:
    data: dict[str, Any]
    served_model: str
    input_tokens: int
    output_tokens: int
    request_id: str | None = None


class JSONModel(Protocol):
    model: str
    settings: dict[str, Any]

    def complete_json(self, *, system: str, user: str, schema: dict[str, Any]) -> LLMResult: ...


def require_key(var: str = "ANTHROPIC_API_KEY") -> None:
    if not os.environ.get(var):
        raise SkillGateError(
            f"{var} is not set. This step calls the model API. Export the key "
            f"(for example from a .env file you do not commit) and run it again. "
            f"Skill Gate never switches to another model or provider when a key is missing."
        )


class AnthropicJSONModel:
    def __init__(self, cfg: ModelConfig):
        require_key()
        import anthropic  # imported here so tests and offline commands never need it

        self._anthropic = anthropic
        self.model = cfg.model
        self.settings = dict(cfg.settings)
        self._max_tokens = int(self.settings.get("max_tokens", 16000))
        self._client = anthropic.Anthropic(max_retries=cfg.max_retries, timeout=cfg.timeout_seconds)

    def complete_json(self, *, system: str, user: str, schema: dict[str, Any]) -> LLMResult:
        a = self._anthropic
        output_config: dict[str, Any] = {"format": {"type": "json_schema", "schema": schema}}
        if self.settings.get("effort"):
            output_config["effort"] = self.settings["effort"]
        try:
            resp = self._client.messages.create(
                model=self.model,
                max_tokens=self._max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
                output_config=output_config,
            )
        except a.APIStatusError as e:
            raise LLMError(f"API error {e.status_code}: {e.message}") from e
        except a.APIConnectionError as e:
            raise LLMError(f"connection error: {e}") from e
        if resp.stop_reason == "refusal":
            category = getattr(getattr(resp, "stop_details", None), "category", None)
            raise LLMError(f"model declined the request (refusal, category={category})")
        if resp.stop_reason == "max_tokens":
            raise LLMError("answer truncated at max_tokens")
        text = next((b.text for b in resp.content if b.type == "text"), None)
        if text is None:
            raise LLMError("no text block in the response")
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise LLMError(f"response was not valid JSON: {e}") from e
        return LLMResult(
            data=data,
            served_model=resp.model,
            input_tokens=resp.usage.input_tokens,
            output_tokens=resp.usage.output_tokens,
            request_id=getattr(resp, "_request_id", None),
        )


def make_model(cfg: ModelConfig) -> JSONModel:
    if cfg.provider != "anthropic":
        raise SkillGateError(f"provider '{cfg.provider}' is not supported for this step")
    return AnthropicJSONModel(cfg)
