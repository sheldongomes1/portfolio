# Deploying & maintaining the portfolio

The site is a single static `index.html` deployed on **GitHub Pages** via a GitHub Actions
workflow (`.github/workflows/deploy.yml`), git-backed, auto-deployed on every push to `main`.

**Live URL:** https://sheldongomes1.github.io/portfolio/

---

## How it's wired (already set up)

- Repo: https://github.com/sheldongomes1/portfolio (public — private planning is git-ignored).
- Pages source: **GitHub Actions** (not the legacy "deploy from branch").
- The workflow checks out the repo and publishes it as-is to Pages, so only tracked files ship.
- Path note: this is a **project** Pages site served at the `/portfolio/` subpath, so in-page
  asset links are **relative** (`Resume.pdf`, not `/Resume.pdf`). Keep new asset links relative,
  or they'll 404 on Pages.

## Day-to-day: making a change

```bash
# edit index.html
git add -A
git commit -m "Describe the change"
git push            # the Pages Action redeploys main in ~1 min
```
Watch the deploy: repo → **Actions** tab → latest "Deploy to GitHub Pages" run
(or `gh run watch` locally).

## Rolling back

`git revert <bad-commit> && git push` — the Action redeploys the reverted state.
(Or re-run an older successful workflow run from the Actions tab.)

## If the Pages URL ever changes (e.g. repo rename or custom domain)

Update the canonical/OG URLs in `index.html` — they're absolute and must match the live origin:
- `<meta property="og:url" …>`
- `<meta property="og:image" …>`  (see "Social share image" below)
- `<link rel="canonical" …>`

## Adding a custom domain (when ready)

1. Buy a domain (e.g. `sheldongomes.com`).
2. Repo → Settings → Pages → "Custom domain" → enter it. GitHub writes a `CNAME` file to the repo.
3. At your registrar, add a `CNAME` record for `www` → `sheldongomes1.github.io`, and/or the four
   `A` records GitHub lists for the apex. Tick "Enforce HTTPS" once the cert provisions.
4. A custom domain serves at the **root**, so switch the in-page asset links back to absolute
   (`/Resume.pdf`) and update the OG/canonical URLs in `index.html`.

## Social share image (optional polish)

`index.html`'s OG tags reference `og-card.png` for link previews. Until that file exists, the
text preview still works; the thumbnail just won't show. To add it: drop a `1200×630`
PNG named `og-card.png` in the repo root and commit it.

## Assets

`Resume.pdf` is committed and served at `Resume.pdf` (linked from nav, hero, contact).
It's self-hosted on purpose — recruiters download a clean PDF from your own domain, not a
Google Docs edit screen.

**Editable master** is the public Google Doc. To update the résumé:
```bash
curl -L "https://docs.google.com/document/d/1fGFEOr6d16DXbH6XGcHGRCv5sHb5RPR0/export?format=pdf" -o Resume.pdf
git add Resume.pdf && git commit -m "Update résumé" && git push
```
(Or: edit the Doc → File → Download → PDF → overwrite `Resume.pdf` → commit + push.)
