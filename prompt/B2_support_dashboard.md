Read `CONTEXT_B.md` and `CONTRACT.md` first. `server/main.py` already exists and works. Don't modify it unless something
below truly needs it, and if so, tell me what you changed.

TASK B2: Support Dashboard. Replace `dashboard/index.html` with the real dashboard (a single file: HTML + CSS + vanilla JS).
API base = same origin (`location.origin`). No external libraries or CDNs (the venue wifi may be bad).

## Look
- Title "FixPilot Support Desk". It will be shown on a projector: base font 18px, high contrast, clean.
- Layout: dark left sidebar (260px, #0f172a) + light main area (#f8fafc). Accent blue #2563eb, success #16a34a,
  warning #ea580c, danger #dc2626. Rounded cards, soft shadows, system font stack.
- Sidebar: logo text "🛠️ FixPilot" + "Support Desk"; "Recent sessions" list; at the bottom a server status dot
  (green/red, checks GET /health every 5s).

## Main area, 3 cards
1. **New request**
   - Textarea "Customer's query" (placeholder: "e.g. Customer wants to add a new product: Parle-G, ₹10, GST 18%").
   - Vendor select: one option, value `billing_app`, label "Billing Software".
   - Button "Generate FixPilot code" → POST /sessions → on success show the **Code card** and start polling.
   - Ctrl+Enter in the textarea also submits.
2. **Code card** (hidden until there's a code)
   - The code VERY BIG (64px, monospace, letter-spaced, shown as "482 913"), a "Copy" button (copies 6 digits without the space),
     and the text "Ask the customer to open FixPilot → Support code → enter this code."
3. **Live session**
   - Status badge: waiting = grey "Waiting for customer…", running = blue PULSING "🤖 AI is working",
     solved = green "✅ Solved", escalated = orange "⚠️ Needs human support", stopped = red "🛑 Stopped by customer".
   - Live timer: from accepted_at to now (or finished_at), shown as "0:48". When finished: "Solved in 0:48".
   - Timeline: one row per event, with time (HH:MM:SS), an icon by type (intent 🤖, approval ✋, highlight 👉, done ✅,
     escalate ⚠️, error ❌, stopped 🛑) and the text. New rows fade in. Auto-scroll to the newest.
   - When status is solved/escalated/stopped: a big result card (green/orange/red) with the summary text.

## Behaviour
- Poll GET /sessions/{code}/events every 2s while status is waiting/running. Stop polling when finished.
  Only render NEW events (track how many are already drawn), so there's no flicker.
- Recent sessions (sidebar): GET /sessions every 5s. Each row shows the code, a short query and a colored status dot.
  Clicking a row loads that session into the Code + Live cards.
- Network error: show a small red toast "Server not reachable" and keep retrying. Never crash.
- Button "New request" resets the screen for the next customer.

## Done when
1. Run the server, open http://localhost:9000, type a query and click Generate: the big code appears and the status is "Waiting for customer…".
2. In PowerShell, run the B1 test flow against THAT code. Add a `-Code <code>` param to `server/test_flow.ps1` that skips creating a new session
   and uses the given one, together with `-Pause`. The badge turns blue and pulses, the events appear one by one, the timer runs,
   and then it shows the green result card with "Solved in 0:0X".
3. Stop the server: the red toast appears and the health dot turns red. Start it again and it recovers on its own.
At the end, list what changed (one line each) and the exact test commands.
