# Banner sources

HTML sources for the product hero banners served at the site root
(`/redink-banner.webp`, etc.). Tracked so the banners are regenerable — the
originals (2026-06-28) were screenshotted from sources that were never committed,
so only `redink-banner.html` exists here so far.

This directory is **not** copied into the container (`Dockerfile` lists its
files explicitly), so nothing here is web-served.

## Regenerating

```bash
CHROME=~/.cache/ms-playwright/chromium-*/chrome-linux64/chrome   # any Chrome/Chromium

$CHROME --headless --disable-gpu --no-sandbox --hide-scrollbars \
  --force-device-scale-factor=2 --window-size=1600,904 \
  --screenshot=/tmp/redink.png \
  "file://$PWD/banner-src/redink-banner.html"

python3 -c "
from PIL import Image
Image.open('/tmp/redink.png').convert('RGB') \
     .resize((1600,904), Image.LANCZOS) \
     .save('redink-banner.webp','WEBP',quality=88,method=6)"
```

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

Keep the layout skeleton consistent across banners: gradient cap bars, centred
eyebrow → title → subtitle, a band label, the pipeline row, a formula box, three
claim cards with coloured top rules, stack chips, closing claim.
