# ex04 — Reverse watermelon (sandbagged Red)

**Covers:** R1.8 Red-declared program whose narrative is Green. Contrast with an honest Red.
**Status:** dev example. Visible to the skill author; not a holdout case.

## Requester prompt

```
@Portfolio Brief Gate Brief for week 2026-W38. Four programs should report.
```

## Input

---

**Program: Curlew Core Banking Upgrade** — Status: **Red** — PM: N. Petrov

Holding Red until the steering committee meets on 2 October. For the record: the data
migration finished on 9 September, reconciliation matched on all 212 ledger accounts, and
business users signed off UAT on 16 September. Go-live remains 5 October.

---

**Program: Dunlin Customer Portal** — Status: **Green** — PM: V. Okonkwo

The accessibility audit found 23 issues; 19 are fixed and the remaining 4 are scheduled for
next sprint, within the release buffer. Release date unchanged.

---

**Program: Snipe Field Service** — Status: **Red** — PM: I. Novak

Red. The route-optimisation vendor terminated the contract on 18 September and our field
schedulers are back to spreadsheets. No replacement vendor is shortlisted yet.

---

**Program: Stint Analytics** — Status: **Green** — PM: A. Yilmaz

Dashboards for finance and HR went live on 19 September, with 312 active users in the first
week. Next release on 14 October.

---

## Expected behavior

Each line is a binary check: PASS or FAIL.

- E1. Curlew Core Banking Upgrade [U01] is in the Flags table with the verdict
  CONTRADICTS (sandbagged).
- E2. Curlew is graded Green (grade 1 or 2).
- E3. The quote that decided Curlew's verdict comes from U01 and describes the finished
  migration, the matched reconciliation or the UAT sign-off.
- E4. Curlew's next step names an owner-type and a decision (for example, re-rating at the
  steering committee).
- E5. Snipe Field Service [U03] is graded Red with the verdict CORROBORATES and is not in the
  Flags table.
- E6. The summary does not present Curlew as a program in trouble.
- E7. Coverage reads "Based on 4 of 4 expected updates".
