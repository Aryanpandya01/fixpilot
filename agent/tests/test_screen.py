"""agent/tests/test_screen.py - Test screen capture and downscaling."""
import io
import os
from PIL import Image
from agent.screen import capture


def main():
    os.makedirs("logs", exist_ok=True)
    png_bytes, orig_w, orig_h = capture(max_width=1440)
    img = Image.open(io.BytesIO(png_bytes))
    kb_size = len(png_bytes) / 1024

    output_path = os.path.join("logs", "test_screen.png")
    with open(output_path, "wb") as f:
        f.write(png_bytes)

    print(f"Original screen size: {orig_w}x{orig_h}")
    print(f"PNG size: {kb_size:.2f} KB")
    print(f"Downscaled image dimensions: {img.width}x{img.height}")
    print(f"Saved screenshot to: {output_path}")


if __name__ == "__main__":
    main()
