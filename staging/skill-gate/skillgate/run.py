"""`skillgate run`: produce the outputs to judge.

`--mode manual` writes a run sheet and empty output files to fill by hand.
`--mode api` runs each case through the executor model (see executor.py),
with a cost estimate and budget check first and a cache so unchanged work is
never paid for twice.

There is no known API for running a Google Workspace skill, so manual mode is
the faithful path: a person pastes each case into the Gemini side panel, k
times, and saves each answer. Skill Gate then only judges. Every run gets its
own time-stamped directory and is never overwritten.

The holdout run sheet is a separate file, so the skill author can work from the
dev sheet without seeing held-out inputs. Ideally someone other than the author
runs the holdout sheet, after the skill is frozen.
"""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from skillgate.cache import Cache, cache_key
from skillgate.cases import Case, load_cases, load_golden, verify_splits
from skillgate.config import Config
from skillgate.criteria import load_criteria
from skillgate.prompts import load_prompt
from skillgate.skill import Document, Skill, load_document, load_skill
from skillgate.util import (
    SkillGateError,
    canonical_json,
    dump_yaml,
    iso,
    new_dir,
    rel,
    sha256_file,
    dir_stamp,
    utc_now,
    write_json,
)

if TYPE_CHECKING:
    from skillgate.executor import Executor

SCHEMA_VERSION = 1

CAPTURE_TEMPLATE = {
    "surface": "",
    "run_date": "",
    "operator": "",
    "notes": "",
}

CAPTURE_HELP = """\
# Fill this in when the outputs are saved. The receipt records it.
# surface:  where the skill ran, e.g. "Gemini side panel in Google Docs"
# run_date: the date the outputs were produced (YYYY-MM-DD)
# operator: who pasted the inputs and saved the outputs
"""


def select_cases(cases: list[Case], split: str) -> list[Case]:
    if split == "all":
        return cases
    return [c for c in cases if c.split == split]


def _prepare(cfg: Config, split: str) -> tuple[Skill, list[Document], list[Case]]:
    skill = load_skill(cfg.skill_path, cfg.skill_name)
    refs = [load_document(p) for p in cfg.reference_paths]
    cases = load_cases(cfg.paths["cases"], require_ready=True)
    problems = verify_splits(cases, load_golden(cfg.paths["golden"]))
    if problems:
        raise SkillGateError("Split assignment does not match golden.yaml:\n  " + "\n  ".join(problems))
    chosen = select_cases(cases, split)
    if not chosen:
        raise SkillGateError(f"No cases in split '{split}'")
    return skill, refs, chosen


def config_models(cfg: Config) -> dict[str, Any]:
    """The model IDs and settings in skillgate.yaml, recorded so check-stale can compare them."""
    def one(m):
        return None if m is None else {"provider": m.provider, "model": m.model, "settings": m.settings}
    return {"executor": one(cfg.executor), "judge": one(cfg.judge)}


def _run_record(cfg: Config, run_dir: Path, created, mode: str, k: int, split: str, skill: Skill,
                refs: list[Document], chosen: list[Case], executor: dict[str, Any]) -> dict[str, Any]:
    root = cfg.root
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_dir.name,
        "mode": mode,
        "created_at": iso(created),
        "k": k,
        "split": split,
        "config": {"path": rel(cfg.path, root), "sha256": cfg.sha256},
        "config_models": config_models(cfg),
        "skill": {"name": skill.name, "version": skill.version, "path": rel(skill.path, root), "sha256": skill.sha256},
        "references": [{"path": rel(r.path, root), "sha256": r.sha256} for r in refs],
        "executor": executor,
        "cases": [
            {
                "id": c.id,
                "split": c.split,
                "path": rel(c.path, root),
                "sha256": c.sha256,
                "input_files": c.input_file_hashes(root),
            }
            for c in chosen
        ],
    }


def create_manual_run(cfg: Config, *, split: str = "all", k: int | None = None) -> tuple[Path, list[str]]:
    k = k or cfg.repeats
    warnings = []
    if k == 1:
        warnings.append("k=1: the receipt will be marked SINGLE RUN and VERIFIED will be withheld.")
    skill, refs, chosen = _prepare(cfg, split)
    created = utc_now()
    run_dir = new_dir(cfg.paths["runs"] / f"{dir_stamp()}-manual")
    root = cfg.root
    executor = {"kind": "manual", "note": "Outputs pasted by a person; Skill Gate did not call the model."}
    write_json(run_dir / "run.json", _run_record(cfg, run_dir, created, "manual", k, split, skill, refs, chosen, executor))
    (run_dir / "capture.yaml").write_text(CAPTURE_HELP + dump_yaml(CAPTURE_TEMPLATE), encoding="utf-8")
    for c in chosen:
        d = run_dir / "outputs" / c.id
        d.mkdir(parents=True)
        for r in range(1, k + 1):
            (d / f"{r}.md").write_text("", encoding="utf-8")
    for sp in ("dev", "holdout"):
        subset = [c for c in chosen if c.split == sp]
        if subset:
            (run_dir / f"run_sheet.{sp}.md").write_text(render_sheet(skill.name, run_dir.name, sp, subset, k, root), encoding="utf-8")
    return run_dir, warnings


def executor_cache_keys(cfg: Config, skill: Skill, refs: list[Document], cases: list[Case], k: int) -> dict[str, str]:
    from skillgate.executor import EXECUTOR_PROMPT

    prompt_sha = load_prompt(EXECUTOR_PROMPT).sha256
    keys = {}
    for c in cases:
        for r in range(1, k + 1):
            keys[f"{c.id}/{r}"] = cache_key(
                skill=skill.sha256,
                references=sorted(d.sha256 for d in refs),
                case=c.sha256,
                case_inputs=c.input_file_hashes(cfg.root),
                model=cfg.executor.model,
                settings=cfg.executor.settings,
                prompt=prompt_sha,
                repeat=r,
            )
    return keys


def create_api_run(cfg: Config, *, split: str = "all", k: int | None = None, confirm_budget: bool = False,
                   executor_factory: Callable[[], Executor] | None = None,
                   on_paid: Callable[[], None] | None = None) -> tuple[Path, dict[str, Any]]:
    """Run every chosen case k times through the executor, using the cache where possible."""
    from skillgate.estimate import check_budget, estimate
    from skillgate.executor import EXECUTOR_PROMPT, ExecutorError, assemble, make_executor

    k = k or cfg.repeats
    if cfg.executor is None:
        raise SkillGateError("API mode needs an executor section in skillgate.yaml")
    skill, refs, chosen = _prepare(cfg, split)
    criteria = load_criteria(cfg.paths["criteria"])
    keys = executor_cache_keys(cfg, skill, refs, chosen, k)
    est = estimate(cfg, cases=chosen, criteria=criteria, k=k, mode="api", skill=skill, references=refs, cache_keys=keys)
    check_budget(cfg, est, confirm_budget, "this run and its judging")
    cache = Cache(cfg.paths["cache"])
    executor = None
    if est["executor"]["calls"]:
        if on_paid:
            on_paid()
        executor = executor_factory() if executor_factory else make_executor(cfg.executor)
        verified = executor.describe()
    else:
        verified = {"note": "every output came from the cache; the model was not called"}

    created = utc_now()
    run_dir = new_dir(cfg.paths["runs"] / f"{dir_stamp()}-api")
    root = cfg.root
    prompt_sha = load_prompt(EXECUTOR_PROMPT).sha256
    executor_info = {"kind": "api", "provider": cfg.executor.provider, "model": cfg.executor.model,
                     "settings": cfg.executor.settings, "model_check": verified,
                     "prompt": {EXECUTOR_PROMPT: prompt_sha}}
    write_json(run_dir / "run.json", _run_record(cfg, run_dir, created, "api", k, split, skill, refs, chosen, executor_info))
    log_path = run_dir / "log.jsonl"
    lock = threading.Lock()

    def log(event: dict[str, Any]) -> None:
        with lock, open(log_path, "a", encoding="utf-8") as f:
            f.write(canonical_json({"ts": iso(utc_now()), **event}) + "\n")

    def one(item: tuple[Case, int]) -> tuple[str, dict[str, Any], str]:
        case, r = item
        key = keys[f"{case.id}/{r}"]
        hit = cache.get(key)
        if hit is not None:
            log({"event": "cache_hit", "case_id": case.id, "repeat": r, "key": key})
            return f"{case.id}/{r}", {**hit["meta"], "status": "ok", "cached": True, "cost_usd": 0.0, "cache_key": key}, hit["text"]
        system, user, _ = assemble(skill, refs, case.rendered_input(root))
        try:
            res = executor.run(system=system, user=user)
        except ExecutorError as e:
            log({"event": "executor_call", "case_id": case.id, "repeat": r, "outcome": "error", "error": str(e)})
            return f"{case.id}/{r}", {"status": "error", "cached": False, "error": str(e), "cache_key": key}, ""
        cost = cfg.price(cfg.executor.model, res.input_tokens, res.output_tokens + res.thinking_tokens)
        meta = {"served_model": res.served_model, "finish_reason": res.finish_reason, "input_tokens": res.input_tokens,
                "output_tokens": res.output_tokens, "thinking_tokens": res.thinking_tokens}
        cache.put(key, {"meta": meta, "text": res.text, "created_at": iso(utc_now())})
        log({"event": "executor_call", "case_id": case.id, "repeat": r, "outcome": "ok", "cost_usd": cost, **meta})
        return f"{case.id}/{r}", {**meta, "status": "ok", "cached": False, "cost_usd": cost, "cache_key": key}, res.text

    items = [(c, r) for c in chosen for r in range(1, k + 1)]
    with ThreadPoolExecutor(max_workers=cfg.executor.concurrency) as pool:
        results = list(pool.map(one, items))

    outputs: dict[str, Any] = {}
    for key, meta, text in results:
        cid, r = key.split("/")
        path = run_dir / "outputs" / cid / f"{r}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        outputs[key] = {**meta, "sha256": sha256_file(path)}
    calls = sum(1 for m in outputs.values() if not m["cached"])
    costs = [m.get("cost_usd") for m in outputs.values() if not m["cached"] and m["status"] == "ok"]
    execution = {
        "schema_version": SCHEMA_VERSION,
        "finished_at": iso(utc_now()),
        "outputs": dict(sorted(outputs.items())),
        "calls": calls,
        "cache_hits": sum(1 for m in outputs.values() if m["cached"]),
        "errors": sum(1 for m in outputs.values() if m["status"] != "ok"),
        "served_models": sorted({m["served_model"] for m in outputs.values() if m.get("served_model")}),
        "cost_usd": None if any(c is None for c in costs) else round(sum(costs), 6),
    }
    write_json(run_dir / "execution.json", execution)
    return run_dir, execution


def render_sheet(skill_name: str, run_id: str, split: str, cases: list[Case], k: int, root: Path) -> str:
    lines = [
        f"# Run sheet: {skill_name}, {split} split",
        "",
        f"Run `{run_id}`. {len(cases)} case(s), {k} repeat(s) each.",
        "",
    ]
    if split == "holdout":
        lines += [
            "**Held-out cases.** The skill's author should not read this sheet. Ideally someone else",
            "runs it, after the skill is frozen for this run.",
            "",
        ]
    lines += [
        "For each case and each repeat:",
        "",
        "1. Start a fresh Gemini conversation (so earlier cases do not influence the answer).",
        "2. Paste the input below exactly as shown, including the @mention line if there is one.",
        "3. Copy the complete answer into the output file named for that repeat. Do not edit it.",
        "",
        "When all files are filled, complete `capture.yaml`, then run `skillgate judge`.",
        "",
    ]
    for c in cases:
        fence = "````"
        lines += [f"## Case `{c.id}`", "", fence, c.rendered_input(root).rstrip(), fence, ""]
        lines += [f"- Repeat {r}: `outputs/{c.id}/{r}.md`" for r in range(1, k + 1)]
        lines.append("")
    return "\n".join(lines)
