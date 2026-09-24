# PBG Severity Rubric (anchored, tone-blind)

Reference file for Portfolio Brief Gate, Workspace edition 1.0.0. Used in Stage 1.

The design target: **the reporter's tone is not evidence; the stated consequence is.**
Optimistic authors under-report and anxious authors over-report. The rubric must be immune to
both, or the portfolio inherits every reporter's personality.

Grade each update 1–5 on the consequence its text actually STATES, answering three questions
from the text alone: *Is anything irreversibly lost (time, scope, money, trust)? Was there a
workaround, and at what cost? How much of the program is affected?*

## Anchors

| Grade | Meaning | Example evidence in an update |
|---|---|---|
| **5 — Critical / irrecoverable** | Milestone missed or unmissable; committed date, scope or budget lost; a dependency failed with no path; silent damage already done | "vendor cancelled the contract", "the migration corrupted the config baseline", "we will not make the Q3 energization date" |
| **4 — Blocked** | Fully blocked on the critical path, no workaround in hand; escalation required; "waiting on X" with no date | "cannot proceed until security review completes, no ETA", "hiring req cancelled, no coverage for the workstream" |
| **3 — Costly workaround** | Progressing, but via a significant detour, every time; sustained overrun absorbed by the team | "manually reconciling the two trackers weekly", "borrowing SRE time from Program B to hold the date" |
| **2 — Friction** | Slower or clumsier than planned; task otherwise on track | "approvals taking longer than expected but within buffer" |
| **1 — Healthy / cosmetic** | On track; issues mentioned are preference-level | "on schedule; considering a template change" |

## Rules

1. **Grade the STATED consequence, never a speculated one.** "This could slip the date" is not
   evidence that it did. One exception: structurally severe classes grade high even when
   reported calmly. These are silent loss of committed scope, a safety or compliance breach,
   and damage discovered after the fact.
2. **Ignore tone entirely.** Exclamation marks, "thrilled to share", "unfortunately", emoji:
   none of it is consequence. A cheerful update reporting a cancelled dependency is a 4–5. An
   alarmed update about a renamed dashboard is a 1.
3. **Default down.** If no consequence is described, grade 1–2. A high grade must be earned by
   concrete evidence in the text, never by vibes, never by the program's history.
4. **Evidence quote for every graded update; required for grades 4 and 5.** Copy the
   supporting passage verbatim (200 characters or fewer) as the evidence quote. This is the
   grounding an auditor, or a skeptical director, checks. It is compared character for
   character at the self-check (PBG Self-Check, QUOTES-VERBATIM) and can be re-checked
   mechanically afterward. A quote not found in the raw text downgrades the row to unverified.
   Quote the text or grade lower.
5. **The grade is independent of the declared status.** You are computing what the status
   *should* be from the narrative. The comparison with what was *declared* happens in the
   watermelon check, not here.

## What each graded update records

These fields fill that update's row in the Evidence ledger (PBG Output Format):

- ID, program, declared status (or `—`)
- Graded severity (1–5) and graded status
- Evidence quote: verbatim, 200 characters or fewer, from this update only
- Rationale: one sentence naming the anchor and why (used in By program)

Severity to status: 1–2 → Green, 3 → Amber, 4–5 → Red.
