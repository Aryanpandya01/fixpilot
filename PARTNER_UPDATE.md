# FixPilot — Update for Partner (from Anas, Person A side)

Hi! This zip has **my part** of FixPilot (the AI agent + the FixPilot app). Your part (`server/`, `dashboard/`, `kb/`) is not in it.
Read this once (10 min), then follow **"Merge + test on 2 PCs"** below.

---

## 1. What we built (Person A side)

| Folder / file | What it is | Status |
|---|---|---|
| `agent/screen.py` | Screenshots (DPI-correct, sent as small JPEG) | ✅ tested |
| `agent/executor.py` | Mouse + keyboard (click, type incl. ₹ and Hindi, hotkeys, scroll, drag) | ✅ tested |
| `agent/prompts.py` | FixPilot's rules + tools: `report_done`, `yield_to_user`, `ask_user`, **`open_settings_page`**, **`open_app`** | ✅ |
| `agent/agent.py` | The AI loop: screenshot → Gemini → act → check → repeat. Trust modes, STOP, logs | ✅ tested |
| `app/server.py` | Local app server: connects the panel to the AI, handles **support codes**, sends every step to YOUR server | ✅ tested |
| `app/panel/index.html` | The FixPilot window (redesigned): Personal help + Support code tabs, mode cards, approvals, timeline, STOP | ✅ |
| `app/overlay.py` | Guide mode: an orange pulsing ring on the button the user should click | ✅ |
| `app/run.bat` + `app/dock.ps1` | Double-click to start FixPilot. It docks the panel on the right edge of the screen | ✅ |
| `app/dev_mock_server.py` | **TEST ONLY** fake copy of your server, so I could test without your laptop. Your real server replaces it. | test only |

Results so far: light/dark mode done by itself in **30–47 seconds** (was ~100 s). A full Mode 2 run (code → Accept → AI → solved) passed against the test server.

## 2. Important changes / lessons (please read)

1. **Model:** we use **`gemini-3.5-flash-lite`** (about 8–10 s per step). `gemini-3.8-flash` took 70 s+ per step today, and `gemini-4-argon` hung, so 3.8 Flash is only the fallback.
2. **Every Gemini call is a fresh call.** "Continue the conversation" calls always failed with *503 high demand*, so each step now sends: goal + list of steps done + current screenshot.
3. **Busy/blocked handling:** FixPilot retries 3 times on "busy", and takes a new screenshot if Google wrongly blocks one as "harmful" (this happens when terminal text is visible on screen).
4. **"Done" must be proven:** FixPilot only accepts "done" after a NEW screenshot shows the result. (It once said "light mode on" while Windows stayed dark.)
5. **Speed tools:** `open_settings_page` jumps straight to 27 Windows Settings pages, and `open_app` opens Notepad, Explorer and similar apps in one step.
6. **Demo tip:** minimize terminals during the demo. Text on screen can confuse Gemini or trigger its safety filter.

## 3. What this means for YOUR part (server, dashboard, kb)

`CONTRACT.md` is unchanged, except for the extra fields on `GET /sessions/{code}/events` that you already have. Please check:

- [ ] **Event types your dashboard will receive:** `intent`, `approval`, `highlight` (Guide mode), `done`, `escalate`, `error`, `stopped`. Show unknown types with a neutral icon, never crash.
- [ ] **Order:** events arrive in order, then `POST /finish` comes about 1 second after the last event.
- [ ] **Optional token:** if you added `FIXPILOT_TOKEN` (B4), put the same value in `.env` on the PC running FixPilot. The app sends it as the `X-FixPilot-Token` header.
- [ ] **Knowledge file `kb/billing_app.md`:** add **keyboard shortcuts** (e.g. `F2 = New product`) and the exact menu names. That's the biggest speed win for Mode 2.
- [ ] The first `# Heading` of the kb file is shown to the customer as "**<name> support** wants FixPilot to help…". Make it the software's real name.

---

## 4. Merge + test on 2 PCs (no cloud needed)

**Setup on YOUR laptop (you play the customer, FixPilot runs here):**
1. Unzip into your FixPilot folder, next to your `server/`, `dashboard/`, `kb/`. Don't overwrite your own folders.
2. Install, once:
   ```
   py -3.11 -m venv .venv
   .venv\Scripts\pip install -r agent\requirements.txt -r server\requirements.txt
   ```
3. Create `.env` (copy `.env.example`): put the **Gemini key Anas sends you separately**, and `SERVER_URL=http://localhost:9000`.
4. Start your server: `.venv\Scripts\python -m uvicorn server.main:app --host 0.0.0.0 --port 9000`
5. Allow port 9000 in the firewall (admin PowerShell, once):
   `New-NetFirewallRule -DisplayName "FixPilot 9000" -Direction Inbound -LocalPort 9000 -Protocol TCP -Action Allow`
6. Double-click **`app\run.bat`**. The FixPilot panel appears on the right.
7. Run `ipconfig` and send Anas your **IPv4 address** (e.g. 192.168.43.25). Both laptops must be on the **same hotspot**.

**The test:**
1. **Anas** opens `http://<your-ip>:9000` → your dashboard → types *"Turn on dark mode"* → gets a code.
2. **You:** FixPilot panel → **Support code** tab → enter the code → **Accept**.
3. Your laptop turns dark by itself. Anas sees each step live on your dashboard → **Solved**.
4. Then try a billing software task, e.g. *"Add new product Parle-G, ₹10, GST 18%"*, with the billing app open on your screen.

**Quick test without Anas:** Personal help tab → *"Turn on dark mode"* → Fix it.

## 5. If something breaks
| Problem | Fix |
|---|---|
| Panel says **Offline** | The app server isn't running. Close it and double-click `app\run.bat` again |
| "Can't reach the support server" | Your server isn't running, or `SERVER_URL` in `.env` is wrong |
| Anas can't open your dashboard | Same hotspot? Firewall rule added? Server started with `--host 0.0.0.0`? |
| Clicks land in the wrong place | Windows display scale → set to **100%** |
| Very slow / "Gemini is busy" | Google's servers are busy; it retries by itself. Keep tasks short |
| Panel opens off-screen | Run `powershell -ExecutionPolicy Bypass -File app\dock.ps1` |

## 6. Next steps (together)
1. Merge test above ✅ → 2. Anas builds **`FixPilot.exe`** (so the customer PC needs no Python) → 3. Your **Cloud Run** deploy (B4) →
4. Record backup videos → 5. Rehearse the pitch 3×.

Send Anas any changes you make to the server/dashboard **as a zip of only your folders**, or better, let's switch to GitHub after this merge.
