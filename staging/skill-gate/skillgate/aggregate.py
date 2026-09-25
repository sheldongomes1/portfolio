"""Binary aggregation. Counts only: nothing here computes an average.

A case passes only if every criterion and every expectation passes on every
repeat. A case that passes some repeats and fails others is FLAKY and counts
as failed. A case with an ERROR and no FAIL is ERROR: its result is unknown.
"""

from __future__ import annotations

from typing import Any

STATUSES = ("PASS", "FAIL", "FLAKY", "ERROR")


def case_status(verdicts_by_repeat: dict[int, list[str]]) -> str:
    repeat_pass = {r: all(v == "PASS" for v in vs) for r, vs in verdicts_by_repeat.items()}
    everything = [v for vs in verdicts_by_repeat.values() for v in vs]
    if repeat_pass and all(repeat_pass.values()):
        return "PASS"
    if "FAIL" in everything:
        return "FLAKY" if any(repeat_pass.values()) else "FAIL"
    return "ERROR"


def aggregate(judgments: list[dict[str, Any]], cases: list[dict[str, Any]], k: int) -> dict[str, Any]:
    """`cases` is [{id, split}], `judgments` as written by the judge."""
    by_case: dict[str, dict[int, list[str]]] = {c["id"]: {r: [] for r in range(1, k + 1)} for c in cases}
    split_of = {c["id"]: c["split"] for c in cases}
    per_check: dict[str, dict[str, Any]] = {}
    failed_checks: dict[str, dict[str, dict[str, Any]]] = {c["id"]: {} for c in cases}
    totals = {"judgments": 0, "PASS": 0, "FAIL": 0, "ERROR": 0}

    for j in judgments:
        cid, r, v = j["case_id"], int(j["repeat"]), j["verdict"]
        if cid not in by_case or r not in by_case[cid]:
            continue
        by_case[cid][r].append(v)
        totals["judgments"] += 1
        totals[v] += 1
        key = j["check_id"] if j["check_kind"] == "criterion" else f"{cid}:{j['check_id']}"
        pc = per_check.setdefault(
            key, {"kind": j["check_kind"], "expectation_kind": j.get("expectation_kind"), "PASS": 0, "FAIL": 0, "ERROR": 0, "cases": []}
        )
        pc[v] += 1
        if v != "PASS":
            if cid not in pc["cases"]:
                pc["cases"].append(cid)
            fc = failed_checks[cid].setdefault(
                j["check_id"],
                {"check_id": j["check_id"], "check_kind": j["check_kind"], "expectation_kind": j.get("expectation_kind"),
                 "FAIL_repeats": [], "ERROR_repeats": [], "reasons": []},
            )
            fc[f"{v}_repeats"].append(r)
            fc["reasons"].append({"repeat": r, "verdict": v, "reason": j.get("reason", ""), "evidence": j.get("evidence", "")})

    per_case = {}
    for cid, verdicts in by_case.items():
        missing = [r for r, vs in verdicts.items() if not vs]
        status = case_status({r: (vs or ["ERROR"]) for r, vs in verdicts.items()})
        per_case[cid] = {
            "split": split_of[cid],
            "status": status,
            "repeats_passed": sum(1 for vs in verdicts.values() if vs and all(v == "PASS" for v in vs)),
            "repeats": k,
            "missing_repeats": missing,
            "failed_checks": sorted(failed_checks[cid].values(), key=lambda x: x["check_id"]),
        }

    by_split = {}
    for sp in ("dev", "holdout"):
        ids = [cid for cid, pc in per_case.items() if pc["split"] == sp]
        by_split[sp] = {
            "cases": len(ids),
            "passed": sum(1 for i in ids if per_case[i]["status"] == "PASS"),
            "failed": sum(1 for i in ids if per_case[i]["status"] == "FAIL"),
            "flaky": sum(1 for i in ids if per_case[i]["status"] == "FLAKY"),
            "error_cases": sum(1 for i in ids if per_case[i]["status"] == "ERROR"),
            "error_judgments": sum(
                len(fc["ERROR_repeats"]) for i in ids for fc in per_case[i]["failed_checks"]
            ) + sum(len(per_case[i]["missing_repeats"]) for i in ids),
        }

    misses, false_flags = [], []
    for cid, pc in per_case.items():
        for fc in pc["failed_checks"]:
            if not fc["FAIL_repeats"] or fc["check_kind"] != "expectation":
                continue
            item = {"case_id": cid, "split": pc["split"], "expectation_id": fc["check_id"],
                    "failed_repeats": fc["FAIL_repeats"], "of_repeats": k}
            if fc["expectation_kind"] == "detect":
                misses.append(item)
            elif fc["expectation_kind"] == "no_flag":
                false_flags.append(item)

    per_criterion = {
        key: {"FAIL": v["FAIL"], "ERROR": v["ERROR"], "PASS": v["PASS"], "failing_cases": v["cases"]}
        for key, v in sorted(per_check.items())
        if v["kind"] == "criterion"
    }
    return {
        "k": k,
        "totals": totals,
        "by_split": by_split,
        "per_case": dict(sorted(per_case.items())),
        "per_criterion": per_criterion,
        "misses": misses,
        "false_flags": false_flags,
    }
