# Skill Gate receipt: refund-triage v1.0.0

## Verdict: NOT VERIFIED

Reasons:

- 6 cases; VERIFIED requires at least 10
- dev: 3 of 4 cases passed on every repeat (0 failed, 1 flaky, 0 ERROR)
- holdout: 0 of 2 cases passed on every repeat (1 failed, 1 flaky, 0 ERROR)

Warnings: 6 cases; at least 12 are recommended.

All results are counts of binary PASS, FAIL and ERROR judgments.

## What was tested

| Item | Value |
|---|---|
| Skill | `skill/skill.md` SHA-256 `4b7348940b1d90a2dcf50366d3b38fc50b8469cdb92d01e32a6468add721b93e` |
| Reference | `skill/reference/refund-policy.md` SHA-256 `9bbf024fc27611fc851555db7371cfaafdca490a35275168eebaaa0a9abafbc6` |
| Mode | manual: surface "hand-written fixture; no model was run", run date 2026-09-24, operator Skill Gate maintainers |
| Judge | `claude-opus-5` settings `{"effort": "high", "max_tokens": 16000}` (not called: all checks deterministic) |
| Prompt | `judge.v1` SHA-256 `b21566561723da9c6ecc89694ed211b1ed72d0eb8f2cc95d25eaf3f668414f2d` |
| Run | `20260925T122324.710354Z-manual`, judged `judge-20260925T122324.815740Z`, repeats k = 2 |
| Receipt generated | 2026-09-25T12:23:24Z (UTC) |

## Results by split

| Split | Cases | Passed | Failed | Flaky | ERROR cases | ERROR judgments |
|---|---|---|---|---|---|---|
| dev | 4 | 3 | 0 | 1 | 0 | 0 |
| holdout | 2 | 0 | 1 | 1 | 0 | 0 |

Judgments: 52 (46 PASS, 6 FAIL, 0 ERROR).

## Misses and false flags

Misses (expected issues the skill failed to catch): 1

- `rt-05` E1 (holdout), failed on repeat(s) 2 of 2: redacted (holdout)

False flags (issues raised where the case says not to flag): 1

- `rt-06` E1 (holdout), failed on repeat(s) 1, 2 of 2: redacted (holdout)

## FAIL counts per criterion

| Criterion | FAIL | ERROR | Failing cases |
|---|---|---|---|
| C1 | 0 | 0 | — |
| C2 | 0 | 0 | — |
| C3 | 1 | 0 | rt-02 |

## Cases that did not pass

### `rt-02` (dev): FLAKY, 1 of 2 repeats passed
- C3, repeat 2: **FAIL**. 1 of 1 quote(s) are not verbatim: "I used it a couple of times" (not in the input). Evidence: `I used it a couple of times`

### `rt-05` (holdout): FLAKY, 1 of 2 repeats passed
- E1: redacted (holdout)

### `rt-06` (holdout): FAIL, 0 of 2 repeats passed
- E1: redacted (holdout)
- E2: redacted (holdout)

## Golden set

6 cases: 4 dev, 2 holdout; 4 tagged edge or should_not_flag; sources 6 expert, 0 generated.

Tags: defect_after_window 1, edge 3, happy_path 1, injection 1, late_return 1, over_limit 1, should_not_flag 1, under_limit 1.

Holdout drawn at random; seed(s): 860165454.

## Coverage

8 rules extracted from the skill; **1 uncovered** by any criterion or expectation.

Uncovered: R07 (line 22).

## Judge calibration

NOT APPLICABLE: every check was deterministic; no model judged anything.

## Criteria

`golden/criteria.yaml` SHA-256 `10f2985722dd6cd1a7cf1b9056b5eead6026fbde177c5d2f8c770e798e55c100`, ratified by Example maintainer (fictional) at 2026-09-24T22:47:04Z.

## Model calls

0 judge call(s), 0 input and 0 output tokens, cost $0.0000.

## Artifact manifest

47 files hashed: 1 config, 1 skill, 1 reference, 1 golden, 6 case, 6 case_input, 1 criteria, 1 ratification, 1 run, 1 capture, 12 output, 1 judge, 1 summary, 1 log, 12 judgment.
The full list with SHA-256 hashes is in `receipt.json`. Run `skillgate verify-receipt` on it to
recompute every hash, the results and the verdict.

Consistency hash of receipt.json: `b2b5bfabe95dfcc7e444f7a95942e8d7b20916e631c6f49c47d7f1b700a24239`. This detects accidental edits; it is not a signature.
