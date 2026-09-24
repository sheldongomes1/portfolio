# ex01 — Watermelon with a bullish tone

**Covers:** R1.8 watermelon case 1 (declared Green, narrative Red). Tone-blind grading.
**Status:** dev example. Visible to the skill author; not a holdout case.

## Requester prompt

```
@Portfolio Brief Gate Build the portfolio brief for week 2026-W38. Five programs should be reporting.
```

## Input

---

**Program: Cobalt Treasury Platform** — Status: **Green** — PM: D. Asante

What a sprint! 🚀 The squad shipped the liquidity dashboard two days early and the stakeholder
demos landed brilliantly. On the bank connectivity side, the partner bank's API certification
failed for the second time, and their next certification slot is in six weeks, so we will not
go live on 20 October as planned. Energy on the team is outstanding and we're in great shape
overall!

---

**Program: Meridian HR Suite** — Status: **Amber** — PM: L. Moreau

Payroll parallel runs continue, but the time-and-attendance feed still arrives in the wrong
format, so two analysts rebuild the file by hand every Monday, about a day and a half of effort
each week. Supplier patch expected at the end of October. All other workstreams are on plan.

---

**Program: Sable Document Archive** — Status: **Green** — PM: K. Oyelaran

Migration wave 3 finished on 16 September: 1.2 million records moved, checksum validation
passed on every batch, and the legacy archive is now read-only. Wave 4 starts 30 September on
the published plan.

---

**Program: Tern Procurement Portal** — Status: **Red** — PM: B. Castellanos

Red. Supplier onboarding is blocked: the identity provider rejected our SSO configuration and
security has not scheduled the re-review. We cannot onboard the first 40 suppliers until that
clears, and there is no date yet. Escalated to the CIO office on Tuesday.

---

*Expected but not received this period: Quill Reporting.*

## Expected behavior

Each line is a binary check: PASS or FAIL.

- E1. Cobalt Treasury Platform [U01] is in the Flags table with the verdict CONTRADICTS.
- E2. Cobalt is graded Red (grade 4 or 5).
- E3. The quote that decided Cobalt's verdict comes from U01 and describes the failed
  certification or the missed go-live date, not the team's mood.
- E4. Nowhere is Cobalt described as Green, on track or in great shape.
- E5. Tern Procurement Portal [U04] is graded Red, its verdict is CORROBORATES, and it is not
  in the Flags table.
- E6. Sable Document Archive [U03] is not in the Flags table.
- E7. Coverage reads "Based on 4 of 5 expected updates" and names Quill Reporting.
- E8. Cobalt's next step names an owner-type and a decision or artifact.
