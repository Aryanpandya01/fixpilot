"""agent/screen.py - DPI-aware screen capture and sizing."""
import base64
import ctypes
import io

# Make process DPI-aware BEFORE importing mss or pyautogui
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def _attach_to_default_desktop():
    """Ensure current thread is attached to the interactive Default desktop."""
    try:
        user32 = ctypes.windll.user32
        hdesk = user32.OpenDesktopW("Default", 0, False, 0x10000000)
        if hdesk:
            user32.SetThreadDesktop(hdesk)
    except Exception:
        pass


_attach_to_default_desktop()

import mss
from PIL import Image


def screen_size() -> tuple[int, int]:
    """Return (width, height) of the primary monitor."""
    _attach_to_default_desktop()
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        return monitor["width"], monitor["height"]


def capture_jpeg(max_width: int = 1280, quality: int = 70) -> tuple[bytes, int, int]:
    """Like capture(), but returns a small JPEG (~100 KB instead of ~300 KB PNG).
    Smaller images make every Gemini call faster."""
    png, w, h = capture(max_width)
    img = Image.open(io.BytesIO(png)).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return buf.getvalue(), w, h


def capture(max_width: int = 1440) -> tuple[bytes, int, int]:
    """Grab the primary monitor, downscale proportionally if wider than max_width,
    and return (png_bytes, original_width, original_height)."""
    _attach_to_default_desktop()
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        sct_img = sct.grab(monitor)
        orig_w = monitor["width"]
        orig_h = monitor["height"]

        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

        if orig_w > max_width:
            new_w = max_width
            new_h = int(orig_h * (max_width / orig_w))
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue(), orig_w, orig_h


def to_b64(png_bytes: bytes) -> str:
    """Convert png bytes to base64 string."""
    return base64.b64encode(png_bytes).decode("utf-8")
