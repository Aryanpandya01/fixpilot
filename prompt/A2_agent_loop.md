Read `CONTEXT.md` and `CONTRACT.md` (section 3) first. Don't read the other .md files.
Already done and working (don't rewrite these, only import them):
`agent/screen.py` (capture → png, orig_w, orig_h; to_b64) and `agent/executor.py` (run_action(name, args, w, h) → dict).
Facts from test_gemini: `client.interactions.create(...)` returns an Interaction whose `.steps` contains types like
`thought` and `model_output`. **Ignore `thought` steps everywhere.**

TASK A2: Gemini Computer Use agent loop. No UI yet (that's A3). It must run from the CLI.

## Step 0: probe the real response shape FIRST (agent/tests/probe_cu.py)
Before writing agent.py, make ONE call with the computer_use tool and print the raw structure, so we build on real field names:
```python
interaction = client.interactions.create(
    model="gemini-3.8-flash",
    system_instruction="You control a Windows desktop.",
    input=[{"type": "text", "text": "Click the Windows Start button."},
           {"type": "image", "data": to_b64(png), "mime_type": "image/png"}],
    tools=[{"type": "computer_use", "environment": "desktop", "enable_prompt_injection_detection": True}],
)
```
Print for every step: `type`, `name`, `id`, `arguments` (and `repr(step)` if any field is missing). Do NOT execute the action.
If the SDK auto-runs tools or loops on its own, pass `automatic_continuation=False` (it's an SDK kwarg). Run it, then tell me
the exact field names you found, and use THOSE in agent.py (CONTEXT.md expects `.name`, `.arguments`, `.id`).

## agent/prompts.py
1. `CUSTOM_TOOLS`: three function tools, each `{"type": "function", "name", "description", "parameters": <JSON schema>}`:
   - `report_done(summary: str, learn_path: str)`: the task is finished AND verified on screen. learn_path = the menu path the
     user can follow next time, e.g. "Settings > Personalization > Colors > Dark".
   - `yield_to_user(reason: str, summary: str)`: escalate to human support.
   - `ask_user(question: str)`: needs the user to do something or answer (e.g. click Yes on an admin popup).
2. `build_system_prompt(query: str, kb_text: str, mode: str) -> str`, using the template below. When kb_text is empty, use the
   Windows-help line and drop the KB section entirely.
```
You are FixPilot, an AI support agent running on the user's own Windows 11 PC with their consent.
You see the screen through screenshots and act through the computer_use tools.

GOAL: Solve the user's request: {query}
{kb_line}

HOW TO WORK
1. Look at the screenshot first and confirm what you see. Never guess.
2. Use the fewest, safest steps. After every step, check the new screenshot to confirm it worked.
3. Prefer direct routes: the Windows Search box or Settings pages over long menu hunting.
4. When the goal is done AND visible on screen, call report_done with a 1-2 sentence plain summary and learn_path.

BOUNDARIES (never break these)
- Never click, type into, move, or close the FixPilot panel docked on the right edge of the screen, or the terminal running FixPilot.
- Never delete files or data, never change passwords or accounts, never make payments, never send messages or emails,
  never install or uninstall software.
- If a Windows admin (UAC) "Yes/No" popup appears, call ask_user("Please click Yes on the popup, then tell me").
- Login screens, license/activation problems, data errors, or anything you don't understand: call yield_to_user.
- If 2 different approaches failed, call yield_to_user with what you saw and tried.

TRUST MODE: {mode}
- guide: the user does the clicks. Make each action's intent an instruction, e.g. "Click 'Products' in the top menu".
- assist: every action is shown to the user for approval first. Keep intents short and clear.
- auto: act directly, but follow all boundaries.

STYLE: every intent is ONE short, simple sentence. If the user wrote in Hindi or Hinglish, write intents and summaries in simple Hinglish.
{kb_section}
```
   kb_line (with kb): "You are supporting the software described in the VENDOR KNOWLEDGE BASE below. It is the source of truth for
   menu names, steps and correct settings. Follow a matching How-to exactly."
   kb_line (no kb): "This is a general Windows 11 help request. Use Windows Settings, the Start menu, the taskbar and File Explorer."
   kb_section: "\nVENDOR KNOWLEDGE BASE:\n" + kb_text.

## agent/agent.py
`run_session(query, kb_text, mode, on_event, ask_approval) -> dict`, exactly as in CONTRACT.md section 3.
- Constants: `MODEL = "gemini-3.8-flash"`, `FALLBACK_MODEL = "gemini-4-argon"`, `MAX_TURNS = 25`, `SETTLE_SEC = 0.8`.
- `TOOLS = [{"type": "computer_use", "environment": "desktop", "enable_prompt_injection_detection": True}] + CUSTOM_TOOLS`.
- `emit(type, text, action=None, **extra)` → calls on_event({"type", "text", "action", "ts": time.time(), **extra}) AND appends it to the log.
- First call: input = [text query, image screenshot]. Later calls: `previous_interaction_id=interaction.id`, input = function results.
- Each turn: take the `function_call` steps (skip `thought`). For each call, in order:
  * Check the global STOP flag first → emit "stopped" and return {"status": "stopped", "summary": "Stopped by user"}.
  * `report_done` → emit "done" (text = summary) → return {"status": "solved", "summary", "learn_path"}.
  * `yield_to_user` → emit "escalate" → return {"status": "escalated", "summary", "reason"}.
  * `ask_user` → emit "approval" with the question → ok = ask_approval(question). Result text: "user answered: done" or "user declined".
  * computer action → emit "intent" (text = arguments["intent"], or a readable fallback like "click at (x,y)").
      - needs_ok = mode == "assist" OR arguments.get("safety_decision", {}).get("decision") == "require_confirmation".
      - mode == "guide": DON'T execute. emit "highlight" with px x,y (converted with screen size) + the intent, then
        ask_approval("next"). The user clicks it themselves. Result = {"ok": True, "note": "user performed the step"}.
      - needs_ok and not ask_approval(intent) → emit "stopped", return {"status": "stopped", "summary": "User denied a step"}.
      - else result = executor.run_action(name, args, w, h). If safety confirmation was approved, add `"safety_acknowledgement": True`.
      - Pass ONLY the real action arguments to run_action (drop "intent" and "safety_decision").
- After all the calls in a turn: sleep SETTLE_SEC, take ONE new screenshot, and send one function_result per call_id:
  `{"type": "function_result", "name": name, "call_id": id, "result": [{"type": "text", "text": json.dumps(result)},
  {"type": "image", "data": b64, "mime_type": "image/png"}]}`. Custom tools (ask_user) send the text only.
- No function_call in a turn → collect the `model_output` text → emit "done" → return {"status": "solved", "summary": text, "learn_path": ""}.
- Errors: if run_action returns "error" twice in a row, OR the API raises → switch the model to FALLBACK_MODEL once and continue.
  If the API fails again → emit "error" → return {"status": "escalated", "summary": "AI error: ..."}.
- MAX_TURNS reached → emit "escalate" → return {"status": "escalated", "summary": "Took too many steps"}.
- STOP: module-level `threading.Event` `STOP`. `request_stop()` sets it, and `run_session` clears it at the start.
  Register the `keyboard` hotkey `ctrl+shift+x` → request_stop (wrap in try/except, since it can fail without admin rights. Then print a
  warning and rely on pyautogui FAILSAFE: moving the mouse to the top-left corner).
- Log: append every event + raw action args + result as JSON lines to `logs/session_<YYYYmmdd_HHMMSS>.jsonl`. Also save the
  screenshot of each turn as `logs/<session>_turnNN.png` (needed for escalation tickets later).
- Print a one-line timing per turn: `turn 3 | 2.4s model | click | Click 'Settings'`.

## CLI (bottom of agent.py)
`python -m agent.agent "turn on dark mode" --mode auto|assist|guide [--kb kb/billing_app.md]`
- on_event prints events in color-free plain text: `[intent] Click 'Start'`.
- ask_approval prints the question and reads input(): y/Enter = True, n = False. In guide mode, Enter = "I did it".
- Print the final result dict, the total time and the number of turns.

## Done when (run these yourself, one by one, and show me the output)
1. `python -m agent.tests.probe_cu` prints the real field names.
2. `python -m agent.agent "Turn on dark mode in Windows" --mode auto` → it switches to dark mode by itself, then report_done.
3. `python -m agent.agent "Turn light mode back on" --mode assist` → it asks y/n before each click; answer y.
4. Run `"open Notepad and type hello"` in auto and press Ctrl+Shift+X in the middle → status "stopped".
5. Show me one `logs/session_*.jsonl` file (the first 5 lines).
Then report: the files created, any field name that differed from this prompt, and the average seconds per turn.
