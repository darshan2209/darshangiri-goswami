# Darshangiri Goswami — 3D Cybersecurity Portfolio

An ultra-realistic, single-file 3D portfolio website built with **Three.js** (WebGL +
bloom postprocessing) and an **"Ask my AI twin"** chat assistant powered by the
**Claude API**. Theme: professional *compliance & trust* — deep navy, teal + gold,
a 3D animated data-shield, an orbiting monitoring-network graph, and a particle field.

## Files

| File | What it is |
|------|------------|
| `index.html` | **The website.** Self-contained — open it directly in a browser. Photos are embedded as base64. |
| `index.template.html` | Editable source (photos are placeholders). Edit this, then re-run `build.py`. |
| `build.py` | Embeds the two photos into `index.template.html` → writes `index.html`. |
| `ai-twin-server.py` | Local Claude backend that powers the live chat (keeps your API key server-side). |
| `requirements.txt` | Python deps for the backend. |
| `Darshangiri-Goswami-CV.pdf` | Linked by the "Download CV" buttons. |

## 1. View the site

Just **double-click `index.html`** (or drag it into Chrome/Edge/Firefox).
- The 3D scene loads Three.js from a CDN, so you need an internet connection the first time.
- The "Ask my AI twin" chat works in **offline mode** out of the box (keyword answers from the CV).

## 2. Enable the live Claude AI twin (optional but recommended)

```powershell
cd L:\Claude\portfolio
pip install -r requirements.txt
$env:ANTHROPIC_API_KEY = "sk-ant-..."        # your key from console.anthropic.com
python ai-twin-server.py
```

Leave that running, then refresh `index.html`. The chat header switches from
**"Offline mode"** to **"Online · Claude"** and answers stream live from
`claude-opus-4-8`, grounded entirely in your CV (no hallucinated facts).

> The key lives only in the Python process. The browser talks to `http://localhost:8787`
> and never sees it.

## 3. Update your content or photos

- **Text** (experience, skills, etc.): edit `index.template.html`, then run `python build.py`.
- **Photos**: change the two paths near the top of `build.py`, then run `python build.py`.
- **AI answers**: the CV the assistant uses lives in the `CV` string in `ai-twin-server.py`
  (and the offline fallback `KB` array in `index.template.html`). Keep them in sync.

## 4. Publish it (free)

`index.html` + `Darshangiri-Goswami-CV.pdf` are all you need for static hosting:
- **GitHub Pages**, **Netlify drop**, or **Cloudflare Pages** — drag the folder in.
- For the live AI twin in production, deploy `ai-twin-server.py` to a host (Render,
  Railway, Fly.io…) and update `AI_ENDPOINT` in `index.template.html` to its URL,
  then rebuild. Without that, the published site uses the offline fallback.

---
Built with Three.js & the Claude API.
