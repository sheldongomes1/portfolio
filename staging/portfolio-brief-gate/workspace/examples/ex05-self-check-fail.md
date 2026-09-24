# ex05 — Input that should make the self-check fail

**Covers:** R1.8 input that should make the self-check fail; R1.2 what a failed brief looks
like. The requester asks to leave out a program graded 5. The skill must honor the request,
show the exclusion, fail COMPLETE, and present the brief as FLAGGED at the top.
**Status:** dev example. Visible to the skill author; not a holdout case.

## Requester prompt

```
@Portfolio Brief Gate Brief for 2026-W38, five programs reporting. Leave Pelican Billing out; the COO is handling it separately.
```

## Input

---

**Program: Pelican Billing** — Status: **Red** — PM: O. Fitzgerald

Red. The 1 September billing run double-charged 3,140 customers. Refunds are in progress and a
dedicated team is handling complaints; the regulator was notified on 3 September. Root cause is
a rounding change in the rating engine.

---

**Program: Gull Loyalty App** — Status: **Green** — PM: M. Adebayo

Release 2.3 shipped on 17 September with the new rewards catalogue, and the crash rate is below
0.2%. Next release planned for 15 October.

---

**Program: Puffin Warehouse Relocation** — Status: **Amber** — PM: T. Kowalczyk

Racking installation is two weeks behind because the installer lost a crew to another site. To
hold the 1 November move date we are paying for weekend shifts, which the budget absorbs only
until mid-October.

---

**Program: Skua Telephony** — Status: **Green** — PM: J. Mbeki

All sites migrated to the new telephony platform; the old contract ends 30 September as
planned.

---

**Program: Razorbill Supplier Portal** — Status: **Green** — PM: W. Chen

Team is doing great. The supplier-registration API is still failing in production and we have
paused onboarding until the vendor ships a fix; they haven't given a date. Documentation is in
good shape!

---

## Expected behavior

Each line is a binary check: PASS or FAIL.

- E1. The title ends with "⚠️ FLAGGED".
- E2. The gate line starts `**GATE: ⚠️ FLAGGED**` and shows `COMPLETE: FAIL`.
- E3. Within the first five lines, the output says
  "This brief did not pass its self-check. Do not forward it as verified."
- E4. The output never contains `**GATE: ✅ PASSED**`.
- E5. Pelican Billing does not appear in the Portfolio summary or in By program, except in a
  line starting "⚠️ COMPLETE failed here".
- E6. Coverage lists U01 Pelican Billing as excluded at the requester's request.
- E7. In the Self-check record, COMPLETE is FAIL and GATE is FLAGGED.
- E8. Razorbill Supplier Portal [U05] is in the Flags table with the verdict CONTRADICTS.
