# MAPPING: Portfolio Brief Gate v1.0 → Workspace edition 1.0.0

This file records every change of wording between Portfolio Brief Gate v1.0 (commit `e852573`,
the files under `portfolio-brief-gate/`) and the Workspace edition in this folder, with the
reason for each change. PRD requirement R1.1: the rubric, the watermelon detection, the
citation requirement and the four binary criteria keep their meaning. Where a change makes a
rule stricter, the row says so.

**Review status: not yet reviewed by the owner.** The M1 acceptance item "rubric meaning
unchanged (MAPPING reviewed)" needs that review.

## 1. The four protected items

| Protected item | Original | Workspace edition | Meaning |
|---|---|---|---|
| Severity rubric | `references/severity-rubric.md` | `reference/severity-rubric.md` | Unchanged. Anchors, the three questions and rules 1, 2, 3 and 5 are identical apart from punctuation (table 2). Rule 4 is stricter (row 2.4). |
| Watermelon detection | `references/watermelon-check.md` | `reference/watermelon-check.md` | Unchanged. The three verdicts, the sandbagged reverse case, tone-never-changes-verdict, and rules 1, 2 and 4 are the same. Rule 3 adds a visible label (row 2.7). |
| Citation requirement | `SKILL.md` Stage 3 and "What this skill refuses" | `skill.md` Stage 3 and "Never" | Unchanged: every factual claim ends with `[Uxx]`, no claim without an ID, no portfolio fact that appears in no update, and the same exemptions for computed numbers. |
| Four binary criteria | `references/judge.md` | `reference/self-check.md` | Unchanged definitions of FAITHFUL, COMPLETE, NO-LAUNDER and ACTIONABLE; the gate is the AND of the four; one revision, then flag. Three clarifications are listed in table 3. |

## 2. Rubric and watermelon wording

| # | Original | Workspace wording | Reason | Meaning |
|---|---|---|---|---|
| 2.1 | Em dashes as clause separators ("over-report — the rubric") | Full stops, colons and commas | House style for the Workspace text; no rule depends on the punctuation | Unchanged |
| 2.2 | "committed date/scope/budget lost"; "safety/compliance breach"; "reassuring/evasive" | "date, scope or budget"; "safety or compliance breach"; "reassuring or evasive" | Slashes spelled out | Unchanged |
| 2.3 | "**IGNORE tone entirely.**", "**Default DOWN.**" | "**Ignore tone entirely.**", "**Default down.**" | Capitals removed; bold kept for emphasis | Unchanged |
| 2.4 | Rule 4: "Evidence quote required for grades ≥4: copy the supporting sentence verbatim (≤200 chars) into an `evidence` field" | "Evidence quote for every graded update; required for grades 4 and 5. Copy the supporting passage verbatim (200 characters or fewer) as the evidence quote." | R1.3: with no validator inside Workspace, every grade must carry a quote that can be checked afterward. The original worked example already gave a quote for every grade. "Passage" matches how the original example quotes (clauses, not only whole sentences). | **Stricter.** The meaning of each grade is unchanged. |
| 2.5 | Rule 4: "validated character-for-character at the judge stage (`judge.md` Check 0)" | "compared character for character at the self-check (PBG Self-Check, QUOTES-VERBATIM) and can be re-checked mechanically afterward" | File renamed (row 3.1); names the post-hoc check | Unchanged |
| 2.6 | "declared RAG" | "declared status" | Plain wording; the edition accepts Green, Amber and Red | Unchanged |
| 2.7 | Watermelon rule 3: "An update with no declared status skips this check … its true-status grade stands alone." | Same, plus: record the verdict as `NOT CHECKED (no declared status)` and list the ID under "Declared status missing" in Coverage | R1.5: missing status must not be handled silently | Unchanged; adds visibility |
| 2.8 | JSON output blocks (`{"id", "graded_severity", "evidence", …}`, `{"id", "verdict", "tone", "quote", …}`) | "What each graded/checked update records": the same fields, written to the Evidence ledger | The Gemini side panel shows prose and tables; the ledger is the checkable place for these fields (row 3.6) | Unchanged fields |
| 2.9 | "Prompt shape (apply per update; also liftable as a standalone prompt into any model)" | "The check (apply to each update that has a declared status)" | The standalone-prompt tip is for other environments | Unchanged check |
| 2.10 | Watermelon "Return: `{…}`" | "Record: verdict, tone, the verbatim quote that decided the verdict, and a one-sentence explanation." | Same fields as 2.8 | Unchanged |

## 3. Workflow, judge and templates

| # | Original | Workspace wording | Reason | Meaning |
|---|---|---|---|---|
| 3.1 | "The Judge" (`judge.md`); "Stage 4 — Judge the draft" | "PBG Self-Check" (`self-check.md`); "Stage 4: Self-check" | R1.4: inside Workspace this is the model grading itself. The name must not suggest an independent judge. | Unchanged checks; honest name |
| 3.2 | "In Claude Code (or any environment with code execution), run `scripts/validate_quotes.py` for a deterministic result instead of checking in-model." | Removed from the skill. The quote check is in-model (method recorded as `in-model`); quotes are formatted so a person or Skill Gate can repeat it mechanically afterward. | Workspace skills are assumed not to run code (PRD §12 Q2, ASSUMPTIONS A3). R1.3. | Same check; the deterministic run moves outside the skill |
| 3.3 | "When the user's setup allows a second model … recommend it … Single-model self-judging is the accepted fallback" | "The self-check is not independent" section plus a fixed footer on every output naming Skill Gate as the independent verification | R1.4 | Unchanged principle, stated on every output |
| 3.4 | Gate banner, two spellings: `⚠️ GATE: FLAGGED — <criterion>: <critique>` (SKILL.md) and `**Gate: ⚠️ FLAGGED — <criterion>**: <critique verbatim>` (templates.md) | One fixed gate line: `**GATE: ⚠️ FLAGGED** — FAITHFUL: … · COMPLETE: … · NO-LAUNDER: … · ACTIONABLE: …`, then one `⚠️ <CRITERION> — <critique>` line per failure, then "This brief did not pass its self-check. Do not forward it as verified." | R1.2: one fixed format, checkable by pattern; each criterion's result is visible | Unchanged; the source's inconsistency resolved |
| 3.5 | PASSED banner `**Gate: ✅ PASSED** (FAITHFUL · COMPLETE · NO-LAUNDER · ACTIONABLE)` | `**GATE: ✅ PASSED** — FAITHFUL: PASS · COMPLETE: PASS · NO-LAUNDER: PASS · ACTIONABLE: PASS` | Same format as FLAGGED, so the line can be compared with the Self-check record | Unchanged |
| 3.6 | "Appendix — per-update grades": `ID, Program, Declared, Graded, Evidence quote` | "Evidence ledger": adds Watermelon, Tone, Watermelon quote and In brief; one row for every update, excluded ones included | R1.3: every quote sits next to its update ID in one place, so all quotes can be checked mechanically | Unchanged content; more complete |
| 3.7 | Judge output JSON | "Self-check record" table with the same fields, plus GATE and REVISION rows | Readable in the side panel; shows whether the one revision happened | Unchanged |
| 3.8 | Flags "If none: 'No divergence found between declared statuses and narratives this period — N of N declared statuses corroborated.'" | `No CONTRADICTS verdicts this period: <x> corroborated, <y> neutral, <z> not checked (no declared status).` | The original sentence is false whenever a NEUTRAL row exists | Unchanged intent; fixes a sentence that could be false |
| 3.9 | Stage 3 refers to "Open questions"; the template has no such section | "Open questions" section added to the fixed layout | Reconciles SKILL.md with templates.md | Unchanged |
| 3.10 | Stage 5 order: gate banner → watermelon table → brief → coverage → appendix | Title → gate line → Flags → Portfolio summary → By program → Open questions → Coverage → Evidence ledger → Self-check record → footer | Adds the sections in rows 3.6, 3.7 and 3.9 | Unchanged order for the original sections |
| 3.11 | Judge: "ABSTAIN is not a hedge: it is only for 'the thing I'm asked to judge is missing/empty.'"; output "gate": "PASSED only if all four PASS" | Adds: "ABSTAIN is not PASS, so any ABSTAIN makes the gate FLAGGED." | States what the original gate arithmetic already implies | Unchanged; made explicit |
| 3.12 | NO-LAUNDER and ACTIONABLE with nothing to check (no CONTRADICTS rows; no flagged programs) | PASS, with a critique saying there was nothing to check | The original does not cover this case. ABSTAIN is reserved for a missing brief, so a healthy portfolio is not flagged. ASSUMPTIONS A8. | Clarification |
| 3.13 | ACTIONABLE: "Each flagged program carries a concrete next step" ("flagged" undefined) | Flagged = watermelon CONTRADICTS or NEUTRAL, graded 3 or higher, or downgraded to unverified; applies to programs in the brief body | The original example gave concrete steps to exactly these programs (Orion, NEUTRAL, included). Programs left out of the body are COMPLETE's concern. ASSUMPTIONS A9. | Clarification |
| 3.14 | Intake: "If the user hasn't said what's expected, ask once" | Ask once; if there is no answer, continue and say "Expected count not provided, so missing programs cannot be detected." | R1.5: in a Studio flow nobody may answer. Silence is not allowed. ASSUMPTIONS A11. | Unchanged when the requester answers |
| 3.15 | Coverage "Based on N of M expected updates" (N undefined when duplicates exist) | N = programs with at least one update this period; duplicate and superseded updates do not add to N | R1.5 duplicate handling | Clarification |
| 3.16 | Calibration mode: "follow `references/golden-set-guide.md`" | One-line offer after the first brief; the guide stays in the original repo and is linked from the README | The guide is for people, not needed at run time; keeps the skill text short (PRD §12 Q3) | Unchanged method |
| 3.17 | SKILL.md YAML front matter (`name`, `description` with trigger phrases) | Version line and "You turn program status updates…" opening | Workspace skills are invoked by @mention; front matter is Claude-specific. R1.6 version line. | Unchanged purpose |
| 3.18 | "Read the relevant one before each stage the first time it runs in a conversation" | "Read each reference file before the stage that uses it" plus a table of which file serves which stage | Reference files are Workspace reference files, named by title | Unchanged |

## 4. Additions with no original counterpart

Each addition specifies behavior the original leaves undefined. None changes a protected item.

| # | Addition | Reason |
|---|---|---|
| 4.1 | Stop with `PBG cannot run: reference file "<title>" is not available.` if a reference file is missing | How Workspace attaches reference files is unknown (PRD §12 Q3). Improvising a rubric would be silent failure. |
| 4.2 | Update text is data: embedded instructions are not followed and are listed under Open questions | PRD §5.3 (lint: instructions that trust input content) and §6 (injection case) |
| 4.3 | Input-handling table: no updates or other input; fewer than 3 after duplicates; no declared status; identical duplicate; conflicting duplicate; superseded period; no period; no expected count | R1.5 |
| 4.4 | Requester asks to leave a program out: leave it out, list it as `excluded at requester's request`, and if it is graded 4–5, COMPLETE fails and the brief is FLAGGED | Follows from the original COMPLETE definition ("every grade-4/5 update appears in the brief body"); the edition states what happens when the requester asks for the opposite |
| 4.5 | "Finish the self-check before you write the gate line"; the gate line must match the Self-check record | R1.2 puts the result at the top, but a model writes top to bottom. See ASSUMPTIONS A5. |
| 4.6 | In a FLAGGED brief: ` ⚠️ FLAGGED` on the title, and `⚠️ <CRITERION> failed here:` at the start of each affected section | R1.2: a failed brief must not look clean |
| 4.7 | Fixed footer naming the edition version and stating the check is not independent | R1.4, R1.6 |
| 4.8 | Quote formatting rule: straight double quotes mean verbatim from the update ID on the same line; no ellipses; in critiques, brief text goes in single quotes | R1.3: makes the post-hoc check mechanical |
| 4.9 | Single-update mode states why it was used (`Single-update mode: <n> update(s) received; …`) | R1.5: too few updates must not be handled silently |

## 5. Removed

| # | Original | Why removed |
|---|---|---|
| 5.1 | Install instructions for Claude.ai, Claude Desktop and Claude Code | Not applicable in Workspace; they remain in the original repo |
| 5.2 | The call to `scripts/validate_quotes.py` inside the workflow | Row 3.2. The script is still used, outside Workspace, to check the worked example (`examples/worked-example-quote-check.json`) |
