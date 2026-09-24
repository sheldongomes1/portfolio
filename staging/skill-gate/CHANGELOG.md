# Changelog

Newest first.

## 0.2.0 — 2026-09-24 — Milestone 2: core

### Added
- `skillgate lint`: deterministic findings (vague wording, missing output format, no bad-input
  behavior, no guard against instructions in the input, no examples, missing references), each
  with a line, category, severity and suggested rewrite; optional model pass for untestable and
  conflicting rules, with quote validation. Writes `lint_report.md` and `.json`.
- Golden case schema (one YAML file per case) with `split`, `source`, confirmation fields and
  expectation kinds (`detect`, `no_flag`, `other`).
- `skillgate interview --import cases.csv` and `skillgate split`: holdout drawn at random with a
  recorded, recomputable seed; a `split` column in the CSV is refused.
- `skillgate criteria`: draft (model or skeleton), `--ratify --by`, and `coverage.md` mapping
  skill rules to checks.
- `skillgate run --mode manual`: time-stamped run directory, run sheet per split, `k` empty
  output files per case, `capture.yaml`.
- Deterministic checks: regex, contains, required sections, verbatim quotes (whole input or by
  source segment, reusing Portfolio Brief Gate's validator logic).
- `skillgate judge`: deterministic checks first, then one model call per check with verbatim
  evidence validation, one re-ask, and ERROR for anything that cannot be completed; JSON-lines
  call log with tokens and cost.
- `skillgate receipt` and `skillgate verify-receipt`, with an artifact manifest, recomputed
  results and verdict, and holdout redaction.
- `examples/refund-triage`: a key-free example with a committed receipt.
- 66 tests: every model call is faked; one opt-in live test is skipped by default.

## 0.1.0 — 2026-09-24 — Milestone 1

- `ASSUMPTIONS.md` started alongside Portfolio Brief Gate, Workspace edition.
