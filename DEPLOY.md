# Deploying & maintaining the portfolio

The site is a single static `index.html` deployed on **Vercel**, git-backed, auto-deployed on push.

---

## One-time setup (owner action — needs your accounts)

1. **Create the GitHub repo** and push this folder:
   ```bash
   cd ~/AIProjects/portfolio
   gh repo create sheldongomes/portfolio --public --source=. --remote=origin
   git push -u origin main
   ```
   (Or create the repo in the GitHub UI and `git remote add origin …`.)

   Making the repo **public is safe** — private planning lives in the git-ignored `_meta/`
   and `archive/` folders, which are never pushed.

2. **Connect Vercel:** https://vercel.com/new → "Import Git Repository" → pick the repo.
   - Framework preset: **Other** (it's static HTML).
   - Build command: *none*. Output directory: *root*.
   - Deploy. You'll get `https://<project>.vercel.app`.

3. **Update the canonical/OG URL** in `index.html` once you know the real domain.
   Search for `sheldongomes.vercel.app` and replace it with your actual Vercel domain
   (or custom domain). These tags affect SEO and social-share previews:
   - `<meta property="og:url" …>`
   - `<meta property="og:image" …>`  (see "Social share image" below)
   - `<link rel="canonical" …>`

## Day-to-day: making a change

```bash
# edit index.html
git add -A
git commit -m "Describe the change"
git push            # Vercel auto-deploys main in ~20s
```
Every branch gets its own preview URL. Open a PR to preview before merging to `main`.

## Rolling back

Vercel dashboard → Deployments → pick a previous good deploy → **Promote to Production**.
Instant, no git revert needed.

## Adding a custom domain (when ready)

1. Buy a domain (e.g. `sheldongomes.com`).
2. Vercel → Project → Settings → Domains → add it; Vercel shows the DNS records.
3. Point your registrar's DNS at those records. HTTPS is automatic.
4. Update the OG/canonical URLs in `index.html` (see step 3 above).

## Social share image (optional polish)

`index.html` references `/og-card.png` for link previews. Until that file exists, the
text preview still works; the thumbnail just won't show. To add it: drop a `1200×630`
PNG named `og-card.png` in the repo root and commit it.

## Assets

`Resume.pdf` is committed and served at `/Resume.pdf` (linked from nav, hero, contact).
It's self-hosted on purpose — recruiters download a clean PDF from your own domain, not a
Google Docs edit screen.

**Editable master** is the public Google Doc. To update the résumé:
```bash
curl -L "https://docs.google.com/document/d/1fGFEOr6d16DXbH6XGcHGRCv5sHb5RPR0/export?format=pdf" -o Resume.pdf
git add Resume.pdf && git commit -m "Update résumé" && git push
```
(Or: edit the Doc → File → Download → PDF → overwrite `Resume.pdf` → commit + push.)
