# Skill Gate

Verification for AI skills: the reusable prompts that teams now write for Gemini in Google
Workspace, for Claude, or for any other model.

A skill that looks right on one test input can still fail on the twentieth input, on the unusual
one, or on the second run of the same input. Skill Gate turns "it looked fine" into a receipt:

- golden cases written with the expert who owns the process, with at least 30% held out at
  random so the author cannot tune against them;
- every case run `k` times; a case passes only if it passes every time;
- every check binary, PASS or FAIL, one check per judge call, with verbatim evidence;
- a check that could not be completed is **ERROR**, never PASS or FAIL, and blocks VERIFIED;
- no averages anywhere: results are counts;
- a receipt listing the SHA-256 of every file it rests on, which `verify-receipt` recomputes.

> **Data handling.** Skill Gate sends the skill, its reference files, case inputs and skill
> outputs to external model APIs (Anthropic for judging and linting; Google, from milestone 3,
> for API-mode runs). Use fictional data, or get the data owner's approval before running it on
> anything confidential. The first command that would send data asks you to confirm.

## Status

This is being built in milestones (PRD v2). **Milestone 2 (core) is done:**

| Command | Status |
|---|---|
| `lint` | done: deterministic checks, plus an optional model pass |
| `interview --import cases.csv` | done; the interactive interview is milestone 4 |
| `split` | done: draws dev/holdout splits with a recorded seed |
| `criteria` (draft, ratify, coverage) | done |
| `run --mode manual` | done, with repeats |
| `judge` | done: deterministic checks, model judge, ERROR handling |
| `receipt`, `verify-receipt` | done |
| `estimate`, `run --mode api`, `calibrate`, `check-stale`, CI | milestone 3 |
| Skill Gate skill (`skill/`), invoice demo, SPEC.md, one-pager | milestone 4 |

Until `calibrate` exists, any receipt that used the model judge is marked `JUDGE UNCALIBRATED`
and cannot be VERIFIED. A run decided entirely by deterministic checks needs no calibration.

## Quick start: a receipt in two minutes, no API key

```bash
git clone <this repo> skill-gate && cd skill-gate
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
cd examples/refund-triage
./reproduce.sh
```

`reproduce.sh` lints the example skill, runs its six golden cases in manual mode with two
repeats, fills the outputs from `fixture-outputs/`, judges them, writes a receipt under
`receipts/`, and verifies it. The outputs are hand-written fixtures, not a model run; they are
there to show a flaky case, a miss and a false flag. The verdict is NOT VERIFIED, and the
receipt says why.

To see tamper detection, change one character in any file under `runs/*/outputs/` and run
`skillgate verify-receipt receipts/<id>/receipt.json` again.

## The workflow

```
lint → interview → split → criteria → run → judge → receipt → verify-receipt
```

1. **`skillgate lint`** reads the skill (`.md`, `.txt` or a `.docx` export) and writes
   `lint_report.md` and `.json`. Each finding has a line, a category, a severity and a suggested
   rewrite: vague wording, missing output format, no behavior for bad input, nothing guarding
   against instructions embedded in the input, no examples, references to files that were not
   provided. The model pass adds untestable and conflicting rules; it quotes the line it cites,
   and findings whose quote is not on that line are dropped. `--deterministic-only` skips it.
   Lint informs; it never blocks.
2. **`skillgate interview --import cases.csv`** creates golden cases from a spreadsheet export
   (columns documented in `skillgate/interview.py`). Each case is a YAML file with an `input`,
   binary `expectations` (never the exact expected text), `tags`, `source` and confirmation
   fields. Cases drafted by a model (`source: generated`) are refused until an expert confirms
   them.
3. **`skillgate split`** (run automatically after an import) draws the holdout at random and
   records the seed in `golden.yaml`. Anyone can recompute the draw; a hand-edited split blocks
   VERIFIED.
4. **`skillgate criteria`** drafts general criteria into `criteria.proposed.yaml` (with a model,
   or `--no-model` for one TODO per rule). A person edits and saves `criteria.yaml`, then runs
   `skillgate criteria --ratify --by "Name"`. Editing it afterwards invalidates the
   ratification. `coverage.md` maps the skill's rules to the checks that trace to them and lists
   uncovered rules.
5. **`skillgate run --mode manual`** creates `runs/<time>-manual/` with a run sheet per split,
   empty `outputs/<case>/<repeat>.md` files, and `capture.yaml` for where and when it ran. Paste
   each input into the skill (for a Workspace skill, the Gemini side panel), in a fresh
   conversation each time, and save each answer. The holdout sheet is a separate file: ideally
   someone other than the skill's author runs it.
6. **`skillgate judge`** decides every check on every output. Checks with a `check:` block
   (regex, contains, required sections, verbatim quotes) are decided deterministically first.
   The rest go to the judge model, one check per call; the judge sees the output, the input and
   that one check, never the author's notes or earlier verdicts. Its evidence must appear in the
   output, or it is asked once more, then recorded as ERROR. API failures, refusals and
   malformed answers are ERROR. `report.md` details dev failures and withholds holdout details.
7. **`skillgate receipt`** writes `receipt.md` and `receipt.json`: skill version and hashes,
   mode, judge model and settings, prompt hashes, results by split, misses and false flags,
   FAIL counts per criterion, failing cases (holdout redacted), golden-set make-up and seeds,
   uncovered rules, calibration status, the criteria's ratification, and a manifest of every
   file's SHA-256. The verdict is VERIFIED only if every case passes on both splits on every
   repeat, there are no ERRORs, the judge is calibrated (or unused), and the golden set meets its
   minimums. Otherwise NOT VERIFIED, with every reason.
8. **`skillgate verify-receipt receipt.json`** recomputes every hash, re-aggregates the results
   from the judgment files, recomputes the verdict, and re-renders `receipt.md`. Any difference
   is reported and the command exits 1.

## Writing checks

Criteria (in `criteria.yaml`) apply to every case; expectations (in each case file) apply to
one. Either may carry a deterministic `check:`; without one, the judge model decides.

```yaml
criteria:
- id: C1
  text: The first line is "Decision:" followed by APPROVE, DENY or ESCALATE.
  traces_to: [k0cd1bdd9]        # rule key from coverage.md
  check: {type: regex, pattern: '\A\s*Decision: (APPROVE|DENY|ESCALATE)[ \t]*$'}
- id: C2
  text: Every passage in double quotes appears verbatim in the input.
  traces_to: [k0cd1bdd9]
  check: {type: verbatim_quotes, min_length: 6}
```

Expectation kinds drive the receipt's two error counts: `detect` (the skill must catch this;
a failure is a **miss**) and `no_flag` (the skill must not flag this; a failure is a **false
flag**). Cases tagged `should_not_flag` should carry a `no_flag` expectation.

## Configuration

Copy `skillgate.yaml.example` to your project as `skillgate.yaml`. Model IDs must be exact
versions; floating aliases such as `-latest` are rejected. Missing API keys stop the command
with a clear message; Skill Gate never switches to another model.

Prompts used by Skill Gate live in `prompts/` as versioned files. Their SHA-256 hashes go into
every receipt.

## Tests

```bash
pytest                                   # all model calls are faked
SKILLGATE_LIVE=1 ANTHROPIC_API_KEY=... pytest tests/test_live.py   # one real judge call
```

## Files

```
skillgate/        the CLI and library
prompts/          versioned prompts (judge, lint, criteria drafting)
tests/            pytest suite
examples/         refund-triage: a complete, key-free example with a committed receipt
ASSUMPTIONS.md    every assumption and interpretation made while building this
CHANGELOG.md
```

MIT licensed.
