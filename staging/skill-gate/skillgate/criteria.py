"""`skillgate criteria`: general binary criteria, human ratification, and coverage.

- Criteria apply to every case. Expectations are case-specific and live on the case.
- `criteria.proposed.yaml` is a draft. Only `criteria.yaml`, edited and saved by a
  person, is used downstream, and only after `--ratify` records who ratified it,
  when, and the file's SHA-256. Editing it afterwards invalidates the ratification.
- `coverage.md` maps the skill's rules to the checks that trace to them. Rules with
  no check are listed as uncovered; the receipt reports the count.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from skillgate.cases import Case
from skillgate.checks import validate_check
from skillgate.llm import JSONModel, LLMError
from skillgate.prompts import load_prompt
from skillgate.skill import Rule, Skill
from skillgate.util import SkillGateError, dump_yaml, iso, read_json, read_yaml, sha256_file, utc_now, write_json

PARTIAL_CREDIT = re.compile(
    r"\b(partially|partly|mostly|somewhat|score|scored|rating|scale|out of \d+|\d+\s*[-/]\s*\d+ points?|percent)\b",
    re.I,
)


@dataclass
class Criterion:
    id: str
    text: str
    traces_to: list[str]
    check: dict[str, Any] | None = None
    warnings: list[str] = field(default_factory=list)


def ratification_path(criteria_path: Path) -> Path:
    return Path(criteria_path).with_name(Path(criteria_path).stem + ".ratification.json")


def load_criteria(path: Path) -> list[Criterion]:
    path = Path(path)
    if not path.is_file():
        raise SkillGateError(
            f"{path} not found. Run `skillgate criteria` to draft criteria.proposed.yaml, "
            "edit it, save it as criteria.yaml, then ratify it."
        )
    data = read_yaml(path) or {}
    raw = data.get("criteria") if isinstance(data, dict) else None
    if not isinstance(raw, list) or not raw:
        raise SkillGateError(f"{path}: expected a non-empty 'criteria' list")
    out, ids = [], set()
    for c in raw:
        cid = str(c.get("id", "")).strip()
        text = str(c.get("text", "")).strip()
        where = f"{path}: criterion {cid or '?'}"
        if not cid or cid in ids:
            raise SkillGateError(f"{where}: ids must be present and unique")
        ids.add(cid)
        if not text:
            raise SkillGateError(f"{where}: text is required")
        if PARTIAL_CREDIT.search(text):
            raise SkillGateError(f"{where}: allows partial credit ('{PARTIAL_CREDIT.search(text).group(0)}'); a criterion is PASS or FAIL")
        traces = [str(t) for t in c.get("traces_to") or []]
        if not traces:
            raise SkillGateError(f"{where}: traces_to must name at least one rule key from coverage.md")
        if c.get("check") is not None:
            validate_check(c["check"], where)
        warnings = []
        if re.search(r"\b(and|or)\b", text, re.I) and not c.get("check"):
            warnings.append(f"{cid}: 'and'/'or' may mean two properties in one criterion; split it if so")
        out.append(Criterion(cid, text, traces, c.get("check"), warnings))
    return out


def ratify(criteria_path: Path, by: str) -> dict[str, Any]:
    if not by or not by.strip():
        raise SkillGateError("--by NAME is required: record who ratified the criteria")
    load_criteria(criteria_path)  # must be valid before it can be ratified
    record = {
        "criteria_file": Path(criteria_path).name,
        "criteria_sha256": sha256_file(criteria_path),
        "ratified_by": by.strip(),
        "ratified_at": iso(utc_now()),
    }
    write_json(ratification_path(criteria_path), record)
    return record


def check_ratified(criteria_path: Path) -> dict[str, Any]:
    rp = ratification_path(criteria_path)
    if not rp.is_file():
        raise SkillGateError(f"{Path(criteria_path).name} has not been ratified. Run `skillgate criteria --ratify --by NAME`.")
    record = read_json(rp)
    if record.get("criteria_sha256") != sha256_file(criteria_path):
        raise SkillGateError(
            f"{Path(criteria_path).name} changed after it was ratified by {record.get('ratified_by')}. "
            "Review the change and ratify again."
        )
    return record


# --- drafting -----------------------------------------------------------------

PROPOSE_SCHEMA = {
    "type": "object",
    "properties": {
        "criteria": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "rule_labels": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["text", "rule_labels"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["criteria"],
    "additionalProperties": False,
}

HEADER = """\
# DRAFT criteria for {name}. Nothing reads this file.
# Review every criterion: exactly one observable property, PASS or FAIL, no partial credit,
# traced to a rule of the skill (keys are listed in coverage.md). Then save it as
# {target} and run: skillgate criteria --ratify --by "Your Name"
"""


def propose(skill: Skill, rules: list[Rule], out_path: Path, target_name: str, model: JSONModel | None) -> dict[str, Any]:
    meta: dict[str, Any] = {"mode": "skeleton"}
    items: list[dict[str, Any]] = []
    if model is not None:
        prompt = load_prompt("criteria.v1")
        listing = "\n".join(f"{r.label} (line {r.line}): {r.text}" for r in rules)
        system, user = prompt.render(RULES=listing)
        try:
            result = model.complete_json(system=system, user=user, schema=PROPOSE_SCHEMA)
        except LLMError as e:
            raise SkillGateError(f"Drafting criteria failed: {e}") from e
        by_label = {r.label: r for r in rules}
        for n, c in enumerate(result.data.get("criteria", []), 1):
            keys = [by_label[lbl].key for lbl in c.get("rule_labels", []) if lbl in by_label]
            if keys and c.get("text", "").strip():
                items.append({"id": f"C{n}", "text": c["text"].strip(), "traces_to": keys})
        meta = {"mode": "model", "model": model.model, "prompt_sha256": prompt.sha256}
    else:
        for r in rules:
            items.append({
                "id": f"C{r.index}",
                "text": f"TODO: one observable, binary property of every output that shows rule {r.label} was followed",
                "traces_to": [r.key],
            })
    body = dump_yaml({"criteria": items})
    labels = {r.key: f"{r.label}: {r.text[:90]}" for r in rules}
    body = re.sub(r"^(\s*- )(k[0-9a-f]{8})$", lambda m: f"{m.group(1)}{m.group(2)}  # {labels.get(m.group(2), '')}", body, flags=re.M)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(HEADER.format(name=skill.name, target=target_name) + body, encoding="utf-8")
    return {**meta, "count": len(items)}


# --- coverage -----------------------------------------------------------------


def coverage(rules: list[Rule], criteria: list[Criterion], cases: list[Case]) -> dict[str, Any]:
    by_key: dict[str, list[str]] = {r.key: [] for r in rules}
    dangling = []
    for c in criteria:
        for k in c.traces_to:
            if k in by_key:
                by_key[k].append(c.id)
            else:
                dangling.append(f"{c.id} → {k}")
    for case in cases:
        for e in case.expectations:
            for k in e.traces_to:
                if k in by_key:
                    by_key[k].append(f"{case.id}:{e.id}")
                else:
                    dangling.append(f"{case.id}:{e.id} → {k}")
    uncovered = [r for r in rules if not by_key[r.key]]
    return {
        "rules": len(rules),
        "covered": len(rules) - len(uncovered),
        "uncovered": len(uncovered),
        "uncovered_rules": [{"label": r.label, "key": r.key, "line": r.line, "text": r.text} for r in uncovered],
        "dangling_traces": dangling,
        "matrix": [{"label": r.label, "key": r.key, "line": r.line, "text": r.text, "checks": by_key[r.key]} for r in rules],
    }


def render_coverage(cov: dict[str, Any], skill: Skill) -> str:
    lines = [
        f"# Coverage: {skill.name}" + (f" v{skill.version}" if skill.version else ""),
        "",
        f"Skill SHA-256 `{skill.sha256[:12]}…`. {cov['rules']} rules extracted; "
        f"{cov['covered']} covered by at least one check; **{cov['uncovered']} uncovered**.",
        "",
        "Rules are list items, table rows, and sentences using rule language (must, never, only, …).",
        "A rule's key changes when its wording changes, so a reworded rule shows as uncovered until",
        "its checks are traced again.",
        "",
        "| Rule | Key | Line | Rule text | Checked by |",
        "|---|---|---|---|---|",
    ]
    for row in cov["matrix"]:
        text = row["text"].replace("|", "\\|")
        text = text if len(text) <= 100 else text[:99] + "…"
        checks = ", ".join(row["checks"]) or "**uncovered**"
        lines.append(f"| {row['label']} | `{row['key']}` | {row['line']} | {text} | {checks} |")
    if cov["dangling_traces"]:
        lines += ["", "## Traces to rules that no longer exist", ""]
        lines += [f"- {d}" for d in cov["dangling_traces"]]
    return "\n".join(lines) + "\n"
