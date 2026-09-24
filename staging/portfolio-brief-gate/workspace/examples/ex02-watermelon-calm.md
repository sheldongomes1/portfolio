# ex02 — Watermelon with a calm tone

**Covers:** R1.8 watermelon case 2 (declared Green, narrative Red, reported matter-of-factly).
A minor-friction Green and a thin Green that must not be flagged as CONTRADICTS.
**Status:** dev example. Visible to the skill author; not a holdout case.

## Requester prompt

```
@Portfolio Brief Gate Portfolio brief for 2026-W38, please. Four programs report to this forum.
```

## Input

---

**Program: Kite Regulatory Reporting** — Status: **Green** — PM: F. Nakamura

Build work continued this week on the reporting engine. The regulatory submission window closed
on 12 September without our filing; the next window opens in January, and we have re-sequenced
the plan around it. Test environments are stable.

---

**Program: Wren Branch Refit** — Status: **Green** — PM: P. Adeyemi

Permits for the last six branches are taking longer than expected, but the contractor has
confirmed we remain within the two-week buffer. Fit-out continues on schedule elsewhere.

---

**Program: Heron Contact Centre** — Status: **Green** — PM: G. Silva

On track.

---

**Program: Osprey Data Retention** — Status: **Amber** — PM: E. Brandt

Retention rules for 3 of 7 systems are live. The other four wait on legal sign-off of the
retention schedule, so the team applies retention to those systems by hand every week, about a
day of effort per system.

---

## Expected behavior

Each line is a binary check: PASS or FAIL.

- E1. Kite Regulatory Reporting [U01] is in the Flags table with the verdict CONTRADICTS.
- E2. Kite is graded Red (grade 4 or 5).
- E3. The quote that decided Kite's verdict comes from U01 and mentions the closed submission
  window.
- E4. Wren Branch Refit [U02] is graded Green (grade 1 or 2) and is not in the Flags table.
- E5. Heron Contact Centre [U03] has the verdict NEUTRAL, not CONTRADICTS.
- E6. Heron's next step asks for evidence, naming an owner-type and an artifact.
- E7. Osprey Data Retention [U04] is graded Amber (3) with the verdict CORROBORATES.
- E8. Coverage reads "Based on 4 of 4 expected updates".
