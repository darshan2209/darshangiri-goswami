"""
Darshan's AI Twin — production backend for the portfolio chat widget.

It proxies the browser to the Claude API so your API key NEVER ships to the client,
streams Claude's answer back token-by-token, and is grounded in the CV below so it
only answers from real information.

LOCAL RUN (Windows PowerShell):
    pip install -r requirements.txt
    $env:ANTHROPIC_API_KEY = "sk-ant-..."
    python ai_twin_server.py

PRODUCTION (Render/Railway/Fly) uses gunicorn (see Procfile / render.yaml):
    gunicorn ai_twin_server:app --worker-class gthread --threads 4 --timeout 120 --bind 0.0.0.0:$PORT

Abuse protection (this endpoint is public): per-IP rate limit, message-length and
history caps, and CORS locked to the portfolio origin.
"""
import os, time, collections
from flask import Flask, request, Response, stream_with_context
import anthropic

app = Flask(__name__)
client = anthropic.Anthropic()                 # reads ANTHROPIC_API_KEY from the environment
MODEL = os.environ.get("AI_TWIN_MODEL", "claude-haiku-4-5-20251001")  # cheap & fast; override via env
PORT = int(os.environ.get("PORT", "8787"))

# --- Abuse protection ----------------------------------------------------------
ALLOWED_ORIGINS = {
    "https://darshan2209.github.io",           # the live site
    "http://localhost:8090", "http://127.0.0.1:8090",  # local preview
}
MAX_MSG_CHARS = 2000          # max length of a single user message
MAX_HISTORY   = 12            # only the most recent N turns are forwarded
RATE_MAX, RATE_WINDOW = 20, 60        # max requests per IP per 60s
_hits = collections.defaultdict(collections.deque)

def rate_limited(ip):
    now = time.time(); dq = _hits[ip]
    while dq and now - dq[0] > RATE_WINDOW:
        dq.popleft()
    if len(dq) >= RATE_MAX:
        return True
    dq.append(now); return False

# --- Grounding: Darshan's CV, given to Claude as a cached system prompt ---------
CV = """\
Darshangiri Goswami — Working Student candidate: Governance, Risk & Compliance (GRC) | Identity & Access Management (IAM) | Monitoring & Investigations | AI in Cybersecurity.
Location: Berlin, Germany (open to relocation). Available immediately, up to 40 hrs/week.
Contact: +49 155 1083 7720 | darshangoswami22922@gmail.com | linkedin.com/in/darshangiri-goswami-033283213 | credly.com/users/darshan-goswami.e4c6c92c

SUMMARY
Business Management & Cybersecurity master's student focused on Governance, Risk & Compliance (GRC), Identity &
Access Management (IAM) and AI in cybersecurity, with hands-on experience in compliance and regulatory training,
policy and controls documentation, and monitoring flagged activity through checks and assessments of system alerts.
Particular strength in process automation and AI-driven workflows, applied with a focus on ethical and responsible
AI. Fluent in English (C1), conversational German (A2). Seeking a Working Student role in GRC, IAM or compliance.

SKILLS
- Governance, Risk & Compliance (GRC): policy & procedure documentation, Code of Conduct / acceptable-use training,
  controls monitoring, risk assessment & registers, audit support, regulatory & compliance training; frameworks GDPR, DORA, NIS2, ISO 27001, NIST CSF.
- Identity & Access Management (IAM): access control & access reviews, Joiner-Mover-Leaver, least-privilege / RBAC,
  Microsoft Entra ID (SC-300), conditional access, identity governance.
- Monitoring & Investigations: reviewing system flags and alerts, checks and assessments, anomaly detection,
  SIEM & log analysis (Wazuh), case documentation, remediation tracking, follow-up communication.
- AI in Cybersecurity & Automation: Python, PowerShell, workflow automation, AI-driven alert triage and risk
  scoring, anomaly detection, Microsoft Copilot; awareness of the EU AI Act and ethical / responsible AI practices.
- Tools: MS Excel, MS PowerPoint, MS Office, SQL.
- Strengths: discretion with sensitive information, attention to detail, clear written and verbal communication.

EXPERIENCE
1) Cybersecurity Trainer — NIIT Foundation — Ahmedabad, India — Apr 2025 to Oct 2025
   - Delivered compliance and policy training to 4500+ students on acceptable-use and access-control requirements,
     with 95% achieving certification, building day-to-day adherence to governance and Code-of-Conduct policies.
   - Maintained policy, training and controls documentation in the LMS, keeping records current and audit-ready.
   - Created awareness content mapped to ISO 27001 and NIST CSF for non-specialist staff.
2) Cybersecurity Research Analyst — The CyberDiplomat — Bengaluru, India — Jul 2023 to Mar 2024
   - Monitored activity across 50+ platforms, performing checks and assessments of flags and alerts and escalating
     policy and access exceptions for review.
   - Tracked each remediation item to closure on schedule and documented outcomes and follow-up communication.
   - Supported case documentation and ongoing team projects, and tested new tools to improve efficiency/digitalisation.

PROJECTS
1) AI-Assisted Monitoring & Automation (Python, AI Platform API, REST API): an AI-assisted workflow that monitored
   simulated activity and flagged exceptions with a Python anomaly-detection script; integrated an AI platform via
   API to triage flags, score risk and map cases to playbook logic, producing response recommendations as a working
   model for responsible, AI-driven process enhancement.
2) Monitoring & Detection Homelab (Wazuh, Ubuntu, Windows): deployed a centralised monitoring platform and onboarded
   a host for log collection and real-time alerting; configured file-integrity monitoring to detect 100+ unauthorised
   changes, worked from a central dashboard.

EDUCATION
- MSc, Business Management & Cybersecurity — GISMA University of Applied Sciences, Potsdam, Germany — Sep 2025 to expected Oct 2026.
- B.Tech, Information Technology — Swarnim Startup and Innovation University, Gandhinagar, India — Aug 2020 to Jun 2024 — GPA 8.76/10 (German equivalent 1.6).

CERTIFICATIONS
Microsoft SC-900; ISO/IEC 27001 Information Security Associate; Google Cybersecurity Certificate; Cisco CyberOps
Associate; Certified GRC & Threat Intelligence Analyst; Microsoft SC-300 (in progress); CompTIA Security+ SY0-701 (in progress).

LANGUAGES: English (C1), German (A2).
"""

SYSTEM = f"""You are "Darshan's AI twin", a friendly, professional assistant on Darshangiri Goswami's portfolio website. \
Visitors are usually recruiters or hiring managers. Answer their questions about Darshan using ONLY the CV below.

Rules:
- Be concise and conversational (1-3 short paragraphs max). This is a chat widget, not an essay.
- Speak about Darshan in the third person ("Darshan has...", "He worked...").
- Ground every claim in the CV. Do NOT invent employers, dates, numbers, tools, or skills.
- If something isn't covered, say so plainly and point them to darshangoswami22922@gmail.com — never guess.
- Stay warm and recruiter-friendly; you may gently highlight his fit for GRC, IAM, monitoring or responsible-AI roles.
- Respond only with your final answer — no internal reasoning or meta-commentary.

--- CV ---
{CV}
--- END CV ---"""


def cors(resp: Response) -> Response:
    origin = request.headers.get("Origin", "")
    resp.headers["Access-Control-Allow-Origin"] = origin if origin in ALLOWED_ORIGINS else "https://darshan2209.github.io"
    resp.headers["Vary"] = "Origin"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    return resp


@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return cors(Response(status=204))

    ip = (request.headers.get("X-Forwarded-For", request.remote_addr or "")).split(",")[0].strip()
    if rate_limited(ip):
        return cors(Response("You're sending messages too quickly — please wait a moment.", status=429, mimetype="text/plain"))

    data = request.get_json(silent=True) or {}
    raw = data.get("messages", [])

    # connectivity ping from the widget — answer cheaply without calling the API
    if len(raw) == 1 and raw[0].get("content") == "__ping__":
        return cors(Response("ok", mimetype="text/plain"))

    # sanitise + cap inputs
    messages = []
    for m in raw[-MAX_HISTORY:]:
        role, content = m.get("role"), (m.get("content") or "")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content[:MAX_MSG_CHARS]})
    if not messages:
        return cors(Response("Ask me something about Darshan!", mimetype="text/plain"))

    def generate():
        try:
            with client.messages.stream(
                model=MODEL,
                max_tokens=1024,
                system=[{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}],
                messages=messages,
                thinking={"type": "disabled"},
            ) as stream:
                for text in stream.text_stream:
                    yield text
        except Exception as e:                       # never leak internals to the client
            print("Claude API error:", repr(e))
            yield "Sorry — I'm having trouble reaching the AI right now. Please email darshangoswami22922@gmail.com."

    return cors(Response(stream_with_context(generate()), mimetype="text/plain"))


@app.route("/", methods=["GET"])
@app.route("/health", methods=["GET"])
def health():
    return cors(Response("Darshan's AI twin is running. POST to /chat.", mimetype="text/plain"))


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("!! Set ANTHROPIC_API_KEY first:  $env:ANTHROPIC_API_KEY = 'sk-ant-...'")
    print(f">> Darshan's AI twin on http://localhost:{PORT}  (model: {MODEL})")
    app.run(port=PORT, threaded=True)
