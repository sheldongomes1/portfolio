"""`skillgate receipt`: the record a reviewer uses to decide whether a skill is verified.

VERIFIED only if every case passes on both splits across all repeats, there
are zero ERRORs, the judge is calibrated (or no model judged anything), the
golden set meets its minimums, and every input still matches its hash.
Otherwise NOT VERIFIED, with every reason listed.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from skillgate.aggregate import aggregate
from skillgate.calibrate import find_record, judge_identity
from skillgate.cases import golden_stats, load_cases, load_golden, verify_splits
from skillgate.config import Config
from skillgate.criteria import check_ratified, coverage, load_criteria, ratification_path
from skillgate.judge import JUDGE_PROMPT, latest_run
from skillgate.prompts import load_prompt
from skillgate.run import config_models
from skillgate.skill import extract_rules, load_skill
from skillgate.util import (
    SkillGateError,
    canonical_json,
    iso,
    new_dir,
    read_json,
    read_yaml,
    rel,
    sha256_file,
    sha256_text,
    dir_stamp,
    utc_now,
    write_json,
)

SCHEMA_VERSION = 1
API_NOTE = ("Execution emulated Google Workspace through the model API. Behavior inside Workspace "
            "may differ (sampling settings, reference-file handling, surface).")


def latest_judge(run_dir: Path) -> Path:
    judges = sorted(p for p in Path(run_dir).glob("judge-*") if (p / "judge.json").is_file())
    if not judges:
        raise SkillGateError(f"Run {Path(run_dir).name} has not been judged. Run `skillgate judge`.")
    return judges[-1]


def load_judgments(judge_dir: Path) -> tuple[list[dict[str, Any]], list[Path]]:
    files = sorted((Path(judge_dir) / "judgments").rglob("*.json"))
    out = []
    for f in files:
        out.extend(read_json(f))
    return out, files


def executor_block(run: dict[str, Any], capture: dict[str, Any], execution: dict[str, Any] | None) -> dict[str, Any]:
    ex = dict(run["executor"])
    if run["mode"] == "manual":
        ex.update({k: capture[k] for k in ("surface", "run_date", "operator")})
    if execution is not None:
        ex.update({"served_models": execution["served_models"], "calls": execution["calls"],
                   "cache_hits": execution["cache_hits"], "errors": execution["errors"],
                   "cost_usd": execution["cost_usd"]})
    return ex


def calibration_status(cfg: Config, identity: dict[str, Any], judge_used: bool) -> tuple[dict[str, Any], list]:
    """The calibration block for a receipt, and the files it rests on (for the manifest)."""
    if not judge_used:
        return {"status": "NOT APPLICABLE", "reason": "every check was deterministic; no model judged anything"}, []
    path = find_record(cfg, identity)
    if path is None:
        return {"status": "JUDGE UNCALIBRATED",
                "reason": "no calibration record for this judge (model, settings and prompt); run `skillgate calibrate`"}, []
    rec = read_json(path)
    files = [(path, "calibration")] + [(cfg.root / it["judgment_file"], "calibration_judgment") for it in rec["items"]]
    block = calibration_block(rec, rel(path, cfg.root))
    changed = [it["item_id"] for it in rec["items"]
               if not (cfg.root / it["judgment_file"]).is_file()
               or sha256_file(cfg.root / it["judgment_file"]) != it["judgment_sha256"]]
    if changed:
        block.update(status="JUDGE UNCALIBRATED",
                     reason=f"the calibration record's judgments changed after labeling ({', '.join(changed[:5])})")
        files = [(path, "calibration")]
    return block, files


def calibration_block(rec: dict[str, Any], record_path: str) -> dict[str, Any]:
    c, req = rec["counts"], rec["required"]
    detail = (f"{c['agree']} of {c['items']} labels agree with the judge (at least {req['agree']} required); "
              f"{c['judge_fail_agree']} of {c['judge_fail']} on the judge's FAIL verdicts "
              f"(at least {req['judge_fail_agree']} required); labeled blind by {rec['labeled_by']} at {rec['labeled_at']}")
    if rec["status"] == "CALIBRATED":
        return {"status": "CALIBRATED", "reason": detail, "record": record_path, "counts": c, "required": req}
    return {"status": "JUDGE UNCALIBRATED", "reason": "; ".join(rec["reasons"]) + f" ({detail})",
            "record": record_path, "counts": c, "required": req}


def compute_verdict(ctx: dict[str, Any]) -> tuple[str, list[str], list[str]]:
    """Pure function of the receipt's recorded context, so verify-receipt can recompute it."""
    reasons: list[str] = []
    flags: list[str] = []
    summary = ctx["results"]
    reasons += ctx["golden_set"]["blockers"]
    reasons += [f"split assignment: {p}" for p in ctx["split_problems"]]
    rc = ctx["run_coverage"]
    if rc["in_run"] < rc["golden_cases"]:
        reasons.append(f"the run covered {rc['in_run']} of {rc['golden_cases']} golden cases; VERIFIED needs every case in both splits")
    if ctx["run"]["k"] < 2:
        flags.append("SINGLE RUN")
        reasons.append("SINGLE RUN: each case ran once (k=1); VERIFIED needs repeats")
    for sp in ("dev", "holdout"):
        s = summary["by_split"][sp]
        if s["cases"] == 0:
            reasons.append(f"{sp}: no cases in this split")
        elif s["passed"] < s["cases"]:
            reasons.append(
                f"{sp}: {s['passed']} of {s['cases']} cases passed on every repeat "
                f"({s['failed']} failed, {s['flaky']} flaky, {s['error_cases']} ERROR)"
            )
    if summary["totals"]["ERROR"]:
        reasons.append(f"{summary['totals']['ERROR']} judgment(s) are ERROR: a check that could not be completed blocks VERIFIED")
    cal = ctx["calibration"]
    if cal["status"] == "JUDGE UNCALIBRATED":
        flags.append("JUDGE UNCALIBRATED")
        reasons.append(f"JUDGE UNCALIBRATED: {cal['reason']}")
    judge = ctx["judge"]
    other = [m for m in judge["served_models"] if m != judge["model"]]
    if other:
        reasons.append(f"judge calls were served by {', '.join(other)}, not the configured {judge['model']}")
    if ctx["mode"] == "manual" and not ctx["capture"]["complete"]:
        reasons.append("manual run capture is incomplete: fill surface and run_date in capture.yaml")
    if ctx["mode"] == "api":
        flags.append("API EMULATION")
    return ("NOT VERIFIED" if reasons else "VERIFIED"), reasons, flags


def _failing_cases(summary: dict[str, Any], cases_by_id: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for cid, pc in summary["per_case"].items():
        if pc["status"] == "PASS":
            continue
        item: dict[str, Any] = {"case_id": cid, "split": pc["split"], "status": pc["status"],
                                "repeats_passed": pc["repeats_passed"], "repeats": pc["repeats"]}
        if pc["split"] == "holdout":
            item["checks"] = [{"check_id": fc["check_id"], "details": "redacted (holdout)"} for fc in pc["failed_checks"]]
        else:
            checks = []
            for fc in pc["failed_checks"]:
                text = None
                if fc["check_kind"] == "expectation":
                    text = next((e.text for e in cases_by_id[cid].expectations if e.id == fc["check_id"]), None)
                checks.append({"check_id": fc["check_id"], "check_kind": fc["check_kind"], "text": text,
                               "reasons": [{"repeat": r["repeat"], "verdict": r["verdict"], "reason": r["reason"],
                                            "evidence": (r["evidence"] or "")[:300]} for r in fc["reasons"]]})
            item["checks"] = checks
        out.append(item)
    return out


def _issue_list(items: list[dict[str, Any]], cases_by_id: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for m in items:
        entry = dict(m)
        if m["split"] == "dev":
            entry["text"] = next((e.text for e in cases_by_id[m["case_id"]].expectations if e.id == m["expectation_id"]), None)
        else:
            entry["text"] = "redacted (holdout)"
        out.append(entry)
    return out


def build_receipt(cfg: Config, run_dir: Path | None = None, judge_dir: Path | None = None) -> Path:
    root = cfg.root
    run_dir = Path(run_dir) if run_dir else latest_run(cfg.paths["runs"])
    judge_dir = Path(judge_dir) if judge_dir else latest_judge(run_dir)
    run = read_json(run_dir / "run.json")
    meta = read_json(judge_dir / "judge.json")
    problems = []

    skill = load_skill(cfg.skill_path, cfg.skill_name)
    if skill.sha256 != run["skill"]["sha256"]:
        problems.append("the skill file changed after the run")
    current_refs = {rel(p, root): sha256_file(p) for p in cfg.reference_paths}
    if current_refs != {r["path"]: r["sha256"] for r in run["references"]}:
        problems.append("reference files changed after the run")
    cases = load_cases(cfg.paths["cases"])
    cases_by_id = {c.id: c for c in cases}
    for rc in run["cases"]:
        c = cases_by_id.get(rc["id"])
        if c is None or c.sha256 != rc["sha256"] or c.input_file_hashes(root) != rc["input_files"]:
            problems.append(f"case {rc['id']} changed after the run")
    for key, h in meta["outputs"].items():
        cid, r = key.split("/")
        p = run_dir / "outputs" / cid / f"{r}.md"
        if (sha256_file(p) if p.is_file() else "") != h:
            problems.append(f"output {key} changed after it was judged")
    criteria_path = cfg.paths["criteria"]
    ratification = check_ratified(criteria_path)
    if sha256_file(criteria_path) != meta["criteria"]["sha256"]:
        problems.append("criteria.yaml changed after judging")
    prompt = load_prompt(JUDGE_PROMPT)
    if prompt.sha256 != meta["prompts"][JUDGE_PROMPT]["sha256"]:
        problems.append(f"prompt {JUDGE_PROMPT} changed after judging")
    if problems:
        raise SkillGateError("Cannot issue a receipt; re-run or re-judge:\n  " + "\n  ".join(problems))

    judgments, judgment_files = load_judgments(judge_dir)
    k = int(run["k"])
    summary = aggregate(judgments, [{"id": rc["id"], "split": rc["split"]} for rc in run["cases"]], k)
    stats = golden_stats(cases, cfg.thresholds)
    golden = load_golden(cfg.paths["golden"])
    split_problems = verify_splits(cases, golden)
    rules = extract_rules(skill.text)
    cov = coverage(rules, load_criteria(criteria_path), cases)

    capture = {"complete": True}
    if run["mode"] == "manual":
        cap = read_yaml(run_dir / "capture.yaml") or {}
        capture = {k2: (str(cap.get(k2)) if cap.get(k2) else "") for k2 in ("surface", "run_date", "operator", "notes")}
        capture["complete"] = bool(capture["surface"] and capture["run_date"])

    manifest: list[dict[str, str]] = []

    def add(path: Path, role: str) -> None:
        manifest.append({"path": rel(path, root), "role": role, "sha256": sha256_file(path)})

    identity = judge_identity(meta["judge"]["model"], meta["judge"]["settings"], meta["prompts"][JUDGE_PROMPT]["sha256"])
    calibration, calibration_files = calibration_status(cfg, identity, meta["judge"]["used"])

    add(cfg.path, "config")
    add(skill.path, "skill")
    for p in cfg.reference_paths:
        add(p, "reference")
    add(cfg.paths["golden"], "golden")
    input_files = set()
    for c in cases:
        add(c.path, "case")
        input_files.update(c.input_files)
    for f in sorted(input_files):
        add(root / f, "case_input")
    add(criteria_path, "criteria")
    add(ratification_path(criteria_path), "ratification")
    add(run_dir / "run.json", "run")
    if run["mode"] == "manual":
        add(run_dir / "capture.yaml", "capture")
    execution = None
    if run["mode"] == "api":
        execution = read_json(run_dir / "execution.json")
        add(run_dir / "execution.json", "execution")
        add(run_dir / "log.jsonl", "execution_log")
    for rc in run["cases"]:
        for r in range(1, k + 1):
            p = run_dir / "outputs" / rc["id"] / f"{r}.md"
            if p.is_file():
                add(p, "output")
    for name, role in (("judge.json", "judge"), ("summary.json", "summary"), ("log.jsonl", "log")):
        add(judge_dir / name, role)
    for f in judgment_files:
        add(f, "judgment")
    listed = {m["path"] for m in manifest}
    for path, role in calibration_files:
        if rel(path, root) not in listed:
            add(path, role)
            listed.add(rel(path, root))

    now = utc_now()
    ctx: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": iso(now),
        "project": {"root_marker": "skillgate.yaml"},
        "skill": {"name": skill.name, "version": skill.version, "path": rel(skill.path, root), "sha256": skill.sha256},
        "references": run["references"],
        "mode": run["mode"],
        "executor": executor_block(run, capture, execution),
        "config_models": run.get("config_models") or config_models(cfg),
        "api_note": API_NOTE if run["mode"] == "api" else None,
        "judge": {"provider": meta["judge"]["provider"], "model": meta["judge"]["model"], "settings": meta["judge"]["settings"],
                  "used": meta["judge"]["used"], "served_models": meta["judge"]["served_models"]},
        "prompts": {**{name: p["sha256"] for name, p in meta["prompts"].items()},
                    **(run["executor"].get("prompt") or {})},
        "run": {"run_id": run["run_id"], "created_at": run["created_at"], "judged_at": meta["finished_at"],
                "judge_id": meta["judge_id"], "k": k,
                "cases": [{"id": rc["id"], "split": rc["split"]} for rc in run["cases"]]},
        "run_coverage": {"golden_cases": len(cases), "in_run": len(run["cases"])},
        "capture": capture,
        "results": {k2: summary[k2] for k2 in ("totals", "by_split", "per_criterion")},
        "misses": _issue_list(summary["misses"], cases_by_id),
        "false_flags": _issue_list(summary["false_flags"], cases_by_id),
        "failing_cases": _failing_cases(summary, cases_by_id),
        "golden_set": {**stats, "holdout_share": golden.get("holdout_share"),
                       "seeds": [d["seed"] for d in golden.get("draws", [])]},
        "split_problems": split_problems,
        "coverage": {"rules": cov["rules"], "uncovered": cov["uncovered"],
                     "uncovered_rules": [f"{r['label']} (line {r['line']})" for r in cov["uncovered_rules"]],
                     "dangling_traces": cov["dangling_traces"]},
        "calibration": calibration,
        "criteria": {"path": rel(criteria_path, root), "sha256": sha256_file(criteria_path),
                     "ratified_by": ratification["ratified_by"], "ratified_at": ratification["ratified_at"]},
        "calls": meta["calls"],
        "manifest": manifest,
    }
    verdict, reasons, flags = compute_verdict(ctx)
    ctx.update(verdict=verdict, reasons=reasons, flags=flags, warnings=stats["warnings"])
    ctx["consistency_sha256"] = consistency_hash(ctx)

    out_dir = new_dir(cfg.paths["receipts"] / f"{dir_stamp()}-{skill.name}")
    write_json(out_dir / "receipt.json", ctx)
    (out_dir / "receipt.md").write_text(render_md(ctx), encoding="utf-8")
    return out_dir


def consistency_hash(receipt: dict[str, Any]) -> str:
    body = {k: v for k, v in receipt.items() if k != "consistency_sha256"}
    return sha256_text(canonical_json(body))


def render_md(r: dict[str, Any]) -> str:
    s = r["skill"]
    L = [f"# Skill Gate receipt: {s['name']}" + (f" v{s['version']}" if s["version"] else ""), ""]
    L += [f"## Verdict: {r['verdict']}", ""]
    if r["reasons"]:
        L += ["Reasons:", ""] + [f"- {x}" for x in r["reasons"]] + [""]
    if r["flags"]:
        L += ["Flags: " + " · ".join(r["flags"]), ""]
    if r["api_note"]:
        L += [f"**Note:** {r['api_note']}", ""]
    if r["warnings"]:
        L += ["Warnings: " + "; ".join(r["warnings"]) + ".", ""]
    L += ["All results are counts of binary PASS, FAIL and ERROR judgments.", ""]

    ex = r["executor"]
    L += ["## What was tested", "", "| Item | Value |", "|---|---|",
          f"| Skill | `{s['path']}` SHA-256 `{s['sha256']}` |"]
    for ref in r["references"]:
        L.append(f"| Reference | `{ref['path']}` SHA-256 `{ref['sha256']}` |")
    if r["mode"] == "manual":
        L.append(f"| Mode | manual: surface \"{ex.get('surface') or 'not recorded'}\", run date {ex.get('run_date') or 'not recorded'}, operator {ex.get('operator') or 'not recorded'} |")
    else:
        L.append(f"| Mode | {r['mode']}: executor `{ex.get('model')}` settings `{canonical_json(ex.get('settings', {}))}` |")
        L.append(f"| Executor calls | {ex.get('calls')} call(s), {ex.get('cache_hits')} from cache, {ex.get('errors')} failed; "
                 f"served by {', '.join(ex.get('served_models') or []) or 'no call'} |")
    j = r["judge"]
    L.append(f"| Judge | `{j['model']}` settings `{canonical_json(j['settings'])}`" + ("" if j["used"] else " (not called: all checks deterministic)") + " |")
    for name, h in sorted(r["prompts"].items()):
        L.append(f"| Prompt | `{name}` SHA-256 `{h}` |")
    run = r["run"]
    L += [f"| Run | `{run['run_id']}`, judged `{run['judge_id']}`, repeats k = {run['k']} |",
          f"| Receipt generated | {r['generated_at']} (UTC) |", ""]

    L += ["## Results by split", "", "| Split | Cases | Passed | Failed | Flaky | ERROR cases | ERROR judgments |",
          "|---|---|---|---|---|---|---|"]
    for sp, x in r["results"]["by_split"].items():
        L.append(f"| {sp} | {x['cases']} | {x['passed']} | {x['failed']} | {x['flaky']} | {x['error_cases']} | {x['error_judgments']} |")
    t = r["results"]["totals"]
    L += ["", f"Judgments: {t['judgments']} ({t['PASS']} PASS, {t['FAIL']} FAIL, {t['ERROR']} ERROR).", ""]

    L += ["## Misses and false flags", "", f"Misses (expected issues the skill failed to catch): {len(r['misses'])}", ""]
    L += [f"- `{m['case_id']}` {m['expectation_id']} ({m['split']}), failed on repeat(s) {', '.join(map(str, m['failed_repeats']))} of {m['of_repeats']}: {m['text']}" for m in r["misses"]]
    L += ["", f"False flags (issues raised where the case says not to flag): {len(r['false_flags'])}", ""]
    L += [f"- `{m['case_id']}` {m['expectation_id']} ({m['split']}), failed on repeat(s) {', '.join(map(str, m['failed_repeats']))} of {m['of_repeats']}: {m['text']}" for m in r["false_flags"]]
    L.append("")

    L += ["## FAIL counts per criterion", "", "| Criterion | FAIL | ERROR | Failing cases |", "|---|---|---|---|"]
    for cid, x in r["results"]["per_criterion"].items():
        L.append(f"| {cid} | {x['FAIL']} | {x['ERROR']} | {', '.join(x['failing_cases']) or '—'} |")
    L.append("")

    L += ["## Cases that did not pass", ""]
    if not r["failing_cases"]:
        L += ["None.", ""]
    for fc in r["failing_cases"]:
        L.append(f"### `{fc['case_id']}` ({fc['split']}): {fc['status']}, {fc['repeats_passed']} of {fc['repeats']} repeats passed")
        for ch in fc["checks"]:
            if "details" in ch:
                L.append(f"- {ch['check_id']}: {ch['details']}")
                continue
            label = ch["check_id"] + (f" ({ch['text']})" if ch.get("text") else "")
            for rr in ch["reasons"]:
                ev = f" Evidence: `{rr['evidence'][:160]}`" if rr["evidence"] else ""
                L.append(f"- {label}, repeat {rr['repeat']}: **{rr['verdict']}**. {rr['reason']}{ev}")
        L.append("")

    g = r["golden_set"]
    L += ["## Golden set", "",
          f"{g['size']} cases: {g['splits']['dev']} dev, {g['splits']['holdout']} holdout; "
          f"{g['edge_or_should_not_flag']} tagged edge or should_not_flag; sources {g['sources']['expert']} expert, {g['sources']['generated']} generated.",
          "", "Tags: " + (", ".join(f"{k} {v}" for k, v in g["tags"].items()) or "none") + ".",
          "", "Holdout drawn at random; seed(s): " + (", ".join(map(str, g["seeds"])) or "none") + ".", ""]

    c = r["coverage"]
    L += ["## Coverage", "", f"{c['rules']} rules extracted from the skill; **{c['uncovered']} uncovered** by any criterion or expectation."]
    if c["uncovered_rules"]:
        L += ["", "Uncovered: " + ", ".join(c["uncovered_rules"]) + "."]
    L.append("")

    cal = r["calibration"]
    L += ["## Judge calibration", "", f"{cal['status']}: {cal['reason']}.", ""]
    cr = r["criteria"]
    L += ["## Criteria", "", f"`{cr['path']}` SHA-256 `{cr['sha256']}`, ratified by {cr['ratified_by']} at {cr['ratified_at']}.", ""]
    calls = r["calls"]
    cost = "unknown (no pricing configured)" if calls["cost_usd"] is None else f"${calls['cost_usd']:.4f}"
    L += ["## Model calls", "", f"{calls['model_calls']} judge call(s), {calls['input_tokens']} input and {calls['output_tokens']} output tokens, cost {cost}.", ""]

    roles: dict[str, int] = {}
    for m in r["manifest"]:
        roles[m["role"]] = roles.get(m["role"], 0) + 1
    L += ["## Artifact manifest", "",
          f"{len(r['manifest'])} files hashed: " + ", ".join(f"{v} {k}" for k, v in roles.items()) + ".",
          "The full list with SHA-256 hashes is in `receipt.json`. Run `skillgate verify-receipt` on it to",
          "recompute every hash, the results and the verdict.", "",
          f"Consistency hash of receipt.json: `{r['consistency_sha256']}`. This detects accidental edits; it is not a signature.", ""]
    return "\n".join(L)
