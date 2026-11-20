I'm pitching my startup FixPilot at a Google startup buildathon in India (judges: startup mentors + Google engineers, 3-minute pitch + live demo). Please make me a polished **10-slide PowerPoint (.pptx)** I can download and present, with speaker notes on every slide.

## What FixPilot is
FixPilot is "AnyDesk, but the AI does the fixing." Today, when a shop owner has a problem with their billing/POS/GST software, they call support and wait hours until a human connects over AnyDesk and clicks around for 10 minutes. With FixPilot, the customer types or says the problem, and an AI (Gemini Computer Use) looks at their screen, finds the right buttons and fixes it on their own PC, or guides them step by step. It already works live: it changes Windows settings by itself in ~30–45 seconds.

Two modes:
- **Personal help (free):** anyone with a Windows problem ("my WiFi icon is missing", "turn on dark mode").
- **Business support (paid by software vendors):** support types the customer's request into a dashboard and gets a 6-digit code (like an AnyDesk ID). The customer enters the code in FixPilot and clicks Accept. The AI solves it inside the vendor's software using that vendor's knowledge base, and support watches every step live until "Solved in 0:45".

Trust modes: Guide me (AI points with a glowing circle, user clicks) · Ask first (approve every step) · Just fix it (AI acts alone).
Safety: code + Accept consent, big STOP button + Ctrl+Shift+X, never touches passwords/payments/deleting, every step logged, unsure → hands off to a human.
Tech: Python desktop agent (screen capture + mouse/keyboard), Gemini API Computer Use in desktop mode (gemini-3.5-flash-lite main, gemini-3.8-flash fallback), FastAPI session server (Cloud Run), web support dashboard, built with Google Antigravity. Roadmap: Firestore, Vertex AI Vector Search for vendor knowledge, shipping FixPilot inside vendors' software as a "Help" button.
Business: free for individuals. Vendors pay ₹4,999/month (300 AI fixes) or ₹14,999/month (1,500 fixes), plus pay per extra fix. Estimated cost of a manual AnyDesk session: ₹150–300 of agent time vs ~₹15–25 per FixPilot fix.
Competition: AnyDesk/TeamViewer need a human for every fix · ChatGPT/chatbots can only tell you, not do it · WalkMe/Whatfix only do guided tours on web apps and need manual setup · FixPilot acts on the real desktop screen and knows the vendor's product.
Traction: our first pilot partner is a billing software company (a friend's business) that faces these support calls every day.

## The story to tell (use it for the slide flow + speaker notes)
Hook: "7 PM in a kirana shop. Ramesh bhai's bill shows the wrong GST, the queue is growing, and support says an engineer will connect on AnyDesk in 2 hours." → Problem: vendors answer the same questions all day, support only scales by hiring → Solution: FixPilot → Live demo → Why now: Gemini can now control a full desktop, fast and cheap enough per ticket → Business → Close: "The support engineer that never sleeps."

## Slides
1. Title: "FixPilot" + "AnyDesk, but the AI does the fixing." + "Built with Gemini Computer Use · Google Cloud" + team: [TEAM NAMES]
2. The 7 PM problem (Ramesh's story + timeline: calls → waits 2–3 hrs → human on AnyDesk → 10-min fix)
3. Why it keeps happening (3 question bubbles + "Support only scales by hiring more people")
4. Meet FixPilot (before/after: human in the middle 2–3 hrs vs AI in the middle ~1 min)
5. How it works (5 steps: code → Accept → AI sees screen → AI fixes or guides → Solved + "Next time: Products > Add > Save")
6. Two modes (Personal help free vs Business support paid)
7. Live demo (stays on screen while we switch laptops: Mode 1 dark mode · Mode 2 real billing software · STOP button)
8. Built on Google (simple architecture diagram: Customer PC app → Gemini Computer Use → Session server on Cloud Run → Support dashboard)
9. Safe by design (6 tiles)
10. Business + competition + closing line "The support engineer that never sleeps."

## Design
- Dark navy background (#0F1722), white text, ONE accent "signal orange" (#FF6A2B) for key words; green (#3DDC84) only for "Fixed/Solved".
- Bold modern title font, clean sans body. Max ~25 words of body text per slide, big visuals, left-aligned titles, generous margins.
- Draw diagrams and flows with real shapes and arrows (not bullet lists). No stock robots or clichés.
- Motif: a mouse cursor with a small orange spark (the AI "pilot").

Please keep body text short (I will talk over it), put the full talking points in the speaker notes, and don't invent statistics or customer names. Where something needs my input (team names, partner company name), leave a clear [PLACEHOLDER].
