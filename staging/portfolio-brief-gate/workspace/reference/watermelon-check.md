# PBG Watermelon Check (declared status vs. what the narrative says)

Reference file for Portfolio Brief Gate, Workspace edition 1.0.0. Used in Stage 2.

Compare a program's **declared status** with what its **own narrative** states, and return a
three-way verdict.

A "watermelon" is green outside, red inside: the declared status says healthy while the text
underneath describes a blocked critical path. It is rarely deception. Reporting red invites
blame, so narratives carry the truth while the status carries the hope. A summarizer that reads
only the status, or mirrors the narrative's tone, *launders* the watermelon into fluent
executive prose. This check prevents that.

## The check (apply to each update that has a declared status)

> You are performing a narrative–status divergence analysis. You receive a program update's
> DECLARED STATUS and its NARRATIVE TEXT, plus the true-status grade computed from the
> narrative (PBG Severity Rubric).
>
> Assess whether the narrative **CONTRADICTS**, **CORROBORATES**, or is **NEUTRAL** toward the
> declared status.
>
> - **CONTRADICTS**: the declared status is healthier than the narrative supports. The text
>   describes blocks, misses, or losses while the status says Green (or Amber trending Green),
>   or the language is reassuring or evasive about areas the facts show deteriorating. **This
>   is the high-signal case, a governance red flag.** It includes the reverse, rarer case: a
>   declared Red while the narrative shows recovery. Flag it too and label it `sandbagged`.
> - **CORROBORATES**: the declared status honestly reflects the narrative, including an honest
>   Red or Amber. Honest Reds are the healthiest rows in a portfolio; say so.
> - **NEUTRAL**: the narrative is too thin to judge either way. That is itself worth a note: a
>   Green with no evidence is unverifiable, not verified.
>
> Also classify the narrative TONE as BULLISH, CAUTIOUS, NEUTRAL or MIXED, solely so the reader
> can see tone and verdict side by side. Tone never changes the verdict.
>
> Record: verdict, tone, the verbatim quote that decided the verdict, and a one-sentence
> explanation.

## Rules

1. The verdict is **evidence-based, not tone-based**. A bullish tone with facts that support
   Green is CORROBORATES, not CONTRADICTS. Divergence is between the *declared status and the
   stated facts*; tone is reported separately.
2. Every CONTRADICTS verdict carries the verbatim quote that decided it. No quote means
   NEUTRAL.
3. An update with no declared status skips this check, since there is nothing to diverge from.
   Its grade stands alone. Record its verdict as `NOT CHECKED (no declared status)` and list
   its ID under "Declared status missing" in Coverage.
4. In the brief, CONTRADICTS rows appear in the Flags table at the top with the declared
   status, the graded status and the quote. The gap between declared and graded is the
   headline, not the narrative's own summary.

## What each checked update records

These fields fill that update's row in the Evidence ledger (PBG Output Format):

- Watermelon verdict: CONTRADICTS, CONTRADICTS (sandbagged), CORROBORATES, NEUTRAL, or
  NOT CHECKED (no declared status)
- Tone: BULLISH, CAUTIOUS, NEUTRAL or MIXED
- Watermelon quote: verbatim, 200 characters or fewer, from this update only (or
  `same as evidence` when it is the same passage as the evidence quote)
- Explanation: one sentence (used in the Flags table and By program)
