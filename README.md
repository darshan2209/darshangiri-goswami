# Darshangiri Goswami — 3D Cybersecurity Portfolio

An ultra-realistic 3D portfolio built with **Three.js** (WebGL + bloom) and an
**"Ask my AI twin"** chat assistant that can run on the **Claude API**. Theme:
professional *compliance & trust* — deep navy, teal + gold, an animated 3D data-shield,
an orbiting monitoring-network graph, and a particle field.

## Files

| File | What it is |
|------|------------|
| `index.html` | **The website** — edit this directly. References external assets (no base64). |
| `assets/portrait.jpg` · `assets/portrait.webp` | Shared portrait used by hero + about (one download, served twice). |
| `assets/og-image.jpg` | 1200×630 social-share card. |
| `assets/favicon.svg` | SVG favicon (the shield mark). |
| `site.webmanifest` | PWA manifest. |
| `.well-known/security.txt` | Security contact (RFC 9116). |
| `generate_assets.py` | Regenerates `portrait.*` and `og-image.jpg` from the source photo. |
| `ai_twin_server.py` | Claude backend that powers live chat (keeps the API key server-side). |
| `Procfile` · `render.yaml` | Deploy config for hosting the backend (Render/Railway/Heroku-style). |
| `requirements.txt` | Python deps for the backend / asset generator. |
| `Darshangiri-Goswami-CV.pdf` | Linked by the "Download CV" buttons. |

## View the site

Open `index.html` in a browser (Three.js loads from a CDN, so the first load needs
internet). The AI twin works in **offline mode** out of the box — answers come from a
built-in summary of the CV, with no network calls and no API key.

## Regenerate the images

```powershell
pip install -r requirements.txt
python generate_assets.py
```
Edit the source photo paths at the top of `generate_assets.py` to swap the portrait.

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
4. Deploy → copy the service URL, e.g. `https://darshan-ai-twin.onrender.com`.
5. In `index.html`, set the one config constant to that URL **+ `/chat`**:
   ```js
   const AI_ENDPOINT = 'https://darshan-ai-twin.onrender.com/chat';
   ```
   Then rebuild assets aren't needed — just commit & push `index.html`.

Leave `AI_ENDPOINT = ''` for offline mode. **Never put an API key in `index.html`.**
When set, the chat header shows **"Online · Claude"** and answers stream live from
`claude-opus-4-8` (override with the `AI_TWIN_MODEL` env var), grounded in the CV.

### Built-in safeguards (public endpoint)
- CORS locked to the portfolio origin · per-IP rate limit (20 req/min)
- Message-length cap (2000 chars) and history cap (12 turns) to bound token spend
- The API key lives only in the host's environment, never in the browser

> Render's free tier sleeps after ~15 min idle, so the first message after a pause
> takes a few seconds to wake the service. Upgrade the plan to keep it always-on.

## Publish

`index.html`, `assets/`, `site.webmanifest`, `.well-known/`, and the CV are static —
host on GitHub Pages / Netlify / Cloudflare Pages. Live URL:
**https://darshan2209.github.io/darshangiri-goswami/**

---
Built with Three.js & the Claude API.
