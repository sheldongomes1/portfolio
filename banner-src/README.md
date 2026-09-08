# Banner sources

HTML sources for the product hero banners served at the site root
(`/redink-diagram.webp`, `/pm-confessional-diagram.webp`). Tracked so the banners
are regenerable — the original 2026-06-28 banners were screenshotted from sources
that were never committed, so `psis-banner.webp` has no source here yet.

`banner.css` holds the shared grammar; each page adds only its own overrides.

This directory is **not** copied into the container (`Dockerfile` lists its
files explicitly), so nothing here is web-served.

## Regenerating

```bash
CHROME=~/.cache/ms-playwright/chromium-*/chrome-linux64/chrome   # any Chrome/Chromium
NAME=redink            # or: pm-confessional

$CHROME --headless --disable-gpu --no-sandbox --hide-scrollbars \
  --allow-file-access-from-files \
  --force-device-scale-factor=2 --window-size=1600,904 \
  --screenshot=/tmp/$NAME.png \
  "file://$PWD/banner-src/$NAME-banner.html"

python3 -c "
from PIL import Image
Image.open('/tmp/$NAME.png').convert('RGB') \
     .resize((1600,904), Image.LANCZOS) \
     .save('$NAME-diagram.webp','WEBP',quality=88,method=6)"
```

**Rename the `.webp` on every redesign.** `nginx.conf` caches `*.webp` for 24h
(`max-age=86400`), so republishing under the same filename leaves visitors — and
you — looking at the old image for a day. Version by filename and update the
`src` in `index.html` plus the `COPY` list in the `Dockerfile`.

Render at 2× and downsample: a 1× headless shot hints text badly, and the
LANCZOS downsample supplies the antialiasing the browser won't.

## Visual grammar

Both featured banners (PSIS, RedInk) share one convention, and it carries the
argument rather than decorating it:

| Border | Meaning |
|---|---|
| gray | deterministic step — no model involved |
| purple | LLM step |
| cyan | gated / verified output |
| amber | refusal / stop path |

Keep the layout skeleton consistent across banners: gradient cap bars, centred
eyebrow → title → subtitle, a band label, the pipeline row, a formula box, three
claim cards with coloured top rules, stack chips, closing claim.
