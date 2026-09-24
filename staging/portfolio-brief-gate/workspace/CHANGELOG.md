# Changelog: Portfolio Brief Gate, Workspace edition

Newest first. Bump the version line at the top of `skill.md` on every change.

## 1.0.0 — 2026-09-24

First Workspace edition, derived from Portfolio Brief Gate v1.0 (commit `e852573`).

### Added
- `skill.md`: the six-stage workflow rewritten for a Gemini skill invoked by @mention, with a
  version line, an input-handling table, an input-trust rule and a fixed footer.
- `reference/`: severity rubric, watermelon check, self-check (from `judge.md`), output format
  (from `templates.md`) and a worked example with a PASSED and a FLAGGED output.
- `examples/`: ten test inputs with binary expected behavior (R1.8 and R1.5 cases), plus the
  validator input that checks the worked example's quotes.
- `MAPPING.md`: every wording change from the original, with its reason.

### Changed (from the original; details in MAPPING.md)
- An evidence quote is required for every grade, not only grades 4 and 5.
- One fixed gate line replaces the original's two banner spellings.
- The appendix becomes an Evidence ledger holding every quote next to its update ID.
- The judge is renamed Self-Check and no longer calls `validate_quotes.py`.

### Not yet done
- Not yet run inside Google Workspace. Record the first run here: date, surface (Gmail, Docs,
  Slides, Drive or Chat), how reference files were attached, and anything that behaved
  differently from `skill.md`.
