# ex03 — A genuine Green that must not be flagged

**Covers:** R1.8 genuinely Green program that must not be flagged. Tone-blind grading in both
directions: an exuberant real Green, and an alarmed update about a cosmetic issue.
**Status:** dev example. Visible to the skill author; not a holdout case.

## Requester prompt

```
@Portfolio Brief Gate Build the 2026-W38 portfolio brief. Four programs are expected.
```

## Input

---

**Program: Falcon Branch Network** — Status: **Green** — PM: H. Lindgren

Thrilled to report we're LIVE!!! 🎉🎉 Cutover completed on 15 September, all 14 branches are
running on the new network, and there have been zero Sev-1 incidents in the first five days.
Hypercare ends 3 October as planned.

---

**Program: Plover Intranet** — Status: **Green** — PM: C. Byrne

URGENT!!! The intranet homepage is still showing last year's logo and several people have
noticed. This is really embarrassing. Everything else is on schedule and the content migration
finished on time.

---

**Program: Gannet Expense System** — Status: **Amber** — PM: R. Haddad

The bank changed its card-feed file format, so finance staff upload the card file by hand each
morning, around two hours a day, until the new format is supported. The revised integration
date is 10 October.

---

**Program: Auk Warehouse Automation** — Status: **Red** — PM: S. Mensah

Red: the conveyor supplier went into administration on 11 September and the order for the
sorting line is cancelled. We are sourcing a replacement supplier; no revised date yet.

---

## Expected behavior

Each line is a binary check: PASS or FAIL.

- E1. Falcon Branch Network [U01] is graded Green (grade 1 or 2).
- E2. Falcon's watermelon verdict is CORROBORATES.
- E3. Falcon is not in the Flags table and is not described anywhere as at risk.
- E4. Plover Intranet [U02] is graded Green (grade 1 or 2) despite its alarmed tone.
- E5. Auk Warehouse Automation [U04] is graded Red with the verdict CORROBORATES.
- E6. The Flags section has no table rows and uses the line starting
  "No CONTRADICTS verdicts this period".
- E7. The gate line is `**GATE: ✅ PASSED**`.
