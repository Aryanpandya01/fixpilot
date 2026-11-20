"""agent/tests/test_gemini.py - Test Gemini Interactions API."""
import os
from dotenv import load_dotenv
from google import genai


def main():
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in environment or .env")
        return

    client = genai.Client(api_key=api_key)

    try:
        interaction = client.interactions.create(
            model="gemini-3.8-flash",
            input="Reply with exactly: FixPilot online",
        )

        print(f"type(interaction): {type(interaction)}")

        steps = getattr(interaction, "steps", None)
        if steps is not None:
            step_types = [getattr(s, "type", type(s).__name__) for s in steps]
            print(f"Step types: {step_types}")

            for s in steps:
                if hasattr(s, "text") and s.text:
                    print(s.text)
                elif hasattr(s, "content") and s.content:
                    if isinstance(s.content, list):
                        for item in s.content:
                            if hasattr(item, "text") and item.text:
                                print(item.text)
                            else:
                                print(item)
                    else:
                        print(s.content)
        else:
            print(f"Raw interaction: {interaction}")

    except Exception as e:
        print(f"Error calling Interactions API: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
