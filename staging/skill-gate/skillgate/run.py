"""`skillgate run --mode manual`: a run sheet and empty output files to fill by hand.

There is no known API for running a Google Workspace skill, so manual mode is
the faithful path: a person pastes each case into the Gemini side panel, k
times, and saves each answer. Skill Gate then only judges. Every run gets its
own time-stamped directory and is never overwritten.

The holdout run sheet is a separate file, so the skill author can work from the
dev sheet without seeing held-out inputs. Ideally someone other than the author
runs the holdout sheet, after the skill is frozen.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from skillgate.cases import Case, load_cases, load_golden, verify_splits
from skillgate.config import Config
from skillgate.skill import load_document, load_skill
from skillgate.util import SkillGateError, dump_yaml, iso, new_dir, rel, stamp, utc_now, write_json

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


def create_manual_run(cfg: Config, *, split: str = "all", k: int | None = None) -> tuple[Path, list[str]]:
    k = k or cfg.repeats
    warnings = []
    if k == 1:
        warnings.append("k=1: the receipt will be marked SINGLE RUN and VERIFIED will be withheld.")
    skill = load_skill(cfg.skill_path, cfg.skill_name)
    refs = [load_document(p) for p in cfg.reference_paths]
    cases = load_cases(cfg.paths["cases"], require_ready=True)
    problems = verify_splits(cases, load_golden(cfg.paths["golden"]))
    if problems:
        raise SkillGateError("Split assignment does not match golden.yaml:\n  " + "\n  ".join(problems))
    chosen = select_cases(cases, split)
    if not chosen:
        raise SkillGateError(f"No cases in split '{split}'")

    created = utc_now()
    run_dir = new_dir(cfg.paths["runs"] / f"{stamp(created)}-manual")
    root = cfg.root
    run: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_dir.name,
        "mode": "manual",
        "created_at": iso(created),
        "k": k,
        "split": split,
        "config": {"path": rel(cfg.path, root), "sha256": cfg.sha256},
        "skill": {"name": skill.name, "version": skill.version, "path": rel(skill.path, root), "sha256": skill.sha256},
        "references": [{"path": rel(r.path, root), "sha256": r.sha256} for r in refs],
        "executor": {"kind": "manual", "note": "Outputs pasted by a person; Skill Gate did not call the model."},
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
    write_json(run_dir / "run.json", run)
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
