# Changelog

All notable changes to the portfolio site. Newest first.

## [4.0.0] — 2026-08-19 — Problem-first repositioning: the Problem Map + Agent Frontier

Reframed the whole site around the problems that stall enterprise AI, distilled from the
private problem-map brief (`google-problem-map-brief.pdf` — kept **unpublished** on purpose:
it's framed as interview prep and stays out of the Docker image and off the page).

### Added
- **"The Problem Map" section** (`#problem-map`, after the impact strip): four named gaps —
  Evaluation Gap, Model Upgrade Tax, Agent Operations Gap, Activation Gap — each as
  pain → shipped-receipt cards, closed by the wedge pull-quote ("a proof problem, not a
  capability problem"). New `.gap-*` / `.wedge` CSS on existing tokens.
- **"Agent Frontier / Now Building" section** (`#frontier`, after the Arc): the three open
  agent problems — memory & context management, continuous learning, planning & long
  horizons — each with a position earned from shipped systems plus an "In progress" item:
  the weekly reconciliation agent, the draft-vs-accepted error-discovery loop, the PSIS
  workflow→agent coordinator, and LangGraph routed chat. Platform-depth footer
  (ADK 2.2 in production · LangGraph · deterministic Python).
- **Arc rung "Unattended · Long-running"** — the two agents already running without
  supervision (daily hiring-signal job, weekly repo reconciler); caption extended.

### Changed
- **Hero**: h1 now "AI doesn't stall on capability. It stalls on proof."; sub leads with the
  pilot-to-production stat and the proof-discipline value prop; primary CTA → `#problem-map`.
- Philosophy card principle 2 adds "workflow when the order is known; agent when the order
  depends on findings."
- Nav: added Problem Map + Now Building (dropped Skills/The Arc links to keep six).
- `<title>` / meta / OG / Twitter descriptions moved to the problem-first framing.
- Skills: added Agent Memory & Context, Continuous Learning · Golden Sets, LangGraph.
- Contact sub now names the four problem areas as the roadmap being hired for.

### Facts discipline
- Survey stats attributed generically ("2026 industry surveys"); Gartner named only for its
  public 2027 decommission prediction. All product numbers (42% fail rate, 5/13→12/13,
  21.4-h hang → 240-s deadline, silent 7-day outage) trace to the owner's own writeups in
  `linkedin-coach/interview-prep/` and `signal-intelligence-system` docs.

## [3.1.0] — 2026-06-28 — Pain Signal Intelligence accuracy + depth pass

Reconciled the flagship section against the source-of-truth product repo
(`signal-intelligence-system`) and enriched it with real specifics.

### Fixed
- **Source count 6 → 5.** Active sources are GitHub, Hacker News, Stack Overflow, Discourse, G2.
  **Reddit was dropped at go-live** (API onboarding wasn't worth it) — removed from the count,
  pipeline tooltip, and the stats box; tooltip now notes the drop.
- **ADK 2.0 → 2.2** (the deployed system runs the ADK 2.2 graph `Workflow`).
- Confirmed `frequency × intensity × addressability²` is correct — the scorer raises
  addressability to a 2.0 exponent (`tools/score_tools.py`), so the square stays.

### Changed (richer)
- **Insight** now explains the multiplicative *veto* (a near-zero pillar kills the score vs.
  being averaged away) and why addressability carries the highest exponent.
- **Tradeoff** adds per-stage BigQuery persistence / crash-resume; model reserved for judgment.
- **Result** names the two planted lies (count inflated 12→80, fabricated "users want dark mode")
  caught first-run with row-level evidence; same-family control flagged nothing.
- **Stack tags** specified: Gemini 2.5 Flash + Pro · Vertex AI, Claude Sonnet (Judge),
  Cloud Run · Scheduler · Trace. Pipeline tooltips enriched (formula, retry max 2, model tiers).

## [3.0.0] — 2026-06-27 — RedInk-palette re-skin + Pain Signal Intelligence flagship

Re-skinned the site to the RedInk product palette and reframed the work around the most
"googly" build (multi-agent on Google ADK). Tuned for an ICP of a Google hiring manager.

### Changed
- **Full palette re-skin to the RedInk product system** — indigo/blurple `#635bff` accent
  (hover `#4f46e5`, tint `#ede9fe`) on clean white + neutral grays (`#111827` ink,
  `#f9fafb` surfaces, `#e5e7eb` borders). Dark bands moved from forest-green-black to a deep
  indigo-navy (`#0e1020`). Kept the Fraunces + Plus Jakarta type system. All ~15 design
  tokens remapped; hardcoded greens inside the dark bands hand-converted to the navy family.
- **New flagship: Pain Signal Intelligence** (`paintoprd.dev`) — multi-agent system on Google
  ADK 2.0, promoted to the featured slot. CSS-rendered cross-model judge verdict
  (GROUNDED / ACTIONABLE / RETRY-FIRES), Problem→Insight→Tradeoff→Result, a deterministic-graph
  pipeline strip (6 sources → classify·Flash → score·Python → BigQuery → synthesize·Pro →
  judge·Claude → PRD), and stats. Links to the live app + the public repo.
- **RedInk demoted to secondary featured** ("Also Featured") — same content, quieter surface.
- **Featured-visual demo panels** (judge verdict + divergence labels) moved from dark navy to
  the light lilac `#ede9fe` surface with white inner cards — lighter, matches the newsletter ribbon.
- **The Arc + AI-PM matrix** updated — Pain Signal Intelligence added as the flagship rung
  (Multi-agent · Self-verifying) and the top matrix row (full marks across all five capabilities).
- **Skills** refreshed toward the Google stack — Multi-agent Systems, Google ADK · Gemini,
  BigQuery, LLM-as-judge.

### Added
- **"No Black Boxes" newsletter as a centerpiece** — a hero subscribe ribbon under the hero,
  plus a dedicated dark section (`#newsletter`) with a subscribe CTA, what's-inside points,
  and a recent-threads list. Nav gains a Newsletter link; the Writing section's CTA leads with
  Subscribe. Newsletter URL:
  `linkedin.com/newsletters/no-black-boxes-7472113158434934784/`.

### Fixed
- **Scroll-reveal robustness** — the `IntersectionObserver` fade now has defense-in-depth so
  content can never stay permanently hidden after a hash/deep-link jump or fast scroll: a
  load/hashchange "reveal what's in view" sweep plus a hard `setTimeout` failsafe.

## [2.0.0] — 2026-05-31 — "Google-PM-grade" overhaul

The site was redesigned from a generic PM portfolio into a focused, eval-first AI-PM case.
Every CTA now resolves to a live product; nothing dead-ends. Source of truth moved from the
surge CDN into this git repo.

### Added
- **Brand images** — an editorial `og-card.png` (1200×630) share thumbnail in the site's own
  Fraunces/forest-green identity, and a full favicon set (`favicon.svg`, `favicon-16/32.png`,
  `favicon.ico`, `apple-touch-icon.png`) — an "SG" monogram replacing the placeholder tab icon.
  Plus `theme-color`. Generator: `_meta/make-brand-assets.py`.
- **RedInk multi-repo architecture strip** — the flagship card now shows the four public repos
  in data-flow order (`qqq-anomaly-lab → scoring-pipeline → qqq-eval-suite → redink-ui`), each
  clickable. (Superseded the single "Code ↗" link once all four RedInk repos went public 2026-05-31.)
- **"Build in Public" section** — four curated LinkedIn posts (binary evals, precision-as-trust,
  11s→0.1s latency, few-shot > instructions), sourced from the user's live posts doc, linking to
  the LinkedIn activity feed. Refreshable via `_meta/REFRESH.md`.
- **RedInk as the featured project** — Problem → Insight → Tradeoff → Result framing, with a
  CSS-rendered narrative-divergence demo (CONTRADICTS / NEUTRAL / CORROBORATES) and real stats.
- **"The Arc" maturity ladder** — the deliberate progression from shipping → measuring →
  systems → agentic.
- **"The AI-PM Bar" capability matrix** — products × (grounding, evals, agentic, telemetry, shipped).
- **Résumé CTA** wired to `/Resume.pdf` in nav, hero, and contact.
- OpenGraph + Twitter share meta, canonical URL.
- Subtle scroll fade-in (respects `prefers-reduced-motion`).
- Git repo + Vercel config (`vercel.json`): clean URLs, security headers, cache policy.

### Changed
- **Hero eyebrow** → `Senior PM · 15 Years · CFA · Now Building AI Products` (senior pedigree up front).
- **Hero sub** → eval-first AI products positioning.
- **Impact band** → real metrics (`1,900+ filings`, `700+ sources`, `33→90% precision`, `56× latency`)
  replacing the old vanity numbers (`3+ / 1 / GCP / MCP`).
- **"Also Building"** → three real, live products (PM Confessional, Strategic Fit Canvas,
  Product Management OS), each Problem → Result, each with a working link.
- **Skills** curated — removed junior signals (`SQL (working)`, `CI/CD Basics`, `HTML/CSS`, `Replit`).
- PM Philosophy card #1 reframed around grounding + measurement.

### Fixed
- **All dead CTAs** (`href="#"`, `open('#')`) replaced with live URLs or removed. No link dead-ends.
- Removed the empty "Coming Soon" card and the placeholder "GCP Mini Products" /
  "Replit → GCP Migration" cards.
- Removed dependency on missing binary assets (Loom `.mp4`, `placeholder-screenshot.png`).

### Notes
- Owner-only follow-ups (GitHub profile, repo renames, RedInk repo visibility) tracked privately
  in `_meta/OWNER-ACTIONS.md`.
- Pre-overhaul snapshot preserved in `archive/` (git-ignored).

## [1.0.0] — earlier — initial site
- Single-file HTML portfolio, hand-deployed to `sheldon-gomes.surge.sh`. Featured project: Product
  Management OS. Several placeholder CTAs.
