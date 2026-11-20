"""agent/tests/probe_cu.py - Probe Gemini Computer Use response shape."""
import os
from dotenv import load_dotenv
from google import genai
from agent.screen import capture, to_b64


def main():
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in environment or .env")
        return

    client = genai.Client(api_key=api_key)

    print("Capturing primary screen...")
    png_bytes, orig_w, orig_h = capture(max_width=1440)
    b64_img = to_b64(png_bytes)
    print(f"Captured screen: {orig_w}x{orig_h}, base64 len: {len(b64_img)}")

    print("Sending probe request to client.interactions.create with computer_use tool...")
    try:
        interaction = client.interactions.create(
            model="gemini-3.8-flash",
            system_instruction="You control a Windows desktop.",
            input=[
                {"type": "text", "text": "Click the Windows Start button."},
                {"type": "image", "data": b64_img, "mime_type": "image/png"},
            ],
            tools=[
                {
                    "type": "computer_use",
                    "environment": "desktop",
                    "enable_prompt_injection_detection": True,
                }
            ],
            automatic_continuation=False,
        )

        print("\n--- Interaction Summary ---")
        print("interaction.id:", getattr(interaction, "id", None))
        print("type(interaction):", type(interaction))

        steps = getattr(interaction, "steps", [])
        print(f"Total steps returned: {len(steps)}")

        for idx, step in enumerate(steps):
            print(f"\n--- Step {idx} ---")
            step_type = getattr(step, "type", None)
            print("step.type:", step_type)

            name = getattr(step, "name", None)
            step_id = getattr(step, "id", None)
            call_id = getattr(step, "call_id", None)
            arguments = getattr(step, "arguments", None)

            print("step.name:", name)
            print("step.id:", step_id)
            print("step.call_id:", call_id)
            print("step.arguments:", arguments)
            print("step attributes:", [a for a in dir(step) if not a.startswith("_")])
            print("repr(step):", repr(step))

    except Exception as e:
        print(f"Error in probe_cu: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
