# ex10 — Input that is not status updates

**Covers:** R1.5 bad or out-of-scope input. The skill must say it found no status updates and
stop, instead of inventing a brief.
**Status:** dev example. Visible to the skill author; not a holdout case.

## Requester prompt

```
@Portfolio Brief Gate Can you turn this into the portfolio brief?
```

## Input

---

**Team offsite — agenda (draft)**

09:30 Coffee and welcome
10:00 Year in review (15 min per team)
12:00 Lunch at the harbour café
13:30 Workshop: how we run planning next year
15:30 Walk along the river, weather permitting
17:00 Close

---

## Expected behavior

Each line is a binary check: PASS or FAIL.

- E1. The output is a single line starting "PBG: no program status updates found."
- E2. The output contains no gate line, no brief headings, and no grades.
