# Skill Gate: notes for Claude Code

Skill Gate is a CLI that verifies AI skills: golden cases with a held-out split, k repeated
runs, one binary check per judge call, a calibrated judge, and a receipt whose every input is
hashed. It is built from the owner's PRD ("Skill Gate + Portfolio Brief Gate for Google
Workspace", v2).

## Where things are

- This folder is staged inside the owner's public `portfolio` repo. After the build it becomes
  its own `skill-gate` repository (ASSUMPTIONS A1). The Portfolio Brief Gate Workspace edition
  (PRD D1) is staged next door, in `../portfolio-brief-gate/workspace/`.
- The PRD is `PRD.md` in this folder. It is git-ignored because the repo is public: never commit
  it or quote large parts of it into committed files. If it is missing, ask the owner to copy it
  in.
- `ASSUMPTIONS.md` records every interpretation (A1–A51 so far). `CHANGELOG.md` has what each
  milestone added.

## Rules from the PRD (section 0), plus the owner's

1. Work milestone by milestone (PRD §11). At the end of each one, show the acceptance checklist
   with PASS/FAIL per item, then stop and wait for the owner's approval.
2. Fictional data only: no employer data, real client names or real invoices.
3. Keys come from `ANTHROPIC_API_KEY` and `GEMINI_API_KEY`. Never print, hardcode or commit them.
4. Model IDs live in config, never in code. They must be exact versions; `-latest` aliases are
   rejected. Verify them from official docs (or the provider's API) before relying on them.
5. Don't invent facts about Google Workspace skills. What is known is in PRD §3; anything else
   is an open question (§12).
6. When the PRD is ambiguous, pick the stricter reading and log it in `ASSUMPTIONS.md` with the
   next number.
7. The owner labels calibration samples. Never fill in `labels.csv` or answer `skillgate
   calibrate` prompts yourself: a calibration labeled by the model it measures is worthless.
8. Don't put model identifiers in commit messages or PR descriptions.

## Status

- M1 (PBG Workspace edition), M2 (core CLI) and M3 (API mode, estimate and budget cap,
  calibration, check-stale, CI) are done and merged (portfolio PRs #1–#3).
- **Next: M4**, only after the owner says go. It covers the interactive `interview`, the D2b
  skill (`SKILL.md` plus Gemini Gem instructions), the invoice dataset and four-step demo, the
  PBG dogfood receipt, `SPEC.md` and `docs/one-pager.md`. It is accepted when every PRD §7
  checkbox passes. Layout is in PRD §8.
- API mode has not yet run against the real Gemini API. The first real run is part of M4.

## Setup and commands

```bash
./setup.sh                    # once: .venv, install, tests, .env from .env.example
. .venv/bin/activate
pytest                        # all model calls are faked
ruff check --select F,E9 .
SKILLGATE_LIVE=1 pytest tests/test_live.py    # one real judge call (costs a few cents)
```

`skillgate` loads `.env` itself: from the working directory, or the nearest parent up to the
repo root. Each Bash tool call starts a fresh shell, so when calling an SDK directly, load the
file in the same command: `set -a; . ./.env; set +a; python ...`.

Check the keys without spending anything (model lookups are free):

```bash
set -a; . ./.env; set +a
python -c "import anthropic; print(anthropic.Anthropic().models.retrieve('claude-opus-5').id)"
python -c "from google import genai; m = genai.Client().models.get(model='gemini-3.8-flash'); print(m.name, m.version)"
```

Before pushing, run what CI runs (`../../.github/workflows/skill-gate.yml`): `pytest`, then
`skillgate verify-receipt` on every committed `*/receipts/*/receipt.json`, then `skillgate
check-stale` in `examples/refund-triage`. If a change alters receipts, the committed example
stops verifying: regenerate it with `examples/refund-triage/reproduce.sh`. Receipts and runs
are never overwritten, so delete the old example run and receipt folders first.

## Checked facts (2026-09-25)

- Judge: `claude-opus-5` (A18). Settings are `effort` and `max_tokens`; the model rejects
  `temperature` and `top_p`. No refusal fallback: a refusal is ERROR (A19).
- Executor: `gemini-3.8-flash` is a stable model ID on ai.google.dev (models page). The paid
  tier costs $0.75 input and $3.75 output per million tokens (output includes thinking) until
  2026-12-31, then $1.50 and $7.50. It supports thinking levels low, medium and high; `minimal`
  returns an error. Gemini 3.1 Pro exists only as a preview, which can change or be retired on
  two weeks' notice, so it is not used.
- Google's pricing page says free-tier requests are used to improve Google's products and
  paid-tier requests are not.
- google-genai sends the key in the `x-goog-api-key` header.

## Code map

`skillgate/`: `cli.py` (commands), `config.py` (skillgate.yaml, model-ID rules), `envfile.py`
(.env), `skill.py` (loading and rule extraction), `lint.py`, `cases.py` and `interview.py`
(golden cases and splits), `criteria.py`, `checks.py` (deterministic checks), `run.py` (manual
and API runs), `executor.py` (Gemini), `cache.py`, `estimate.py`, `llm.py` (Anthropic client),
`judge.py`, `aggregate.py`, `calibrate.py`, `receipt.py`, `verify.py`, `stale.py`, `notice.py`
(data-handling confirmation). Prompts are versioned files in `prompts/` and hashed into every receipt.
