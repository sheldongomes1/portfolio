# ex06 — Too few updates

**Covers:** R1.5 too few updates. Two updates are not enough for a portfolio brief; the skill
switches to single-update mode and says why.
**Status:** dev example. Visible to the skill author; not a holdout case.

## Requester prompt

```
@Portfolio Brief Gate Portfolio brief for 2026-W38 please.
```

## Input

---

**Program: Merlin Data Centre Exit** — Status: **Green** — PM: Y. Tanaka

Racks in hall B were decommissioned on schedule. Hall C starts 6 October.

---

**Program: Kestrel Mobile Banking** — Status: **Amber** — PM: U. Ferreira

The app store review rejected build 5.2 over a privacy-label mismatch; we resubmitted on
20 September and expect a decision within a week. The launch date holds if the build is
approved by 30 September.

---

## Expected behavior

Each line is a binary check: PASS or FAIL.

- E1. The first line is
  "Single-update mode: 2 update(s) received; a portfolio brief needs at least 3."
- E2. There is no gate line and no "Portfolio summary" heading.
- E3. Each of the two programs has a grade, a watermelon verdict and a verbatim quote.
- E4. Each of the two programs has a line starting "Ask the program lead next".
