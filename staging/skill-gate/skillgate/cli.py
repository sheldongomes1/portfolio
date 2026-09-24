"""The `skillgate` command line."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from skillgate import __version__
from skillgate.util import SkillGateError


def _cfg(args):
    from skillgate.config import load_config

    return load_config(Path(args.config) if args.config else None)


def cmd_lint(args) -> int:
    from skillgate.lint import run_lint
    from skillgate.llm import make_model
    from skillgate.notice import ensure_accepted
    from skillgate.skill import load_document, load_skill

    cfg = _cfg(args)
    skill = load_skill(Path(args.skill) if args.skill else cfg.skill_path, cfg.skill_name)
    refs = [load_document(p) for p in cfg.reference_paths]
    model = None
    if not args.deterministic_only:
        ensure_accepted(cfg.root, "the skill text", "Anthropic", args.yes)
        model = make_model(cfg.judge)
    out = Path(args.out) if args.out else cfg.paths["reports"]
    report = run_lint(skill, refs, out, model)
    c = report["counts"]
    print(f"Lint: {c['high']} high, {c['medium']} medium, {c['low']} low. Wrote {out / 'lint_report.md'} and .json")
    return 0


def cmd_interview(args) -> int:
    from skillgate.cases import golden_stats, load_cases
    from skillgate.interview import import_csv

    cfg = _cfg(args)
    if not args.import_csv:
        print("Interactive interview arrives in milestone 4. Use --import cases.csv (see `skillgate interview -h`).",
              file=sys.stderr)
        return 2
    res = import_csv(Path(args.import_csv), cfg.paths["cases"], cfg.paths["golden"], cfg.thresholds["holdout_share"], args.seed)
    print(f"Imported {len(res['written'])} case(s); {len(res['unchanged'])} unchanged.")
    if res["draw"]:
        d = res["draw"]
        print(f"Drew splits for {len(d['pool'])} new case(s): {d['holdout_count']} to holdout (seed {d['seed']}).")
    stats = golden_stats(load_cases(cfg.paths["cases"]), cfg.thresholds)
    print(f"Golden set: {stats['size']} cases ({stats['splits']['dev']} dev, {stats['splits']['holdout']} holdout).")
    for w in stats["warnings"]:
        print(f"WARNING: {w}")
    return 0


def cmd_split(args) -> int:
    from skillgate.cases import assign_splits, golden_stats, load_cases

    cfg = _cfg(args)
    draw = assign_splits(cfg.paths["cases"], cfg.paths["golden"], cfg.thresholds["holdout_share"], args.seed)
    if draw is None:
        print("Every case already has a split; nothing drawn.")
    else:
        print(f"Drew splits for {len(draw['pool'])} case(s): {draw['holdout_count']} to holdout (seed {draw['seed']}).")
    stats = golden_stats(load_cases(cfg.paths["cases"]), cfg.thresholds)
    print(f"Golden set: {stats['size']} cases ({stats['splits']['dev']} dev, {stats['splits']['holdout']} holdout).")
    for w in stats["warnings"]:
        print(f"WARNING: {w}")
    return 0


def cmd_criteria(args) -> int:
    from skillgate.cases import load_cases
    from skillgate.criteria import coverage, load_criteria, propose, ratify, render_coverage
    from skillgate.llm import make_model
    from skillgate.notice import ensure_accepted
    from skillgate.skill import extract_rules, load_skill
    from skillgate.util import write_json

    cfg = _cfg(args)
    criteria_path = cfg.paths["criteria"]
    skill = load_skill(Path(args.skill) if args.skill else cfg.skill_path, cfg.skill_name)
    rules = extract_rules(skill.text)
    if args.ratify:
        rec = ratify(criteria_path, args.by or "")
        print(f"Ratified {criteria_path.name} (SHA-256 {rec['criteria_sha256'][:12]}…) by {rec['ratified_by']} at {rec['ratified_at']}.")
    elif not args.coverage:
        proposed = criteria_path.with_name("criteria.proposed.yaml")
        model = None
        if not args.no_model:
            ensure_accepted(cfg.root, "the skill's rules", "Anthropic", args.yes)
            model = make_model(cfg.judge)
        meta = propose(skill, rules, proposed, criteria_path.name, model)
        print(f"Drafted {meta['count']} criteria ({meta['mode']}) in {proposed}. Review, save as {criteria_path.name}, then ratify.")
    if criteria_path.is_file():
        try:
            cases = load_cases(cfg.paths["cases"])
        except SkillGateError:
            cases = []
        crit = load_criteria(criteria_path)
        for c in crit:
            for w in c.warnings:
                print(f"WARNING: {w}")
        cov = coverage(rules, crit, cases)
        cov_path = criteria_path.with_name("coverage.md")
        cov_path.write_text(render_coverage(cov, skill), encoding="utf-8")
        write_json(criteria_path.with_name("coverage.json"), cov)
        print(f"Coverage: {cov['covered']} of {cov['rules']} rules covered, {cov['uncovered']} uncovered. Wrote {cov_path}.")
    else:
        cov = coverage(rules, [], [])
        cov_path = criteria_path.with_name("coverage.md")
        cov_path.parent.mkdir(parents=True, exist_ok=True)
        cov_path.write_text(render_coverage(cov, skill), encoding="utf-8")
        print(f"Wrote {cov_path} listing {len(rules)} rules and their keys (no criteria.yaml yet).")
    return 0


def cmd_run(args) -> int:
    from skillgate.run import create_manual_run

    cfg = _cfg(args)
    if args.mode != "manual":
        print("API mode arrives in milestone 3. Use --mode manual.", file=sys.stderr)
        return 2
    run_dir, warnings = create_manual_run(cfg, split=args.split, k=args.k)
    for w in warnings:
        print(f"WARNING: {w}")
    sheets = sorted(p.name for p in run_dir.glob("run_sheet.*.md"))
    print(f"Created {run_dir}. Fill the files in outputs/ using {', '.join(sheets)}, complete capture.yaml, then run `skillgate judge`.")
    return 0


def cmd_judge(args) -> int:
    from skillgate.judge import judge_run
    from skillgate.notice import ensure_accepted
    from skillgate.util import read_json

    cfg = _cfg(args)

    def notice():
        ensure_accepted(cfg.root, "case inputs and the skill's outputs", "Anthropic", args.yes)

    judge_dir = judge_run(cfg, Path(args.run) if args.run else None, on_model_needed=notice)
    s = read_json(judge_dir / "summary.json")
    for sp, x in s["by_split"].items():
        print(f"{sp}: {x['passed']} of {x['cases']} cases passed ({x['failed']} failed, {x['flaky']} flaky, {x['error_cases']} ERROR)")
    print(f"Judgments: {s['totals']['PASS']} PASS, {s['totals']['FAIL']} FAIL, {s['totals']['ERROR']} ERROR. Report: {judge_dir / 'report.md'}")
    return 0


def cmd_receipt(args) -> int:
    from skillgate.receipt import build_receipt
    from skillgate.util import read_json

    cfg = _cfg(args)
    out = build_receipt(cfg, Path(args.run) if args.run else None, Path(args.judge) if args.judge else None)
    r = read_json(out / "receipt.json")
    print(f"{r['verdict']}. Wrote {out / 'receipt.md'} and receipt.json.")
    for reason in r["reasons"]:
        print(f"  - {reason}")
    return 0


def cmd_verify(args) -> int:
    from skillgate.verify import verify_receipt

    problems, checked = verify_receipt(Path(args.receipt), Path(args.root) if args.root else None)
    if problems:
        print(f"MISMATCH: {len(problems)} problem(s) in {args.receipt}")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"OK: {checked} files match their hashes; results, verdict and receipt.md recompute identically.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="skillgate", description="Verification for AI skills.")
    p.add_argument("--version", action="version", version=f"skillgate {__version__}")
    p.add_argument("--config", help="path to skillgate.yaml (default: search upward from the current directory)")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("lint", help="find vague, untestable and missing rules in a skill")
    s.add_argument("skill", nargs="?", help="skill file (.md, .txt or .docx); default from skillgate.yaml")
    s.add_argument("--out", help="directory for lint_report.md/.json (default: paths.reports)")
    s.add_argument("--deterministic-only", action="store_true", help="skip the model pass (no API key needed)")
    s.add_argument("--yes", action="store_true", help="confirm the data-handling notice non-interactively")
    s.set_defaults(func=cmd_lint)

    s = sub.add_parser("interview", help="create golden cases (import from CSV)")
    s.add_argument("skill", nargs="?")
    s.add_argument("--import", dest="import_csv", metavar="CSV", help="import cases from a CSV export")
    s.add_argument("--seed", type=int, help="seed for the holdout draw (default: random, recorded)")
    s.set_defaults(func=cmd_interview)

    s = sub.add_parser("split", help="draw dev/holdout splits for cases that have none (seed recorded)")
    s.add_argument("--seed", type=int, help="seed for the draw (default: random, recorded in golden.yaml)")
    s.set_defaults(func=cmd_split)

    s = sub.add_parser("criteria", help="draft criteria, ratify them, and write coverage.md")
    s.add_argument("skill", nargs="?")
    s.add_argument("--ratify", action="store_true", help="ratify criteria.yaml as it is now")
    s.add_argument("--by", help="who is ratifying (required with --ratify)")
    s.add_argument("--coverage", action="store_true", help="only rewrite coverage.md")
    s.add_argument("--no-model", action="store_true", help="draft a skeleton (one TODO per rule) without a model")
    s.add_argument("--yes", action="store_true")
    s.set_defaults(func=cmd_criteria)

    s = sub.add_parser("run", help="run the golden cases (manual mode: run sheet + output files)")
    s.add_argument("skill", nargs="?")
    s.add_argument("--mode", choices=["manual", "api"], default="manual")
    s.add_argument("--split", choices=["all", "dev", "holdout"], default="all")
    s.add_argument("--k", type=int, help="repeats per case (default: repeats in skillgate.yaml)")
    s.set_defaults(func=cmd_run)

    s = sub.add_parser("judge", help="judge every output of a run")
    s.add_argument("--run", help="run directory (default: latest)")
    s.add_argument("--yes", action="store_true")
    s.set_defaults(func=cmd_judge)

    s = sub.add_parser("receipt", help="write receipt.md and receipt.json for a judged run")
    s.add_argument("--run", help="run directory (default: latest)")
    s.add_argument("--judge", help="judge directory inside the run (default: latest)")
    s.set_defaults(func=cmd_receipt)

    s = sub.add_parser("verify-receipt", help="recompute every hash, result and the verdict of a receipt")
    s.add_argument("receipt", help="path to receipt.json")
    s.add_argument("--root", help="project root (default: the directory holding skillgate.yaml)")
    s.set_defaults(func=cmd_verify)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except SkillGateError as e:
        print(f"skillgate: {e}", file=sys.stderr)
        return 2
