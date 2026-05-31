# Changelog

All notable changes to the portfolio site. Newest first.

## [2.0.0] — 2026-05-31 — "Google-PM-grade" overhaul

The site was redesigned from a generic PM portfolio into a focused, eval-first AI-PM case.
Every CTA now resolves to a live product; nothing dead-ends. Source of truth moved from the
surge CDN into this git repo.

### Added
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
