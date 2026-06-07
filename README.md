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
| `ai-twin-server.py` | Optional Claude backend that powers live chat (keeps the API key server-side). |
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

## Enable the live Claude AI twin (optional)

1. Deploy `ai-twin-server.py` (locally or on Render/Railway/Fly.io):
   ```powershell
   pip install -r requirements.txt
   $env:ANTHROPIC_API_KEY = "sk-ant-..."
   python ai-twin-server.py
   ```
2. In `index.html`, set the one config constant to your backend's HTTPS URL:
   ```js
   const AI_ENDPOINT = 'https://your-backend.example.com/chat';
   ```
   Leave it `''` (default) for offline mode. **Never put an API key in `index.html`.**

When `AI_ENDPOINT` is set, the chat header shows **"Online · Claude"** and answers
stream live from `claude-opus-4-8`, grounded in the CV. When empty, it stays offline
and the footer does not claim the live API is in use.

## Publish

`index.html`, `assets/`, `site.webmanifest`, `.well-known/`, and the CV are static —
host on GitHub Pages / Netlify / Cloudflare Pages. Live URL:
**https://darshan2209.github.io/darshangiri-goswami/**

---
Built with Three.js & the Claude API.
