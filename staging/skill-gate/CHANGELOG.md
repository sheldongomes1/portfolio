# Changelog

Newest first.

## 0.3.1 — 2026-09-25 — Local setup

### Added
- API keys are read from the nearest `.env` (the working directory up to the repository root);
  the shell's own variables take precedence. `.env.example` is the template.
- `setup.sh`: virtual environment, install, tests and `.env` in one step.
- `CLAUDE.md`: project rules, status and key checks for Claude Code.

### Changed
- `skillgate.yaml.example` names `gemini-3.8-flash` with its paid-tier price, both checked on
  Google's model and pricing pages on 2026-09-25.
- With `SKILLGATE_LIVE=1`, the live test also reads the key from `.env`.

## 0.3.0 — 2026-09-25 — Milestone 3: API mode, cost, calibration, staleness

### Added
- `skillgate estimate`: model calls, tokens and cost for the executor and the judge, estimated
  offline. `run --mode api` and `judge` stop above `budget.max_usd` unless `--confirm-budget`;
  a model without a configured price cannot be estimated, so paid steps refuse to start.
- `skillgate run --mode api`: runs each case `k` times through Gemini (google-genai SDK), with the
  skill and reference files assembled by the versioned `prompts/executor.v1.md`. Checks the
  model exists before any paid call and records its reported version and every setting. Outputs
  are cached by skill, references, case, model, settings, prompt and repeat; failures are not
  cached and become ERROR in judging. API-mode receipts are flagged API EMULATION.
- `skillgate calibrate`: a blind, stratified sample of dev-case model judgments, labeled in the
  terminal or through an exported sheet. Agreement is counted overall and on FAIL verdicts; the
  record is tied to the judge's model, settings and prompt hash, and receipts look it up.
- `skillgate check-stale`: STALE (exit 1) when the skill, a reference, a model or its settings, a
  prompt, the criteria or the golden cases differ from the latest receipt.
- CI: tests, `verify-receipt` on every committed receipt, `check-stale` on the example.
- `verify-receipt` also recomputes the calibration from its record and labeled judgments.

### Changed
- Run, judgment and receipt folders carry microseconds in their names, so two created in the
  same second never collide.
- `receipt.md` lists every prompt hash (judge and executor) in sorted order.

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
