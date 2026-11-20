# FixPilot — Agent Context for Person B (read this first in every task)

## Product
FixPilot = AnyDesk, but an AI fixes the problem instead of a human.
Mode 2 flow: the support agent types the customer's query into the **Support Dashboard** → the **Session Server** creates a
6-digit code → the customer enters the code in the FixPilot desktop app (built by Person A) → Accept → the AI solves the query
inside the vendor's Windows billing software → the app posts each AI step to the server → the dashboard shows them live.

## My scope (Person B)
I own `server/`, `dashboard/`, `kb/`, `pitch/` only. NEVER create or edit `agent/` or `app/` (Person A owns those).
`CONTRACT.md` is the frozen API between us. Implement it EXACTLY: same paths, field names, status values.

## Fixed tech decisions (do not change)
- Python 3.11 on Windows 11, venv at `.venv/`. FastAPI + uvicorn. In-memory dict storage (no database).
- Server runs with: `uvicorn server.main:app --host 0.0.0.0 --port 9000`, and serves `dashboard/` at `/`.
- Dashboard: ONE file `dashboard/index.html` with plain HTML + CSS + vanilla JS. No React, no build step, no CDN needed.
- Knowledge base: `kb/billing_app.md` (Markdown, written by me by hand). vendor_id `billing_app` maps to that file.
- Test scripts use PowerShell `Invoke-RestMethod` (we're on Windows).

## Code rules
- Small, readable code with type hints. No features beyond the task.
- Every task ends with a runnable test command and its expected output.
- Don't reprint whole files when changing a few lines; edit them in place.
