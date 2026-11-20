# FixPilot — Person A Tasks (AI Agent + Customer app)

You own: `agent/`, `app/`
Do not edit `server/`, `dashboard/`, `demo_app/`, `kb/`, `pitch/` (Person B). Read **CONTRACT.md** first.

On stage, **your laptop is the "customer PC"**. FixPilot runs here and controls this screen.

Gemini facts (checked against the docs): Interactions API, `google-genai>=2.7.0`, tool
`{"type":"computer_use","environment":"desktop"}`, coordinates normalized **0–999**, models `gemini-3.8-flash`
(main) and `gemini-4-argon` (fallback). Each action has an `intent` sentence → show it in the UI.

---

## Your tasks (in order)

### Task 0 — Together with Person B  ⏱ 0:00–0:20
Create the GitHub repo and folders, commit CONTRACT.md and `.gitignore` (`.env`, `venv/`, `__pycache__/`, `logs/`), create `.env`, and test the API key with one text call to `gemini-3.8-flash`.

### Task 1 — Screen + mouse/keyboard (`agent/screen.py`, `agent/executor.py`)  ⏱ 0:20–1:00
**Antigravity prompt:**
```
Python 3.11, Windows. Create agent/screen.py and agent/executor.py and agent/requirements.txt
(google-genai>=2.7.0, mss, pyautogui, pillow, python-dotenv, keyboard, requests, fastapi, uvicorn).

screen.py:
- On import: ctypes.windll.shcore.SetProcessDpiAwareness(2) (so clicks land correctly at 125%/150% scaling).
- capture() -> (png_bytes, screen_w, screen_h): primary monitor via mss, downscaled to max width 1440 with Pillow;
  return the ORIGINAL screen size.

executor.py: run_action(name, args, screen_w, screen_h) -> dict
- Model coordinates are 0-999 normalized: px = int(x/1000*screen_w), py = int(y/1000*screen_h).
- Implement: click, double_click, triple_click, right_click, middle_click, move, mouse_down, mouse_up,
  type(text, press_enter, optional x/y: click first then ctrl+a, backspace, type interval 0.02),
  drag_and_drop(start_x,start_y,end_x,end_y), wait(seconds), press_key(key), key_down, key_up,
  hotkey(keys list), scroll(x,y,direction,magnitude_in_pixels), take_screenshot (no-op).
- Key name map (Enter->enter, Control->ctrl, Meta/Windows->win, etc.).
- pyautogui.FAILSAFE = True, PAUSE = 0.3. Return {"ok": True} or {"error": str(e)}.
```
✅ Test: a small script that clicks the Start button using normalized coordinates.

### Task 2 — Gemini agent loop (`agent/prompts.py`, `agent/agent.py`)  ⏱ 1:00–3:00
**Antigravity prompt:**
```
Read CONTRACT.md section 3. Create agent/prompts.py and agent/agent.py.

prompts.py: SYSTEM_PROMPT (I will paste it), plus custom function tools:
- report_done(summary: str, learn_path: str)   # learn_path e.g. "Products > Add Product > Save"
- yield_to_user(reason: str, summary: str)     # escalate to human support
- ask_user(question: str)                       # e.g. "Please click Yes on the admin popup"

agent.py: implement run_session(query, kb_text, mode, on_event, ask_approval) exactly as in CONTRACT.md.
- google-genai Interactions API: client.interactions.create(model, system_instruction=SYSTEM_PROMPT filled with
  kb_text and mode, input=[text query, screenshot png base64],
  tools=[{"type":"computer_use","environment":"desktop","enable_prompt_injection_detection":True}, custom tools]).
  Next turns use previous_interaction_id=interaction.id and input=function_results.
- MODEL = "gemini-3.8-flash"; after 2 failed actions in a row switch to "gemini-4-argon".
- Max 25 turns. For each function_call step:
  * on_event({"type":"intent","text":args.get("intent"),"action":name,"ts":time})
  * report_done -> on_event done, return {"status":"solved","summary":..., "learn_path":...}
  * yield_to_user -> on_event escalate, return {"status":"escalated","summary":...}
  * ask_user -> on_event approval with the question, wait for ask_approval(question)
  * mode "assist" OR args.safety_decision.decision == "require_confirmation" -> on_event approval, ask_approval(intent);
    denied -> return {"status":"stopped"}
  * mode "guide" -> do not execute; on_event({"type":"highlight","x":..,"y":..,"text":intent}); wait until ask_approval("next")
  * else executor.run_action(...)
- Sleep 0.8s, then capture a new screenshot. Send a function_result for EVERY call_id: [text json result
  (+ "safety_acknowledgement": true if the user confirmed), image png].
- No function_call in the response -> treat the model text as the summary and return solved.
- Global STOP: keyboard hotkey ctrl+shift+x sets a flag that is checked every step -> return {"status":"stopped"}.
- Log every step to logs/<timestamp>.jsonl.
- CLI: python -m agent.agent "turn on dark mode" --mode auto [--kb kb/billing_app.md]
  (--kb reads the file into kb_text, so Mode 2 can be tested without the server)
```

**SYSTEM_PROMPT (paste into prompts.py):**
```
You are FixPilot, an AI support agent running on the user's own Windows PC with their consent.
You see the screen through screenshots and act through the computer_use tools.

GOAL: Solve the user's request: {QUERY}
{IF kb_text}: You are supporting the software described in the VENDOR KNOWLEDGE BASE below. It is your
source of truth for menu names, steps and correct settings. Follow its steps exactly when one matches.
{IF no kb_text}: This is a general Windows 11 help request. Use standard Windows Settings and File Explorer.

HOW TO WORK
1. Look at the screenshot first and confirm what you see. Never guess.
2. Use the fewest, safest steps. After each step, check the new screenshot to confirm it worked.
3. When done and verified, call report_done with a 1-2 sentence plain summary and learn_path
   (the menu path, so the user can do it alone next time).

BOUNDARIES (never break)
- Never click, type into, or close the FixPilot panel on the right edge of the screen.
- Never delete files or data, never change passwords or accounts, never make payments,
  never send messages or emails, never install or uninstall software.
- If a Windows admin (UAC) "Yes/No" popup appears, call ask_user: "Please click Yes on the popup".
- Login screens, license problems, data errors, or anything you don't understand: call yield_to_user.
- If 2 different approaches failed: call yield_to_user with what you saw and tried.

TRUST MODE: {MODE}
- guide: the user does the clicks. Make each intent an instruction: "Click 'Products' in the left menu".
- assist: every action is shown for approval. Keep intents short and clear.
- auto: act directly, but follow all boundaries.

STYLE: every intent is one short, simple sentence. If the user wrote in Hindi/Hinglish, reply in simple Hinglish.

VENDOR KNOWLEDGE BASE:
{KB_TEXT}
```
✅ Test (Mode 1, no server needed): `turn on dark mode`, `create a new folder named Bills on Desktop`, `show the WiFi and Bluetooth icons in the taskbar`.
**Record a quick backup video the first time one works.**

### ✅ Checkpoint 1 at 3:00: show Person B Mode 1 working.

### Task 3 — FixPilot desktop app (`app/`)  ⏱ 3:00–5:00
**Antigravity prompt:**
```
Read CONTRACT.md. Create app/server.py (FastAPI, port 8000, local only) and app/panel/index.html.
- Local WebSocket /ws between the panel and agent.run_session (run it in a background thread).
  Panel -> server messages: start {query, mode}, join {code}, accept, deny, approve, next, stop.
  Server -> panel: every Event from on_event, plus approval requests.
- Mode 1 tab "Personal help": query box + mic button (browser Web Speech API, en-IN / hi-IN toggle)
  + mode selector (Guide / Assist / Auto) + Start.
- Mode 2 tab "Support code": 6-digit code input -> GET {SERVER_URL}/sessions/{code} -> popup
  "<vendor_name> support wants FixPilot to: <query>. Accept?" -> Accept -> POST accept -> run_session with kb_text.
  Each on_event is ALSO sent to POST {SERVER_URL}/sessions/{code}/events. At the end POST /finish.
- Panel UI: narrow dark panel (400px), status pill, live feed of intents as chat bubbles, Approve/Deny card
  when approval is needed, big red STOP button always visible, green "Solved" card with summary +
  "Next time: <learn_path>", orange escalation card, timer "Solved in 0:48".
- Launch script app/run.bat: start uvicorn, then
  chrome --app=http://localhost:8000 --window-size=400,1000 --window-position=<screen_w-400>,0
- Guide mode highlight: app/overlay.py, a transparent always-on-top click-through Tkinter window that draws a
  glowing circle + arrow + text at the given screen x,y when a "highlight" event arrives.
```

### ✅ Checkpoint 2 at 5:00: MERGE with Person B
`git pull` → set `SERVER_URL=http://<laptopB-ip>:9000` in .env → Person B creates a code → you enter it → Accept → the AI solves it in the **real billing software** → Person B's dashboard shows Solved.

### Task 4 — Polish  ⏱ 5:00–6:30
- Red border "🔴 FixPilot AI in control — press Ctrl+Shift+X to stop" while the AI is acting.
- Speed: test with screenshots at 1280 width; use `gemini-3.8-flash` for all demo queries.
- Lock the demo setup: same resolution, billing software window maximized on the left, panel on the right.

### Task 5 — Rehearse together  ⏱ 6:30–7:30
Demo order: **Mode 1** (WiFi/Bluetooth icons) → **Mode 2** (Person B types "Customer wants to add a new product") → **STOP button** → escalation ("my license expired").

---

## Gotchas
- **Display scaling:** test clicks first. If they're off, the DPI awareness line didn't run before mss/pyautogui loaded.
- **UAC popups can't be clicked by automation** (a Windows security rule). That's why ask_user exists.
- The panel shows up in screenshots. It stays on the right and the prompt says to ignore it.
- Hotspot from your phone as backup internet. Same network as Person B's laptop.
