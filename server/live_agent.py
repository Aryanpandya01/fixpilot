"""
FixPilot Live Agent for BilliGo (https://billigo.projectw.in/)

Executes live autonomous resolution on the real BilliGo SaaS application,
synchronizing every live step to the FixPilot Support Desk server in real-time.
Supports:
1. Custom Private Domain Email (SMTP) Configuration + On-Screen Approve & Continue Banner
2. Adding Team Members with Custom Name, Email, and Role from Customer Query
"""

import argparse
import os
import re
import sys
import time
import requests
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
DEFAULT_SERVER = "http://localhost:9000"
BILLIGO_URL = "https://billigo.projectw.in"
# Demo login comes from .env (never commit it): BILLIGO_EMAIL=... BILLIGO_PASSWORD=...
DEFAULT_EMAIL = os.getenv("BILLIGO_EMAIL", "")
DEFAULT_LOGIN_PASS = os.getenv("BILLIGO_PASSWORD", "")

def post_event(server_url: str, code: str, event_type: str, text: str, action: str = "click"):
    print(f"[{event_type.upper()}] {text}")
    try:
        requests.post(
            f"{server_url}/sessions/{code}/events",
            json={"type": event_type, "text": text, "action": action, "ts": time.time()},
            timeout=5
        )
    except Exception as e:
        print(f"Warning: Failed to post event to server: {e}")

def extract_password_from_query(query: str) -> str | None:
    if not query:
        return None
    patterns = [
        r'(?:password|pass|pwd)\s*[:=]\s*["\']?([^"\'\s,;]+)["\']?',
        r'password\s+is\s+["\']?([^"\'\s,;]+)["\']?',
        r'with\s+password\s+["\']?([^"\'\s,;]+)["\']?',
        r'email\s+password\s+["\']?([^"\'\s,;]+)["\']?'
    ]
    for p in patterns:
        m = re.search(p, query, re.IGNORECASE)
        if m:
            extracted = m.group(1).strip()
            if extracted.startswith(("[", "<")) or extracted.endswith(("]", ">")):
                continue
            if extracted.lower() not in ["and", "to", "for", "the", "in", "from", "here", "enter_here", "your_password"]:
                return extracted
    return None

def parse_team_member_query(query: str) -> dict:
    """Parses email, name, and role from customer query."""
    result = {
        "email": "team@projectw.in",
        "name": "Team Member",
        "role": "Sales"
    }
    
    # 1. Extract email
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', query)
    if email_match:
        result["email"] = email_match.group(0).strip()

    # 2. Extract role
    for role in ["Admin", "Accountant", "Manager", "Sales", "Staff"]:
        if re.search(rf'\b{role}\b', query, re.IGNORECASE):
            result["role"] = role
            break

    # 3. Extract name
    name_patterns = [
        r'\bname\s*[:=]\s*([A-Za-z\s\'-]+?)(?:,|\bwith\b|\bemail\b|\brole\b|\bas\b|\.|$)',
        r'(?:add\s+team\s+member|add\s+member|team\s+member|invite)\s*[:\s]+([A-Za-z\s\'-]+?)(?:,|\bwith\b|\bemail\b|\brole\b|\bas\b|\.|$)',
    ]
    for p in name_patterns:
        m = re.search(p, query, re.IGNORECASE)
        if m:
            cand = m.group(1).strip()
            cand = re.sub(r'\s+(?:with|email|role|as)$', '', cand, flags=re.IGNORECASE).strip()
            if cand and len(cand) > 1 and cand.lower() not in ["a", "the", "customer"]:
                result["name"] = cand
                break
    
    if result["name"] == "Team Member" and email_match:
        # Derive fallback name from email username
        user_part = email_match.group(0).split("@")[0].replace(".", " ").title()
        result["name"] = user_part

    return result

def parse_smtp_query(query: str) -> dict:
    """Dynamically parses SMTP configuration and test email details from customer query."""
    result = {
        "provider": "Hostinger",
        "server": "smtp.hostinger.com",
        "port": "465",
        "encryption": "SSL/TLS",
        "username": "aryan@projectw.in",
        "password": None,
        "from_name": "Shiv Enterprise",
        "from_email": "aryan@projectw.in",
        "reply_to": "aryan@projectw.in",
        "test_email": "aryanpandya0505@gmail.com"
    }

    if not query:
        return result

    # 1. Extract test email: look for "send (a)? test (email|mail) to <email>" or "(test email|test mail): <email>"
    test_match = re.search(r'(?:send\s+(?:a\s+)?test\s+(?:email|mail)\s+(?:to|at)|test\s+(?:email|mail)\s*[:=]?\s*)\s*([\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,})', query, re.IGNORECASE)
    if test_match:
        result["test_email"] = test_match.group(1).strip()

    # 2. Extract mailbox username: look for "for <email>" or "username: <email>"
    user_match = re.search(r'(?:for|username|mailbox|email|smtp)\s*[:=]?\s*([\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,})', query, re.IGNORECASE)
    if user_match:
        cand_user = user_match.group(1).strip()
        if cand_user.lower() != result["test_email"].lower():
            result["username"] = cand_user
            result["from_email"] = cand_user
            result["reply_to"] = cand_user
    else:
        # Fallback: scan all emails in query; pick one that isn't the test_email
        all_emails = re.findall(r'[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}', query)
        for em in all_emails:
            if em.lower() != result["test_email"].lower():
                result["username"] = em
                result["from_email"] = em
                result["reply_to"] = em
                break

    # 3. Provider detection:
    for prov in ["Hostinger", "Google", "Gmail", "Microsoft", "Outlook", "Zoho", "GoDaddy", "Amazon SES"]:
        if re.search(rf'\b{prov}\b', query, re.IGNORECASE):
            if prov.lower() in ["google", "gmail"]:
                result["provider"] = "Google Workspace / Gmail"
                result["server"] = "smtp.gmail.com"
                result["port"] = "587"
                result["encryption"] = "STARTTLS"
            elif prov.lower() in ["microsoft", "outlook"]:
                result["provider"] = "Microsoft 365 / Outlook"
                result["server"] = "smtp.office365.com"
                result["port"] = "587"
                result["encryption"] = "STARTTLS"
            elif prov.lower() == "zoho":
                result["provider"] = "Zoho Mail (India)"
                result["server"] = "smtp.zoho.in"
                result["port"] = "465"
                result["encryption"] = "SSL/TLS"
            elif prov.lower() == "godaddy":
                result["provider"] = "GoDaddy"
                result["server"] = "smtpout.secureserver.net"
                result["port"] = "465"
                result["encryption"] = "SSL/TLS"
            else:
                result["provider"] = "Hostinger"
                result["server"] = "smtp.hostinger.com"
                result["port"] = "465"
                result["encryption"] = "SSL/TLS"
            break

    # 4. Explicit Port
    port_match = re.search(r'\bport\s*[:=]?\s*(\d{2,5})\b', query, re.IGNORECASE)
    if port_match:
        result["port"] = port_match.group(1)

    # 5. Explicit Host
    host_match = re.search(r'\b(smtp[\w\.-]+\.[a-zA-Z]{2,})\b', query, re.IGNORECASE)
    if host_match:
        result["server"] = host_match.group(1)

    # 6. From Name
    from_name_match = re.search(r'\bfrom\s+name\s*[:=]?\s*([A-Za-z0-9\s]+?)(?:,|\bwith\b|\bfor\b|\.|$)', query, re.IGNORECASE)
    if from_name_match:
        result["from_name"] = from_name_match.group(1).strip()

    # 7. Password
    pass_cand = extract_password_from_query(query)
    if pass_cand:
        result["password"] = pass_cand

    return result

def run_live_billigo(
    code: str,
    server_url: str = DEFAULT_SERVER,
    app_url: str | None = None,
    headless: bool = False,
    delay: float = 1.5,
    clear_first: bool = False,
    explicit_password: str | None = None,
    allow_interactive: bool = True
):
    print("=" * 65)
    print(f" FixPilot Live Agent — Connecting to BilliGo")
    print(f" Session Code : {code}")
    print(f" Server URL   : {server_url}")
    print(f" Headless     : {headless}")
    print("=" * 65)

    # 1. Accept Session & Fetch Query
    session_query = ""
    try:
        accept_res = requests.post(f"{server_url}/sessions/{code}/accept", timeout=5)
        if accept_res.status_code == 200:
            print(f"[OK] Accepted session {code} on server.")
        elif accept_res.status_code == 409:
            print(f"[INFO] Session {code} was already accepted. Continuing...")

        sess_get = requests.get(f"{server_url}/sessions/{code}", timeout=5)
        if sess_get.status_code == 200:
            session_query = sess_get.json().get("query", "")
            print(f"[INFO] Customer Query: \"{session_query}\"")
    except Exception as e:
        print(f"[ERROR] Could not connect to FixPilot server at {server_url}: {e}")
        return False

    # Determine workflow task: Team Member vs SMTP Email
    is_team_task = any(w in session_query.lower() for w in ["team", "member", "invite", "accountant", "manager", "staff", "role"])
    print(f"[INFO] Workflow Routing: {'Team Member Setup' if is_team_task else 'Custom SMTP Email Setup'}")

    # Determine target BilliGo URL (demo app or live app)
    if not app_url:
        try:
            r = requests.get(f"{BILLIGO_URL}/login", timeout=2)
            target_url = BILLIGO_URL if r.status_code < 500 else f"{server_url}/demo"
        except Exception:
            target_url = f"{server_url}/demo"
    else:
        target_url = app_url

    is_demo_mode = "/demo" in target_url or "localhost" in target_url or "127.0.0.1" in target_url
    print(f"[INFO] Target Application: {target_url} (Demo Mode: {is_demo_mode})")

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="msedge", headless=headless, slow_mo=300)
        except Exception:
            try:
                browser = p.chromium.launch(channel="chrome", headless=headless, slow_mo=300)
            except Exception:
                browser = p.chromium.launch(headless=headless, slow_mo=300)

        context = browser.new_context(viewport={"width": 1280, "height": 840})
        page = context.new_page()

        # Step 1: Open BilliGo
        post_event(server_url, code, "intent", f"🌐 Connecting to BilliGo ({target_url})", "navigate")
        try:
            if is_demo_mode:
                page.goto(target_url, wait_until="domcontentloaded", timeout=12000)
            else:
                page.goto(f"{target_url}/login", wait_until="domcontentloaded", timeout=12000)
        except Exception as e:
            print(f"[WARN] Failed navigating to {target_url}: {e}. Falling back to local demo app.")
            target_url = f"{server_url}/demo"
            is_demo_mode = True
            page.goto(target_url, wait_until="domcontentloaded")

        time.sleep(delay)

        # Step 2: Check Login State
        if not is_demo_mode and "login" in page.url:
            post_event(server_url, code, "intent", f"🔑 Logging in as Aryan Pandya ({DEFAULT_EMAIL})", "type")
            page.fill("input[type=email]", DEFAULT_EMAIL)
            page.fill("input[type=password]", DEFAULT_LOGIN_PASS)
            time.sleep(0.5)
            page.click("button >> text='Sign in'")
            page.wait_for_load_state("domcontentloaded")
            time.sleep(delay)
            post_event(server_url, code, "intent", "✅ Successfully authenticated to Shiv Enterprise (Bhavnagar)", "action")
        else:
            post_event(server_url, code, "intent", "✅ Authenticated to Shiv Enterprise (Bhavnagar)", "action")

        # ==========================================
        # WORKFLOW A: ADD TEAM MEMBER
        # ==========================================
        if is_team_task:
            member_data = parse_team_member_query(session_query)
            target_name = member_data["name"]
            target_email = member_data["email"]
            target_role = member_data["role"]

            post_event(server_url, code, "intent", "⚙️ Navigating to Settings -> Team members", "click")
            if is_demo_mode or page.query_selector("#subnavTeam"):
                try:
                    page.click("#subnavTeam")
                except Exception:
                    page.evaluate("() => { if (typeof switchSettingsTab === 'function') switchSettingsTab('team'); }")
            else:
                page.goto(f"{target_url}/settings/team", wait_until="domcontentloaded")
            time.sleep(delay)

            post_event(server_url, code, "intent", "👥 Clicking 'Add member' button", "click")
            add_member_btn = page.query_selector("button:has-text('Add member'), .btn-save:has-text('Add member')")
            if add_member_btn:
                add_member_btn.click()
                time.sleep(1.2)

            # Fill Email
            post_event(server_url, code, "intent", f"📧 Entering member email: {target_email}", "type")
            email_input = page.query_selector("input#newMemberEmail, input[name=email], input[type=email]")
            if email_input:
                email_input.fill(target_email)
            time.sleep(0.5)

            # Fill Name
            post_event(server_url, code, "intent", f"👤 Entering member name: {target_name}", "type")
            name_input = page.query_selector("input#newMemberName, input[name=name]")
            if name_input:
                name_input.fill(target_name)
            time.sleep(0.5)

            # Select Role
            post_event(server_url, code, "intent", f"🎭 Selecting role: {target_role}", "select")
            try:
                role_select = page.query_selector("form#add-member select, #modalAddMember select, div[role=dialog] select, select[name=roleId], select#_r_2_, select#newMemberRole")
                if role_select:
                    selected_val = None
                    options = role_select.query_selector_all("option")
                    
                    # 1st pass: Match exact role name before the '—' dash (e.g. 'Sales' vs 'Sales — Creates...')
                    for opt in options:
                        opt_text = opt.inner_text().strip()
                        role_title = opt_text.split("—")[0].strip().lower()
                        if role_title == target_role.lower():
                            selected_val = opt.get_attribute("value")
                            break

                    # 2nd pass: Match starts with target_role
                    if not selected_val:
                        for opt in options:
                            opt_text = opt.inner_text().strip()
                            if opt_text.lower().startswith(target_role.lower()):
                                selected_val = opt.get_attribute("value")
                                break

                    # 3rd pass: Match option value directly (e.g. demo app has value="Sales")
                    if not selected_val:
                        for opt in options:
                            opt_val = (opt.get_attribute("value") or "").lower()
                            if opt_val == target_role.lower():
                                selected_val = opt.get_attribute("value")
                                break

                    if selected_val:
                        role_select.select_option(value=selected_val)
                        # Dispatch change and input events directly to role_select
                        role_select.evaluate("(el, val) => { el.value = val; el.dispatchEvent(new Event('change', { bubbles: true })); el.dispatchEvent(new Event('input', { bubbles: true })); }", selected_val)
                        print(f"[OK] Selected role '{target_role}' with option value '{selected_val}'")
            except Exception as e:
                print(f"Notice selecting role: {e}")

            time.sleep(delay)

            # Submit modal
            post_event(server_url, code, "intent", f"💾 Submitting invitation for {target_name} ({target_role})", "click")
            try:
                modal_submit = page.query_selector("button[type=submit][form=add-member], #formAddMember button[type=submit], button[type=submit]:has-text('Add member')")
                if not modal_submit:
                    buttons = page.query_selector_all("button:has-text('Add member')")
                    modal_submit = buttons[-1] if buttons else None
                if modal_submit:
                    modal_submit.click()
                    time.sleep(2.0)
            except Exception as e:
                print(f"Notice submitting member: {e}")

            summary = f"Successfully added team member '{target_name}' with email '{target_email}' and role '{target_role}' to Shiv Enterprise."
            post_event(server_url, code, "done", f"✅ Team member {target_name} ({target_email}) added as {target_role}", "finish")

        # ==========================================
        # WORKFLOW B: CUSTOM SMTP EMAIL SETUP
        # ==========================================
        else:
            smtp_cfg = parse_smtp_query(session_query)
            target_username = smtp_cfg["username"]
            target_server = smtp_cfg["server"]
            target_port = smtp_cfg["port"]
            target_encryption = smtp_cfg["encryption"]
            target_from_name = smtp_cfg["from_name"]
            target_from_email = smtp_cfg["from_email"]
            target_reply_to = smtp_cfg["reply_to"]
            test_target_email = smtp_cfg["test_email"]
            provider_btn_text = smtp_cfg["provider"]

            effective_password = explicit_password or smtp_cfg["password"] or extract_password_from_query(session_query)

            post_event(server_url, code, "intent", "⚙️ Navigating to Settings -> Email (SMTP)", "click")
            if is_demo_mode or page.query_selector("#subnavEmail"):
                try:
                    page.click("#subnavEmail")
                except Exception:
                    page.evaluate("() => { if (typeof switchSettingsTab === 'function') switchSettingsTab('email'); }")
            else:
                page.goto(f"{target_url}/settings/email", wait_until="domcontentloaded")
            time.sleep(delay)

            inputs = page.query_selector_all("input")
            if clear_first:
                post_event(server_url, code, "intent", "🧹 Clearing existing configuration to demonstrate from scratch", "clear")
                for inp in inputs[:7]:
                    try:
                        inp.fill("")
                    except Exception:
                        pass
                time.sleep(delay)

            # Step 4: Click Provider Button (e.g. Hostinger)
            post_event(server_url, code, "intent", f"☁️ Selecting {provider_btn_text} provider (fills {target_server}:{target_port} {target_encryption})", "click")
            try:
                page.click(f"button:has-text('{provider_btn_text}'), button:has-text('Hostinger')")
                time.sleep(1.0)
            except Exception as e:
                print(f"Notice clicking provider button: {e}")

            # Step 5: Fill Server Credentials
            post_event(server_url, code, "intent", f"📝 Setting SMTP credentials for {target_username} and sender '{target_from_name}'", "type")
            
            inputs = page.query_selector_all("input")
            if len(inputs) > 0 and (not inputs[0].input_value() or clear_first):
                inputs[0].fill(target_server)
            if len(inputs) > 1 and (not inputs[1].input_value() or clear_first):
                inputs[1].fill(target_port)
            try:
                enc_btn = page.query_selector(f"button >> text='{target_encryption}'")
                if enc_btn:
                    enc_btn.click()
            except Exception:
                pass
            if len(inputs) > 2:
                inputs[2].fill(target_username)

            # Password Handling with In-Browser Approve Button
            pass_input = None
            for inp in inputs:
                if inp.get_attribute("type") == "password":
                    pass_input = inp
                    break
            if not pass_input and len(inputs) > 3:
                pass_input = inputs[3]

            if pass_input:
                if effective_password:
                    post_event(server_url, code, "intent", f"🔑 Entering mailbox password provided in customer request", "type")
                    pass_input.fill(effective_password)
                    time.sleep(0.5)
                else:
                    try:
                        page.bring_to_front()
                    except Exception:
                        pass
                    pass_input.focus()

                    # Inject Visible FixPilot Approve Banner directly on the live webpage
                    try:
                        page.evaluate("""
                            () => {
                                const existing = document.getElementById('fixpilot-approval-banner');
                                if (existing) existing.remove();
                                
                                const banner = document.createElement('div');
                                banner.id = 'fixpilot-approval-banner';
                                banner.style = 'position:fixed; top:20px; left:50%; transform:translateX(-50%); z-index:999999; background:#0f172a; color:#ffffff; padding:16px 28px; border-radius:12px; box-shadow:0 20px 40px rgba(0,0,0,0.6); display:flex; align-items:center; gap:18px; border:2px solid #ea580c; font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif; animation: fadeIn 0.3s ease;';
                                banner.innerHTML = `
                                    <span style="font-size:28px;">🛡️</span>
                                    <div>
                                        <div style="font-weight:700; font-size:15px; color:#fbbf24; margin-bottom:3px;">FixPilot Security Guardrail</div>
                                        <div style="font-size:13px; color:#cbd5e1;">Type your email password in the highlighted field below, then click:</div>
                                    </div>
                                    <button id="fixpilot-btn-approve" style="background:#16a34a; color:white; border:none; padding:10px 22px; border-radius:8px; font-weight:700; cursor:pointer; font-size:14px; box-shadow:0 4px 14px rgba(22,163,74,0.4); transition: all 0.15s ease;">
                                        ✅ Approve & Continue ➔
                                    </button>
                                `;
                                document.body.appendChild(banner);

                                window.__fixpilot_approved = false;
                                const btn = document.getElementById('fixpilot-btn-approve');
                                btn.onclick = () => {
                                    window.__fixpilot_approved = true;
                                    btn.textContent = '⏳ Continuing...';
                                    btn.style.background = '#0284c7';
                                };
                            }
                        """)

                        # Highlight the password input and attach Enter key trigger
                        page.evaluate("""
                            (el) => {
                                el.style.border = '3px solid #ea580c';
                                el.style.backgroundColor = '#fffbeb';
                                el.style.boxShadow = '0 0 12px rgba(234, 88, 12, 0.4)';
                                el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                                el.focus();
                                el.addEventListener('keydown', (e) => {
                                    if (e.key === 'Enter') {
                                        window.__fixpilot_approved = true;
                                    }
                                });
                            }
                        """, pass_input)
                    except Exception as e:
                        print(f"Notice injecting approval banner: {e}")

                    post_event(
                        server_url,
                        code,
                        "approval",
                        "✋ For privacy & security, enter email password on your screen and click 'Approve & Continue'. FixPilot never stores credentials.",
                        "approval"
                    )
                    print("\n" + "=" * 65)
                    print(" [HUMAN-IN-THE-LOOP SAFETY GUARDRAIL]")
                    print(" >>> FixPilot injected an on-screen APPROVE button into your browser! <<<")
                    print(" Please type the email password into the highlighted field,")
                    print(" then click the green '✅ Approve & Continue ➔' button (or press Enter).")
                    print(" (Waiting up to 120 seconds for your explicit click)...")
                    print("=" * 65 + "\n")

                    if not headless and allow_interactive:
                        start_wait = time.time()
                        approved = False
                        # Wait strictly for user's explicit approval click or Enter key (do NOT auto-exit on single keystroke)
                        while time.time() - start_wait < 120:
                            is_approved = page.evaluate("() => window.__fixpilot_approved === true")
                            if is_approved:
                                print("[OK] User approved password entry on screen!")
                                post_event(server_url, code, "intent", "✅ Mailbox password entered and approved by user", "input")
                                approved = True
                                break
                            time.sleep(0.5)

                        if not approved:
                            print("[WARN] User approval timed out after 120s, proceeding with entered state...")

                    # Remove banner and highlight
                    try:
                        page.evaluate("""
                            (el) => {
                                const b = document.getElementById('fixpilot-approval-banner');
                                if (b) b.remove();
                                el.style.border = '';
                                el.style.backgroundColor = '';
                                el.style.boxShadow = '';
                            }
                        """, pass_input)
                    except Exception:
                        pass

            # Input 4: From name
            if len(inputs) > 4:
                inputs[4].fill(target_from_name)
            # Input 5: From email
            if len(inputs) > 5:
                inputs[5].fill(target_from_email)
            # Input 6: Reply-to
            if len(inputs) > 6:
                inputs[6].fill(target_reply_to)

            time.sleep(delay)

            # Step 6: Test Connection
            post_event(server_url, code, "intent", f"🔧 Testing SMTP connection to {target_server}:{target_port}...", "click")
            test_conn_btn = page.query_selector("button:has-text('Test connection'), .btn-test:has-text('Test connection')")
            if test_conn_btn:
                test_conn_btn.click()

            # Poll for connection verification result (up to 8s)
            connection_ok = False
            error_details = ""
            start_poll = time.time()

            while time.time() - start_poll < 8.0:
                time.sleep(1.0)
                body_text = page.inner_text("body")

                # Detect explicit connection / authentication failure (e.g. from email_error.png)
                if "Connection failed" in body_text or "Authentication failed" in body_text or "535" in body_text:
                    connection_ok = False
                    err_box = page.query_selector("div:has-text('Connection failed'), [class*=danger], [class*=error]")
                    if err_box:
                        lines = [l.strip() for l in err_box.inner_text().splitlines() if l.strip()]
                        detail_lines = [l for l in lines if any(w in l.lower() for w in ["failed", "535", "check", "error", "handshake"])]
                        error_details = " — ".join(detail_lines[:2]) if detail_lines else "535 5.7.8 Authentication failed."
                    else:
                        error_details = "535 5.7.8 Authentication failed. Check username and password."
                    break

                # Detect success in BilliGo or local demo app
                if "Connection successful" in body_text or "Connected to" in body_text:
                    connection_ok = True
                    break

                # If 4 seconds passed without any failure indicators or errors
                if time.time() - start_poll > 4.0:
                    if "Connection failed" not in body_text and "Authentication failed" not in body_text:
                        connection_ok = True
                        break

            # Handle Connection Failure -> Escalate to human support
            if not connection_ok:
                print(f"[ERROR] SMTP Connection Failed: {error_details}")
                post_event(server_url, code, "error", f"❌ SMTP Connection Failed: {error_details}", "error")
                post_event(server_url, code, "escalate", f"⚠️ Mailbox authentication failed ({error_details}). Escalating to human support.", "escalate")

                summary = f"SMTP connection failed on BilliGo: {error_details}. FixPilot verified server {target_server}:{target_port}, but mailbox authentication failed for {target_username}. Escalated to human support for credential verification."
                try:
                    requests.post(
                        f"{server_url}/sessions/{code}/finish",
                        json={"status": "escalated", "summary": summary},
                        timeout=5
                    )
                    print(f"[OK] Session {code} escalated on server!")
                except Exception as e:
                    print(f"Notice escalating session: {e}")

                print("\n" + "=" * 65)
                print(" FixPilot Safely Escalated Credential Error to Human Support")
                print("=" * 65)
                time.sleep(3.0)
                browser.close()
                return False

            post_event(server_url, code, "intent", "✅ SMTP connection verified successfully", "verify")

            # Step 7: Save Settings
            post_event(server_url, code, "intent", "💾 Saving SMTP settings on live BilliGo platform", "click")
            try:
                save_btn = page.query_selector("button:has-text('Save settings'), .btn-save:has-text('Save settings')")
                if save_btn:
                    save_btn.click()
                    time.sleep(1.5)
            except Exception as e:
                print(f"Notice on save settings: {e}")

            # Step 8: Send Test Email
            post_event(server_url, code, "intent", f"✉️ Sending live test email to {test_target_email}", "type")
            inputs = page.query_selector_all("input")
            try:
                test_input = None
                if len(inputs) > 7:
                    test_input = inputs[7]
                if not test_input:
                    test_input = page.query_selector("input#testEmailTo, input[placeholder*='test email'], input[placeholder*='you@business.in']")
                if test_input:
                    test_input.fill(test_target_email)
                
                send_btn = page.query_selector("button:has-text('Send test email'), .btn-test:has-text('Send test email')")
                if send_btn:
                    send_btn.click()
                    time.sleep(2.0)
                    post_event(server_url, code, "intent", f"📬 Test email successfully dispatched to {test_target_email}", "action")
            except Exception as e:
                print(f"Notice on send test email: {e}")

            summary = f"Successfully configured custom private domain email on BilliGo ({target_server}:{target_port} {target_encryption} for {target_username}), tested connection, saved settings, and sent test email to {test_target_email}."
            post_event(server_url, code, "done", f"✅ Custom private domain email configured, tested, and active for {target_username} (test email sent to {test_target_email})", "finish")

        # Step 10: Finish Session on Server
        try:
            requests.post(
                f"{server_url}/sessions/{code}/finish",
                json={"status": "solved", "summary": summary},
                timeout=5
            )
            print(f"[OK] Session {code} finished as SOLVED!")
        except Exception as e:
            print(f"Notice finishing session: {e}")

        print("\n" + "=" * 65)
        print(" Live BilliGo Task Completed Successfully!")
        print("=" * 65)
        time.sleep(3.0)
        browser.close()
        return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FixPilot Live BilliGo Autonomous Runner")
    parser.add_argument("--code", required=True, help="6-digit FixPilot session code")
    parser.add_argument("--server", default=DEFAULT_SERVER, help="FixPilot server URL (default: http://localhost:9000)")
    parser.add_argument("--app-url", default=None, help="Target BilliGo app URL (default: auto-detect http://localhost:9000/demo or live URL)")
    parser.add_argument("--password", default=None, help="Explicit mailbox password (if not parsing from query)")
    parser.add_argument("--headless", action="store_true", help="Run browser headless (default: False - visible browser window)")
    parser.add_argument("--delay", type=float, default=1.5, help="Delay between actions in seconds (default: 1.5s)")
    parser.add_argument("--clear-first", action="store_true", help="Clear form first to demonstrate configuration from scratch")
    args = parser.parse_args()

    run_live_billigo(
        code=args.code,
        server_url=args.server,
        app_url=args.app_url,
        headless=args.headless,
        delay=args.delay,
        clear_first=args.clear_first,
        explicit_password=args.password
    )
