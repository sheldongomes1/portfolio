# PBG Self-Check (a quote check, then four binary criteria)

Reference file for Portfolio Brief Gate, Workspace edition 1.0.0. Used in Stage 4.

Two design rules carry all the weight:

- **Binary, never a scale.** A "4" on a 1–5 scale smooths over exactly the failure a gate must
  stop. Every criterion returns PASS, FAIL or ABSTAIN, nothing else.
- **The gate is computed, not felt.** Gate = PASSED only if all four criteria are PASS. You
  decide each criterion; arithmetic decides the gate. No overall override, ever: that is how a
  fluent, well-cited, WRONG paragraph gets through.

ABSTAIN is not a hedge. It is only for "the thing I am asked to judge is missing or empty." When
torn between PASS and FAIL, decide; the written critique makes the decision reviewable. ABSTAIN
is not PASS, so any ABSTAIN makes the gate FLAGGED.

**Limits of this check.** You are checking a brief you wrote yourself, so you share its blind
spots. This is a self-check, not independent verification, and the footer says so. The same
checks are re-run independently outside Workspace by Skill Gate.

## Check 0: QUOTES-VERBATIM (mechanical, runs before the criteria)

Every evidence quote and watermelon quote, and every other passage in straight double quotes,
must appear **character for character in the raw text of the update whose ID is on the same
line or row**. Runs of whitespace may differ; nothing else may. This is a substring
comparison, not a judgment: do not accept a paraphrase, and do not "fix" the quote to make it
match.

- Quote found: the row stands.
- Quote not found: **downgrade the row to unverified**. Its grade shows
  `unverified (quote not found)`, its watermelon verdict becomes NEUTRAL, and any brief claim
  resting on it counts as Unsupported under FAITHFUL. Downgraded rows are listed in Coverage:
  downgraded, never silently dropped.

Quotes are formatted so a person or Skill Gate can repeat this comparison mechanically after
the fact (see PBG Output Format). Record the method as `in-model`.

## The four criteria

For each criterion, return the verdict and a critique that **quotes the specific claim checked
and the evidence consulted**. "Looks fine" is not a critique. In the critique, put text quoted
from the brief in single quotes ('…') and text quoted from an update in double quotes with its
ID, for example U02 "Declaring Red this week."

1. **FAITHFUL.** Extract each factual claim from the brief (a statement of fact, not a
   judgment word like "concerning"). Mark each *Grounded* (traceable to a specific update: name
   the ID and the phrase), *Unsupported* (no update says this), or *Contradicted* (an update
   says otherwise). PASS only if ALL claims are Grounded. Safe paraphrase, and inference that
   is explicitly labeled as inference, are Grounded; an unlabeled inference is Unsupported. The
   number rule covers **portfolio facts**: a date, cost, count, percentage, or any figure
   describing a program's state that appears in no update is an automatic FAIL. Numbers the
   workflow itself generates are exempt: severity grades, the N-of-M coverage arithmetic
   (checked under COMPLETE), and update IDs. The critique states how many claims were checked
   and quotes every Unsupported or Contradicted claim.

2. **COMPLETE.** Every update in the inventory is either represented in the brief or listed in
   Coverage as excluded, with the reason. Every grade-4 or grade-5 update appears in the brief
   body; a Red absorbed into "some challenges remain" is a FAIL, and so is a grade-4 or
   grade-5 update excluded at the requester's request. The N-of-M arithmetic in Coverage must
   be correct.

3. **NO-LAUNDER.** For every update the watermelon check marked CONTRADICTS, the brief must
   surface the contradiction (declared vs. graded, with the quote), not repeat the declared
   status and not soften the graded one. Reproducing a contradicted Green in the summary is the
   exact failure this criterion exists for: FAIL. If no update was marked CONTRADICTS, the
   criterion is PASS and the critique says "No CONTRADICTS verdicts; nothing to launder."

4. **ACTIONABLE.** Each flagged program in the brief body carries a concrete next step naming
   an owner-type and a decision or artifact ("escalate the vendor dependency at the next
   steering review"), not advice that fits any program ("continue to monitor closely": FAIL).
   A program is flagged if its watermelon verdict is CONTRADICTS or NEUTRAL, its graded
   severity is 3 or higher, or its row was downgraded to unverified. Programs excluded from
   the body are COMPLETE's concern, not this criterion's. If no program in the body is
   flagged, the criterion is PASS and the critique says so.

## Protocol

- Judge the draft against the **inventory and the graded updates only**, not against the
  conversation and not against what the writer intended.
- One retry: if any criterion is not PASS, revise the brief fixing exactly what the critiques
  name, then check again. Feeding the critique back is what makes a retry worth more than a
  re-roll. If the fix would break a requester instruction (for example, restoring a program the
  requester asked to leave out), do not make it; the criterion stays FAIL.
- Still not PASS: present the brief as FLAGGED (PBG Output Format). Flagged and visible is
  acceptable; silently shipped is not.
- Write the gate line only after this check is complete. The gate line and the Self-check
  record must agree exactly.

## Self-check record (fill in and include in the output)

| Check | Result | Critique |
|---|---|---|
| QUOTES-VERBATIM | `<n> checked, <d> downgraded (<IDs or none>)` | `Method: in-model.` |
| FAITHFUL | PASS, FAIL or ABSTAIN | quotes what was checked |
| COMPLETE | PASS, FAIL or ABSTAIN | quotes what was checked |
| NO-LAUNDER | PASS, FAIL or ABSTAIN | quotes what was checked |
| ACTIONABLE | PASS, FAIL or ABSTAIN | quotes what was checked |
| GATE | PASSED or FLAGGED | `Computed: all four PASS.` or `Computed: <criteria> not PASS.` |
| REVISION | `none needed`, `1 revision: <criteria> fixed`, or `1 revision: <criteria> still not PASS` | one sentence |
