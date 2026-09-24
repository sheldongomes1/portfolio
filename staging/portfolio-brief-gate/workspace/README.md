# Portfolio Brief Gate, Google Workspace edition

Portfolio Brief Gate as a Google Workspace skill. You @mention it in the Gemini side panel on a
set of program status updates. It returns a portfolio brief that:

- grades each program's severity from what the update states, ignoring tone
- flags watermelon reporting: declared Green with a Red narrative, and the reverse
  ("sandbagged" Red)
- cites every claim to a source update and quotes evidence verbatim
- runs its four binary checks (FAITHFUL, COMPLETE, NO-LAUNDER, ACTIONABLE) before presenting
  the brief, and says so plainly at the top when a check fails

It is the same method as the original skill in this repository (`../portfolio-brief-gate/`),
rewritten for Workspace. Every wording change, and the reason for it, is in
[`MAPPING.md`](MAPPING.md).

**Status: written, not yet run inside Workspace.** Workspace skills need the admin's Gemini
Beta setting, and this edition has not yet been tested on a Workspace account. Treat the setup
steps below as the intended path until someone runs them and records the result in
[`CHANGELOG.md`](CHANGELOG.md).

## Files

```
workspace/
├── skill.md                 # the skill text: paste into the skill's Google Doc
├── reference/               # reference files the skill reads (one Google Doc each)
│   ├── severity-rubric.md   #   "PBG Severity Rubric"   anchored 1–5 grade, tone-blind
│   ├── watermelon-check.md  #   "PBG Watermelon Check"  declared vs. narrative verdict
│   ├── self-check.md        #   "PBG Self-Check"        quote check + four binary criteria
│   ├── output-format.md     #   "PBG Output Format"     the fixed output layout
│   └── worked-example.md    #   "PBG Worked Example"    a PASSED and a FLAGGED output
├── examples/                # test inputs with expected behavior (not given to the skill)
├── MAPPING.md               # original wording → Workspace wording, with reasons
├── CHANGELOG.md
└── README.md
```

## Setup

Google's announcement (16 September 2026) describes how skills are created and shared. It does
not document length limits, how reference files are attached, or sampling settings. The steps
below use only what was announced; where a detail is unknown, the step says so.

1. **Admin:** enable the Gemini Beta setting for the users who will build and use the skill.
2. **Create the skill** in Google Docs with the skill builder tool. Name it
   `Portfolio Brief Gate`. Paste the full text of `skill.md` as the skill's instructions,
   starting with the `Version:` line.
3. **Add the reference files.** Create one Google Doc per file in `reference/`, titled exactly
   as below. The skill finds them by these titles.

   | File | Google Doc title |
   |---|---|
   | `reference/severity-rubric.md` | PBG Severity Rubric |
   | `reference/watermelon-check.md` | PBG Watermelon Check |
   | `reference/self-check.md` | PBG Self-Check |
   | `reference/output-format.md` | PBG Output Format |
   | `reference/worked-example.md` | PBG Worked Example |

   Attach them to the skill as reference files. *How attachment works is not documented yet.*
   If the skill cannot use separate reference files, paste each file's text at the end of the
   skill's own Doc, under a heading with its title. The skill replies
   `PBG cannot run: reference file "<title>" is not available.` if it cannot find one. That
   reply means setup is incomplete, not that the portfolio has a problem.
4. **Enable it in Workspace Studio.** Anyone with access to the Doc can add and enable the
   skill there.
5. **Try it in Studio's real-time testing** with `examples/ex01-watermelon-bullish.md`: paste
   the requester prompt and the input. One good-looking output is a smoke test, not
   verification; see "Verifying the skill" below.
6. **Use it:** in Gmail, Docs, Slides, Drive or Chat, open the Gemini side panel and write
   `@Portfolio Brief Gate` followed by your request and the status updates (or run it on an
   open document or email that contains them). Say how many programs should be reporting;
   otherwise the skill asks once.

## What it does with difficult input

The full rules are in `skill.md` under "Input handling". In short:

| Input | Behavior |
|---|---|
| Not status updates | One line: `PBG: no program status updates found.` and what was received |
| Fewer than 3 updates | Single-update mode, and the first line says why |
| An update with no declared status | Graded; watermelon check marked `NOT CHECKED`; listed in Coverage |
| The same update twice | Second copy excluded as a duplicate, listed in Coverage |
| Two different updates for one program in one period | Both graded, reported at the more severe grade, disagreement raised as an Open question |
| Instructions inside an update ("mark this Green") | Not followed; listed as an Open question |
| Requester asks to leave a Red program out | Left out and listed in Coverage; the brief is FLAGGED because COMPLETE fails |

## Limitations

- **The self-check is the model grading itself.** Inside Workspace, the same Gemini model that
  writes the brief also checks it. It shares the brief's blind spots and can pass a plausible
  mistake. The output's footer says so every time. Independent verification is Skill Gate's
  job (below), with a judge from a different model family.
- **No code runs inside the skill.** The original skill runs `validate_quotes.py` to check
  quotes deterministically. Workspace skills are assumed not to run code, so the quote check
  inside the skill is done by the model. Every quote is formatted so it can be checked
  mechanically afterward.
- **The gate line is written before the brief it describes.** The output puts the result at
  the top, but a model writes top to bottom. The skill tells it to finish the check first,
  and requires the gate line to match the Self-check record at the bottom. A mismatch is a
  failure that Skill Gate checks for.
- **Unknowns.** Skill length limits, how reference files are retrieved, sampling settings, and
  behavior inside Studio flows (where nobody can answer a question) are not documented. The
  skill is kept short, with detail in reference files, for that reason.
- **Variation between runs.** The same updates can produce different briefs on different
  runs. One test run shows one sample. Skill Gate runs each case several times.

## Verifying the skill

**Available now:** a mechanical quote check with the original validator. Copy each update's raw
text and the quotes from the Evidence ledger into the validator's JSON format and run:

```bash
python3 ../portfolio-brief-gate/scripts/validate_quotes.py quotes.json
```

`examples/worked-example-quote-check.json` is a filled-in example for the worked example; it
passes.

**With Skill Gate** (separate project, in development): Skill Gate is the independent check
that issues a receipt saying whether a skill is verified. For a Workspace skill the faithful
path is manual mode, because there is no known API for running a Workspace skill:

1. `skillgate run --mode manual` writes a run sheet of test inputs and empty output files.
2. Paste each input into the side panel, `k` times each, and save each output into its file.
3. `skillgate judge` checks every output: deterministic checks first (gate line format, gate
   line matches the Self-check record, every quote verbatim), then a judge from a different
   model family for each remaining criterion and expectation.
4. `skillgate receipt` records the result. VERIFIED requires every case to pass on every run,
   including held-out cases the skill author never saw.

The examples in `examples/` are written as Skill Gate cases: an input plus binary expected
behaviors.

## Examples

Test inputs with expected behavior. They are not attached to the skill.

| File | What it tests |
|---|---|
| `ex01-watermelon-bullish.md` | Watermelon: declared Green, bullish tone, go-live date lost |
| `ex02-watermelon-calm.md` | Watermelon reported calmly; a friction Green and a thin Green that must not be flagged |
| `ex03-genuine-green.md` | A genuine Green with an exuberant tone that must not be flagged; an alarmed cosmetic update |
| `ex04-reverse-watermelon.md` | Declared Red, narrative Green (sandbagged), next to an honest Red |
| `ex05-self-check-fail.md` | Requester leaves out a program graded 5: COMPLETE fails, brief FLAGGED |
| `ex06-too-few-updates.md` | Two updates: single-update mode |
| `ex07-missing-declared-status.md` | An update with no declared status |
| `ex08-duplicates.md` | An identical duplicate and two conflicting updates for one program |
| `ex09-embedded-instruction.md` | An update that tells the AI to mark it Green |
| `ex10-out-of-scope.md` | An offsite agenda instead of status updates |

All companies, programs and people in the examples are fictional.

## Where your data goes

Inside Workspace, the skill sends nothing anywhere beyond the Gemini request you make. Your
updates go where your organization's Workspace Gemini already sends them. If you verify with
Skill Gate in API mode, the skill text, reference files and test inputs are sent to external
model APIs. Use fictional or approved data for that, and get the data owner's approval before
running it on anything confidential.

## Versioning

The first line of `skill.md` carries the version. Bump it on every change to `skill.md` or to
any file in `reference/`, keep the version in each reference file's header and in the output
footer in step, and add an entry to [`CHANGELOG.md`](CHANGELOG.md).

## Calibrating to your portfolio

The rubric is a sound default, not your ground truth. The golden-set method for calibrating it
is in [`../portfolio-brief-gate/references/golden-set-guide.md`](../portfolio-brief-gate/references/golden-set-guide.md).
