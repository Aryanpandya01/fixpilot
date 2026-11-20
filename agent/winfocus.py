"""agent/winfocus.py - Bring a window opened by open_app / open_url / open_settings_page to the front.

Windows won't let a background process (our server) push a new window in front of the user's current one,
so launched apps opened BEHIND it and the model kept re-opening them (2026-11-20: Notepad opened 12 times).
"""
import ctypes
import time
from ctypes import wintypes

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.c_void_p]
user32.GetForegroundWindow.restype = wintypes.HWND
TERMINAL_CLASSES = {"CASCADIA_HOSTING_WINDOW_CLASS", "ConsoleWindowClass"}
BROWSER_CLASSES = {"Chrome_WidgetWin_1", "MozillaWindowClass"}
_SKIP_TITLES = ("FixPilot",)  # our own panel


def _title(hwnd) -> str:
    n = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(n + 1)
    user32.GetWindowTextW(hwnd, buf, n + 1)
    return buf.value


def _class(hwnd) -> str:
    buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buf, 256)
    return buf.value


def snapshot() -> dict[int, str]:
    """{hwnd: title} of every visible, titled top-level window."""
    wins: dict[int, str] = {}

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def cb(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            t = _title(hwnd)
            if t:
                wins[hwnd] = t
        return True

    user32.EnumWindows(cb, 0)
    return wins


def focus(hwnd) -> bool:
    """Restore and bring hwnd to the foreground, working around Windows' foreground lock."""
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
    fg = user32.GetForegroundWindow()
    fg_thread = user32.GetWindowThreadProcessId(fg, None)
    me = kernel32.GetCurrentThreadId()
    attached = bool(fg_thread and fg_thread != me and user32.AttachThreadInput(me, fg_thread, True))
    try:
        user32.BringWindowToTop(hwnd)
        user32.SetForegroundWindow(hwnd)
    finally:
        if attached:
            user32.AttachThreadInput(me, fg_thread, False)
    if user32.GetForegroundWindow() != hwnd:
        # Fallback: a synthetic Alt tap gives this process the right to set the foreground window.
        user32.keybd_event(0x12, 0, 0, 0)
        user32.keybd_event(0x12, 0, 2, 0)
        user32.SetForegroundWindow(hwnd)
    return user32.GetForegroundWindow() == hwnd


def bring_to_front(before: dict[int, str], hints: tuple[str, ...] = (), browser: bool = False,
                   timeout: float = 4.0) -> str | None:
    """Wait for the window a launch created (new, or an existing one whose title changed, e.g. a new browser tab)
    and focus it. `hints` are title words to match (e.g. "Notepad"); `browser` limits it to browser windows.
    If nothing new appears but a window matching `hints` already exists, focus that one.
    Returns the focused window's title, or None."""

    def ok(h: int, t: str) -> bool:
        if t.startswith(_SKIP_TITLES) or _class(h) in TERMINAL_CLASSES:
            return False
        if browser and _class(h) not in BROWSER_CLASSES:
            return False
        return not hints or any(k.lower() in t.lower() for k in hints)

    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(0.3)
        now = snapshot()
        new = [h for h, t in now.items() if (h not in before or before[h] != t) and ok(h, t)]
        if new:
            focus(new[0])
            return now[new[0]]
    if hints:  # e.g. the app was already open: focus the existing window
        for h, t in snapshot().items():
            if ok(h, t):
                focus(h)
                return t
    return None
