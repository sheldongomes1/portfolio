"""Golden cases: one YAML file per case, plus golden.yaml recording how splits were drawn.

Splits are never chosen by hand. Each draw records its seed and pool, so
anyone can recompute it; a case whose split disagrees with the recorded draws
blocks VERIFIED.
"""

from __future__ import annotations

import math
import random
import re
import secrets
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from skillgate.checks import validate_check
from skillgate.util import SkillGateError, dump_yaml, iso, read_yaml, sha256_file, utc_now

ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
KINDS = ("detect", "no_flag", "other")
EDGE_TAGS = ("edge", "should_not_flag")


@dataclass
class Expectation:
    id: str
    text: str
    kind: str = "other"
    traces_to: list[str] = field(default_factory=list)
    check: dict[str, Any] | None = None


@dataclass
class Case:
    id: str
    path: Path
    sha256: str
    input_text: str
    input_files: list[str]
    expectations: list[Expectation]
    tags: list[str]
    split: str | None
    source: str
    confirmed_by: str | None
    confirmed_at: str | None
    notes: str | None = None

    @property
    def is_edge(self) -> bool:
        return any(t in EDGE_TAGS for t in self.tags)

    def rendered_input(self, root: Path) -> str:
        """The exact text given to the skill: the case text, then each input file."""
        parts = [self.input_text.rstrip()] if self.input_text.strip() else []
        for rel_path in self.input_files:
            p = (root / rel_path).resolve()
            if not p.is_file():
                raise SkillGateError(f"case {self.id}: input file not found: {rel_path}")
            parts.append(f"--- {Path(rel_path).name} ---\n{p.read_text(encoding='utf-8').rstrip()}")
        return "\n\n".join(parts) + "\n"

    def input_file_hashes(self, root: Path) -> dict[str, str]:
        return {f: sha256_file(root / f) for f in self.input_files}


def _parse_case(path: Path, data: Any) -> Case:
    where = str(path)
    if not isinstance(data, dict):
        raise SkillGateError(f"{where}: expected a mapping")
    cid = str(data.get("id", ""))
    if not ID_RE.match(cid):
        raise SkillGateError(f"{where}: id '{cid}' must be letters, digits, '.', '_' or '-'")
    if path.stem != cid:
        raise SkillGateError(f"{where}: file name must be {cid}.yaml")
    inp = data.get("input") or {}
    if isinstance(inp, str):
        inp = {"text": inp}
    text = str(inp.get("text") or "")
    files = [str(f) for f in inp.get("files") or []]
    if not text.strip() and not files:
        raise SkillGateError(f"{where}: input.text or input.files is required")

    exps = []
    raw_exps = data.get("expectations") or []
    if not raw_exps:
        raise SkillGateError(f"{where}: at least one expectation is required")
    for n, e in enumerate(raw_exps, 1):
        if isinstance(e, str):
            e = {"text": e}
        eid = str(e.get("id") or f"E{n}")
        etext = str(e.get("text") or "").strip()
        if not etext:
            raise SkillGateError(f"{where}: expectation {eid} has no text")
        if len(etext) > 2 and etext[0] == etext[-1] == '"':
            raise SkillGateError(
                f"{where}: expectation {eid} looks like expected output text. Write a binary "
                "statement about the output instead (for example 'Flags INV-1042 as a duplicate')."
            )
        kind = str(e.get("kind", "other"))
        if kind not in KINDS:
            raise SkillGateError(f"{where}: expectation {eid} kind must be one of {', '.join(KINDS)}")
        check = e.get("check")
        if check is not None:
            validate_check(check, f"{where}: expectation {eid}")
        exps.append(Expectation(eid, etext, kind, [str(t) for t in e.get("traces_to") or []], check))
    ids = [e.id for e in exps]
    if len(set(ids)) != len(ids):
        raise SkillGateError(f"{where}: expectation ids must be unique")

    split = data.get("split")
    if split not in (None, "dev", "holdout"):
        raise SkillGateError(f"{where}: split must be dev or holdout")
    source = str(data.get("source", "expert"))
    if source not in ("expert", "generated"):
        raise SkillGateError(f"{where}: source must be expert or generated")
    confirmed_at = data.get("confirmed_at")
    return Case(
        id=cid,
        path=path,
        sha256=sha256_file(path) if path.exists() else "",
        input_text=text,
        input_files=files,
        expectations=exps,
        tags=[str(t) for t in data.get("tags") or []],
        split=split,
        source=source,
        confirmed_by=data.get("confirmed_by") or None,
        confirmed_at=str(confirmed_at) if confirmed_at else None,
        notes=data.get("notes"),
    )


def load_cases(cases_dir: Path, *, require_ready: bool = False) -> list[Case]:
    cases_dir = Path(cases_dir)
    if not cases_dir.is_dir():
        raise SkillGateError(f"Cases directory not found: {cases_dir}")
    cases = [_parse_case(p, read_yaml(p)) for p in sorted(cases_dir.glob("*.yaml"))]
    if not cases:
        raise SkillGateError(f"No case files in {cases_dir}")
    if require_ready:
        problems = []
        for c in cases:
            if c.source == "generated" and not (c.confirmed_by and c.confirmed_at):
                problems.append(f"{c.id}: generated case not confirmed by the expert (confirmed_by, confirmed_at)")
            if c.split is None:
                problems.append(f"{c.id}: no split assigned (run `skillgate interview --import` or `skillgate split`)")
        if problems:
            raise SkillGateError("Cases are not ready:\n  " + "\n  ".join(problems))
    return cases


def golden_stats(cases: list[Case], thresholds: dict[str, float]) -> dict[str, Any]:
    n = len(cases)
    tags: dict[str, int] = {}
    for c in cases:
        for t in c.tags:
            tags[t] = tags.get(t, 0) + 1
    edge = sum(1 for c in cases if c.is_edge)
    splits = {s: sum(1 for c in cases if c.split == s) for s in ("dev", "holdout")}
    warnings, blockers = [], []
    if n < thresholds["min_cases_warn"]:
        warnings.append(f"{n} cases; at least {int(thresholds['min_cases_warn'])} are recommended")
    if n < thresholds["min_cases_verified"]:
        blockers.append(f"{n} cases; VERIFIED requires at least {int(thresholds['min_cases_verified'])}")
    if edge < math.ceil(thresholds["edge_share"] * n):
        msg = f"{edge} of {n} cases tagged edge or should_not_flag; at least {math.ceil(thresholds['edge_share'] * n)} required"
        warnings.append(msg)
        blockers.append(msg)
    if splits["holdout"] < math.ceil(thresholds["holdout_share"] * n):
        blockers.append(
            f"{splits['holdout']} of {n} cases in holdout; at least {math.ceil(thresholds['holdout_share'] * n)} required"
        )
    for c in cases:
        if "should_not_flag" in c.tags and not any(e.kind == "no_flag" for e in c.expectations):
            warnings.append(f"{c.id}: tagged should_not_flag but has no no_flag expectation")
    return {
        "size": n,
        "tags": dict(sorted(tags.items())),
        "edge_or_should_not_flag": edge,
        "splits": splits,
        "sources": {s: sum(1 for c in cases if c.source == s) for s in ("expert", "generated")},
        "warnings": warnings,
        "blockers": blockers,
    }


def load_golden(path: Path) -> dict[str, Any]:
    if not Path(path).is_file():
        return {"schema_version": 1, "draws": []}
    return read_yaml(path) or {"schema_version": 1, "draws": []}


def draw_holdout(seed: int, pool: list[str], k: int) -> list[str]:
    return sorted(random.Random(seed).sample(sorted(pool), k))


def assign_splits(cases_dir: Path, golden_path: Path, share: float, seed: int | None = None) -> dict[str, Any] | None:
    """Draw splits for cases that have none. Returns the draw, or None if nothing was new."""
    cases = load_cases(cases_dir)
    new = [c for c in cases if c.split is None]
    if not new:
        return None
    current_holdout = sum(1 for c in cases if c.split == "holdout")
    need = math.ceil(share * len(cases)) - current_holdout
    k = min(len(new), max(math.ceil(share * len(new)), need))
    seed = secrets.randbelow(2**32) if seed is None else int(seed)
    pool = sorted(c.id for c in new)
    holdout = draw_holdout(seed, pool, k)
    draw = {"drawn_at": iso(utc_now()), "seed": seed, "pool": pool, "holdout_count": k, "holdout": holdout}
    for c in new:
        data = read_yaml(c.path)
        data["split"] = "holdout" if c.id in holdout else "dev"
        c.path.write_text(dump_yaml(data), encoding="utf-8")
    golden = load_golden(golden_path)
    golden.setdefault("schema_version", 1)
    golden["holdout_share"] = share
    golden.setdefault("draws", []).append(draw)
    Path(golden_path).parent.mkdir(parents=True, exist_ok=True)
    Path(golden_path).write_text(dump_yaml(golden), encoding="utf-8")
    return draw


def verify_splits(cases: list[Case], golden: dict[str, Any]) -> list[str]:
    """Recompute every recorded draw from its seed and compare with the case files."""
    problems = []
    pooled: dict[str, str] = {}
    for d in golden.get("draws", []):
        expected = draw_holdout(int(d["seed"]), list(d["pool"]), int(d["holdout_count"]))
        if expected != sorted(d["holdout"]):
            problems.append(f"draw with seed {d['seed']}: recorded holdout does not match the seed")
        for cid in d["pool"]:
            if cid in pooled:
                problems.append(f"{cid}: appears in more than one draw")
            pooled[cid] = "holdout" if cid in expected else "dev"
    for c in cases:
        if c.id not in pooled:
            problems.append(f"{c.id}: split not drawn by Skill Gate (not in golden.yaml)")
        elif c.split != pooled[c.id]:
            problems.append(f"{c.id}: split is '{c.split}' but the recorded draw says '{pooled[c.id]}'")
    return problems
