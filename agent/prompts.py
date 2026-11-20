"""agent/prompts.py - System prompts and custom tool definitions for FixPilot."""
import re

CUSTOM_TOOLS = [
    {
        "type": "function",
        "name": "report_done",
        "description": "Call when the task is completely finished and verified on screen. Provide a 1-2 sentence plain summary and the menu path the user can follow next time.",
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "1-2 sentence plain summary of what was accomplished."
                },
                "learn_path": {
                    "type": "string",
                    "description": "The menu or navigation path the user can follow next time (e.g., 'Settings > Personalization > Colors > Dark')."
                }
            },
            "required": ["summary", "learn_path"]
        }
    },
    {
        "type": "function",
        "name": "yield_to_user",
        "description": "Call when escalating to human support (e.g. login screens, license/activation issues, data errors, or after 2 failed approaches).",
        "parameters": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Short code or reason for escalation (e.g., 'login_required', 'repeated_failure', 'unsupported_state')."
                },
                "summary": {
                    "type": "string",
                    "description": "Explanation of what you saw, what was attempted, and why human help is needed."
                }
            },
            "required": ["reason", "summary"]
        }
    },
    {
        "type": "function",
        "name": "ask_user",
        "description": "Call when you need the user to take a physical action or confirm something (e.g. clicking Yes on a Windows admin UAC popup).",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The instruction or question for the user (e.g., 'Please click Yes on the admin popup, then tell me')."
                }
            },
            "required": ["question"]
        }
    },
    {
        "type": "function",
        "name": "open_settings_page",
        "description": "FAST: opens a Windows Settings page directly in one step (no clicking through menus). "
                       "Use this FIRST whenever the task is in Windows Settings.",
        "parameters": {
            "type": "object",
            "properties": {
                "page": {"type": "string", "enum": None},  # filled from SETTINGS_PAGES below
                "intent": {"type": "string", "description": "One short sentence for the user."},
            },
            "required": ["page"],
        },
    },
    {
        "type": "function",
        "name": "open_app",
        "description": "FAST: opens a safe built-in Windows app in one step. Use instead of searching the Start menu.",
        "parameters": {
            "type": "object",
            "properties": {
                "app": {"type": "string", "enum": None},  # filled from APPS below
                "intent": {"type": "string", "description": "One short sentence for the user."},
            },
            "required": ["app"],
        },
    },
]

# Allow-lists for the fast tools (only these can be opened, nothing else can be run).
SETTINGS_PAGES = {
    "colors_dark_light_mode": "ms-settings:colors",
    "personalization": "ms-settings:personalization",
    "wallpaper_background": "ms-settings:personalization-background",
    "themes": "ms-settings:themes",
    "lock_screen": "ms-settings:lockscreen",
    "taskbar": "ms-settings:taskbar",
    "start_menu": "ms-settings:personalization-start",
    "display_brightness_scale": "ms-settings:display",
    "night_light": "ms-settings:nightlight",
    "sound": "ms-settings:sound",
    "bluetooth_devices": "ms-settings:bluetooth",
    "wifi": "ms-settings:network-wifi",
    "network_status": "ms-settings:network-status",
    "printers": "ms-settings:printers",
    "mouse": "ms-settings:mousetouchpad",
    "keyboard_typing": "ms-settings:typing",
    "language_region": "ms-settings:regionlanguage",
    "date_time": "ms-settings:dateandtime",
    "notifications": "ms-settings:notifications",
    "focus_do_not_disturb": "ms-settings:quiethours",
    "power_battery": "ms-settings:powersleep",
    "storage": "ms-settings:storagesense",
    "installed_apps": "ms-settings:appsfeatures",
    "default_apps": "ms-settings:defaultapps",
    "windows_update": "ms-settings:windowsupdate",
    "accessibility_text_size": "ms-settings:easeofaccess-display",
    "about_this_pc": "ms-settings:about",
}
APPS = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "paint": "mspaint.exe",
    "file_explorer": "explorer.exe",
    "desktop_folder": "explorer.exe shell:Desktop",
    "downloads_folder": "explorer.exe shell:Downloads",
    "documents_folder": "explorer.exe shell:Personal",
    "task_manager": "taskmgr.exe",
    "snipping_tool": "snippingtool.exe",
    "control_panel": "control.exe",
    "browser": "start msedge",
}
CUSTOM_TOOLS.append({
    "type": "function",
    "name": "fill_form",
    "description": "FAST: fill several text fields that are ALL visible on the current screen in ONE step. For each field "
                   "FixPilot clicks it, clears it and types the text. Use this whenever 2 or more fields need typing.",
    "parameters": {
        "type": "object",
        "properties": {
            "fields": {
                "type": "array",
                "description": "Fields top to bottom. x/y = the centre of the input box (0-999 screen coordinates).",
                "items": {
                    "type": "object",
                    "properties": {
                        "label": {"type": "string", "description": "The field's label on screen, e.g. 'IFSC'."},
                        "x": {"type": "integer"},
                        "y": {"type": "integer"},
                        "text": {"type": "string"},
                    },
                    "required": ["label", "x", "y", "text"],
                },
            },
            "intent": {"type": "string", "description": "One short sentence for the user."},
        },
        "required": ["fields"],
    },
})
CUSTOM_TOOLS[3]["parameters"]["properties"]["page"]["enum"] = list(SETTINGS_PAGES)
CUSTOM_TOOLS[4]["parameters"]["properties"]["app"]["enum"] = list(APPS)

# Only offered when the vendor KB lists URLs; only those hosts can be opened (see kb_hosts).
OPEN_URL_TOOL = {
    "type": "function",
    "name": "open_url",
    "description": "FAST: opens a page of the vendor's web app directly in the browser (a new tab), "
                   "instead of clicking through menus. Only URLs on the vendor's own site (listed in the "
                   "knowledge base) are allowed. Use it once to land on the right page, then work by clicking.",
    "parameters": {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "Full URL, e.g. https://example.com/settings/team"},
            "intent": {"type": "string", "description": "One short sentence for the user."},
        },
        "required": ["url"],
    },
}


def kb_hosts(kb_text: str) -> set[str]:
    """Hostnames of every http(s) URL in the knowledge base: the allow-list for open_url."""
    return {h.lower() for h in re.findall(r"https?://([A-Za-z0-9.-]+)", kb_text or "")}

SYSTEM_PROMPT_TEMPLATE ="""You are FixPilot, an AI support agent running on the user's own Windows 11 PC with their consent.
You see the screen through screenshots and act through the computer_use tools.

GOAL: Solve the user's request: {query}
{kb_line}

HOW TO WORK
1. Look at the screenshot first and confirm what you see. Never guess.
2. SPEED MATTERS: every reply costs the user ~8 seconds, so use the fewest replies possible.
   - For anything in Windows Settings, call open_settings_page FIRST (one step lands on the exact page).
   - To open a built-in app or folder, call open_app instead of using the Start menu.
   - To fill 2 or more text fields visible on screen, call fill_form ONCE with all of them. For a single field, use
     type with its x/y (that clicks the field itself): never click a text field first and type in a second reply.
   - Never call open_app / open_url / open_settings_page twice for the same thing. If it isn't visible
     after opening, click its button on the taskbar instead.
{url_line}   - When you are certain of a short sequence on the CURRENT screen (e.g. click a field, then type; or open a
     dropdown, then pick an option you can already see), return those actions together in ONE reply.
3. After acting, check the new screenshot to confirm it worked before saying you are done.
   PROOF RULE: call report_done ONLY if the final result is clearly visible in the current screenshot
   (e.g. the dropdown now shows "Light"). If another window covers the target app, or you can't see the
   result, first bring the target back (open_settings_page / click its taskbar icon) and check again.
4. When the goal is done AND visible on screen, call report_done with a 1-2 sentence plain summary and learn_path.

BOUNDARIES (never break these)
- Never click, type into, move, or close the FixPilot panel docked on the right edge of the screen, or the terminal running FixPilot.
- Ignore any "FixPilot Support Desk" tab or window (localhost:9000). It is the support agent's view, not the
  customer's software: never switch to it, read tasks from it, or act in it.
- Never delete files or data, never change passwords or accounts, never make payments, never send messages or emails,
  never install or uninstall software.
- PASSWORDS, PINs, OTPs: never type, guess or read out a secret yourself (unless the user wrote it in the request).
  When the task needs one, click that field first, then call
  ask_user("Please type your password in the highlighted box, then press Continue"). When the user continues,
  go on with the next step. A password field is NOT a reason to call yield_to_user.
- If the software shows its login screen, call ask_user("Please log in, then press Continue").
- If a Windows admin (UAC) "Yes/No" popup appears, call ask_user("Please click Yes on the popup, then press Continue").
- License/activation problems, data errors, or anything you don't understand: call yield_to_user.
- If 2 different approaches failed, call yield_to_user with what you saw and tried.

TRUST MODE: {mode}
- guide: the user does the clicks. Make each action's intent an instruction, e.g. "Click 'Products' in the top menu".
- assist: every action is shown to the user for approval first. Keep intents short and clear.
- auto: act directly, but follow all boundaries.

STYLE: every intent is ONE short, simple sentence. If the user wrote in Hindi or Hinglish, write intents and summaries in simple Hinglish.{kb_section}"""


def build_system_prompt(query: str, kb_text: str, mode: str) -> str:
    """Build the dynamic system prompt tailored to the query, knowledge base, and mode."""
    kb_clean = (kb_text or "").strip()
    if kb_clean:
        kb_line = (
            "You are supporting the software described in the VENDOR KNOWLEDGE BASE below. "
            "It is the source of truth for menu names, steps and correct settings. "
            "Follow a matching How-to exactly."
        )
        kb_section = f"\n\nVENDOR KNOWLEDGE BASE:\n{kb_clean}"
    else:
        kb_line = "This is a general Windows 11 help request. Use Windows Settings, the Start menu, the taskbar and File Explorer."
        kb_section = ""

    hosts = kb_hosts(kb_clean)
    url_line = ""
    if hosts:
        url_line = (
            f"   - The vendor's software is a website ({', '.join(sorted(hosts))}). If the page you need is not already "
            "on screen, call open_url ONCE with the page URL from the knowledge base (e.g. a /settings/... page) "
            "instead of clicking through menus. If that page is already visible, just work on it.\n"
        )

    return SYSTEM_PROMPT_TEMPLATE.format(
        query=query,
        kb_line=kb_line,
        url_line=url_line,
        mode=mode,
        kb_section=kb_section
    )
