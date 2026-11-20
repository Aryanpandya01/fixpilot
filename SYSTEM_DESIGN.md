# FixPilot — Complete System Design + Step-by-Step Roadmap

Setup: 2 people (both can code) · about 8 hours · local demo · **the real Windows billing software** installed on Laptop A.

Detailed build prompts for each person: `PERSON_A_TASKS.md`, `PARTNER_START_HERE.md`. Shared API: `CONTRACT.md`.

---

## PART 1 — SYSTEM DESIGN

### 1.1 What the system does

**FixPilot = AnyDesk, but the AI does the fixing instead of a human.**

| | Mode 1: Personal help | Mode 2: Business support |
|---|---|---|
| Who uses it | Anyone with a Windows PC | Customers of a software company (billing software) |
| Example | "My WiFi icon is missing" | "How do I add a new product with 18% GST?" |
| How it starts | User types or speaks into FixPilot | Support desk creates a **6-digit code**, customer enters it and clicks **Accept** |
| Knowledge | Gemini's general Windows knowledge | Vendor's knowledge base (`kb/billing_app.md`) |
| Who watches | The user | The user **and** the support desk (live dashboard) |

### 1.2 Architecture (MVP — what we build today)

```
 LAPTOP A  (Customer PC — owner: Person A)                       LAPTOP B  (Support desk — owner: Person B)
┌────────────────────────────────────────────────────────┐      ┌──────────────────────────────────────┐
│                                                        │      │                                      │
│  ┌──────────────────────┐   ┌───────────────────────┐  │      │  ┌────────────────────────────────┐  │
│  │ Billing Software     │   │ FixPilot Panel (UI)   │  │      │  │ Support Dashboard (HTML/JS)    │  │
│  │ (real .exe, dummy    │   │ - Mode 1 / Mode 2 tabs│  │      │  │ - type query → get code        │  │
│  │  data, left side)    │   │ - mic, live feed      │  │      │  │ - live timeline of AI steps    │  │
│  └──────────▲───────────┘   │ - Accept/Approve/STOP │  │      │  │ - Solved ✅ / Escalated ⚠️     │  │
│             │ clicks/keys   └──────────┬────────────┘  │      │  └───────────────┬────────────────┘  │
│             │                  WebSocket (localhost)    │      │        HTTP poll │ every 2s         │
│  ┌──────────┴──────────────────────────▼────────────┐  │      │  ┌───────────────▼────────────────┐  │
│  │ FixPilot Agent (Python, app/server.py :8000)     │  │ HTTP │  │ Session Server (FastAPI :9000) │  │
│  │                                                  │◄─┼──────┼─►│ - sessions + 6-digit codes     │  │
│  │  agent.py  ── the loop (see 1.4)                 │  │      │  │ - events store (in-memory)     │  │
│  │  screen.py ── mss screenshot + DPI fix           │  │      │  │ - serves kb_text per vendor    │  │
│  │  executor.py ─ pyautogui mouse/keyboard          │  │      │  └───────────────┬────────────────┘  │
│  │  prompts.py ── system prompt + custom tools      │  │      │                  │ reads             │
│  │  overlay.py ── Guide-mode highlight circle       │  │      │        ┌─────────▼──────────┐        │
│  │  logs/ ─────── audit log (jsonl)                 │  │      │        │ kb/billing_app.md  │        │
│  └──────────────────────────┬───────────────────────┘  │      │        └────────────────────┘        │
└─────────────────────────────┼──────────────────────────┘      └──────────────────────────────────────┘
                              │ HTTPS (screenshot + query + kb)
                              ▼
               ┌───────────────────────────────────────────┐
               │ Gemini API — Interactions API              │
               │ tool: computer_use, environment: desktop   │
               │ main: gemini-3.8-flash · fallback: 4-argon │
               └───────────────────────────────────────────┘
```

### 1.3 Components

| # | Component | Owner | Tech | Job |
|---|---|---|---|---|
| 1 | Screen module | A | `mss`, Pillow, DPI awareness | Takes a screenshot and gets the screen size |
| 2 | Executor | A | `pyautogui` | Turns Gemini's 0–999 coordinates into real clicks and keys |
| 3 | Agent loop | A | `google-genai` Interactions API | Screenshot → Gemini → action → repeat, plus trust modes, safety and STOP |
| 4 | Prompts + tools | A | Python | System prompt and the custom tools `report_done`, `yield_to_user`, `ask_user` |
| 5 | Panel UI + local server | A | FastAPI + WebSocket + HTML | What the customer sees and clicks |
| 6 | Guide overlay | A | Tkinter, transparent and always-on-top | Draws a circle and arrow on the button the user should click |
| 7 | Session server | B | FastAPI | Codes, accept, events, finish |
| 8 | Support dashboard | B | HTML/JS | Support creates the code and watches progress live |
| 9 | Knowledge base | B | Markdown | Exact menus, steps and fixes for the billing software |
| 10 | Pitch + video | B | Google Slides, OBS / Win+Alt+R | Slides and the backup video |

### 1.4 The agent loop (the heart of the system)

```
 START(query, kb_text, mode)
   │
   ▼
 take screenshot ──► send to Gemini (system prompt + kb + query + screenshot)
   │
   ▼
 Gemini returns steps ──┬── no action / text only ──────────────► DONE (summary)
                        ├── report_done(summary, learn_path) ───► DONE ✅
                        ├── yield_to_user(reason, summary) ─────► ESCALATE ⚠️ (ticket)
                        ├── ask_user(question) ─────────────────► show question, wait, continue
                        └── computer action (click/type/...)
                                 │
                 ┌───────────────┼────────────────────────────┐
             mode=guide      mode=assist OR             mode=auto
                 │           safety=require_confirmation       │
           draw highlight,   ask Approve/Deny ──Deny──► STOPPED │
           wait for "next"       │Approve                       │
                 │               ▼                              ▼
                 └──────────► EXECUTE with pyautogui ◄──────────┘
                                 │
                       wait 0.8s, new screenshot
                                 │
                 send function_result (result + screenshot) ─► back to Gemini
   STOP hotkey (Ctrl+Shift+X) or STOP button → checked every step → STOPPED 🛑
   max 25 turns · 2 failures in a row → switch to gemini-4-argon
```

### 1.5 Mode 2 sequence (end to end)

```
Support (Laptop B)        Session Server          FixPilot App (Laptop A)          Gemini
      │ type query            │                          │                            │
      │──POST /sessions──────►│ create code 482913       │                            │
      │◄──{code}──────────────│ status=waiting           │                            │
      │ tell customer the code (phone/WhatsApp)          │                            │
      │                       │◄──GET /sessions/482913───│ customer enters code       │
      │                       │──query, kb_text─────────►│ popup "Accept?"            │
      │                       │◄──POST accept────────────│ customer clicks Accept     │
      │                       │ status=running           │──screenshot+query+kb──────►│
      │                       │                          │◄──click "Products"─────────│
      │                       │◄──POST event (intent)────│ execute, new screenshot    │
      │──GET events (poll)───►│                          │   ... loop ...             │
      │◄──timeline────────────│                          │◄──report_done──────────────│
      │                       │◄──POST finish(solved)────│ "Solved ✅ Next time:      │
      │ dashboard: Solved ✅   │                          │  Products > Add > Save"    │
```

### 1.6 Data model

```
Session {
  code: "482913", query: str, vendor_id: "billing_app", vendor_name: str, kb_text: str,
  status: waiting|running|solved|escalated|stopped,
  events: [Event], summary: str, created_at, finished_at
}
Event { type: intent|approval|highlight|done|escalate|error|stopped, text, action, ts }
Log line (logs/*.jsonl): { ts, turn, action, args, result, model, mode }
```

### 1.7 Safety layers (put this on one slide)

1. **Consent:** Mode 2 needs a code and an Accept click. Mode 1 is started by the user.
2. **Trust modes:** Guide (AI only points), Assist (approve every step), Auto (AI acts by itself).
3. **Gemini safety_decision:** risky actions always need confirmation.
4. **Prompt boundaries:** no deleting, no passwords, no payments, no messages, and it never touches the FixPilot panel.
5. **STOP:** a red button plus the Ctrl+Shift+X hotkey, plus pyautogui failsafe (moving the mouse to a corner stops it).
6. **Prompt-injection detection** is switched on.
7. **Audit log** of every step.
8. **Escalation** to a human when the AI is unsure.

### 1.8 Production architecture (pitch slide, not built today)

- Session server → **Cloud Run** · sessions/logs → **Firestore** · recordings → **Cloud Storage**
- Knowledge → **Gemini Embedding + Vertex AI Vector Search** (one index per vendor)
- Dashboard → **Firebase Hosting + Auth** · alerts → **Pub/Sub**
- Desktop agent → signed installer shipped **inside the vendor's software** (a "Help" button / F1)
- Live human takeover → **RustDesk** (open source) integration
- Auto-onboarding: FixPilot **explores the vendor's app by itself** and builds the menu map

---

## PART 2 — STEP-BY-STEP ROADMAP (8 hours)

Every step has a **✅ test**. Don't move on until the test passes.

### PHASE 0 — Setup (0:00–0:30) · TOGETHER

| Step | Who | Do | ✅ Test |
|---|---|---|---|
| 0.1 | Both | Install the **Antigravity editor** (antigravity.google), Python 3.11 and Git | `python --version`, `git --version` |
| 0.2 | A | Create the GitHub repo `fixpilot`, add your partner, push the CONTRACT.md, PERSON_A/B, SYSTEM_DESIGN.md files and `.gitignore` | Partner can `git clone` it |
| 0.3 | Both | Get the Gemini API key (AI Studio) and put it in `.env` | — |
| 0.4 | A | Quick test: a Python call to `gemini-3.8-flash` that says "hello" | A reply is printed |
| 0.5 | A | **Laptop A demo setup:** install the billing software with dummy data. Set **Windows display scaling to 100%** and resolution to 1920×1080. | The software opens maximized |
| 0.6 | Both | Same phone hotspot. Partner runs `ipconfig` and shares his IP. | `ping <partner-ip>` works |

### PHASE 1 — Build alone, in parallel (0:30–3:00)

| Step | Person A (Agent) | ✅ Test | Person B (Cloud) | ✅ Test |
|---|---|---|---|---|
| 1.1 | `screen.py` + `executor.py` (A Task 1) | A script clicks the Start button | `server/main.py`, all endpoints (B Task 1) | `test_flow.sh` passes |
| 1.2 | `agent.py` loop in **auto** mode, CLI (A Task 2) | `"turn on dark mode"` works | `dashboard/index.html` (B Task 2) | Fake curl events appear live |
| 1.3 | Add **assist** mode + STOP hotkey + logs | It asks before each click, Ctrl+Shift+X stops it | **Knowledge file** `kb/billing_app.md`: 10–15 how-tos with exact menu names (B Task 3) | Partner checks every step by hand in the real software |
| 1.4 | **Record backup video #1** (Mode 1 working) | Video saved | — | — |

### ✅ CHECKPOINT 1 (3:00) — 10 minutes together
A shows Mode 1 working, B shows the dashboard and the kb file. **Then A runs the CLI with the kb:** `python -m agent.agent "add new product Parle-G ₹10 GST 18%" --kb kb/billing_app.md` on the real billing software.
This is the **most important test of the day**. If it works, you have a product.

### PHASE 2 — UI + integration (3:00–5:00)

| Step | Person A | ✅ Test | Person B | ✅ Test |
|---|---|---|---|---|
| 2.1 | Panel UI + local server, Mode 1 tab (A Task 3) | Mode 1 runs from the panel | Improve the kb from what failed at checkpoint 1 | The failing task now works |
| 2.2 | Mode 2 tab: enter code → Accept popup → run → POST events/finish | Works against B's server | Dashboard polish: big code, timer, summary card | Looks good on a projector |
| 2.3 | Guide mode overlay (highlight circle) | The circle appears on the right button | Start the pitch slides (B Task 5) | Slide outline done |

### ✅ CHECKPOINT 2 (5:00) — MERGE + full run
`git pull` on both laptops → set `SERVER_URL` on A → **full Mode 2 flow**: B creates the code → A enters it → Accept → the AI adds the product in the real billing software → B's dashboard shows Solved ✅.
**Record backup video #2** (both screens).

### PHASE 3 — Polish (5:00–6:30)

| Person A | Person B |
|---|---|
| Red "AI in control" border, Solved timer, "Next time: path" learn card | Finish the slides (problem, solution, demo, tech, safety, business, competition, traction, team) |
| Hinglish test: *"naya product add karna hai"* | Get a WhatsApp proof message from the friend (vendor) |
| Speed tuning: screenshot width 1280, fewer waits | Backup video edit (Clipchamp), 90 seconds |
| Fix the top 3 bugs found in the rehearsal | Print or write down the demo script |

### PHASE 4 — Rehearse (6:30–7:30) · TOGETHER
Run the full demo **5 times** in this exact order:
1. **Mode 1:** "show WiFi and Bluetooth icons in the taskbar" (or dark mode), about 30s
2. **Mode 2:** B types "Customer wants to add a new product: Parle-G, ₹10, GST 18%" → code → Accept → Solved, about 60s
3. **Safety:** start a task in Assist mode, then press STOP
4. **Escalation:** "my license expired" → the AI hands off to a human

Reset the dummy data between runs. Keep the backup video open in a tab.

### Buffer (7:30–8:00)
Always leave 30 minutes free. Something will break.

---

## PART 3 — If things go wrong (fallbacks)

| Problem | Fallback |
|---|---|
| Clicks land in the wrong place | Check the scaling is 100%, check the DPI line in screen.py, and maximize the billing app |
| The AI is wrong in the real billing software | Make the kb more exact (button names), or use Assist mode so a wrong step can be denied |
| The AI is too slow | Use `gemini-3.8-flash` only, 1280px screenshots, fewer `wait`s |
| Free API rate limit hit | Ask the organizers for credits, or use the Google Cloud $300 trial. Have a second key ready. |
| The laptops can't connect | Run the session server on Laptop A too (`SERVER_URL=http://localhost:9000`) and open the dashboard on B through A's IP, or show it on A |
| Mode 2 breaks completely | Demo Mode 1 live and Mode 2 from backup video #2 |
| Everything breaks | Backup video + slides. Still a strong pitch. |
