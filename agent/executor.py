"""agent/executor.py - Mouse and keyboard action executor."""
# Must import screen first to ensure DPI awareness is set before pyautogui loads
import agent.screen
from agent.screen import _attach_to_default_desktop

import subprocess
import time
import pyautogui

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.25

KEY_MAP = {
    "enter": "enter",
    "return": "enter",
    "control": "ctrl",
    "ctrl": "ctrl",
    "alt": "alt",
    "shift": "shift",
    "meta": "win",
    "win": "win",
    "windows": "win",
    "super": "win",
    "escape": "esc",
    "esc": "esc",
    "backspace": "backspace",
    "delete": "delete",
    "tab": "tab",
    "space": "space",
    "arrowup": "up",
    "up": "up",
    "arrowdown": "down",
    "down": "down",
    "arrowleft": "left",
    "left": "left",
    "arrowright": "right",
    "right": "right",
    "pageup": "pageup",
    "pagedown": "pagedown",
    "home": "home",
    "end": "end",
}
for i in range(1, 13):
    KEY_MAP[f"f{i}"] = f"f{i}"


def _normalize_key(key: str) -> str:
    """Map model key name to pyautogui key name."""
    k = str(key).strip().lower()
    return KEY_MAP.get(k, k)


def _px(x: float, y: float, screen_w: int, screen_h: int) -> tuple[int, int]:
    """Convert normalized 0-999 coordinates to pixel coordinates clamped inside the screen (avoiding exact corner failsafe points)."""
    px = min(max(5, int(float(x) / 1000.0 * screen_w)), screen_w - 6)
    py = min(max(5, int(float(y) / 1000.0 * screen_h)), screen_h - 6)
    return px, py


def _set_clipboard(text: str) -> None:
    """Set text to the Windows clipboard using PowerShell."""
    _attach_to_default_desktop()
    subprocess.run(
        ["powershell", "-NoProfile", "-Sta", "-Command", "$input | Set-Clipboard"],
        input=text,
        text=True,
        encoding="utf-8",
        check=True,
    )


def _type_text(text: str) -> None:
    """Type ASCII characters directly or copy-paste non-ASCII characters."""
    if text.isascii():
        pyautogui.write(text, interval=0.02)
    else:
        _set_clipboard(text)
        time.sleep(0.05)
        pyautogui.hotkey("ctrl", "v")


def run_action(name: str, args: dict, screen_w: int, screen_h: int) -> dict:
    """Execute a single UI action from Gemini desktop environment."""
    _attach_to_default_desktop()
    action = name.lower().strip()
    try:
        if action == "click":
            button = args.get("button", "left")
            if "x" in args and "y" in args and args["x"] is not None and args["y"] is not None:
                px, py = _px(args["x"], args["y"], screen_w, screen_h)
                pyautogui.click(px, py, button=button, duration=0.15)
            else:
                pyautogui.click(button=button)

        elif action == "double_click":
            if "x" in args and "y" in args and args["x"] is not None and args["y"] is not None:
                px, py = _px(args["x"], args["y"], screen_w, screen_h)
                pyautogui.doubleClick(px, py, duration=0.15)
            else:
                pyautogui.doubleClick()

        elif action == "triple_click":
            if "x" in args and "y" in args and args["x"] is not None and args["y"] is not None:
                px, py = _px(args["x"], args["y"], screen_w, screen_h)
                pyautogui.tripleClick(px, py)
            else:
                pyautogui.tripleClick()

        elif action == "right_click":
            if "x" in args and "y" in args and args["x"] is not None and args["y"] is not None:
                px, py = _px(args["x"], args["y"], screen_w, screen_h)
                pyautogui.rightClick(px, py, duration=0.15)
            else:
                pyautogui.rightClick()

        elif action == "middle_click":
            if "x" in args and "y" in args and args["x"] is not None and args["y"] is not None:
                px, py = _px(args["x"], args["y"], screen_w, screen_h)
                pyautogui.middleClick(px, py, duration=0.15)
            else:
                pyautogui.middleClick()

        elif action == "move":
            px, py = _px(args.get("x", 0), args.get("y", 0), screen_w, screen_h)
            pyautogui.moveTo(px, py, duration=0.15)

        elif action == "mouse_down":
            button = args.get("button", "left")
            if "x" in args and "y" in args and args["x"] is not None and args["y"] is not None:
                px, py = _px(args["x"], args["y"], screen_w, screen_h)
                pyautogui.moveTo(px, py, duration=0.15)
            pyautogui.mouseDown(button=button)

        elif action == "mouse_up":
            button = args.get("button", "left")
            if "x" in args and "y" in args and args["x"] is not None and args["y"] is not None:
                px, py = _px(args["x"], args["y"], screen_w, screen_h)
                pyautogui.moveTo(px, py, duration=0.15)
            pyautogui.mouseUp(button=button)

        elif action == "type":
            text = args.get("text", "")
            press_enter = args.get("press_enter", False)
            if "x" in args and "y" in args and args["x"] is not None and args["y"] is not None:
                px, py = _px(args["x"], args["y"], screen_w, screen_h)
                pyautogui.click(px, py, duration=0.15)
                pyautogui.hotkey("ctrl", "a")
                pyautogui.press("backspace")
            _type_text(text)
            if press_enter:
                pyautogui.press("enter")

        elif action == "drag_and_drop":
            sx, sy = _px(args.get("start_x", 0), args.get("start_y", 0), screen_w, screen_h)
            ex, ey = _px(args.get("end_x", 0), args.get("end_y", 0), screen_w, screen_h)
            pyautogui.moveTo(sx, sy, duration=0.15)
            pyautogui.mouseDown()
            pyautogui.moveTo(ex, ey, duration=0.15)
            pyautogui.mouseUp()

        elif action == "wait":
            seconds = float(args.get("seconds", 1))
            time.sleep(seconds)

        elif action == "press_key":
            k = _normalize_key(args.get("key", ""))
            pyautogui.press(k)

        elif action == "key_down":
            k = _normalize_key(args.get("key", ""))
            pyautogui.keyDown(k)

        elif action == "key_up":
            k = _normalize_key(args.get("key", ""))
            pyautogui.keyUp(k)

        elif action == "hotkey":
            keys = args.get("keys", [])
            if isinstance(keys, str):
                keys = [keys]
            normalized = [_normalize_key(k) for k in keys]
            pyautogui.hotkey(*normalized)

        elif action == "scroll":
            if "x" in args and "y" in args and args["x"] is not None and args["y"] is not None:
                px, py = _px(args["x"], args["y"], screen_w, screen_h)
                pyautogui.moveTo(px, py, duration=0.15)
            magnitude = int(args.get("magnitude_in_pixels", 300))
            clicks = max(1, magnitude // 40)
            direction = str(args.get("direction", "down")).lower().strip()
            if direction == "up":
                pyautogui.scroll(clicks)
            elif direction == "down":
                pyautogui.scroll(-clicks)
            elif direction == "right":
                pyautogui.hscroll(clicks)
            elif direction == "left":
                pyautogui.hscroll(-clicks)
            else:
                return {"error": f"unsupported scroll direction: {direction}"}

        elif action == "take_screenshot":
            # No-op, screenshot is taken by the agent loop between turns
            pass

        else:
            return {"error": f"unsupported action: {name}"}

        return {"ok": True}

    except Exception as e:
        return {"error": str(e)}
