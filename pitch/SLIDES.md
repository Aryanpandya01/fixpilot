# FixPilot — Pitch Deck (8–10 Slides)

## Slide 1: Problem
- **Headline:** Desktop Software Support Is Broken & Expensive.
- Retail software vendors (billing, ERP, accounting) spend 70%+ of support time on repetitive navigation questions: *"Where is the GST menu?", "How do I add a new item?"*
- Today's workflow: Customer calls → opens AnyDesk/TeamViewer → waits 30+ minutes for an agent → agent takes control and clicks the same 3 buttons.
- Costs vendors ₹30,000–50,000/month per support executive; frustrates busy shopkeepers.

## Slide 2: Solution
- **Headline:** FixPilot — AnyDesk, But The AI Fixes It.
- Instant, automated desktop troubleshooting with Computer Use AI.
- **Mode 1 (Personal Help):** Windows 11 assistance for everyday users ("Fix my missing WiFi icon", "Turn on dark mode").
- **Mode 2 (Business Support):** Instant 6-digit session code connecting vendor software directly to autonomous desktop resolution.

## Slide 3: How It Works
- **3 Simple Steps:**
  1. **Generate:** Support agent enters customer problem in Dashboard → gets 6-digit session code.
  2. **Consent & Connect:** Customer types code in FixPilot app → clicks "Accept".
  3. **Autonomous Execution:** FixPilot AI inspects screen, reads vendor Knowledge Base, clicks & types on screen, and confirms resolution live on support dashboard.

## Slide 4: Live Demo
- **On Stage Execution:**
  - Support Agent (Laptop B) generates code for: *"Customer wants to configure private domain email (Hostinger SMTP for aryan@projectw.in) and send a test mail"*.
  - Customer PC (Laptop A) accepts connection.
  - Watch FixPilot AI autonomously navigate BilliGo (`https://billigo.projectw.in/`), select Hostinger provider, fill port 465 and SSL/TLS encryption, enter mailbox credentials, test connection, save settings, send test email to `aryanpandya0505@gmail.com`, and report **"Solved ✅ in 0:48"**.

## Slide 5: Architecture & Google AI Stack
- **Gemini Computer Use:** Native multimodal desktop action grounding (0-999 normalized coordinates).
- **Primary Model:** Gemini 3.8 Flash for ultra-fast action latency (<1s per step).
- **Resilience Fallback:** Automatic failover to Gemini 4 Argon on complex states.
- **Knowledge Base RAG:** High-precision markdown domain grounding (`kb/billigo.md`).
- **Production Infrastructure:** Google Cloud Run, Cloud Firestore, Vertex AI Search.

## Slide 6: Safety & Trust by Design
- **Explicit Consent:** 6-digit ephemeral code + mandatory customer Accept dialog.
- **Human-in-the-Loop Modes:**
  - *Guide Mode:* AI highlights elements on screen; user performs clicks.
  - *Assist Mode:* Every action requires one-click user confirmation.
  - *Auto Mode:* Autonomous action within strict boundary constraints.
- **Emergency STOP:** Instant global kill switch (Ctrl+Shift+X or prominent UI button).
- **Strict Guardrails:** Never touches passwords, admin UAC popups, financial transactions, or system deletions.

## Slide 7: Business Model & Monetization
- **B2C (Personal):** 100% Free for individuals.
- **B2B SaaS (Software Vendors):**
  - **Starter:** ₹4,999 / month (300 automated fixes included).
  - **Growth:** ₹14,999 / month (1,500 automated fixes included).
  - **Overages:** ₹15 per automated fix (vs ₹150+ human cost).
  - **Enterprise Custom:** Dedicated on-premise knowledge models + private cloud.

## Slide 8: Competition & Moat
| Feature | AnyDesk / TeamViewer | Chatbots (ChatGPT) | Web WalkMe/Whatfix | **FixPilot** |
|---|---|---|---|---|
| Works on Windows Desktop Apps | ✅ | ❌ | ❌ | **✅** |
| Requires Zero Code Setup | ✅ | ✅ | ❌ (Weeks) | **✅ (Instant)** |
| Fully Autonomous Action | ❌ (Human required) | ❌ (Text only) | ❌ (Guided only) | **✅ (AI Solves It)** |
| Hinglish & Indian Context | ❌ | Partial | ❌ | **✅** |

## Slide 9: Traction & Pilot Partner
- **Live Pilot Partner:** **BilliGo** (`https://billigo.projectw.in/`) — Cloud ERP & GST billing platform by Aryan Pandya (Shiv Enterprise, Bhavnagar).
- **Validated High-Frequency Problem:** Shopkeepers struggle with complex setups like private domain SMTP (Hostinger/Gmail) for email invoicing, tying up support agents for 30–45 minutes over AnyDesk.
- **Immediate Value:** FixPilot slashes resolution time from 40 minutes to under 50 seconds.
- **Rollout:** Deploying pilot across 50 active retail businesses in Q1 2027.
- **Proof:** Active SaaS integration and vendor agreement.

## Slide 10: Team & Roadmap
- **Team:** Anas (Person A - AI Agent & Desktop Systems) & Partner (Person B - Cloud Architecture, Support Platform & Domain Knowledge).
- **Q1 2027:** Live pilots with billing vendors, Hindi/Gujarati voice interface.
- **Q2 2027:** Auto-learning knowledge engine (AI watches human solve once, compiles KB automatically).
