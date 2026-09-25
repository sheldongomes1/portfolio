"""The executor for `run --mode api`: runs the skill on a case through the Gemini API.

This emulates a Workspace skill; it is not one. The skill text and its reference
files become the system instruction (assembled by prompts/executor.v1.md) and
the case input is the user message. Every receipt from API mode says so.

- Requires GEMINI_API_KEY; never switches to another model or provider.
- Before a paid run, `describe()` asks the API for the configured model, so a
  mistyped or retired model ID fails before anything is spent, and the model's
  reported version is recorded.
- Every sampling setting is passed explicitly and recorded.
- API failures after the SDK's retries, blocked prompts and blocked answers
  raise ExecutorError; the judge records those repeats as ERROR.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Protocol

from skillgate.config import ModelConfig
from skillgate.prompts import load_prompt
from skillgate.skill import Document, Skill
from skillgate.util import SkillGateError

EXECUTOR_PROMPT = "executor.v1"

# Settings passed through to the Gemini API as generation config.
SAMPLING_KEYS = ("temperature", "top_p", "top_k", "max_output_tokens", "seed", "candidate_count",
                 "presence_penalty", "frequency_penalty", "stop_sequences")

# Finish reasons that mean the model produced its answer (possibly cut short), not a block.
COMPLETED = {"STOP", "MAX_TOKENS", "FINISH_REASON_UNSPECIFIED", None}


class ExecutorError(Exception):
    """The skill could not be run for this repeat. Recorded as ERROR."""


@dataclass
class ExecResult:
    text: str
    served_model: str | None
    finish_reason: str | None
    input_tokens: int
    output_tokens: int
    thinking_tokens: int


class Executor(Protocol):
    model: str
    settings: dict[str, Any]

    def describe(self) -> dict[str, Any]: ...

    def run(self, *, system: str, user: str) -> ExecResult: ...


def assemble(skill: Skill, references: list[Document], case_input: str) -> tuple[str, str, str]:
    """Return (system, user, prompt_sha256) exactly as sent to the executor."""
    prompt = load_prompt(EXECUTOR_PROMPT)
    refs = "\n\n".join(f"## Reference file: {r.title}\n\n{r.text.rstrip()}" for r in references)
    system, user = prompt.render(SKILL=skill.text.rstrip(), REFERENCES=refs or "(no reference files)",
                                 INPUT=case_input.rstrip())
    return system, user, prompt.sha256


class GeminiExecutor:
    def __init__(self, cfg: ModelConfig):
        key = os.environ.get("GEMINI_API_KEY")
        if not key:
            raise SkillGateError(
                "GEMINI_API_KEY is not set. API mode runs the skill on Gemini. Export the key "
                "(for example from a .env file you do not commit) and run it again. Skill Gate never "
                "switches to another model or provider when a key is missing."
            )
        from google import genai  # imported here so tests and offline commands never need it
        from google.genai import errors, types

        self._types = types
        self._errors = errors
        self.model = cfg.model
        self.settings = dict(cfg.settings)
        unknown = sorted(set(self.settings) - set(SAMPLING_KEYS))
        if unknown:
            raise SkillGateError(f"executor.settings: unsupported key(s) {', '.join(unknown)}; "
                                 f"supported: {', '.join(SAMPLING_KEYS)}")
        retry = types.HttpRetryOptions(attempts=cfg.max_retries + 1)
        self._client = genai.Client(
            api_key=key,
            http_options=types.HttpOptions(timeout=int(cfg.timeout_seconds * 1000), retry_options=retry),
        )

    def describe(self) -> dict[str, Any]:
        try:
            m = self._client.models.get(model=self.model)
        except self._errors.APIError as e:
            raise SkillGateError(f"executor model '{self.model}' could not be found: {e}") from e
        return {"name": m.name, "version": m.version, "display_name": m.display_name}

    def run(self, *, system: str, user: str) -> ExecResult:
        import httpx

        config = self._types.GenerateContentConfig(system_instruction=system, **self.settings)
        try:
            resp = self._client.models.generate_content(model=self.model, contents=user, config=config)
        except self._errors.APIError as e:
            raise ExecutorError(f"API error {e.code}: {e.message}") from e
        except httpx.HTTPError as e:
            raise ExecutorError(f"connection error: {e}") from e
        feedback = getattr(resp, "prompt_feedback", None)
        if feedback is not None and getattr(feedback, "block_reason", None):
            raise ExecutorError(f"prompt blocked: {feedback.block_reason}")
        finish = None
        if resp.candidates:
            fr = resp.candidates[0].finish_reason
            finish = getattr(fr, "value", fr)
        if finish not in COMPLETED:
            raise ExecutorError(f"answer not completed: finish_reason {finish}")
        usage = resp.usage_metadata
        return ExecResult(
            text=resp.text or "",
            served_model=resp.model_version,
            finish_reason=finish,
            input_tokens=(usage.prompt_token_count or 0) if usage else 0,
            output_tokens=(usage.candidates_token_count or 0) if usage else 0,
            thinking_tokens=(usage.thoughts_token_count or 0) if usage else 0,
        )


def make_executor(cfg: ModelConfig | None) -> Executor:
    if cfg is None:
        raise SkillGateError("API mode needs an executor section in skillgate.yaml")
    if cfg.provider != "gemini":
        raise SkillGateError(f"executor provider '{cfg.provider}' is not supported")
    return GeminiExecutor(cfg)
