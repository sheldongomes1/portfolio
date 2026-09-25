"""skillgate.yaml: paths, model IDs and settings, repeats, thresholds, budget and pricing."""

from __future__ import annotations

import glob
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from skillgate.util import SkillGateError, read_yaml, sha256_file

CONFIG_NAME = "skillgate.yaml"

# Claude aliases that point at a dated snapshot. A receipt must name the exact
# version, so these are rejected with the full ID to use instead. Source: the
# Claude API model catalog (current models such as claude-opus-5 have no
# separate dated ID; the ID itself is the exact version).
CLAUDE_ALIASES = {
    "claude-haiku-4-5": "claude-haiku-4-5-20251001",
    "claude-opus-4-5": "claude-opus-4-5-20251101",
    "claude-opus-4-1": "claude-opus-4-1-20250805",
    "claude-sonnet-4-5": "claude-sonnet-4-5-20250929",
    "claude-sonnet-4-0": "claude-sonnet-4-20250514",
    "claude-opus-4-0": "claude-opus-4-20250514",
}

DEFAULT_THRESHOLDS = {
    "min_cases_warn": 12,
    "min_cases_verified": 10,
    "edge_share": 0.30,
    "holdout_share": 0.30,
    "calibration_agreement": 0.90,
    "calibration_min_sample": 30,
}

DEFAULT_ESTIMATE = {
    "chars_per_token": 4,          # rough token count without calling an API
    "executor_output_tokens": 2000,  # assumed per executor call (answer plus any thinking)
    "judge_output_tokens": 1500,   # assumed per judge call (thinking plus the JSON verdict)
    "margin": 1.25,                # multiplier on the total, for re-asks and estimation error
}

DEFAULT_PATHS = {
    "cases": "golden/cases",
    "golden": "golden/golden.yaml",
    "criteria": "golden/criteria.yaml",
    "runs": "runs",
    "receipts": "receipts",
    "reports": "reports",
    "cache": ".skillgate/cache",
    "calibration": "calibration",
}


def validate_model_id(model: Any, where: str) -> str:
    """Reject empty IDs and floating aliases: a receipt must name an exact model version."""
    if not isinstance(model, str) or not model.strip():
        raise SkillGateError(f"{where}: a model ID is required")
    model = model.strip()
    if re.search(r"(^|[-_.@])latest($|[-_.@])", model) or model.endswith("latest"):
        raise SkillGateError(
            f"{where}: '{model}' is a floating alias. Use an exact model version so the receipt "
            "names what actually ran."
        )
    if model in CLAUDE_ALIASES:
        raise SkillGateError(
            f"{where}: '{model}' is an alias for a dated snapshot. Use '{CLAUDE_ALIASES[model]}'."
        )
    return model


@dataclass
class ModelConfig:
    provider: str
    model: str
    settings: dict[str, Any] = field(default_factory=dict)
    max_retries: int = 4
    timeout_seconds: float = 120.0
    concurrency: int = 4


@dataclass
class Config:
    path: Path
    root: Path
    raw: dict[str, Any]
    skill_name: str | None
    skill_path: Path
    reference_paths: list[Path]
    paths: dict[str, Path]
    judge: ModelConfig
    executor: ModelConfig | None
    repeats: int
    thresholds: dict[str, float]
    budget: dict[str, Any]
    pricing: dict[str, dict[str, float]]
    estimate: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_ESTIMATE))

    @property
    def sha256(self) -> str:
        return sha256_file(self.path)

    def price(self, model: str, input_tokens: int, output_tokens: int) -> float | None:
        p = self.pricing.get(model)
        if not p:
            return None
        return round(
            input_tokens / 1e6 * float(p["input_per_mtok"])
            + output_tokens / 1e6 * float(p["output_per_mtok"]),
            6,
        )


def find_config(start: Path | None = None) -> Path:
    here = Path(start or Path.cwd()).resolve()
    for d in [here, *here.parents]:
        candidate = d / CONFIG_NAME
        if candidate.is_file():
            return candidate
    raise SkillGateError(
        f"No {CONFIG_NAME} found in {here} or its parents. Copy skillgate.yaml.example to start."
    )


def _model_config(raw: Any, where: str, *, default_provider: str) -> ModelConfig:
    if not isinstance(raw, dict):
        raise SkillGateError(f"{where}: expected a mapping")
    return ModelConfig(
        provider=str(raw.get("provider", default_provider)),
        model=validate_model_id(raw.get("model"), f"{where}.model"),
        settings=dict(raw.get("settings") or {}),
        max_retries=int(raw.get("max_retries", 4)),
        timeout_seconds=float(raw.get("timeout_seconds", 120)),
        concurrency=max(1, int(raw.get("concurrency", 4))),
    )


def load_config(path: Path | None = None) -> Config:
    path = Path(path).resolve() if path else find_config()
    if not path.is_file():
        raise SkillGateError(f"Config file not found: {path}")
    raw = read_yaml(path) or {}
    root = path.parent

    skill = raw.get("skill") or {}
    if not skill.get("path"):
        raise SkillGateError(f"{path}: skill.path is required")
    skill_path = (root / skill["path"]).resolve()

    refs: list[Path] = []
    for pattern in skill.get("references") or []:
        matches = sorted(glob.glob(str(root / pattern), recursive=True))
        if not matches:
            raise SkillGateError(f"{path}: reference pattern '{pattern}' matches no files")
        refs.extend(Path(m).resolve() for m in matches)

    paths = {k: (root / v).resolve() for k, v in {**DEFAULT_PATHS, **(raw.get("paths") or {})}.items()}

    if "judge" not in raw:
        raise SkillGateError(f"{path}: a judge section is required")
    judge = _model_config(raw["judge"], "judge", default_provider="anthropic")
    if judge.provider != "anthropic":
        raise SkillGateError("judge.provider: only 'anthropic' is supported")
    executor = None
    if raw.get("executor"):
        executor = _model_config(raw["executor"], "executor", default_provider="gemini")
        if executor.provider != "gemini":
            raise SkillGateError("executor.provider: only 'gemini' is supported")

    repeats = int(raw.get("repeats", 3))
    if repeats < 1:
        raise SkillGateError("repeats must be at least 1")

    return Config(
        path=path,
        root=root,
        raw=raw,
        skill_name=skill.get("name"),
        skill_path=skill_path,
        reference_paths=refs,
        paths=paths,
        judge=judge,
        executor=executor,
        repeats=repeats,
        thresholds={**DEFAULT_THRESHOLDS, **(raw.get("thresholds") or {})},
        budget=dict(raw.get("budget") or {}),
        pricing={k: dict(v) for k, v in (raw.get("pricing") or {}).items()},
        estimate={**DEFAULT_ESTIMATE, **(raw.get("estimate") or {})},
    )
