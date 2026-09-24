# PBG Output Format

Reference file for Portfolio Brief Gate, Workspace edition 1.0.0. Used in Stages 3 and 5 and in
single-update mode.

This format is fixed. Keep the headings, their order, the table columns, and the exact wording
of the gate lines and the footer. Everything in `<angle brackets>` is filled in.

## Quotes

Any text in straight double quotes (") is a verbatim passage from the update whose ID (U01,
U02, …) is on the same line or table row. Copy it character for character. No ellipses, no
corrections; if the passage contains a double quote character, pick another passage. This is
what lets a person or Skill Gate check every quote mechanically afterward.

## Brief: PASSED

```markdown
# Portfolio Brief — <period>
**GATE: ✅ PASSED** — FAITHFUL: PASS · COMPLETE: PASS · NO-LAUNDER: PASS · ACTIONABLE: PASS

## 🍉 Flags — declared vs. evidence
| Program | Declared | Graded | Verdict | The sentence that decided it |
|---|---|---|---|---|
| <program> [U07] | Green | Red (4) | CONTRADICTS | "<verbatim quote>" |

## Portfolio summary
<3–6 sentences. Every factual claim ends with its [U-ids]. Acknowledge honest Reds as healthy
reporting. No portfolio fact that appears in no update.>

## By program
- **<Program>** — Graded <status> (<grade>): <one line> [U03]. Next step: <owner-type + a
  decision or artifact>.

## Open questions
- <question> (or `None.`)

## Coverage
Based on <N> of <M> expected updates. Not represented: <programs — "no update received", or
"none">. Excluded: <Uxx — reason, or "none">. Declared status missing: <U-ids, or "none">.
Downgraded to unverified by the quote check: <U-ids, or "none">.
<If one program supplies more than half of the content: "Weighting note: …">

## Evidence ledger
| ID | Program | Declared | Graded | Evidence quote | Watermelon | Tone | Watermelon quote | In brief |
|---|---|---|---|---|---|---|---|---|
| U01 | <program> | Green | Red (4) | "<verbatim>" | CONTRADICTS | BULLISH | same as evidence | included |

## Self-check record
<the table from PBG Self-Check, filled in>

_Self-check by the same model that wrote this brief; it is not independent verification.
Verify independently with Skill Gate. Portfolio Brief Gate, Workspace edition 1.0.0._
```

Rules for the sections:

- **Flags.** One row per CONTRADICTS verdict, sandbagged included (write the verdict as
  `CONTRADICTS (sandbagged)`). If there are none, replace the table with one line:
  `No CONTRADICTS verdicts this period: <x> corroborated, <y> neutral, <z> not checked (no
  declared status).`
- **By program.** One bullet per program in the body. Every flagged program (see PBG
  Self-Check, ACTIONABLE) gets a concrete next step. Other programs may say
  `Next step: none required.`
- **Coverage.** N is the number of programs with at least one update this period; duplicate and
  superseded updates do not add to N. M is the number of programs expected to report. When the
  expected count is unknown, the first sentence is instead `Based on <N> updates received.
  Expected count not provided, so missing programs cannot be detected.`
- **Evidence ledger.** One row for every update in the inventory, including excluded,
  duplicate and downgraded ones. `In brief` is `included`, `excluded: <reason>`, or
  `downgraded: quote not found`. `Graded` is `<status> (<grade>)` or
  `unverified (quote not found)`.
- **Calibration offer.** After the first brief in a conversation, add one line after the
  footer offering calibration (see the skill's Calibration section).

## Brief: FLAGGED

Identical layout, with four differences. The brief must not look clean.

1. The title ends with ` ⚠️ FLAGGED`.
2. The gate line reads `**GATE: ⚠️ FLAGGED**` and shows each criterion's actual result:
   `**GATE: ⚠️ FLAGGED** — FAITHFUL: PASS · COMPLETE: FAIL · NO-LAUNDER: PASS · ACTIONABLE: PASS`
3. Directly under the gate line: one line per criterion that is not PASS, then a fixed
   sentence:
   ```markdown
   ⚠️ COMPLETE — <critique, one or two sentences>
   **This brief did not pass its self-check. Do not forward it as verified.**
   ```
4. Every section containing a failure starts with
   `⚠️ <CRITERION> failed here: <what, in one line>`.

## Single-update mode

No brief, no gate line, no self-check record. For each update:

```markdown
Single-update mode: <n> update(s) received; a portfolio brief needs at least 3.

## <Program> [U01]
- Graded: <status> (<grade>). Evidence: "<verbatim quote>"
- Declared: <status, or —>. Watermelon: <verdict> (tone: <tone>). "<verbatim quote, or same
  as evidence>"
- Ask the program lead next: <one sentence>

_Single-update check by the same model; not independent verification. Portfolio Brief Gate,
Workspace edition 1.0.0._
```

When the requester asked about one report on purpose, the first line is
`Single-update mode: 1 update received.` instead.

## Cannot run

Exactly one line, nothing else:

- `PBG cannot run: reference file "<title>" is not available.`
- `PBG: no program status updates found. <one sentence saying what was received>`
