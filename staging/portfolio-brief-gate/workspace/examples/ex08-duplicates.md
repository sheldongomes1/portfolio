# ex08 — Duplicate and conflicting updates for the same program

**Covers:** R1.5 duplicate updates. One update was forwarded twice (identical text). One
program sent two different updates for the same week that disagree.
**Status:** dev example. Visible to the skill author; not a holdout case.

## Requester prompt

```
@Portfolio Brief Gate Brief for 2026-W38. Four programs are expected.
```

## Input

---

**Program: Albatross CRM Rollout** — Status: **Green** — PM: S. Olsen

Wave 2 go-live completed for the Nordics sales team on 19 September; 96% of users logged in
during week one.

---

**Program: Petrel Treasury Reporting** — Status: **Amber** — PM: C. Mwangi

The FX rate feed fails about twice a week, and each failure takes the reporting team half a day
to backfill by hand. Vendor ticket open; no fix date.

---

**Program: Albatross CRM Rollout** — Status: **Green** — PM: S. Olsen

Wave 2 go-live completed for the Nordics sales team on 19 September; 96% of users logged in
during week one.

---

**Program: Shearwater Mobile Workforce** — Status: **Green** — PM: D. Rossi

On track for the 10 October pilot. Device procurement complete.

---

**Program: Shearwater Mobile Workforce** — Status: **Red** — PM: D. Rossi

Correction to earlier note: the device supplier has delayed shipment to 24 October, so the
10 October pilot will not happen on that date.

---

**Program: Fulmar Procurement** — Status: **Amber** — PM: J. Varga

The catalogue load is 60% complete. The remaining suppliers send files in the wrong template,
so two buyers reformat them by hand, roughly two days a week between them. Target end date
31 October unchanged.

---

## Expected behavior

Each line is a binary check: PASS or FAIL.

- E1. Coverage lists U03 as "excluded: duplicate of U01".
- E2. Albatross CRM Rollout appears once in By program.
- E3. Both U04 and U05 are in the Evidence ledger, each with its own grade.
- E4. Shearwater Mobile Workforce is reported in By program at Red, citing both U04 and U05.
- E5. An Open question says that U04 and U05 disagree.
- E6. Coverage reads "Based on 4 of 4 expected updates".
