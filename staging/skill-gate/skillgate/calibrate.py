"""`skillgate calibrate`: measure whether a person agrees with the judge, without seeing its verdicts.

A random sample of model judgments (at least `calibration_min_sample`, drawn
from dev cases only, stratified so FAIL verdicts are represented) is shown to
a person blind: the input, the output and the check, never the verdict. The
person labels each PASS or FAIL. Agreement is counted overall and on the
judge's FAIL verdicts. Both must reach the threshold for the judge to count
as calibrated.

A calibration belongs to one judge: its model ID, its settings and the SHA-256
of its prompt. Changing any of them means calibrating again.

Two ways to label: interactively in the terminal, or with a sheet exported for
someone who will not use a terminal (`--export`, then `--import labels.csv`).
"""

from __future__ import annotations

import csv
import math
import random
import secrets
from pathlib import Path
from typing import Any, Callable

from skillgate.config import Config
from skillgate.util import (
    SkillGateError,
    canonical_json,
    iso,
    read_json,
    rel,
    sha256_file,
    sha256_text,
    dir_stamp,
    utc_now,
    write_json,
)

SCHEMA_VERSION = 1


def judge_identity(model: str, settings: dict[str, Any], prompt_sha256: str) -> dict[str, Any]:
    return {"model": model, "settings": settings, "prompt_sha256": prompt_sha256}


def identity_key(identity: dict[str, Any]) -> str:
    return sha256_text(canonical_json(identity))[:16]


def current_identity(cfg: Config) -> dict[str, Any]:
    from skillgate.judge import JUDGE_PROMPT
    from skillgate.prompts import load_prompt

    return judge_identity(cfg.judge.model, cfg.judge.settings, load_prompt(JUDGE_PROMPT).sha256)


def _judge_dir_identity(judge_dir: Path) -> dict[str, Any]:
    meta = read_json(judge_dir / "judge.json")
    return judge_identity(meta["judge"]["model"], meta["judge"]["settings"], meta["prompts"]["judge.v1"]["sha256"])


def draw_sample(judge_dir: Path, n: int, seed: int) -> list[dict[str, Any]]:
    """Model judgments on dev cases with a PASS or FAIL verdict, stratified to include FAILs."""
    pool = []
    for f in sorted((judge_dir / "judgments").rglob("*.json")):
        for j in read_json(f):
            if j["method"] == "model" and j["split"] == "dev" and j["verdict"] in ("PASS", "FAIL"):
                pool.append({**j, "_file": f})
    fails = [j for j in pool if j["verdict"] == "FAIL"]
    passes = [j for j in pool if j["verdict"] == "PASS"]
    if len(pool) < n:
        raise SkillGateError(
            f"Calibration needs {n} model judgments on dev cases; this run has {len(pool)}. "
            "Judge a larger run (or one with more model-judged checks) first."
        )
    rng = random.Random(seed)
    take_fail = min(len(fails), n // 2)
    take_pass = min(len(passes), n - take_fail)
    take_fail = min(len(fails), n - take_pass)
    chosen = rng.sample(fails, take_fail) + rng.sample(passes, take_pass)
    rng.shuffle(chosen)
    return chosen


def _items(chosen: list[dict[str, Any]], root: Path) -> list[dict[str, Any]]:
    return [
        {"item_id": f"I{i:03d}", "case_id": j["case_id"], "repeat": j["repeat"], "check_id": j["check_id"],
         "judgment_file": rel(j["_file"], root)}
        for i, j in enumerate(chosen, 1)
    ]


def _check_text(cfg: Config, case_id: str, check_id: str) -> tuple[str, str]:
    from skillgate.cases import load_cases
    from skillgate.criteria import load_criteria

    case = next(c for c in load_cases(cfg.paths["cases"]) if c.id == case_id)
    for c in load_criteria(cfg.paths["criteria"]):
        if c.id == check_id:
            return case.rendered_input(cfg.root), c.text
    return case.rendered_input(cfg.root), next(e.text for e in case.expectations if e.id == check_id)


def _output_for(cfg: Config, item: dict[str, Any]) -> str:
    run_dir = (cfg.root / item["judgment_file"]).parents[3]
    p = run_dir / "outputs" / item["case_id"] / f"{item['repeat']}.md"
    return p.read_text(encoding="utf-8") if p.is_file() else ""


def _prepare(cfg: Config, judge_dir: Path, sample: int | None, seed: int | None) -> tuple[dict, list[dict], int]:
    identity = _judge_dir_identity(judge_dir)
    if identity != current_identity(cfg):
        raise SkillGateError(
            "This run was judged with a different judge (model, settings or prompt) than skillgate.yaml "
            "now names. Calibrate a run judged by the current judge."
        )
    n = max(int(cfg.thresholds["calibration_min_sample"]), int(sample or 0))
    seed = secrets.randbelow(2**32) if seed is None else int(seed)
    return identity, _items(draw_sample(judge_dir, n, seed), cfg.root), seed


def export_sheet(cfg: Config, judge_dir: Path, *, sample: int | None = None, seed: int | None = None) -> Path:
    identity, items, seed = _prepare(cfg, judge_dir, sample, seed)
    out = cfg.paths["calibration"] / f"pending-{identity_key(identity)}-{dir_stamp()}"
    out.mkdir(parents=True)
    write_json(out / "items.json", {"schema_version": SCHEMA_VERSION, "identity": identity, "seed": seed,
                                    "source": rel(judge_dir, cfg.root), "items": items})
    lines = ["# Calibration sheet", "",
             "For each item, read the input, the output and the check. Decide whether the OUTPUT satisfies",
             "the CHECK, and write PASS or FAIL in labels.csv. The judge's verdicts are deliberately not",
             "shown; please do not look them up before you finish.", ""]
    for it in items:
        inp, check = _check_text(cfg, it["case_id"], it["check_id"])
        lines += [f"## {it['item_id']}", "", f"**Check:** {check}", "", "**Input:**", "", "````", inp.rstrip(), "````",
                  "", "**Output:**", "", "````", _output_for(cfg, it).rstrip(), "````", ""]
    (out / "sheet.md").write_text("\n".join(lines), encoding="utf-8")
    with open(out / "labels.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["item_id", "human_label", "notes"])
        for it in items:
            w.writerow([it["item_id"], "", ""])
    return out


def _normalize_label(value: str) -> str | None:
    v = (value or "").strip().upper()
    return {"P": "PASS", "PASS": "PASS", "F": "FAIL", "FAIL": "FAIL"}.get(v)


def import_labels(cfg: Config, labels_csv: Path, *, by: str) -> Path:
    labels_csv = Path(labels_csv)
    pending = read_json(labels_csv.with_name("items.json"))
    with open(labels_csv, newline="", encoding="utf-8-sig") as f:
        labels = {row["item_id"].strip(): _normalize_label(row.get("human_label", "")) for row in csv.DictReader(f)}
    missing = [it["item_id"] for it in pending["items"] if not labels.get(it["item_id"])]
    if missing:
        raise SkillGateError(f"Every item needs a PASS or FAIL label; missing or invalid: {', '.join(missing)}")
    return write_record(cfg, pending, {k: v for k, v in labels.items() if v}, by=by)


def interactive(cfg: Config, judge_dir: Path, *, by: str, sample: int | None = None, seed: int | None = None,
                ask: Callable[[str], str] = input) -> Path:
    identity, items, seed = _prepare(cfg, judge_dir, sample, seed)
    labels = {}
    for n, it in enumerate(items, 1):
        inp, check = _check_text(cfg, it["case_id"], it["check_id"])
        print(f"\n=== Item {n} of {len(items)} ({it['item_id']}) ===\n--- INPUT ---\n{inp.rstrip()}\n"
              f"--- OUTPUT ---\n{_output_for(cfg, it).rstrip()}\n--- CHECK ---\n{check}\n")
        label = None
        while label is None:
            label = _normalize_label(ask("Does the output satisfy the check? [p]ass / [f]ail: "))
        labels[it["item_id"]] = label
    pending = {"identity": identity, "seed": seed, "source": rel(judge_dir, cfg.root), "items": items}
    return write_record(cfg, pending, labels, by=by)


def evaluate(items: list[dict[str, Any]], threshold: float, min_sample: int) -> dict[str, Any]:
    n = len(items)
    agree = sum(1 for it in items if it["judge_verdict"] == it["human_label"])
    fail_items = [it for it in items if it["judge_verdict"] == "FAIL"]
    fail_agree = sum(1 for it in fail_items if it["human_label"] == "FAIL")
    required = {"agree": math.ceil(threshold * n), "judge_fail_agree": math.ceil(threshold * len(fail_items))}
    reasons = []
    if n < min_sample:
        reasons.append(f"{n} items labeled; at least {min_sample} required")
    if not fail_items:
        reasons.append("the sample has no FAIL verdicts, so agreement on FAIL cannot be measured")
    if agree < required["agree"]:
        reasons.append(f"agreement {agree} of {n}; at least {required['agree']} required")
    if fail_items and fail_agree < required["judge_fail_agree"]:
        reasons.append(f"agreement on the judge's FAIL verdicts {fail_agree} of {len(fail_items)}; "
                       f"at least {required['judge_fail_agree']} required")
    return {
        "counts": {"items": n, "agree": agree, "judge_fail": len(fail_items), "judge_fail_agree": fail_agree},
        "required": required,
        "status": "CALIBRATED" if not reasons else "BELOW THRESHOLD",
        "reasons": reasons,
    }


def write_record(cfg: Config, pending: dict[str, Any], labels: dict[str, str], *, by: str) -> Path:
    if not by or not by.strip():
        raise SkillGateError("--by NAME is required: record who labeled the sample")
    items = []
    for it in pending["items"]:
        path = cfg.root / it["judgment_file"]
        judgment = next(j for j in read_json(path) if j["check_id"] == it["check_id"])
        items.append({**it, "judgment_sha256": sha256_file(path), "judge_verdict": judgment["verdict"],
                      "human_label": labels[it["item_id"]]})
    threshold = float(cfg.thresholds["calibration_agreement"])
    result = evaluate(items, threshold, int(cfg.thresholds["calibration_min_sample"]))
    now = utc_now()
    record = {
        "schema_version": SCHEMA_VERSION,
        "judge": pending["identity"],
        "key": identity_key(pending["identity"]),
        "source": pending["source"],
        "seed": pending["seed"],
        "labeled_by": by.strip(),
        "labeled_at": iso(now),
        "threshold": threshold,
        "min_sample": int(cfg.thresholds["calibration_min_sample"]),
        "items": items,
        **result,
    }
    out = cfg.paths["calibration"] / f"{record['key']}-{dir_stamp()}.json"
    write_json(out, record)
    return out


def find_record(cfg: Config, identity: dict[str, Any]) -> Path | None:
    """The newest calibration record for this judge identity, if any."""
    d = cfg.paths["calibration"]
    if not d.is_dir():
        return None
    matches = sorted(d.glob(f"{identity_key(identity)}-*.json"))
    return matches[-1] if matches else None
