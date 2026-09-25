"""`skillgate verify-receipt`: detect a receipt, or anything it rests on, edited after the fact.

1. Recompute the SHA-256 of every file in the manifest.
2. Compare the judge prompt hashes with the prompt files in this installation.
3. Re-aggregate the results from the judgment files and compare.
4. Recompute the golden-set statistics and split draws from the case files, and the judge
   calibration from its record and the judgments it labeled.
5. Recompute the verdict and its reasons from all of the above.
6. Re-render receipt.md from receipt.json and compare with the file on disk.
7. Check the receipt's consistency hash.

This detects edits; it is not a signature. Someone who rewrites every file
consistently is out of scope (no cryptographic signing in v1).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from skillgate.aggregate import aggregate
from skillgate.calibrate import evaluate, judge_identity
from skillgate.cases import _parse_case, golden_stats, verify_splits
from skillgate.config import DEFAULT_THRESHOLDS
from skillgate.prompts import PROMPTS_DIR
from skillgate.receipt import SCHEMA_VERSION, calibration_block, compute_verdict, consistency_hash, render_md
from skillgate.util import SkillGateError, read_json, read_yaml, sha256_file


def find_root(receipt_path: Path, marker: str = "skillgate.yaml") -> Path:
    for d in Path(receipt_path).resolve().parents:
        if (d / marker).is_file():
            return d
    raise SkillGateError(f"Could not find {marker} above {receipt_path}; pass --root")


def verify_receipt(receipt_path: Path, root: Path | None = None) -> tuple[list[str], int]:
    """Return (problems, files_checked). No problems means the receipt verifies."""
    receipt_path = Path(receipt_path)
    r = read_json(receipt_path)
    if r.get("schema_version") != SCHEMA_VERSION:
        raise SkillGateError(f"Unsupported receipt schema_version {r.get('schema_version')}")
    root = Path(root) if root else find_root(receipt_path, r.get("project", {}).get("root_marker", "skillgate.yaml"))
    problems: list[str] = []

    if consistency_hash(r) != r.get("consistency_sha256"):
        problems.append("receipt.json: consistency hash does not match its content (the receipt was edited)")

    checked = 0
    by_role: dict[str, list[Path]] = {}
    for entry in r["manifest"]:
        p = root / entry["path"]
        checked += 1
        if not p.is_file():
            problems.append(f"{entry['path']}: missing")
            continue
        actual = sha256_file(p)
        if actual != entry["sha256"]:
            problems.append(f"{entry['path']}: SHA-256 mismatch (receipt {entry['sha256'][:12]}…, file {actual[:12]}…)")
        by_role.setdefault(entry["role"], []).append(p)

    for name, h in r["prompts"].items():
        p = PROMPTS_DIR / f"{name}.md"
        if not p.is_file():
            problems.append(f"prompt {name}: not found in this installation")
        elif sha256_file(p) != h:
            problems.append(f"prompt {name}: differs from the one recorded in the receipt")

    judgments: list[dict[str, Any]] = []
    for f in sorted(by_role.get("judgment", [])):
        judgments.extend(read_json(f))
    summary = aggregate(judgments, r["run"]["cases"], int(r["run"]["k"]))
    for key in ("totals", "by_split", "per_criterion"):
        if summary[key] != r["results"][key]:
            problems.append(f"results.{key}: does not match the judgment files")
    for key in ("misses", "false_flags"):
        recomputed = [(m["case_id"], m["expectation_id"], m["failed_repeats"]) for m in summary[key]]
        recorded = [(m["case_id"], m["expectation_id"], m["failed_repeats"]) for m in r[key]]
        if recomputed != recorded:
            problems.append(f"{key}: does not match the judgment files")
    failing = sorted((c, pc["status"]) for c, pc in summary["per_case"].items() if pc["status"] != "PASS")
    if failing != sorted((fc["case_id"], fc["status"]) for fc in r["failing_cases"]):
        problems.append("failing_cases: does not match the judgment files")

    ctx = dict(r)
    ctx["results"] = {k: summary[k] for k in ("totals", "by_split", "per_criterion")}
    cfg_files = by_role.get("config", [])
    thresholds = dict(DEFAULT_THRESHOLDS)
    if cfg_files:
        thresholds.update((read_yaml(cfg_files[0]) or {}).get("thresholds") or {})
    case_files = by_role.get("case", [])
    if case_files:
        cases = [_parse_case(p, read_yaml(p)) for p in case_files]
        stats = golden_stats(cases, thresholds)
        for key in ("size", "splits", "edge_or_should_not_flag", "blockers"):
            if stats[key] != r["golden_set"][key]:
                problems.append(f"golden_set.{key}: does not match the case files")
        ctx["golden_set"] = {**r["golden_set"], **stats}
        golden_files = by_role.get("golden", [])
        split_problems = verify_splits(cases, read_yaml(golden_files[0]) if golden_files else {})
        if split_problems != r["split_problems"]:
            problems.append("split_problems: does not match the case files and golden.yaml")
        ctx["split_problems"] = split_problems
    cal_files = by_role.get("calibration", [])
    if cal_files:
        rec = read_json(cal_files[0])
        expected_identity = judge_identity(r["judge"]["model"], r["judge"]["settings"], r["prompts"].get("judge.v1", ""))
        if rec["judge"] != expected_identity:
            problems.append("calibration: the record belongs to a different judge (model, settings or prompt)")
        for it in rec["items"]:
            jf = root / it["judgment_file"]
            if not jf.is_file() or sha256_file(jf) != it["judgment_sha256"]:
                problems.append(f"calibration: judgment {it['judgment_file']} changed after labeling")
                continue
            actual = next((j["verdict"] for j in read_json(jf) if j["check_id"] == it["check_id"]), None)
            if actual != it["judge_verdict"]:
                problems.append(f"calibration: item {it['item_id']} records a judge verdict the judgment file does not have")
        recomputed = evaluate(rec["items"], float(rec["threshold"]), int(rec["min_sample"]))
        if {k: rec[k] for k in ("counts", "required", "status")} != {k: recomputed[k] for k in ("counts", "required", "status")}:
            problems.append("calibration: counts or status do not match the labeled items")
        if not problems or not any(p.startswith("calibration:") for p in problems):
            ctx["calibration"] = {**r["calibration"], **calibration_block(rec, r["calibration"].get("record", ""))}
    elif r["calibration"]["status"] == "CALIBRATED":
        problems.append("calibration: the receipt says CALIBRATED but lists no calibration record")
    verdict, reasons, flags = compute_verdict(ctx)
    if verdict != r["verdict"] or reasons != r["reasons"] or flags != r["flags"]:
        problems.append(f"verdict: recomputes to {verdict}, receipt says {r['verdict']}")

    md = receipt_path.with_name("receipt.md")
    if md.is_file() and md.read_text(encoding="utf-8") != render_md(r):
        problems.append("receipt.md: does not match receipt.json")
    elif not md.is_file():
        problems.append("receipt.md: missing")
    return problems, checked
