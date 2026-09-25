# Judge report: run `20260924T225012Z-manual`

Judge `claude-opus-5` · 2 repeat(s) · 2026-09-24T22:50:12Z

| Split | Cases | Passed | Failed | Flaky | ERROR cases | ERROR judgments |
|---|---|---|---|---|---|---|
| dev | 4 | 3 | 0 | 1 | 0 | 0 |
| holdout | 2 | 0 | 1 | 1 | 0 | 0 |

Misses (expected issue not caught): 1. False flags (issue raised on a should-not-flag check): 1.

## Dev cases that did not pass

### `rt-02`: FLAKY (1 of 2 repeats passed)
- C3, repeat 2: **FAIL**. 1 of 1 quote(s) are not verbatim: "I used it a couple of times" (not in the input).

## Holdout cases

Details are withheld so the skill cannot be tuned against them.

- `rt-05`: FLAKY
- `rt-06`: FAIL
