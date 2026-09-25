"""`skillgate check-stale`: is the latest receipt still about the skill as it is now?

A receipt describes one skill version, one set of reference files, one
executor and one judge. It goes STALE when any of these changes: the skill
file, a reference file, the executor or judge model ID or settings in
skillgate.yaml, a Skill Gate prompt, the ratified criteria, or the golden
cases. Exit code 1 on STALE, so CI or a scheduled job can act on it.
"""

from __future__ import annotations

from pathlib import Path

from skillgate.config import Config
from skillgate.prompts import PROMPTS_DIR
from skillgate.run import config_models
from skillgate.util import SkillGateError, read_json, rel, sha256_file


def latest_receipt(cfg: Config) -> Path:
    receipts = sorted(cfg.paths["receipts"].glob("*/receipt.json"),
                      key=lambda p: (read_json(p).get("generated_at", ""), p.parent.name))
    if not receipts:
        raise SkillGateError(f"No receipts in {cfg.paths['receipts']}. Issue one with `skillgate receipt`.")
    return receipts[-1]


def check_stale(cfg: Config, receipt_path: Path | None = None) -> tuple[list[str], Path]:
    receipt_path = Path(receipt_path) if receipt_path else latest_receipt(cfg)
    r = read_json(receipt_path)
    root = cfg.root
    changes: list[str] = []

    if sha256_file(cfg.skill_path) != r["skill"]["sha256"]:
        changes.append(f"skill: {rel(cfg.skill_path, root)} changed")
    now_refs = {rel(p, root): sha256_file(p) for p in cfg.reference_paths}
    then_refs = {x["path"]: x["sha256"] for x in r["references"]}
    for path in sorted(set(now_refs) | set(then_refs)):
        if path not in then_refs:
            changes.append(f"reference added: {path}")
        elif path not in now_refs:
            changes.append(f"reference removed: {path}")
        elif now_refs[path] != then_refs[path]:
            changes.append(f"reference changed: {path}")

    now_models = config_models(cfg)
    then_models = r.get("config_models", {})
    for role in ("executor", "judge"):
        now, then = now_models.get(role), then_models.get(role)
        if (now or {}).get("model") != (then or {}).get("model"):
            changes.append(f"{role} model: {(then or {}).get('model')} → {(now or {}).get('model')}")
        elif (now or {}).get("settings") != (then or {}).get("settings"):
            changes.append(f"{role} settings changed")

    for name, h in r.get("prompts", {}).items():
        p = PROMPTS_DIR / f"{name}.md"
        if not p.is_file() or sha256_file(p) != h:
            changes.append(f"prompt {name} changed")

    crit = root / r["criteria"]["path"]
    if not crit.is_file() or sha256_file(crit) != r["criteria"]["sha256"]:
        changes.append("criteria.yaml changed")

    then_cases = {m["path"]: m["sha256"] for m in r["manifest"] if m["role"] == "case"}
    now_cases = {rel(p, root): sha256_file(p) for p in sorted(cfg.paths["cases"].glob("*.yaml"))}
    if then_cases != now_cases:
        added = sorted(set(now_cases) - set(then_cases))
        removed = sorted(set(then_cases) - set(now_cases))
        edited = sorted(p for p in set(now_cases) & set(then_cases) if now_cases[p] != then_cases[p])
        parts = [f"{len(x)} {label}" for x, label in ((added, "added"), (removed, "removed"), (edited, "edited")) if x]
        changes.append("golden cases changed: " + ", ".join(parts))
    return changes, receipt_path
