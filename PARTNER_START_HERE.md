# FixPilot — Partner Guide (START HERE)

Hi! This is everything you need for today. Read it once fully (5 min), then follow it step by step.
Also read **CONTRACT.md**: your code must match it exactly. The full design is in `SYSTEM_DESIGN.md` if you want the big picture.

---

## 1. What we are building (1 minute)

**FixPilot = AnyDesk, but the AI fixes the problem instead of a human.**

- **Mode 1 (Personal help):** anyone with a Windows problem types it ("my WiFi icon is missing"), and FixPilot fixes it on their screen.
- **Mode 2 (Business support), the part you build:**
  1. A customer of our friend's **billing software** asks support: "How do I add a new product?"
  2. Support types the query into **your dashboard** and gets a **6-digit code** (like an AnyDesk ID).
  3. The customer enters the code in FixPilot and clicks **Accept**.
  4. The AI solves it on the customer's screen inside the billing software.
  5. **Your dashboard shows every AI step live**, then "Solved ✅ in 0:48".

On stage: **Laptop A (Anas) = customer PC**, **your laptop = support desk**.

## 2. Who does what

| Anas (Person A) | You (Person B) |
|---|---|
| AI engine: screenshots, Gemini, mouse/keyboard | **Session server** (codes, accept, live events) |
| FixPilot desktop app (panel, Accept popup, STOP) | **Support dashboard** (the support desk web page) |
| Guide-mode highlight | **Knowledge file** for the billing software (the most important one) |
| | **Pitch slides + backup video** |

**Your folders:** `server/`, `dashboard/`, `kb/`, `pitch/`. Don't edit `agent/` or `app/`, and Anas won't touch yours. That's why merging will be easy.

## 3. Your tech stack (all free)

| Need | Use |
|---|---|
| Code editor | **Antigravity editor** (download from antigravity.google) |
| Server | **Python 3.11 + FastAPI + uvicorn** |
| Dashboard | **Single HTML file, plain CSS + JavaScript** (no React) |
| Storage | Python dict in memory (no database needed today) |
| Testing the API | Browser + `curl` (already in Windows) |
| Slides | Google Slides or Canva |
| Video | **Win + Alt + R** (built-in recorder) or OBS Studio, and edit in Clipchamp |

---

## 4. Your step-by-step plan

Every step has a **✅ test**. Don't move on until it passes.

### PHASE 0 — Setup with Anas (0:00–0:30)

- [ ] Install the **Antigravity editor**, **Python 3.11** and **Git**. Test with `python --version` and `git --version`.
- [ ] Accept Anas's GitHub invite, then `git clone` the `fixpilot` repo.
- [ ] Create a `.env` file (never commit it) with the Gemini key Anas gives you.
- [ ] **Install the billing software on YOUR laptop too** (you need it to write the knowledge file).
- [ ] Join the same phone hotspot as Anas. Run `ipconfig` and send Anas your **IPv4 address**.
- [ ] Allow port 9000 in Windows Firewall: run this in PowerShell **as admin**:
  ```
  New-NetFirewallRule -DisplayName "FixPilot 9000" -Direction Inbound -LocalPort 9000 -Protocol TCP -Action Allow
  ```

### PHASE 1 — Build (0:30–3:00)

#### Step 1.1 — Session server (0:30–1:30)
Open Antigravity in the repo folder. Paste CONTRACT.md first, then this prompt:
```
Read CONTRACT.md. Build server/main.py with FastAPI implementing EXACTLY the Server API in section 1.
- In-memory dict sessions[code] = {code, query, vendor_id, vendor_name, kb_text, status, events: [],
  summary, created_at, finished_at}.
- POST /sessions: random unique 6-digit code, status "waiting", kb_text = contents of kb/<vendor_id>.md,
  vendor_name = the text of the first "# " heading in that file.
- POST /sessions/{code}/accept sets status "running". POST /finish sets status + summary + finished_at.
- 404 JSON error for unknown codes. CORS: allow all origins.
- Serve the dashboard/ folder as static files at "/" (so one command runs everything).
- Run command: uvicorn server.main:app --host 0.0.0.0 --port 9000
- server/requirements.txt: fastapi, uvicorn.
- server/test_flow.ps1: PowerShell script using Invoke-RestMethod that creates a session, accepts it,
  posts 3 fake events (2 "intent", 1 "done"), finishes it as "solved", then prints GET /events.
```
✅ **Test:** run the server, then `server/test_flow.ps1`. You should see the 3 events and status `solved`.
Also open `http://localhost:9000/health` in the browser and check it shows `{"ok": true}`.

#### Step 1.2 — Support dashboard (1:30–2:30)
```
Read CONTRACT.md. Build dashboard/index.html (single file: HTML + CSS + vanilla JS), title "FixPilot Support Desk".
Design: professional, dark left sidebar with the FixPilot logo text, light content area, large readable fonts
(it will be shown on a projector).
1. "New request" card: textarea "Customer's query", vendor dropdown (one option: billing_app),
   button "Generate FixPilot code" -> POST /sessions.
   Show the code VERY BIG (e.g. 482 913) with a Copy button and the text
   "Ask the customer to enter this code in FixPilot".
2. "Live session" panel: polls GET /sessions/{code}/events every 2 seconds.
   Status badge: waiting = grey "Waiting for customer", running = blue pulsing "AI is working",
   solved = green, escalated = orange "Needs human", stopped = red.
   Timeline: each event as a row with time, icon by type (🤖 intent, ✋ approval, ✅ done, ⚠️ escalate, ❌ error, 🛑 stopped)
   and the text. Newest at the bottom, auto-scroll.
   Timer from accept to finish: "Solved in 0:48".
3. When finished: big summary card with the summary text.
4. "Recent sessions" list in the sidebar (localStorage): code, query, status. Click to reopen.
API base URL = same origin as the page.
```
✅ **Test:** open `http://localhost:9000`, create a code, run the test script with that code (or curl), and watch the events appear live and the badge turn green.

#### Step 1.3 — Knowledge file `kb/billing_app.md` (2:30–3:00, then keep improving)
**This is the most important thing you do.** The AI follows this file as the truth. Wrong or vague names make it click the wrong things.

Open the billing software and write down everything **using the EXACT names shown on screen** (same spelling, same capital letters).

Template:
```
# <Billing Software Name>

## Main screen layout
- Top menu bar: <list menus left to right>
- Left sidebar (if any): <list items top to bottom>
- Main shortcuts: F2 = ..., Ctrl+N = ...

## How to: Add a new product
Steps:
1. Click "<menu>" in the <top menu / left sidebar>
2. Click "<button>"
3. Fill "<field name>" = product name, "<field name>" = price, "<field>" = GST % (dropdown), "<field>" = HSN
4. Click "<Save button text>"
Required fields: ...
Check it worked: product appears in "<list name>"

## How to: <next task>
...

## Common errors and fixes
- "<exact error text>": cause → fix steps

## Do NOT do — escalate to human support
- License / activation problems, login or password, deleting data, database or backup restore errors
```

Write **at least 10–15 "How to"** entries for the questions customers really ask, for example: add product, edit price, change GST, create a bill, print a duplicate bill, add a customer, daily sales report, GST report, change the bill format/printer, take a backup, find an old bill.

✅ **Test:** follow every entry yourself in the software, step by step. If you get stuck, the AI will get stuck too, so fix the entry.

### ✅ CHECKPOINT 1 (3:00) — 10 minutes with Anas
- Show the dashboard working with fake events.
- Give Anas `kb/billing_app.md` (git push). He will test the AI on the real billing software with it.
- **Write down every step where the AI got confused.** That's your next job.

### PHASE 2 — Improve + integrate (3:00–5:00)

- [ ] **Fix the kb** for each step the AI got wrong (more exact names, positions like "top-right", shortcut keys).
- [ ] Dashboard polish: bigger code, the timer, the summary card, and check it looks clean on a big screen.
- [ ] Start the **pitch slides** (Step 3.1 outline below).

### ✅ CHECKPOINT 2 (5:00) — MERGE with Anas
1. Both: `git pull`.
2. You: start the server (`uvicorn server.main:app --host 0.0.0.0 --port 9000`).
3. Anas sets `SERVER_URL=http://<your-ip>:9000` in his `.env`.
4. Full run: you type **"Customer wants to add a new product: Parle-G, ₹10, GST 18%"** → generate the code → tell Anas → he enters it and clicks Accept → watch the steps arrive live → **Solved ✅**.
5. **Record backup video #2** (your screen + his screen; a phone recording is fine).

If the laptops can't connect, Anas runs the server on his laptop too, and you open the dashboard from his IP.

### PHASE 3 — Pitch + polish (5:00–6:30)

#### Step 3.1 — Slides (8–10 max)
1. **Problem:** software vendors answer the same "where is this menu?" questions all day over AnyDesk. Customers wait hours.
2. **Solution:** FixPilot = AnyDesk with AI. Two modes: personal help + business support.
3. **How it works:** code → accept → AI sees the screen → fixes it or guides → learns.
4. **Live demo** (switch to the laptops).
5. **Tech:** Gemini Computer Use (desktop), Gemini 3.8 Flash + Gemini 4 Argon fallback, Google Cloud (Cloud Run, Firestore, Vector Search in production).
6. **Safety:** consent code + Accept, Guide/Assist/Auto modes, STOP button, only the app window, audit log, human escalation.
7. **Business model:** free for individuals. Vendors: ₹4,999/month (300 fixes), ₹14,999/month (1,500 fixes), pay per extra fix.
8. **Competition:** AnyDesk/TeamViewer (needs a human) · ChatGPT/chatbots (text only, can't see the screen) · WalkMe/Whatfix (web apps only, manual setup). **FixPilot: works on Windows desktop software, no setup, Hindi voice.**
9. **Traction:** a real billing software vendor (our friend) is ready to pilot. Put a screenshot of his WhatsApp message here.
10. **Team + roadmap:** pilots Q1 2027, Hindi/Gujarati voice, auto-learning of new software.

#### Step 3.2 — Backup video (90 sec)
Edit video #2 in Clipchamp: Mode 1 clip → Mode 2 full flow → the Solved screen. Add short text captions. Save it on both laptops **and your phone**.

#### Step 3.3 — Get proof
Ask our friend (the vendor) for a short WhatsApp message like *"I want to try FixPilot for my customers' support."* Screenshot it for slide 9.

### PHASE 4 — Rehearse together (6:30–7:30)
Your role on stage: **you are the support agent.** You type the query live and read the code out loud.
Demo order: Mode 1 (Anas) → **Mode 2 (you start it)** → STOP button → escalation ("my license expired").
Run it 5 times. Reset the dummy data in the billing software between runs.

### Buffer (7:30–8:00): keep it free for surprises.

---

## 5. Git rules (so merging never hurts)
1. Commit **only inside** `server/`, `dashboard/`, `kb/`, `pitch/`.
2. `git pull` before every `git push`. Push small, every ~30 min.
3. **Never commit `.env`** (the API key).
4. Need a change in CONTRACT.md? Talk to Anas first and change it together.

## 6. Quick fixes
| Problem | Fix |
|---|---|
| Anas's app can't reach your server | Same hotspot? Firewall rule added? Server started with `--host 0.0.0.0`? Try `http://<your-ip>:9000/health` from his browser |
| Dashboard shows nothing | Press F12 → Console tab for errors. Check the code you are polling is the right one |
| The AI clicks the wrong thing in the billing software | Make that kb entry more exact: the exact button text and where it is on screen |
| Stuck for more than 20 min | Tell Anas, and move on to slides/kb while you think |

Good luck! 🚀
