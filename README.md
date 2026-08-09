# Darshangiri Goswami — 3D Cybersecurity Portfolio

A single-file 3D portfolio built with **Three.js** (WebGL + bloom) and an
**"Ask my AI twin"** chat assistant running on the **Claude API**. Deep navy, teal +
gold, an animated 3D data-shield, an orbiting monitoring-network graph and a particle
field. The content leads with **detection engineering** — the labs, the research, the
stack — and carries governance, identity and compliance as the second half.

## Files

| File | What it is |
|------|------------|
| `index.html` | **The website** — everything lives here: markup, CSS, JS, the German translation map, the terminal easter egg and the access-review simulator. Edit directly. |
| `assets/portrait.*` · `about.*` · `portrait-cyber.webp` | Hero portrait, About headshot, hologram twin. |
| `assets/og-image.jpg` | 1200×630 social-share card. |
| `assets/writing.json` · `ops.json` | Written by the LinkedIn agent; feed the Writing cards and the Live Ops room. |
| `artifacts/` | Three illustrative GRC work samples (risk register, access-review procedure, ISO 27001 SoA excerpt). Fictional company, robots-noindexed. |
| `fonts/` · `vendor/three/` | Self-hosted fonts and a vendored Three.js. No third-party requests at page load except GoatCounter. |
| `datenschutz.html` · `kolophon.html` | DSGVO Art. 13 privacy notice and the colophon (sub-processor register, AI-system inventory, open items). |
| `404.html` | RBAC-flavoured "access denied" page with a redirect. |
| `site.webmanifest` · `sitemap.xml` · `robots.txt` · `.well-known/security.txt` | PWA manifest, SEO, security contact (RFC 9116). |
| `generate_assets.py` | Regenerates `portrait.*`, `about.*` and `og-image.jpg`. |
| `ai_twin_server.py` | Claude backend for the chat and the JD fit-check (keeps the API key server-side). |
| `Procfile` · `render.yaml` · `requirements.txt` | Backend deploy config and Python deps. |
| `Darshangiri-Goswami-CV.pdf` | Linked by the "Download CV" buttons. Built from `resume-agent/base/resume.yaml` — regenerate there, then copy it here, so the CV and the site never drift apart. |

## View the site

Open `index.html` in a browser. Fonts and Three.js are served from this repo, so it
renders fully offline. The AI twin also has an **offline mode** — if the backend is
unreachable, answers come from a built-in CV summary with no network calls and no key.

## Regenerate the images

```powershell
pip install -r requirements.txt
python generate_assets.py
```

The source photos are read from `Downloads/`; when those are missing,
`generate_assets.py` falls back to the committed `assets/portrait.jpg` and
`assets/about.jpg`. That fallback is fine for rebuilding the OG card, which only needs
a circle crop, but re-point `SRC` / `ABOUT_SRC` at the originals before regenerating
the hero and about portraits — otherwise it resamples an already-compressed JPEG.

To rebuild only the social card:

```powershell
python -c "import generate_assets as g; g.make_og()"
```

Both text lines on that card have to clear the portrait circle at x=800; longer strings
run under the photo instead of wrapping, so look at the result after editing.

## Enable the live Claude AI twin

### Run locally
```powershell
pip install -r requirements.txt
$env:ANTHROPIC_API_KEY = "sk-ant-..."
python ai_twin_server.py            # http://localhost:8787
```

### Deploy to Render (free)
1. Push this repo to GitHub (already done).
2. On [render.com](https://render.com) → **New → Web Service** → connect this repo.
   `render.yaml` is detected automatically (gunicorn start command, health check).
3. Add an environment variable **`ANTHROPIC_API_KEY`** = your key from
   [console.anthropic.com](https://console.anthropic.com). Never commit the key.
4. Deploy → copy the service URL. This site's is `https://darshangiri-goswami.onrender.com`.
5. In `index.html`, set the one config constant to that URL **+ `/chat`**:
   ```js
   const AI_ENDPOINT = 'https://darshangiri-goswami.onrender.com/chat';
   ```
   No asset rebuild needed — just commit and push `index.html`.

Leave `AI_ENDPOINT = ''` for offline mode. **Never put an API key in `index.html`.**
When set, the chat header shows **"Online · Claude"** and answers stream live from
`claude-haiku-4-5` (override with the `AI_TWIN_MODEL` env var), grounded in the CV
block at the top of `ai_twin_server.py`. That block is the twin's whole world: it also
carries a **KNOWN GAPS** section, and both the chat and the fit-check are instructed to
state those plainly rather than soften them. Keep it in sync with the master résumé.

### Built-in safeguards (public endpoint)
- CORS locked to the portfolio origin · per-IP rate limit (20 req/min)
- Message-length cap (2000 chars) and history cap (12 turns) to bound token spend
- The API key lives only in the host's environment, never in the browser

> Render's free tier sleeps after ~15 min idle, which is what makes the widget show
> "Offline · from CV". The repo's GitHub Actions `keep-alive.yml` is **not** reliable —
> GitHub throttles scheduled jobs well below the needed interval. An external
> cron-job.org job pings `/health` every 5 minutes instead. If the twin reads Offline,
> check that job first.

## Publish

`index.html`, `assets/`, `site.webmanifest`, `.well-known/`, and the CV are static —
host on GitHub Pages / Netlify / Cloudflare Pages. Live URL:
**https://darshan2209.github.io/darshangiri-goswami/**

---
Built with Three.js & the Claude API.
