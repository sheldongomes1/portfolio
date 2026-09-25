# sheldongomes.dev — portfolio

Personal portfolio of **Sheldon Gomes** — Senior Product Manager (Societe Generale, CFA) building eval-first AI products.

**Live:** https://sheldongomes.dev/  ·  **Stack:** single static `index.html`, no build step, deployed on GitHub Pages via Actions.

---

## Why it's built this way

One self-contained HTML file. No framework, no bundler, no `node_modules`. The entire site — markup, design system, and the small amount of JS (scroll fade-in) — lives in `index.html`. This is a deliberate choice:

- **Zero build = zero rot.** Nothing to `npm install`, nothing to patch, no lockfile drift. It will deploy identically in five years.
- **Edit → push → live.** Vercel auto-deploys every push to `main`, with a preview URL per branch and one-click rollback.
- **No binary-asset dependencies.** The featured-project visual is rendered in CSS, not a video/screenshot, so a fresh clone always renders correctly.

## Repository layout

```
index.html        The entire website (markup + CSS + JS)
Resume.pdf        Served at /Resume.pdf — linked from nav, hero, contact
vercel.json       Clean URLs + security headers + cache policy
CHANGELOG.md      What changed and why, newest first
DEPLOY.md         How to deploy, roll back, and add a custom domain
README.md         This file
```

> Private planning docs (goals, internal notes, owner to-dos) live in a git-ignored
> `_meta/` folder so this repo stays safe to make public. See `DEPLOY.md`.

## Local preview

No tooling required — open `index.html` in a browser, or serve it:

```bash
python3 -m http.server 8000   # then visit http://localhost:8000
```

## Deploying

Push to `main`; Vercel builds and deploys automatically. Full instructions, rollback,
and custom-domain steps are in [`DEPLOY.md`](./DEPLOY.md).

---

© 2026 Sheldon Gomes.
