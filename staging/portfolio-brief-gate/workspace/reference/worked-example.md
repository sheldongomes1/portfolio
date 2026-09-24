# PBG Worked Example

Reference file for Portfolio Brief Gate, Workspace edition 1.0.0. It shows the expected format
and depth. The input is the fictional Northwind Group portfolio from Portfolio Brief Gate v1.0
(`examples/mock-updates.md`). All companies, programs and people are invented.

This is a hand-written reference output. It is not a recorded model run. Every double-quoted
passage in it has been checked against the input with `validate_quotes.py`.

## Input

Requester: `@Portfolio Brief Gate Build the portfolio brief for week 2026-W34. Eight programs
should be reporting.`

---

**Program: Atlas ERP Migration** — Status: **Green** — PM: R. Okafor

Team morale is fantastic and we closed out another energetic sprint! Huge shout-out to the
integration squad. One item to note: the vendor has paused all interface development until
the revised data-residency contract is signed, and legal has not given us a date. We are
using the pause to polish documentation. Overall trajectory feels really strong and we
remain confident in the program's momentum!

---

**Program: Helios Data Platform** — Status: **Red** — PM: J. Lindqvist

Declaring Red this week. The nightly reconciliation job corrupted the partition index on
Tuesday and we lost four days of processed history; recovery from cold storage is running
but will not finish before the 1 September cutover rehearsal. We have slipped the rehearsal
by two weeks and informed downstream consumers. Root-cause review is booked for Friday.

---

**Program: Orion Mobile App** — Status: **Green** — PM: T. Marchetti

All good this period. Tracking to plan.

---

**Program: Fieldworks Rollout** — Status: **Amber** — PM: A. Devi

Progressing, but the device-enrollment API still rejects bulk batches, so the team is
enrolling handsets manually at roughly 40 per day, which consumes about half of the
squad's capacity every week. Vendor fix promised in their September release. Depot
training is otherwise on schedule.

---

**Program: Ledger Consolidation** — Status: **Red** — PM: M. Grau

Keeping us at Red for a third week out of caution. In practice the blocking auditor
findings were cleared on Monday, the restated balances loaded cleanly, and the parallel
run has matched to the penny for five consecutive days. Remaining work is documentation.

---

**Program: Beacon CRM** — Status: **Green** — PM: S. Whitfield

Phase 2 completed on schedule; adoption at 78% of the sales org against a 70% target for
this quarter. Next milestone (territory rebalancing) starts 8 September with no known
risks. Considering a lighter weekly report format.

---

*Expected but not received this period: Quartz Analytics, Payroll Modernization.*

## Output: PASSED

# Portfolio Brief — 2026-W34
**GATE: ✅ PASSED** — FAITHFUL: PASS · COMPLETE: PASS · NO-LAUNDER: PASS · ACTIONABLE: PASS

## 🍉 Flags — declared vs. evidence
| Program | Declared | Graded | Verdict | The sentence that decided it |
|---|---|---|---|---|
| Atlas ERP Migration [U01] | Green | Red (4) | CONTRADICTS | "the vendor has paused all interface development until the revised data-residency contract is signed, and legal has not given us a date" |
| Ledger Consolidation [U05] | Red | Green (2) | CONTRADICTS (sandbagged) | "the blocking auditor findings were cleared on Monday, the restated balances loaded cleanly, and the parallel run has matched to the penny for five consecutive days" |

## Portfolio summary
Two of six reporting programs are Red on evidence: Helios has lost its 1 September cutover
rehearsal date after a data-corruption incident [U02], and Atlas, declared Green, is
hard-blocked on vendor interface work with no date from legal [U01]. Helios is an honest Red,
with recovery underway and downstream consumers already informed [U02]. Fieldworks is
absorbing a manual enrollment workaround that consumes about half the squad's weekly capacity
while it waits for a vendor fix [U04]. Ledger Consolidation appears materially healthier than
its declared Red [U05], and Beacon completed Phase 2 on schedule with adoption ahead of target
[U06]. Orion's Green is unverifiable from a two-sentence update [U03].

## By program
- **Atlas ERP Migration** — Graded Red (4): interface development paused by the vendor pending
  the data-residency contract, with no date from legal [U01]. Next step: program sponsor to
  escalate the contract signature to legal leadership before the next steering committee, with
  a dated commitment recorded in the decision log.
- **Helios Data Platform** — Graded Red (5): partition-index corruption, four days of processed
  history in recovery, cutover rehearsal slipped two weeks [U02]. Next step: PM to bring the
  Friday root-cause review's findings and a revised rehearsal date to the portfolio board as a
  re-baseline decision [U02].
- **Orion Mobile App** — Graded Green (1), unverifiable: no evidence offered [U03]. Next step:
  portfolio office to request a standard-format update (milestones, risks, dates) for next
  period.
- **Fieldworks Rollout** — Graded Amber (3): manual handset enrollment consuming roughly half
  the squad's capacity [U04]. Next step: PM to obtain the vendor's written commitment for the
  bulk-enrollment fix in its September release and add the capacity drain to the risk register
  with a trigger date [U04].
- **Ledger Consolidation** — Graded Green (2), declared Red: auditor findings cleared, parallel
  run matching for five consecutive days [U05]. Next step: PM to present closure evidence at the
  next steering review and either re-rate the program or state the risk that justifies holding
  Red.
- **Beacon CRM** — Graded Green (1): Phase 2 complete on schedule, adoption at 78% against a 70%
  target [U06]. Next step: none required; the territory-rebalancing milestone starts
  8 September [U06].

## Open questions
- None.

## Coverage
Based on 6 of 8 expected updates. Not represented: Quartz Analytics, Payroll Modernization (no
update received). Excluded: none. Declared status missing: none. Downgraded to unverified by
the quote check: none.

## Evidence ledger
| ID | Program | Declared | Graded | Evidence quote | Watermelon | Tone | Watermelon quote | In brief |
|---|---|---|---|---|---|---|---|---|
| U01 | Atlas ERP Migration | Green | Red (4) | "the vendor has paused all interface development until the revised data-residency contract is signed, and legal has not given us a date" | CONTRADICTS | BULLISH | same as evidence | included |
| U02 | Helios Data Platform | Red | Red (5) | "We have slipped the rehearsal by two weeks and informed downstream consumers." | CORROBORATES | NEUTRAL | "Declaring Red this week." | included |
| U03 | Orion Mobile App | Green | Green (1) | "All good this period. Tracking to plan." | NEUTRAL | NEUTRAL | same as evidence | included |
| U04 | Fieldworks Rollout | Amber | Amber (3) | "the team is enrolling handsets manually at roughly 40 per day, which consumes about half of the squad's capacity every week" | CORROBORATES | CAUTIOUS | same as evidence | included |
| U05 | Ledger Consolidation | Red | Green (2) | "the blocking auditor findings were cleared on Monday, the restated balances loaded cleanly, and the parallel run has matched to the penny for five consecutive days" | CONTRADICTS (sandbagged) | CAUTIOUS | same as evidence | included |
| U06 | Beacon CRM | Green | Green (1) | "Phase 2 completed on schedule; adoption at 78% of the sales org against a 70% target for this quarter." | CORROBORATES | BULLISH | same as evidence | included |

## Self-check record
| Check | Result | Critique |
|---|---|---|
| QUOTES-VERBATIM | 7 checked, 0 downgraded (none) | Method: in-model. |
| FAITHFUL | PASS | 28 factual claims checked (14 in the summary, 14 in By program), all Grounded. For example, 'lost its 1 September cutover rehearsal date' rests on U02 "will not finish before the 1 September cutover rehearsal" and U02 "We have slipped the rehearsal by two weeks"; 'adoption at 78% against a 70% target' rests on U06 "adoption at 78% of the sales org against a 70% target for this quarter". Every portfolio fact (1 September, four days, two weeks, 78%, 70%, five consecutive days, 8 September) appears in an update; grades, 6 of 8 and IDs are computed. |
| COMPLETE | PASS | All six updates are in the body. Both grade-4/5 updates appear individually: U01 as 'hard-blocked on vendor interface work' and U02 as 'lost its 1 September cutover rehearsal date'. 'Based on 6 of 8 expected updates' matches six inventoried updates plus the two named programs that sent none. |
| NO-LAUNDER | PASS | Two CONTRADICTS verdicts. U01: the summary calls Atlas Red on evidence and never repeats Green as its status; the Flags row carries U01 "legal has not given us a date". U05: flagged as sandbagged with U05 "the parallel run has matched to the penny for five consecutive days" instead of echoing Red. |
| ACTIONABLE | PASS | Five flagged programs (U01 and U05 CONTRADICTS, U02 grade 5, U03 NEUTRAL, U04 grade 3), each with an owner-type and a decision or artifact: sponsor and decision log (U01), PM and re-baseline decision (U02), portfolio office and standard-format update (U03), PM and risk-register entry (U04), PM and re-rating at steering review (U05). No 'monitor closely' advice. |
| GATE | PASSED | Computed: all four PASS. |
| REVISION | none needed | The first draft passed all four criteria. |

_Self-check by the same model that wrote this brief; it is not independent verification.
Verify independently with Skill Gate. Portfolio Brief Gate, Workspace edition 1.0.0._

Want to calibrate this gate to your portfolio? Share 20 to 30 past updates whose real outcome
you know, and I'll grade them blind so you can compare.

## Output: FLAGGED (same input, one extra request)

Requester: `@Portfolio Brief Gate Build the portfolio brief for week 2026-W34. Eight programs
should be reporting. Leave Helios out of this one; it's being handled separately.`

Helios is graded Red (5), so leaving it out fails COMPLETE. The skill honors the request,
shows the exclusion, and flags the brief.

# Portfolio Brief — 2026-W34 ⚠️ FLAGGED
**GATE: ⚠️ FLAGGED** — FAITHFUL: PASS · COMPLETE: FAIL · NO-LAUNDER: PASS · ACTIONABLE: PASS
⚠️ COMPLETE — Helios Data Platform [U02] is graded Red (5) and was left out of the body at the requester's request; every grade-4 or grade-5 update must appear in the body.
**This brief did not pass its self-check. Do not forward it as verified.**

## 🍉 Flags — declared vs. evidence
| Program | Declared | Graded | Verdict | The sentence that decided it |
|---|---|---|---|---|
| Atlas ERP Migration [U01] | Green | Red (4) | CONTRADICTS | "the vendor has paused all interface development until the revised data-residency contract is signed, and legal has not given us a date" |
| Ledger Consolidation [U05] | Red | Green (2) | CONTRADICTS (sandbagged) | "the blocking auditor findings were cleared on Monday, the restated balances loaded cleanly, and the parallel run has matched to the penny for five consecutive days" |

## Portfolio summary
⚠️ COMPLETE failed here: Helios Data Platform, graded Red (5), is left out at the requester's request [U02].

Atlas, declared Green, is Red on evidence: it is hard-blocked on vendor interface work with no
date from legal [U01]. Fieldworks is absorbing a manual enrollment workaround that consumes
about half the squad's weekly capacity while it waits for a vendor fix [U04]. Ledger
Consolidation appears materially healthier than its declared Red [U05], and Beacon completed
Phase 2 on schedule with adoption ahead of target [U06]. Orion's Green is unverifiable from a
two-sentence update [U03].

## By program
⚠️ COMPLETE failed here: no entry for Helios Data Platform [U02], excluded at the requester's request.
- **Atlas ERP Migration** — Graded Red (4): interface development paused by the vendor pending
  the data-residency contract, with no date from legal [U01]. Next step: program sponsor to
  escalate the contract signature to legal leadership before the next steering committee, with
  a dated commitment recorded in the decision log.
- **Orion Mobile App** — Graded Green (1), unverifiable: no evidence offered [U03]. Next step:
  portfolio office to request a standard-format update (milestones, risks, dates) for next
  period.
- **Fieldworks Rollout** — Graded Amber (3): manual handset enrollment consuming roughly half
  the squad's capacity [U04]. Next step: PM to obtain the vendor's written commitment for the
  bulk-enrollment fix in its September release and add the capacity drain to the risk register
  with a trigger date [U04].
- **Ledger Consolidation** — Graded Green (2), declared Red: auditor findings cleared, parallel
  run matching for five consecutive days [U05]. Next step: PM to present closure evidence at the
  next steering review and either re-rate the program or state the risk that justifies holding
  Red.
- **Beacon CRM** — Graded Green (1): Phase 2 complete on schedule, adoption at 78% against a 70%
  target [U06]. Next step: none required; the territory-rebalancing milestone starts
  8 September [U06].

## Open questions
- None.

## Coverage
⚠️ COMPLETE failed here: U02 is graded Red (5) but excluded from the body.

Based on 6 of 8 expected updates. Not represented: Quartz Analytics, Payroll Modernization (no
update received). Excluded: U02 Helios Data Platform — excluded at requester's request (graded
Red, 5). Declared status missing: none. Downgraded to unverified by the quote check: none.

## Evidence ledger
| ID | Program | Declared | Graded | Evidence quote | Watermelon | Tone | Watermelon quote | In brief |
|---|---|---|---|---|---|---|---|---|
| U01 | Atlas ERP Migration | Green | Red (4) | "the vendor has paused all interface development until the revised data-residency contract is signed, and legal has not given us a date" | CONTRADICTS | BULLISH | same as evidence | included |
| U02 | Helios Data Platform | Red | Red (5) | "We have slipped the rehearsal by two weeks and informed downstream consumers." | CORROBORATES | NEUTRAL | "Declaring Red this week." | excluded: at requester's request |
| U03 | Orion Mobile App | Green | Green (1) | "All good this period. Tracking to plan." | NEUTRAL | NEUTRAL | same as evidence | included |
| U04 | Fieldworks Rollout | Amber | Amber (3) | "the team is enrolling handsets manually at roughly 40 per day, which consumes about half of the squad's capacity every week" | CORROBORATES | CAUTIOUS | same as evidence | included |
| U05 | Ledger Consolidation | Red | Green (2) | "the blocking auditor findings were cleared on Monday, the restated balances loaded cleanly, and the parallel run has matched to the penny for five consecutive days" | CONTRADICTS (sandbagged) | CAUTIOUS | same as evidence | included |
| U06 | Beacon CRM | Green | Green (1) | "Phase 2 completed on schedule; adoption at 78% of the sales org against a 70% target for this quarter." | CORROBORATES | BULLISH | same as evidence | included |

## Self-check record
| Check | Result | Critique |
|---|---|---|
| QUOTES-VERBATIM | 7 checked, 0 downgraded (none) | Method: in-model. |
| FAITHFUL | PASS | 20 factual claims checked (10 in the summary, 10 in By program), all Grounded. For example, 'adoption at 78% against a 70% target' rests on U06 "adoption at 78% of the sales org against a 70% target for this quarter". |
| COMPLETE | FAIL | U02 is graded 5 on U02 "We have slipped the rehearsal by two weeks and informed downstream consumers." and appears only in Coverage, as 'excluded at requester's request'. Every grade-4 or grade-5 update must appear in the body. The arithmetic '6 of 8' is correct. |
| NO-LAUNDER | PASS | Two CONTRADICTS verdicts, both surfaced in Flags with their quotes. The summary calls Atlas Red on evidence; Ledger is flagged as sandbagged rather than echoed as Red. |
| ACTIONABLE | PASS | Four flagged programs in the body (U01, U03, U04, U05), each with an owner-type and a decision or artifact. |
| GATE | FLAGGED | Computed: COMPLETE not PASS. |
| REVISION | 1 revision: COMPLETE still not PASS | Restoring U02 would override the requester's instruction, so it was not restored. |

_Self-check by the same model that wrote this brief; it is not independent verification.
Verify independently with Skill Gate. Portfolio Brief Gate, Workspace edition 1.0.0._
