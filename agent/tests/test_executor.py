"""agent/tests/test_executor.py - Test executor with Notepad."""
import time
from agent.executor import run_action
from agent.screen import screen_size


def main():
    print("WARNING: Safe test starting in 3 seconds. Keep hands off mouse/keyboard.")
    for i in range(3, 0, -1):
        print(f"{i}...")
        time.sleep(1)

    screen_w, screen_h = screen_size()
    print(f"Detected screen size: {screen_w}x{screen_h}")

    steps = [
        ("move", {"x": 500, "y": 500}),
        ("press_key", {"key": "win"}),
        ("wait", {"seconds": 1}),
        ("type", {"text": "notepad"}),
        ("press_key", {"key": "Enter"}),
        ("wait", {"seconds": 2}),
        ("type", {"text": "FixPilot executor works ✅ ₹"}),
    ]

    for name, args in steps:
        res = run_action(name, args, screen_w, screen_h)
        print(f"Step {name}({args}) -> {res}")


if __name__ == "__main__":
    main()
