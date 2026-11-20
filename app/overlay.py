"""app/overlay.py - Guide-mode highlight.

A full-screen, transparent, always-on-top, click-through window that draws a pulsing ring
at (x, y) in physical screen pixels plus a short instruction label. The user can click straight through it.
Usage: python app/overlay.py <x> <y> "<text>"     (the panel server kills it when the step is done)
"""
import ctypes
import sys
import tkinter as tk

try:  # same pixel space as screen.py / pyautogui
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# Remember who has keyboard focus (e.g. the password box) so the overlay never takes it away.
PREV_FG = ctypes.windll.user32.GetForegroundWindow()
X, Y = int(sys.argv[1]), int(sys.argv[2])
TEXT = sys.argv[3] if len(sys.argv) > 3 else ""
KEY = "#010203"      # this color becomes fully transparent
RING = "#ff5a1f"

root = tk.Tk()
root.overrideredirect(True)
root.attributes("-topmost", True)
W, H = root.winfo_screenwidth(), root.winfo_screenheight()
root.geometry(f"{W}x{H}+0+0")
root.configure(bg=KEY)
root.attributes("-transparentcolor", KEY)

c = tk.Canvas(root, width=W, height=H, bg=KEY, highlightthickness=0)
c.pack()
outer = c.create_oval(0, 0, 0, 0, outline=RING, width=5)
inner = c.create_oval(X - 6, Y - 6, X + 6, Y + 6, fill=RING, outline=RING)

# Instruction label: to the right of the ring, flipped to the left near the screen edge.
if TEXT:
    lx = X + 48 if X < W - 460 else X - 48
    anchor = "w" if X < W - 460 else "e"
    ly = min(max(Y, 30), H - 30)
    t = c.create_text(lx, ly, text=TEXT, anchor=anchor, fill="white",
                      font=("Segoe UI", 15, "bold"), width=400)
    x1, y1, x2, y2 = c.bbox(t)
    bg = c.create_rectangle(x1 - 12, y1 - 8, x2 + 12, y2 + 8, fill="#14202e", outline=RING, width=2)
    c.tag_lower(bg, t)

r, grow = 26, 1


def pulse() -> None:
    global r, grow
    r += 1.2 * grow
    if r > 40 or r < 24:
        grow *= -1
    c.coords(outer, X - r, Y - r, X + r, Y + r)
    root.after(30, pulse)


def click_through() -> None:
    hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
    style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)        # GWL_EXSTYLE
    # WS_EX_LAYERED | WS_EX_TRANSPARENT (click-through) | WS_EX_NOACTIVATE (never takes keyboard focus)
    ctypes.windll.user32.SetWindowLongW(hwnd, -20, style | 0x80000 | 0x20 | 0x08000000)
    if PREV_FG and ctypes.windll.user32.GetForegroundWindow() == hwnd:
        ctypes.windll.user32.SetForegroundWindow(PREV_FG)  # give the keyboard back so typing goes into the field


root.after(10, click_through)
pulse()
root.after(10 * 60 * 1000, root.destroy)  # safety: never stay forever
root.mainloop()
