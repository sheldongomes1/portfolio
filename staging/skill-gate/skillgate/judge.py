"""`skillgate judge`: decide every check on every output of a run.

- Deterministic checks first. Everything else goes to the model judge, one
  criterion or expectation per call. The judge sees the output, the case input
  and that single check: never the skill author's notes, never earlier verdicts.
- The judge returns PASS or FAIL, a one-sentence reason, and a verbatim piece
  of evidence from the output. Evidence not found in the output is re-asked
  once; if it is still not found, the judgment is ERROR.
- A check that cannot be completed (API failure after retries, refusal,
  malformed answer, missing output) is ERROR: never PASS, never FAIL.

Judgments are written to a new judge-<time> directory inside the run, one file
per case and repeat, with a JSON-lines log of every model call.
"""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from skillgate.aggregate import aggregate
from skillgate.cases import Case, load_cases
from skillgate.checks import run_check
from skillgate.config import Config
from skillgate.criteria import check_ratified, load_criteria, ratification_path
from skillgate.estimate import check_budget, estimate
from skillgate.llm import JSONModel, LLMError, make_model
from skillgate.prompts import Prompt, load_prompt
from skillgate.util import (
    SkillGateError,
    canonical_json,
    iso,
    new_dir,
    normalize_for_match,
    read_json,
    rel,
    sha256_file,
    dir_stamp,
    utc_now,
    write_json,
)

SCHEMA_VERSION = 1
JUDGE_PROMPT = "judge.v1"

JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": ["PASS", "FAIL"]},
        "reason": {"type": "string"},
        "evidence": {"type": "string"},
    },
    "required": ["verdict", "reason", "evidence"],
    "additionalProperties": False,
}

REASK = (
    "\n\nYour previous answer could not be accepted: {problem} Answer again. The evidence must be "
    "copied exactly, character for character, from the OUTPUT section above."
)


@dataclass
class Check:
    id: str
    kind: str  # criterion | expectation
    text: str
    check: dict[str, Any] | None
    expectation_kind: str | None = None


class CallLog:
    def __init__(self, path: Path, cfg: Config):
        self.path = path
        self.cfg = cfg
        self.lock = threading.Lock()
        self.calls = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.cost_usd = 0.0
        self.cost_known = True
        self.served_models: set[str] = set()

    def write(self, event: dict[str, Any]) -> None:
        with self.lock:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(canonical_json({"ts": iso(utc_now()), **event}) + "\n")

    def call(self, model: str, served: str | None, inp: int, out: int, **extra: Any) -> None:
        cost = self.cfg.price(model, inp, out)
        with self.lock:
            self.calls += 1
            self.input_tokens += inp
            self.output_tokens += out
            if served:
                self.served_models.add(served)
            if cost is None:
                self.cost_known = False
            else:
                self.cost_usd += cost
        self.write({"event": "model_call", "model": model, "served_model": served, "input_tokens": inp,
                    "output_tokens": out, "cost_usd": cost, **extra})


def judge_with_model(model: JSONModel, prompt: Prompt, check: Check, case_input: str, output: str,
                     log: CallLog, where: dict[str, Any]) -> dict[str, Any]:
    system, user = prompt.render(INPUT=case_input, OUTPUT=output, CHECK=check.text)
    attempts = 0
    problem = None
    served = None
    while attempts < 2:
        attempts += 1
        message = user if problem is None else user + REASK.format(problem=problem)
        try:
            result = model.complete_json(system=system, user=message, schema=JUDGE_SCHEMA)
        except LLMError as e:
            log.call(model.model, None, 0, 0, outcome="error", error=str(e), attempt=attempts, **where)
            return {"verdict": "ERROR", "reason": f"Judge call failed: {e}", "evidence": "", "attempts": attempts,
                    "served_model": served}
        served = result.served_model
        data = result.data
        verdict = data.get("verdict")
        evidence = str(data.get("evidence", ""))
        if verdict not in ("PASS", "FAIL"):
            problem = f"the verdict was {verdict!r}; it must be PASS or FAIL."
        elif not output.strip():
            problem = None if not evidence.strip() else "the output is empty, so the evidence must be empty."
        elif not evidence.strip():
            problem = "the evidence was empty."
        elif normalize_for_match(evidence) not in normalize_for_match(output):
            problem = "the evidence was not found in the output."
        else:
            problem = None
        log.call(model.model, served, result.input_tokens, result.output_tokens,
                 outcome="ok" if problem is None else "rejected", problem=problem, attempt=attempts, **where)
        if problem is None:
            return {"verdict": verdict, "reason": str(data.get("reason", "")).strip(), "evidence": evidence,
                    "attempts": attempts, "served_model": served}
    return {"verdict": "ERROR", "reason": f"Judge answer rejected twice: {problem}", "evidence": "",
            "attempts": attempts, "served_model": served}


def build_checks(criteria: list, case: Case) -> list[Check]:
    out = [Check(c.id, "criterion", c.text, c.check) for c in criteria]
    out += [Check(e.id, "expectation", e.text, e.check, e.kind) for e in case.expectations]
    return out


def latest_run(runs_dir: Path) -> Path:
    runs = sorted(p for p in Path(runs_dir).glob("*") if (p / "run.json").is_file())
    if not runs:
        raise SkillGateError(f"No runs in {runs_dir}. Start one with `skillgate run`.")
    return runs[-1]


def judge_run(cfg: Config, run_dir: Path | None = None, *,
              model_factory: Callable[[], JSONModel] | None = None,
              on_model_needed: Callable[[], None] | None = None,
              confirm_budget: bool = False) -> Path:
    run_dir = Path(run_dir) if run_dir else latest_run(cfg.paths["runs"])
    run = read_json(run_dir / "run.json")
    root = cfg.root
    k = int(run["k"])

    cases_by_id = {c.id: c for c in load_cases(cfg.paths["cases"], require_ready=True)}
    for rc in run["cases"]:
        c = cases_by_id.get(rc["id"])
        if c is None:
            raise SkillGateError(f"case {rc['id']} was in the run but its file is gone")
        if c.sha256 != rc["sha256"] or c.input_file_hashes(root) != rc["input_files"]:
            raise SkillGateError(f"case {rc['id']} changed after the run started; start a new run")

    criteria_path = cfg.paths["criteria"]
    ratification = check_ratified(criteria_path)
    criteria = load_criteria(criteria_path)
    prompt = load_prompt(JUDGE_PROMPT)

    plan = []
    for rc in run["cases"]:
        case = cases_by_id[rc["id"]]
        checks = build_checks(criteria, case)
        for r in range(1, k + 1):
            out_path = run_dir / "outputs" / case.id / f"{r}.md"
            plan.append((case, r, out_path, checks))

    # In API mode, execution.json says which repeats produced an output. A repeat whose
    # executor call failed is ERROR; a completed but empty answer is judged like any other.
    execution = read_json(run_dir / "execution.json") if run["mode"] == "api" else None
    if run["mode"] == "api" and execution is None:
        raise SkillGateError(f"{run_dir.name}: API run has no execution.json; it did not finish")

    def exec_status(case_id: str, r: int) -> dict[str, Any] | None:
        return execution["outputs"].get(f"{case_id}/{r}") if execution else None

    needs_model = any(ch.check is None for _, _, _, checks in plan for ch in checks)
    model = None
    if needs_model:
        outputs = {f"{c.id}/{r}": (p.read_text(encoding="utf-8") if p.is_file() else "") for c, r, p, _ in plan}
        est = estimate(cfg, cases=[cases_by_id[rc["id"]] for rc in run["cases"]], criteria=criteria, k=k,
                       mode="judge", outputs=outputs)
        check_budget(cfg, est, confirm_budget, "judging this run")
        if on_model_needed:
            on_model_needed()
        model = model_factory() if model_factory else make_model(cfg.judge)

    started = utc_now()
    judge_dir = new_dir(run_dir / f"judge-{dir_stamp()}")
    log = CallLog(judge_dir / "log.jsonl", cfg)
    log.write({"event": "start", "run_id": run["run_id"], "judge_model": cfg.judge.model})

    output_hashes: dict[str, str] = {}

    def judge_one(item: tuple) -> list[dict[str, Any]]:
        case, r, out_path, checks = item
        output = out_path.read_text(encoding="utf-8") if out_path.is_file() else ""
        case_input = case.rendered_input(root)
        results = []
        for ch in checks:
            base = {"case_id": case.id, "split": case.split, "repeat": r, "check_id": ch.id,
                    "check_kind": ch.kind, "expectation_kind": ch.expectation_kind}
            status = exec_status(case.id, r)
            if status is not None and status["status"] != "ok":
                results.append({**base, "method": "none", "verdict": "ERROR",
                                "reason": f"The executor produced no output: {status.get('error', status['status'])}",
                                "evidence": ""})
            elif execution is None and not output.strip():
                results.append({**base, "method": "none", "verdict": "ERROR",
                                "reason": "Output file is missing or empty; the case was not run.", "evidence": ""})
            elif ch.check is not None:
                verdict, reason, evidence = run_check(ch.check, output, case_input)
                results.append({**base, "method": "deterministic", "check_type": ch.check["type"],
                                "verdict": verdict, "reason": reason, "evidence": evidence})
            else:
                res = judge_with_model(model, prompt, ch, case_input, output, log,
                                       {"case_id": case.id, "repeat": r, "check_id": ch.id})
                results.append({**base, "method": "model", **res})
        return results

    for case, r, out_path, _ in plan:
        output_hashes[f"{case.id}/{r}"] = sha256_file(out_path) if out_path.is_file() else ""

    with ThreadPoolExecutor(max_workers=cfg.judge.concurrency if model else 1) as pool:
        batches = list(pool.map(judge_one, plan))

    all_judgments = []
    for (case, r, _, _), results in zip(plan, batches):
        results.sort(key=lambda j: (j["check_kind"], j["check_id"]))
        write_json(judge_dir / "judgments" / case.id / f"{r}.json", results)
        all_judgments.extend(results)

    summary = aggregate(all_judgments, [{"id": rc["id"], "split": rc["split"]} for rc in run["cases"]], k)
    finished = utc_now()
    meta = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run["run_id"],
        "judge_id": judge_dir.name,
        "started_at": iso(started),
        "finished_at": iso(finished),
        "judge": {
            "provider": cfg.judge.provider,
            "model": cfg.judge.model,
            "settings": cfg.judge.settings,
            "max_retries": cfg.judge.max_retries,
            "used": model is not None,
            "served_models": sorted(log.served_models),
        },
        "prompts": {JUDGE_PROMPT: {"path": rel(prompt.path, prompt.path.parent.parent), "sha256": prompt.sha256}},
        "criteria": {"path": rel(criteria_path, root), "sha256": sha256_file(criteria_path),
                     "ratification_path": rel(ratification_path(criteria_path), root), **ratification},
        "outputs": output_hashes,
        "calls": {"model_calls": log.calls, "input_tokens": log.input_tokens, "output_tokens": log.output_tokens,
                  "cost_usd": round(log.cost_usd, 6) if log.cost_known else None},
    }
    write_json(judge_dir / "judge.json", meta)
    write_json(judge_dir / "summary.json", summary)
    (judge_dir / "report.md").write_text(render_report(meta, summary, cases_by_id), encoding="utf-8")
    log.write({"event": "finish", **meta["calls"]})
    return judge_dir


def render_report(meta: dict[str, Any], summary: dict[str, Any], cases: dict[str, Case]) -> str:
    """The run report. Holdout cases show counts and IDs only: no inputs, reasons or evidence."""
    lines = [f"# Judge report: run `{meta['run_id']}`", "",
             f"Judge `{meta['judge']['model']}` · {summary['k']} repeat(s) · {meta['finished_at']}", "",
             "| Split | Cases | Passed | Failed | Flaky | ERROR cases | ERROR judgments |", "|---|---|---|---|---|---|---|"]
    for sp, s in summary["by_split"].items():
        lines.append(f"| {sp} | {s['cases']} | {s['passed']} | {s['failed']} | {s['flaky']} | {s['error_cases']} | {s['error_judgments']} |")
    lines += ["", f"Misses (expected issue not caught): {len(summary['misses'])}. "
              f"False flags (issue raised on a should-not-flag check): {len(summary['false_flags'])}.", ""]
    lines += ["## Dev cases that did not pass", ""]
    any_dev = False
    for cid, pc in summary["per_case"].items():
        if pc["split"] != "dev" or pc["status"] == "PASS":
            continue
        any_dev = True
        lines.append(f"### `{cid}`: {pc['status']} ({pc['repeats_passed']} of {pc['repeats']} repeats passed)")
        for fc in pc["failed_checks"]:
            text = next((e.text for e in cases[cid].expectations if e.id == fc["check_id"]), None) if fc["check_kind"] == "expectation" else None
            label = f"{fc['check_id']}" + (f" ({text})" if text else "")
            for rr in fc["reasons"]:
                lines.append(f"- {label}, repeat {rr['repeat']}: **{rr['verdict']}**. {rr['reason']}")
        lines.append("")
    if not any_dev:
        lines += ["None.", ""]
    lines += ["## Holdout cases", "", "Details are withheld so the skill cannot be tuned against them.", ""]
    for cid, pc in summary["per_case"].items():
        if pc["split"] == "holdout":
            lines.append(f"- `{cid}`: {pc['status']}")
    return "\n".join(lines).rstrip() + "\n"
