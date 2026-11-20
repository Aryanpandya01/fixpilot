"""agent/agent.py - Gemini Computer Use agent loop for FixPilot."""
import argparse
import datetime
import json
import os
import sys
import threading
import time
from dotenv import load_dotenv
from google import genai

from agent.executor import _px, run_action
import subprocess

from urllib.parse import urlparse

from agent.prompts import APPS, CUSTOM_TOOLS, OPEN_URL_TOOL, SETTINGS_PAGES, build_system_prompt, kb_hosts
from agent.screen import capture_jpeg, screen_size, to_b64
from agent import winfocus

load_dotenv()

# Constants (override in .env without touching code)
# Measured 2026-11-20: gemini-3.8-flash took 70s+ per step, gemini-3.5-flash-lite ~9s with the same click accuracy.
MODEL = os.getenv("FIXPILOT_MODEL", "gemini-3.5-flash-lite")
# gemini-4-argon hung for minutes and 3.8 Flash took 70s+/step on 2026-11-20, so by default the
# "fallback" is one more round on the fast model; set FIXPILOT_FALLBACK_MODEL to change it.
FALLBACK_MODEL = os.getenv("FIXPILOT_FALLBACK_MODEL", MODEL)
# Hard wall-clock limit per Gemini call. The SDK timeout only limits each network read, so a call
# once hung ~25 min (2026-11-20 20:52 session); _call_with_deadline enforces this one.
CALL_TIMEOUT = float(os.getenv("FIXPILOT_CALL_TIMEOUT", "40"))
RETRIES = 3  # retries on "high demand" (503/429) or timeout before falling back
# Thinking level: minimal | low | medium | high. Default thinking made each step take ~70s; "low" is much faster.
THINKING = os.getenv("FIXPILOT_THINKING", "low")
MAX_TURNS = 25
SETTLE_SEC = 0.8
IMG_WIDTH = 1280
IMG_MIME = "image/jpeg"
ENABLE_PID = os.getenv("FIXPILOT_PROMPT_INJECTION_DETECTION", "false").lower() == "true"
TOOLS = [
    {
        "type": "computer_use",
        "environment": "desktop",
        "enable_prompt_injection_detection": ENABLE_PID,
    }
] + CUSTOM_TOOLS

# Title words of each open_app window, so the launched window can be found and brought to the front
APP_TITLES = {
    "notepad": ("Notepad",), "calculator": ("Calculator",), "paint": ("Paint",),
    "file_explorer": ("File Explorer", "Home", "This PC"), "desktop_folder": ("Desktop",),
    "downloads_folder": ("Downloads",), "documents_folder": ("Documents",), "task_manager": ("Task Manager",),
    "snipping_tool": ("Snipping",), "control_panel": ("Control Panel",), "browser": ("Edge",),
}

# Global STOP flag
STOP = threading.Event()


class StopRequested(Exception):
    """Raised when STOP is pressed while waiting for Gemini."""


def _call_with_deadline(fn, timeout: float):
    """Run fn() in a daemon thread; give up after `timeout` seconds or when STOP is pressed."""
    box: dict = {}

    def _run():
        try:
            box["result"] = fn()
        except Exception as e:  # handed back to the caller below
            box["error"] = e

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    deadline = time.time() + timeout
    while t.is_alive() and time.time() < deadline:
        if STOP.is_set():
            raise StopRequested()
        t.join(0.25)
    if t.is_alive():
        raise TimeoutError(f"Gemini call timed out after {timeout:.0f}s")
    if "error" in box:
        raise box["error"]
    return box["result"]


def request_stop():
    """Trigger an emergency stop of the agent loop."""
    print("\n[STOP] Stop requested by user.", flush=True)
    STOP.set()


try:
    import keyboard

    keyboard.add_hotkey("ctrl+shift+x", request_stop)
except Exception as e:
    print(
        f"Warning: Could not register global hotkey ctrl+shift+x ({e}). "
        f"You can also use PyAutoGUI FAILSAFE (slam mouse into screen corner).",
        flush=True
    )


def run_session(
    query: str,
    kb_text: str = "",
    mode: str = "auto",
    on_event: callable = None,
    ask_approval: callable = None,
) -> dict:
    """Run an autonomous computer use session following CONTRACT.md section 3."""
    STOP.clear()

    # Fallback CLI callbacks if none provided
    if on_event is None:

        def on_event(ev: dict):
            print(f"[{ev.get('type', 'event')}] {ev.get('text', '')}")

    if ask_approval is None:

        def ask_approval(question: str) -> bool:
            ans = input(f"[Approval] {question} (Y/n): ").strip().lower()
            return ans in ("", "y", "yes")

    # Logging setup
    os.makedirs("logs", exist_ok=True)
    session_id = f"session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    log_path = os.path.join("logs", f"{session_id}.jsonl")

    def emit(ev_type: str, text: str, action: str = None, **extra) -> dict:
        event = {
            "type": ev_type,
            "text": text,
            "action": action,
            "ts": time.time(),
            **extra,
        }
        try:
            on_event(event)
        except Exception as e:
            print(f"Error in on_event callback: {e}")

        # Append to jsonl log
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Error writing to log: {e}")

        return event

    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        err = "GEMINI_API_KEY not found in environment or .env"
        emit("error", err)
        return {"status": "escalated", "summary": err}

    client = genai.Client(api_key=api_key)
    current_model = MODEL
    switched_to_fallback = False
    consecutive_action_errors = 0
    last_point = None  # screen px of the last click, used to ring the field when asking the user (e.g. a password box)

    system_instruction = build_system_prompt(query, kb_text, mode)
    url_hosts = kb_hosts(kb_text)  # open_url may only open the vendor's own site
    session_tools = TOOLS + ([OPEN_URL_TOOL] if url_hosts else [])

    # STATELESS turns: every turn is a fresh call with the goal + steps done so far + the current screenshot.
    # Why: on 2026-11-20 every continuation call (previous_interaction_id + function_result) returned
    # "503 high demand" while fresh calls worked in ~10s. Fresh calls are also easier to retry and to switch models.
    history: list[str] = []

    def build_input(b64: str) -> list:
        done = "\n".join(history[-8:]) if history else "None yet."
        text = (
            f"USER REQUEST: {query}\n\n"
            f"STEPS ALREADY DONE (oldest first):\n{done}\n\n"
            "The image is the CURRENT screen, taken after those steps. Decide only the NEXT action. "
            "Don't repeat a step that already worked. If the request is complete and visible on screen, call report_done."
        )
        return [
            {"type": "text", "text": text},
            {"type": "image", "data": b64, "mime_type": IMG_MIME},
        ]

    def call_model(model: str, inp: list, prev_id=None):
        """One fresh Gemini Computer Use call (prev_id is ignored, see STATELESS note above)."""
        kwargs = dict(
            model=model,
            input=inp,
            tools=session_tools,
            system_instruction=system_instruction,
            generation_config={"thinking_level": THINKING},
            automatic_continuation=False,
        )
        last_err = None
        for attempt in range(RETRIES):
            try:
                return _call_with_deadline(
                    lambda: client.interactions.create(timeout=CALL_TIMEOUT, **kwargs), CALL_TIMEOUT)
            except StopRequested:
                raise
            except Exception as e:
                msg = str(e).lower()
                busy = any(k in msg for k in ("503", "429", "high demand", "unavailable", "timeout", "timed out", "resource_exhausted"))
                if not busy:
                    raise
                last_err = e
                wait = 2 * (attempt + 1)
                print(f"  Gemini busy ({model}), retry {attempt + 1}/{RETRIES} in {wait}s...", flush=True)
                emit("intent", f"Gemini is busy, retrying ({attempt + 1}/{RETRIES})...", action="retry")
                time.sleep(wait)
        raise last_err

    # Initial screen capture
    png_bytes, screen_w, screen_h = capture_jpeg(max_width=IMG_WIDTH)
    b64_img = to_b64(png_bytes)

    # Avoid starting with mouse in failsafe corner (0,0)
    try:
        import pyautogui
        mx, my = pyautogui.position()
        if mx <= 2 and my <= 2:
            pyautogui.FAILSAFE = False
            pyautogui.moveTo(screen_w // 2, screen_h // 2)
            pyautogui.FAILSAFE = True
    except Exception:
        pass

    # Save turn 0 screenshot
    turn0_path = os.path.join("logs", f"{session_id}_turn00.jpg")
    with open(turn0_path, "wb") as f:
        f.write(png_bytes)

    next_input = build_input(b64_img)
    previous_interaction_id = None

    for turn in range(1, MAX_TURNS + 1):
        if STOP.is_set():
            emit("stopped", "Stopped by user")
            return {"status": "stopped", "summary": "Stopped by user"}

        t_model_start = time.time()
        try:
            interaction = call_model(current_model, next_input, previous_interaction_id)
        except StopRequested:
            emit("stopped", "Stopped by user")
            return {"status": "stopped", "summary": "Stopped by user"}
        except Exception as e:
            print(f"[Turn {turn}] API Error on {current_model}: {e}")
            if "safety" in str(e).lower():
                # False-positive screenshot block (e.g. text from a terminal on screen).
                # Take a fresh screenshot and retry the same fast model once.
                time.sleep(1.5)
                png_bytes, screen_w, screen_h = capture_jpeg(max_width=IMG_WIDTH)
                next_input = build_input(to_b64(png_bytes))
                try:
                    interaction = call_model(current_model, next_input)
                    e = None
                except Exception as e_safe:
                    e = e_safe
            if STOP.is_set():
                emit("stopped", "Stopped by user")
                return {"status": "stopped", "summary": "Stopped by user"}
            if e is None:
                pass
            elif not switched_to_fallback:
                print(f"Switching to fallback model: {FALLBACK_MODEL}")
                current_model = FALLBACK_MODEL
                switched_to_fallback = True
                try:
                    interaction = call_model(current_model, next_input, previous_interaction_id)
                except StopRequested:
                    emit("stopped", "Stopped by user")
                    return {"status": "stopped", "summary": "Stopped by user"}
                except Exception as e2:
                    emit("error", f"AI error on fallback: {e2}")
                    return {"status": "escalated", "summary": f"AI error: {e2}"}
            else:
                emit("error", f"AI error: {e}")
                return {"status": "escalated", "summary": f"AI error: {e}"}

        model_duration = time.time() - t_model_start

        # Extract steps
        steps = getattr(interaction, "steps", [])
        function_calls = [
            s for s in steps if getattr(s, "type", None) == "function_call"
        ]
        model_outputs = [
            s for s in steps if getattr(s, "type", None) == "model_output"
        ]

        # No function call -> model responded with text completion
        if not function_calls:
            text_parts = []
            for mo in model_outputs:
                content = getattr(mo, "content", None)
                if isinstance(content, list):
                    for c in content:
                        if hasattr(c, "text") and c.text:
                            text_parts.append(c.text)
                elif isinstance(content, str):
                    text_parts.append(content)
            summary_text = " ".join(text_parts).strip() or "Task completed"
            emit("done", summary_text)
            return {"status": "solved", "summary": summary_text, "learn_path": ""}

        turn_results = []
        acted_this_turn = False
        for call in function_calls:
            if STOP.is_set():
                emit("stopped", "Stopped by user")
                return {"status": "stopped", "summary": "Stopped by user"}

            call_name = getattr(call, "name", "")
            call_id = getattr(call, "id", None)
            arguments = getattr(call, "arguments", {}) or {}

            # 1. Custom tool: report_done
            # Only trust "done" if it was decided by LOOKING at a screenshot taken after the last action.
            # Bug seen 2026-11-20: model sent "click Light" + report_done in one reply, but the click hadn't
            # worked (Windows stayed dark). So if an action ran in this same turn, defer and verify next turn.
            if call_name == "report_done" and acted_this_turn:
                history.append(
                    f"{len(history) + 1}. (you said the task is done; VERIFY on this new screenshot that "
                    f"it really is, and call report_done again only if it is visible)"
                )
                continue
            if call_name == "report_done":
                summary = arguments.get("summary", "Goal completed")
                learn_path = arguments.get("learn_path", "")
                emit("done", summary, action="report_done", learn_path=learn_path)
                return {
                    "status": "solved",
                    "summary": summary,
                    "learn_path": learn_path,
                }

            # 2. Custom tool: yield_to_user
            if call_name == "yield_to_user":
                summary = arguments.get("summary", "Escalated to human support")
                reason = arguments.get("reason", "unknown")
                emit("escalate", summary, action="yield_to_user", reason=reason)
                return {
                    "status": "escalated",
                    "summary": summary,
                    "reason": reason,
                }

            # 3. Custom tool: ask_user
            if call_name == "ask_user":
                question = arguments.get("question", "")
                where = {"x": last_point[0], "y": last_point[1]} if last_point else {}
                emit("approval", question, action="ask_user", **where)
                approved = ask_approval(question)
                if not approved:
                    emit("stopped", "User cancelled")
                    return {"status": "stopped", "summary": "User cancelled"}
                ans_text = "user answered: done"
                history.append(f"{len(history) + 1}. asked user: {question} -> {ans_text}")
                turn_results.append(
                    {
                        "type": "function_result",
                        "name": call_name,
                        "call_id": call_id,
                        "result": [{"type": "text", "text": ans_text}],
                    }
                )
                continue

            # 3b. Fast tools: open a Settings page / safe app directly (allow-listed, see prompts.py)
            if call_name in ("open_settings_page", "open_app", "open_url"):
                key = arguments.get("page") or arguments.get("app") or arguments.get("url") or ""
                if call_name == "open_url":
                    u = urlparse(key)
                    ok = u.scheme in ("http", "https") and (u.hostname or "").lower() in url_hosts
                    target = key if ok else None
                else:
                    table = SETTINGS_PAGES if call_name == "open_settings_page" else APPS
                    target = table.get(key)
                intent = arguments.get("intent") or f"Open {key.replace('_', ' ')}"
                print(f"turn {turn} | {model_duration:.1f}s model | {call_name} | {intent}", flush=True)
                emit("intent", intent, action=call_name)
                if mode == "guide" or (mode == "assist" and not ask_approval(intent)):
                    if mode == "assist":
                        emit("stopped", "User denied a step")
                        return {"status": "stopped", "summary": "User denied a step"}
                    ask_approval("next")  # guide: user opens it themselves
                    outcome = "user performed the step"
                elif not target:
                    outcome = f"error: '{key}' is not allowed"
                else:
                    try:
                        before = winfocus.snapshot()
                        if call_name == "open_url" or target.startswith("ms-settings:"):
                            os.startfile(target)
                        else:
                            subprocess.Popen(target, shell=True)
                        # Windows opens it BEHIND the current window, so find it and bring it to the front
                        hints = (("Settings",) if call_name == "open_settings_page"
                                 else APP_TITLES.get(key, ()) if call_name == "open_app" else ())
                        front = winfocus.bring_to_front(before, hints, browser=call_name == "open_url")
                        if call_name == "open_url":
                            time.sleep(1.5)  # let the web page load before the next screenshot
                        outcome = (f"ok, the '{front}' window is now in front" if front else
                                   "launched, but it may be behind other windows: click it on the taskbar, don't open it again")
                    except Exception as ex:
                        outcome = f"error: {ex}"
                acted_this_turn = True
                history.append(f"{len(history) + 1}. {call_name}({key}): {intent} -> {outcome}")
                continue

            # 3c. Custom tool: fill_form (several text fields in one Gemini reply instead of a click + type per field)
            if call_name == "fill_form":
                fields = [f for f in (arguments.get("fields") or []) if "x" in f and "y" in f]
                labels = ", ".join(f.get("label", "?") for f in fields)
                intent = arguments.get("intent") or f"Fill in {labels}"
                print(f"turn {turn} | {model_duration:.1f}s model | fill_form | {intent}", flush=True)
                emit("intent", intent, action="type")
                if mode == "assist" and not ask_approval(intent):
                    emit("stopped", "User denied a step")
                    return {"status": "stopped", "summary": "User denied a step"}
                done, errors = [], []
                for f in fields:
                    if STOP.is_set():
                        break
                    if mode == "guide":  # the user types each one; ring the box and wait
                        gx, gy = _px(f["x"], f["y"], screen_w, screen_h)
                        emit("highlight", f"Type {f.get('text', '')} in {f.get('label', 'this field')}", action="highlight", x=gx, y=gy)
                        ask_approval("next")
                        res = {"ok": True}
                    else:
                        res = run_action("type", {"x": f["x"], "y": f["y"], "text": str(f.get("text", ""))}, screen_w, screen_h)
                    (errors if "error" in res else done).append(f.get("label", "?"))
                    last_point = _px(f["x"], f["y"], screen_w, screen_h)
                acted_this_turn = True
                outcome = f"filled {', '.join(done) or 'nothing'}" + (f"; FAILED: {', '.join(errors)}" if errors else "")
                history.append(f"{len(history) + 1}. fill_form: {intent} -> {outcome}")
                continue

            # 4. Computer action
            intent = arguments.get("intent")
            if not intent:
                if "x" in arguments and "y" in arguments:
                    intent = f"{call_name} at ({arguments['x']}, {arguments['y']})"
                else:
                    intent = f"{call_name} action"

            print(
                f"turn {turn} | {model_duration:.1f}s model | {call_name} | {intent}",
                flush=True
            )
            emit("intent", intent, action=call_name)
            if "x" in arguments and "y" in arguments:
                last_point = _px(arguments["x"], arguments["y"], screen_w, screen_h)

            safety_decision = arguments.get("safety_decision") or {}
            needs_confirmation = (mode == "assist") or (
                safety_decision.get("decision") == "require_confirmation"
            )

            if mode == "guide":
                # Guide mode: don't execute, highlight for user to click
                raw_x = arguments.get("x", 500)
                raw_y = arguments.get("y", 500)
                px_x, px_y = _px(raw_x, raw_y, screen_w, screen_h)
                emit("highlight", intent, action="highlight", x=px_x, y=px_y)
                ask_approval("next")
                action_result = {"ok": True, "note": "user performed the step"}
            elif needs_confirmation:
                approved = ask_approval(intent)
                if not approved:
                    emit("stopped", "User denied a step")
                    return {
                        "status": "stopped",
                        "summary": "User denied a step",
                    }
                # Filter arguments (drop intent & safety_decision)
                real_args = {
                    k: v
                    for k, v in arguments.items()
                    if k not in ("intent", "safety_decision")
                }
                action_result = run_action(
                    call_name, real_args, screen_w, screen_h
                )
                action_result["safety_acknowledgement"] = True
            else:
                real_args = {
                    k: v
                    for k, v in arguments.items()
                    if k not in ("intent", "safety_decision")
                }
                action_result = run_action(
                    call_name, real_args, screen_w, screen_h
                )

            # Check consecutive action errors
            if "error" in action_result:
                consecutive_action_errors += 1
                if consecutive_action_errors >= 2 and not switched_to_fallback:
                    print(
                        f"Action failed twice in a row. Switching to fallback model {FALLBACK_MODEL}."
                    )
                    current_model = FALLBACK_MODEL
                    switched_to_fallback = True
            else:
                consecutive_action_errors = 0

            acted_this_turn = True
            outcome = action_result.get("error") or action_result.get("note") or "ok"
            history.append(f"{len(history) + 1}. {call_name}: {intent} -> {outcome}")

            turn_results.append(
                {
                    "name": call_name,
                    "call_id": call_id,
                    "action_result": action_result,
                }
            )

        # Pause and capture fresh screen after executing turn actions
        time.sleep(SETTLE_SEC)
        png_bytes, screen_w, screen_h = capture_jpeg(max_width=IMG_WIDTH)
        b64_img = to_b64(png_bytes)

        # Save turn screenshot
        turn_img_path = os.path.join(
            "logs", f"{session_id}_turn{turn:02d}.jpg"
        )
        with open(turn_img_path, "wb") as f:
            f.write(png_bytes)

        # Assemble next turn payload: fresh call with history + current screen (see STATELESS note)
        next_input = build_input(b64_img)
        for res in []:  # old continuation payload, kept disabled
            if "result" in res:
                next_input.append(res)
            else:
                next_input.append(
                    {
                        "type": "function_result",
                        "name": res["name"],
                        "call_id": res["call_id"],
                        "result": [
                            {
                                "type": "text",
                                "text": json.dumps(res["action_result"]),
                            },
                            {
                                "type": "image",
                                "data": b64_img,
                                "mime_type": IMG_MIME,
                            },
                        ],
                    }
                )

    emit("escalate", "Took too many steps")
    return {"status": "escalated", "summary": "Took too many steps"}


def main():
    parser = argparse.ArgumentParser(description="FixPilot AI Agent CLI")
    parser.add_argument("query", type=str, help="Problem or request to solve")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["auto", "assist", "guide"],
        default="auto",
        help="Trust mode: auto | assist | guide",
    )
    parser.add_argument(
        "--kb", type=str, default="", help="Path to vendor knowledge base .md file"
    )
    args = parser.parse_args()

    kb_text = ""
    if args.kb:
        if os.path.exists(args.kb):
            with open(args.kb, "r", encoding="utf-8") as f:
                kb_text = f.read()
        else:
            print(f"Warning: KB file '{args.kb}' not found. Continuing without KB.")

    def cli_on_event(ev: dict):
        ev_type = ev.get("type", "event")
        text = ev.get("text", "")
        if ev_type == "highlight":
            print(f"[highlight] ({ev.get('x')}, {ev.get('y')}): {text}", flush=True)
        else:
            print(f"[{ev_type}] {text}", flush=True)

    def cli_ask_approval(prompt: str) -> bool:
        if args.mode == "guide" or prompt == "next":
            input(f"[guide] {prompt} - Press Enter when you have performed the action...")
            return True
        ans = input(f"[approval required] {prompt} (Y/n): ").strip().lower()
        return ans in ("", "y", "yes")

    print(f"\n=== FixPilot Agent Starting ===", flush=True)
    print(f"Query: {args.query}", flush=True)
    print(f"Mode:  {args.mode}", flush=True)
    print(f"KB:    {args.kb if args.kb else '(None - Mode 1)'}", flush=True)
    print(f"Press Ctrl+Shift+X at any time to STOP.\n", flush=True)

    start_time = time.time()
    result = run_session(
        query=args.query,
        kb_text=kb_text,
        mode=args.mode,
        on_event=cli_on_event,
        ask_approval=cli_ask_approval,
    )
    elapsed = time.time() - start_time

    print(f"\n=== Session Finished ===", flush=True)
    print(f"Result: {result}", flush=True)
    print(f"Total time: {elapsed:.1f}s", flush=True)


if __name__ == "__main__":
    main()
