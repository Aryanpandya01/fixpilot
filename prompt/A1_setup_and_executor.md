Read `CONTEXT.md` and `CONTRACT.md` in this workspace first. Don't read the other .md files; they aren't needed for this task.

TASK 1: Project setup + screen capture + mouse/keyboard executor + Gemini key check.
Build ONLY what's listed below. No agent loop and no UI yet; those are the next tasks.

## 1. Setup
- Create `.gitignore`: `.env`, `.venv/`, `__pycache__/`, `logs/`, `*.pyc`.
- Create `.env.example` with `GEMINI_API_KEY=` and `SERVER_URL=http://localhost:9000`.
- Create `agent/requirements.txt`: google-genai>=2.7.0, mss, pyautogui, pillow, python-dotenv, keyboard, requests, fastapi, uvicorn.
- Create `agent/__init__.py` (empty) and `logs/` (it's in .gitignore, so create it at runtime).
- Give me the exact PowerShell commands to create `.venv` with Python 3.11, activate it, and install the requirements. Run them if you can.

## 2. `agent/screen.py`
- At the TOP, before importing mss or pyautogui anywhere, make the process DPI-aware:
  `ctypes.windll.shcore.SetProcessDpiAwareness(2)` inside try/except, falling back to `ctypes.windll.user32.SetProcessDPIAware()`.
  Also, executor.py must `import agent.screen` first, so this always runs before pyautogui loads.
- `capture(max_width: int = 1440) -> tuple[bytes, int, int]`: grab the primary monitor (mss monitor 1), convert to a PIL image,
  downscale proportionally to max_width if it's wider (LANCZOS), return (png_bytes, ORIGINAL_width, ORIGINAL_height).
- `screen_size() -> tuple[int, int]`.
- `to_b64(png_bytes) -> str`.

## 3. `agent/executor.py`
`run_action(name: str, args: dict, screen_w: int, screen_h: int) -> dict`
- `_px(x, y)` converts normalized 0-999 → pixels, clamped inside the screen.
- Actions (from the Gemini desktop environment):
  click, double_click, triple_click, right_click, middle_click, move, mouse_down, mouse_up,
  type(text, press_enter=False, optional x/y: if given, click there first, then ctrl+a + backspace to clear, then type),
  drag_and_drop(start_x, start_y, end_x, end_y), wait(seconds=1), press_key(key), key_down(key), key_up(key),
  hotkey(keys: list[str]), scroll(x, y, direction up/down/left/right, magnitude_in_pixels=300), take_screenshot (no-op).
- Typing: use `pyautogui.write(text, interval=0.02)` for ASCII. For NON-ASCII text (Hindi, ₹), put the text on the clipboard
  with PowerShell `Set-Clipboard` via subprocess, then ctrl+v.
- Key names: map model names to pyautogui (Enter→enter, Return→enter, Control/Ctrl→ctrl, Alt→alt, Shift→shift,
  Meta/Win/Windows/Super→win, Escape/Esc→esc, Backspace→backspace, Delete→delete, Tab→tab, Space→space,
  ArrowUp/Up→up, ArrowDown/Down→down, ArrowLeft/Left→left, ArrowRight/Right→right, PageUp→pageup, PageDown→pagedown,
  Home→home, End→end, F1..F12→f1..f12). Lowercase everything else.
- Scroll: vertical uses `pyautogui.scroll(±clicks)`, horizontal uses `pyautogui.hscroll`, with clicks = magnitude_in_pixels // 40 (minimum 1).
- `pyautogui.FAILSAFE = True`, `pyautogui.PAUSE = 0.25`. Move the mouse with `duration=0.15` so the demo looks human.
- Unknown action → `{"error": "unsupported action: <name>"}`. Any exception → `{"error": str(e)}`. Success → `{"ok": True}`.
- Pure function, no Gemini code in this file.

## 4. Tests: `agent/tests/`
- `test_screen.py`: capture once, print the original size, the png size in KB and the downscaled dimensions, and save `logs/test_screen.png`.
- `test_executor.py`: SAFE, visible test. Print a 3-second countdown, then:
  move to the center (500,500) → press `win` → wait 1 → type "notepad" → press Enter → wait 2 →
  type "FixPilot executor works ✅ ₹" → print each result dict. (I'll close Notepad myself. Don't save anything.)
- `test_gemini.py`: load .env, make ONE Interactions API call to `gemini-3.8-flash` with input "Reply with exactly: FixPilot online",
  then print the text reply AND `type(interaction)` plus the list of step types, so we can confirm the response shape.
  If the field names differ from CONTEXT.md, print the raw object and tell me.

## 5. Done when
- `python -m agent.tests.test_screen` prints the sizes and saves the png.
- `python -m agent.tests.test_executor` opens Notepad and types the line, including ✅ and ₹.
- `python -m agent.tests.test_gemini` prints "FixPilot online".
At the end, give me: the files created (one line each), the 3 test commands, and anything that didn't match CONTEXT.md.
