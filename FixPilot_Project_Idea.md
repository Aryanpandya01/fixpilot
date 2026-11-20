# FixPilot

**The AI support agent that fixes software issues directly on your customer's screen.**

Startup Buildathon India 2026 · Founder: Anas Pathan · Built with Gemini & Google Cloud

---

## One-line summary

FixPilot is an AI support agent that learns a software company's product and fixes customer issues directly on the customer's screen, by voice or chat, replacing slow manual AnyDesk support with instant, 24/7 resolution.

---

## Problem

Software companies, especially Indian SMB software vendors selling POS, billing, GST/accounting, ERP and inventory tools, still handle most customer issues through manual remote sessions:

1. The customer reports a problem.
2. They wait for a support agent to be free.
3. The agent connects over AnyDesk or TeamViewer and fixes it by hand.

Most of these issues repeat: wrong settings, printer setup, GST configuration, sync errors and login problems. This creates four problems:

| Problem | Impact |
|---|---|
| **Long waits** | Customers wait hours while their shop or restaurant is stalled. |
| **High support cost** | Vendors keep hiring agents to fix the same problems again and again. |
| **Doesn't scale** | Support capacity grows only with headcount. No fixes after hours or on weekends. |
| **Lost knowledge** | Fixes stay in individual agents' heads and are never reused. |

---

## Solution

FixPilot is an AI agent that each software vendor trains on its own product. When a customer hits a problem, FixPilot sees their screen, diagnoses the issue, and fixes it.

### How it works

1. **Train:** The vendor uploads product docs, past support tickets and known fixes.
2. **Ask:** The customer opens the FixPilot desktop app and describes the issue by voice or chat.
3. **See:** FixPilot reads the screen and diagnoses the issue using the vendor's product knowledge.
4. **Fix:** It resolves the issue in one of three trust modes, or hands off to a human.
5. **Learn:** Every resolved issue is added back to the knowledge base, so FixPilot keeps getting better.

### Trust modes

| Mode | What FixPilot does |
|---|---|
| **Guide** | Highlights the exact buttons and steps on screen for the customer to follow. |
| **Assist** | Performs the fix, asking the customer's approval before each step. |
| **Auto** | Fixes known, safe issues on its own, 24/7. |

If FixPilot isn't confident, it escalates to the vendor's human support team with full context: a summary, screenshots and the steps already tried.

### Safe by design

- Acts only with the customer's consent
- Can be limited to the vendor's app window
- Visible "AI in control" overlay with a one-click stop
- Every session recorded for audit

### Impact

- Issues fixed in minutes instead of hours
- Support available 24/7
- Target of 50–70% fewer manual remote sessions for vendors

---

## Target customers

**Business model type:** B2B (B2B2C in practice)

- **Paying customers:** Software vendors and SaaS companies, starting with Indian SMB software providers (POS, billing, GST/accounting, ERP, inventory) handling 10–200 support tickets a day through AnyDesk or TeamViewer.
- **End users:** The vendors' customers, such as shop owners, restaurant staff and small-business operators, who aren't tech-savvy and need their software problems fixed fast.

### Target markets

| Priority | Market |
|---|---|
| **Primary** | India, starting with SMB software vendors in Gujarat |
| **Secondary** | Southeast Asia (Indonesia, Vietnam, Philippines) and the Middle East (UAE, Saudi Arabia) |
| **Later** | US and UK SaaS markets, where support labour costs are high |

---

## Solution architecture

```
Customer PC                      Google Cloud
┌──────────────────┐     ┌──────────────────────┐     ┌─────────────────────────┐
│  Desktop Agent   │ ──► │  Agent Orchestrator  │ ──► │      AI Layer           │
│  (Electron)      │     │  (Cloud Run)         │     │  Gemini Computer Use    │
│  screen capture  │ ◄── │  agent loop          │ ◄── │  Gemini Live (voice)    │
│  voice / chat    │     │  trust modes         │     │  Gemini 4 Argon         │
│  mouse/keyboard  │     │  safety rules        │     │                         │
│  consent + stop  │     │  sessions            │     │                         │
└──────────────────┘     └──────────┬───────────┘     └─────────────────────────┘
                                    │
        ┌───────────────────┬───────┴──────────┬────────────────────┐
        ▼                   ▼                  ▼                    ▼
┌───────────────┐  ┌────────────────┐  ┌─────────────────┐  ┌────────────────┐
│ Knowledge/RAG │  │ Data           │  │ Vendor          │  │ Human Handoff  │
│ Gemini        │  │ Firestore      │  │ Dashboard       │  │ escalation to  │
│ Embedding +   │  │ Cloud Storage  │  │ (Firebase)      │  │ vendor agents  │
│ Vector Search │  │ (recordings)   │  │                 │  │ with context   │
└───────────────┘  └────────────────┘  └─────────────────┘  └────────────────┘
```

### Components

1. **Desktop agent** (Electron, Windows): captures the screen, takes voice/chat input, carries out mouse and keyboard actions, and shows the consent and stop controls.
2. **Agent orchestrator** (Cloud Run): runs the screenshot → reason → act loop, applies the trust mode and safety rules, and manages sessions.
3. **AI layer:**
   - Gemini with Computer Use: understands the screen and decides on UI actions
   - Gemini Live: real-time voice conversation with the customer
   - RAG knowledge base: vendor docs and tickets turned into Gemini embeddings, stored in Vertex AI Vector Search
4. **Data layer:** Firestore for sessions, tickets and audit logs. Cloud Storage for session recordings.
5. **Vendor dashboard** (Firebase): upload docs, set trust modes and allowed actions, view analytics, take over escalated sessions.
6. **Human handoff:** escalates to the vendor's support team with the full session context.

### Flow

Customer asks → agent captures the screen → orchestrator retrieves product knowledge (RAG) → Gemini decides the action → agent performs it with consent → issue resolved or handed to a human → fix saved back to the knowledge base.

---

## Google AI stack

### Models

| Model | Role |
|---|---|
| **Gemini 3.8 Flash + Computer Use** | Core engine. Reads the customer's screen, understands the software UI, and performs the fix (clicks, typing, settings). Fast and low-cost, so most sessions run here. |
| **Gemini 4 Argon** | Complex multi-step diagnosis when Flash's confidence is low. Routed only when needed to keep the cost per fix low. |
| **Gemini 3.1 Flash Live** | Real-time voice conversation, so non-technical users can simply say what's wrong. Hindi and Gujarati planned. |
| **Gemini Embedding** | Turns vendor docs, past tickets and known fixes into a searchable RAG index, so every fix is grounded in the vendor's own product. |

### Tools

| Tool | How it's used |
|---|---|
| **Google AI Studio** | Prototyping and testing prompts, Computer Use flows on real POS/billing screens, and model settings. |
| **Google Antigravity** | Main development environment for the desktop agent, Cloud Run orchestrator and vendor dashboard. |
| **Google Agent Skills** | Packaging each vendor's fix procedures as reusable skills the agent loads only when needed. Every resolved issue can become a new skill. |

### Google Cloud services

Cloud Run, Vertex AI (Gemini API + Vector Search), Firestore, Cloud Storage, Firebase Hosting and Auth, Pub/Sub, Cloud Logging and Monitoring.

---

## Deployment & scaling

**Deployment**
- **Cloud Run** hosts the orchestrator and APIs as serverless containers, scaling with live sessions and down to zero when idle.
- **Gemini API on Vertex AI** provides model calls with enterprise security and data residency in an India region.
- **Vertex AI Vector Search** stores each vendor's knowledge base, kept separate per vendor (multi-tenant).
- **Firestore** holds sessions, tickets and audit logs. **Cloud Storage** keeps recordings with lifecycle rules.
- **Firebase Hosting + Auth** serves the vendor dashboard.
- **Pub/Sub** queues escalation and handoff events. **Cloud Logging and Monitoring** track uptime, latency and resolution rates.

**Scaling**
- Model routing sends most sessions to low-cost Gemini Flash and only complex ones to Gemini Argon.
- The stateless orchestrator scales horizontally from pilot vendors to thousands of concurrent sessions.
- Self-serve vendor onboarding: upload docs, auto-index, go live.
- New markets get regional Google Cloud deployments for low latency and local data rules.
- Enterprise customers get a dedicated private deployment.

---

## Business model

B2B SaaS subscription for software vendors, priced on issues actually fixed.

| Plan | Price | Includes |
|---|---|---|
| **Starter** | ₹4,999 / month | Up to 300 AI-resolved sessions |
| **Growth** | ₹14,999 / month | Up to 1,500 sessions, voice support, analytics |
| **Enterprise** | Custom | Private deployment, SLAs, custom integrations |

- **Overage:** ₹15–25 per extra AI-fixed issue, compared with an estimated ₹150–300 in agent time for a manual AnyDesk session.
- **Additional revenue:** one-time onboarding fees for training the AI on a vendor's product, and a white-label plan so vendors can offer AI support under their own brand.

---

## Competition

| | Acts on the screen | Knows the product | Fixes with no human |
|---|---|---|---|
| **AnyDesk, TeamViewer, Zoho Assist, ScreenMeet** | Yes, by a human | No | No |
| **Intercom Fin, Zendesk AI, eesel AI** | No | Yes | Text answers only |
| **FixPilot** | **Yes, by AI** | **Yes** | **Yes, with consent** |

**Our edge:** Remote tools need a human to fix every issue, and AI chatbots can only answer questions. FixPilot combines both: an AI that knows the vendor's product and acts on the customer's real screen. It's built for Indian SMB software, voice-first for non-technical users, and priced per fix.

---

## Roadmap

| Timeline | Milestone |
|---|---|
| **Nov 2026** | Working MVP at the Startup Buildathon |
| **Q1 2027** | Pilots with 3 POS/billing vendors in Gujarat |
| **Q2 2027** | Hindi and Gujarati voice support, vendor dashboard v1 |
| **H2 2027** | Scale across India, enter Southeast Asia and the Middle East |

---

## Founder

**Anas Pathan**, Founder & AI Engineer

- AI/LLM developer at ProjectW, building client solutions with LangChain, LangGraph, RAG pipelines, n8n automation and AI agents
- Former data analyst intern at First Quadrant Labs (London, remote): built an ML model with 96% accuracy on collision-severity prediction
- Shipped SmokeWatcher, a published Android app (Flutter + Firebase) on Google Play
- Won ₹1.5 lakh in SSIP government startup funding and a first-place startup award
