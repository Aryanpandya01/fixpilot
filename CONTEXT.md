# FixPilot — Agent Context (read this first in every task)

## Product
FixPilot = AnyDesk, but an AI fixes the problem instead of a human. It runs on the customer's own Windows PC:
it takes a screenshot, Gemini decides the next UI action, and we run that action with mouse/keyboard, in a loop.
- Mode 1: personal Windows help (no server, kb_text = "").
- Mode 2: business support. Support creates a 6-digit code → the customer enters it → Accept → the AI solves the query
  inside the vendor's Windows billing software, using that vendor's knowledge base (kb_text).
- Trust modes: guide (only point at the button), assist (approve each step), auto (act directly).

## My scope (Person A)
I own `agent/` and `app/` only. NEVER create or edit `server/`, `dashboard/`, `kb/`, `pitch/` (the partner owns those).
The API between us is in `CONTRACT.md` and is frozen. Follow it exactly.

## Fixed tech decisions (do not change)
- Python 3.11, Windows 11, venv at `.venv/`. Secrets in `.env` (GEMINI_API_KEY, SERVER_URL). Never hardcode keys.
- Gemini: `google-genai>=2.7.0`, **Interactions API** (`client.interactions.create`), NOT generate_content.
  Tool: `{"type":"computer_use","environment":"desktop","enable_prompt_injection_detection":True}`.
  Models: `gemini-3.8-flash` (main), `gemini-4-argon` (fallback).
  Response: `interaction.steps`. A step with `type=="function_call"` has `.name`, `.arguments` (dict, includes `intent`,
  maybe `safety_decision`), and `.id`. Reply with `{"type":"function_result","name","call_id","result":[text, image]}`
  and use `previous_interaction_id=interaction.id`.
  Coordinates are normalized 0-999: `px = int(x/1000*screen_w)`.
- Screen: `mss` + Pillow. Input: `pyautogui`. Local UI: FastAPI + WebSocket + one HTML file. No React, no Electron, no LangChain.

## Code rules
- Small files, type hints, short docstrings. No extra features beyond the task.
- Every task ends with a runnable test command and its expected output.
- Don't reprint whole files when changing a few lines; edit them in place.
- If an API field name differs from this file, check it by printing the real response, then tell me.
