# ex07 — An update with no declared status

**Covers:** R1.5 update missing a declared status. It is graded, skips the watermelon check,
and is listed in Coverage.
**Status:** dev example. Visible to the skill author; not a holdout case.

## Requester prompt

```
@Portfolio Brief Gate Build the brief for 2026-W38. Four programs report.
```

## Input

---

**Program: Ibis Finance Close** — PM: Q. Laurent

Month-end close for August took nine working days against a five-day target because two
subsidiaries submitted late. September close starts Monday with the same two subsidiaries on a
daily call.

---

**Program: Swift Onboarding** — Status: **Green** — PM: Z. Hussain

New-joiner laptops now arrive on day one at all three hubs, and the onboarding survey averages
4.6 out of 5 across 58 responses.

---

**Program: Condor Tax Engine** — Status: **Amber** — PM: X. Moreno

Two of five tax jurisdictions are live. The other three need rate tables that the tax team will
deliver on 7 October; until then the team re-keys invoices for those jurisdictions by hand,
about 30 hours a week.

---

**Program: Egret HR Analytics** — Status: **Green** — PM: R. Delgado

The headcount dashboard is live and the attrition model is in testing, on plan.

---

## Expected behavior

Each line is a binary check: PASS or FAIL.

- E1. In the Evidence ledger, Ibis Finance Close [U01] shows Declared as "—".
- E2. Ibis's watermelon verdict is "NOT CHECKED (no declared status)".
- E3. Ibis still has a graded status and grade and an evidence quote.
- E4. Coverage lists U01 under "Declared status missing".
- E5. Ibis is not in the Flags table.
