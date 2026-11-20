# FixPilot

**AnyDesk, but an AI fixes the problem instead of a human.**
FixPilot is an AI support agent for software vendors. It runs on the customer's own Windows PC, looks at the screen,
and fixes the issue with the mouse and keyboard, using the vendor's own product knowledge.

Built for Startup Buildathon India 2026 with Gemini Computer Use.

| | Link |
|---|---|
| Live support desk (session server + dashboard) | https://fixpilot-server-382332871298.asia-south1.run.app |
| Demo video | `VIDEO_URL` |
| Customer app download | [Download ZIP](https://github.com/Aryanpandya01/fixpilot/archive/refs/heads/main.zip) (setup below) |

## How it works

```
 Support desk (cloud)                     Customer PC                              Google
┌─────────────────────┐  6-digit code   ┌──────────────────────────────┐  screenshot  ┌───────────────────┐
│ Dashboard: support  │ ──────────────► │ FixPilot panel → Accept      │ ───────────► │ Gemini Computer   │
│ types the request   │                 │ Agent loop: see → decide →   │ ◄─────────── │ Use (next action) │
│ Live step timeline  │ ◄── events ──── │ click/type → check → repeat  │   action     └───────────────────┘
└─────────────────────┘                 └──────────────────────────────┘
```

1. **Support** types the customer's request in the dashboard and gets a 6-digit code.
2. **The customer** enters the code in the FixPilot panel, sees the request, picks a trust mode and presses **Accept**.
3. **The agent** takes a screenshot, Gemini decides the next action using the vendor's knowledge base, FixPilot performs it,
   checks the new screen, and repeats until the result is visible. Every step appears live on the support dashboard.
4. It finishes as **Solved** (with a "do it yourself next time" path) or **hands off to a human** with what it tried.

Two modes: **Personal help** (any Windows task, e.g. "turn on dark mode") and **Business support** (inside the vendor's
software, here the BilliGo billing app, using `kb/billigo.md`).

## Safety
- Nothing happens without consent: a code plus an **Accept** click.
- Trust modes: **Guide me** (only points at the button), **Ask first** (approve every step), **Just fix it**.
- **Passwords are never typed by the AI**: it rings the field, pauses, and the customer types it ("FixPilot is paused").
- Big red **STOP** button and **Ctrl+Shift+X**, checked between every step and during every AI call.
- Hard rules in the prompt: no deleting data, no payments, no messages, no installs. Gemini prompt-injection detection is on.
- Every step is logged; the cloud server never sees the Gemini API key (it stays on the customer PC).

## Run it

**Customer PC (Windows 10/11, Python 3.11+)**
```powershell
py -3.11 -m venv .venv
.venv\Scripts\pip install -r agent\requirements.txt
copy .env.example .env      # set GEMINI_API_KEY, SERVER_URL=https://fixpilot-server-382332871298.asia-south1.run.app, FIXPILOT_TOKEN
app\run.bat                 # opens the FixPilot panel docked on the right
```
Set Windows display scaling to 100% for the most accurate clicks.

**Support desk**: open the live URL above, or run it locally:
`python -m uvicorn server.main:app --host 0.0.0.0 --port 9000` → http://localhost:9000

**Deploy the support desk to Cloud Run (Mumbai):** `server\deploy_cloudrun.ps1 -Project <PROJECT_ID>`
(one instance only, because sessions are kept in memory). No-cloud backup: `server\tunnel.ps1` (Cloudflare quick tunnel).

## Repo map
| Folder | What |
|---|---|
| `agent/` | The AI loop (`agent.py`), Gemini tools and system prompt (`prompts.py`), screen capture, mouse/keyboard, window focus |
| `app/` | Local panel server (FastAPI + WebSocket), the panel UI, the Guide-mode highlight overlay |
| `server/` | Session server: codes, accept, live events, finish (API in `CONTRACT.md`) |
| `dashboard/` | Support desk web page |
| `kb/` | Vendor knowledge base: menus, page URLs and step-by-step recipes |
| `pitch/`, `explainer/` | Pitch deck and explainer page |

## Tech
Gemini Computer Use (Interactions API, `gemini-3.5-flash-lite` main model) · Python · FastAPI · WebSockets ·
mss + Pillow (screen) · pyautogui (input) · vanilla HTML/JS · Google Cloud Run.

Team: TEAM_NAMES
