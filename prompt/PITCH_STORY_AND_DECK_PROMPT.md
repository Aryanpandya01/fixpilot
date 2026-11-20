# FixPilot — Pitch Story + Deck Prompt

## PART 1 — THE STORY (3-minute pitch, read it out loud)

**[0:00 — Hook]**
"It's 7 PM in a kirana shop in Bhavnagar. Ramesh bhai is billing customers when his software shows the wrong GST.
The queue is growing. He calls support. They say: *an engineer will connect on AnyDesk in 2 hours.*"

**[0:20 — Problem]**
"This happens thousands of times a day across India. Billing, POS and GST software vendors answer the same
questions again and again: *where is this menu, how do I add a product, why is my bill wrong.*
Every answer costs a support person 10–15 minutes on AnyDesk. Customers wait hours, and vendors keep hiring
just to repeat the same clicks."

**[0:45 — Solution]**
"We built **FixPilot: AnyDesk, but the AI does the fixing.**
The customer types or says the problem. FixPilot, powered by Gemini Computer Use, looks at the screen,
finds the right buttons, and fixes it on the customer's own PC, or guides them step by step."

**[1:00 — LIVE DEMO, ~75 seconds]**
1. Mode 1: "Turn on dark mode." FixPilot opens Settings, picks Dark, done. *"Same thing a friend does on AnyDesk, no friend needed."*
2. Mode 2: my partner, as the support desk, types the customer's request and gets a code. I enter the code and click **Accept**.
   FixPilot works inside the **real billing software**. The support dashboard shows every step live, then "Solved in 0:45".
3. Press **STOP** mid-task: the customer is always in control.

**[2:15 — Why us / why now]**
"Two things changed in 2026. Gemini can now control a full desktop, not just a browser, and it's fast and cheap
enough to run per support ticket. Remote-desktop tools still need a human for every fix. Chatbots can only *tell* you what to do.
FixPilot is the first to *know the vendor's software and act on the real screen*, with consent."

**[2:30 — Business]**
"Vendors pay us, not shop owners. ₹4,999 a month for 300 AI fixes, ₹14,999 for 1,500. A manual AnyDesk session
costs a vendor ₹150–300 of agent time. FixPilot does it for ₹15–25.
Our first pilot partner is a billing software company that already has the problem every day."

**[2:45 — Close]**
"Free for anyone with a Windows problem. Paid by software companies that want their support to scale.
FixPilot: the support engineer that never sleeps, never makes the customer wait, and teaches them along the way."

---

## PART 2 — PROMPT FOR A VERY GOOD DECK
Works in **Gamma**, **Canva Magic Design**, **Google Slides "Help me create"**, or **Antigravity** (ask for a single HTML slide deck).
Copy everything between the lines.

-----------------------------------------------------------------
Create a 10-slide startup pitch deck for **FixPilot**, for a Google startup buildathon in India. Audience: startup judges and Google engineers.
Tone: confident, simple English, very little text per slide (max 25 words of body text), big visuals.

DESIGN
- Theme: dark navy background (#0F1722), white text, ONE accent color "signal orange" (#FF6A2B) used only for key words and highlights.
  Success green (#3DDC84) only for "solved/fixed" moments.
- Fonts: a bold geometric display font for titles (e.g. Bricolage Grotesque or Sora), a clean sans for body (e.g. IBM Plex Sans).
- 16:9, generous margins, left-aligned titles, one idea per slide. No stock-photo clichés, no robots with glowing eyes.
- Visual motif: a mouse cursor with a small orange spark (the AI "pilot" moving the cursor).

SLIDES
1. **Title** — "FixPilot" / subtitle "AnyDesk, but the AI does the fixing." / small line "Built with Gemini Computer Use · Google Cloud". Team names at the bottom.
2. **The 7 PM problem** — Ramesh's shop: queue growing, wrong GST on the bill, support says "engineer will connect on AnyDesk in 2 hours".
   Visual: a timeline bar, "Customer calls → waits 2–3 hrs → human connects on AnyDesk → 10 min fix".
3. **Why it keeps happening** — Software vendors answer the same questions daily: "Where is this menu?", "How do I add a product?",
   "Why is my GST wrong?". Three speech-bubble cards. Bottom line: "Support only scales by hiring more people."
4. **Meet FixPilot** — One line: "You say the problem. FixPilot sees your screen and fixes it." Visual: Before/after comparison:
   Today = human in the middle (2–3 hrs). FixPilot = AI in the middle (~1 minute).
5. **How it works** — 5 numbered steps in a horizontal flow: Support creates a code → Customer enters code + Accept →
   AI sees the screen (Gemini) → AI clicks / guides → "Solved" + "Next time: Products > Add > Save".
6. **Two modes** — Two cards. Personal help (free): anyone, any Windows problem. Business support (paid): software vendors,
   uses the vendor's own knowledge base, support watches live.
7. **Live demo** — Big title "Live demo" with 3 small checkpoints: Mode 1 dark mode · Mode 2 real billing software · STOP button.
   (This slide stays on screen while we switch to the laptops.)
8. **Built on Google** — Architecture diagram: Customer PC (FixPilot app: screen capture, mouse/keyboard, panel with STOP) →
   Gemini API Computer Use (desktop) gemini-3.5-flash-lite main, gemini-3.8-flash fallback → Session server on Cloud Run
   → Support dashboard. Small chips: Antigravity, Gemini, Cloud Run, Firestore (roadmap), Vertex AI Vector Search (roadmap).
9. **Safe by design** — 6 icon tiles: Code + Accept consent · Guide / Ask-first / Auto modes · Big STOP button ·
   No passwords, payments or deleting · Every step logged · Unsure → hands off to a human.
10. **Business + ask** — Pricing: Free for individuals · ₹4,999/month (300 fixes) · ₹14,999/month (1,500 fixes) · pay per extra fix.
    Comparison line: "Manual AnyDesk session ≈ ₹150–300 of agent time. FixPilot ≈ ₹15–25."
    Competition table (3 rows): AnyDesk/TeamViewer = human needed · Chatbots = text only · FixPilot = AI acts on screen, knows the product.
    Closing line in orange: "The support engineer that never sleeps."

SPEAKER NOTES: add 2–3 short sentences of speaker notes to every slide, based on this story: [paste PART 1 here].
-----------------------------------------------------------------

## PART 3 — PROMPT FOR A ONE-PAGE WEBSITE (optional, for judges to open on their phone)
-----------------------------------------------------------------
Build a single-file responsive landing page (HTML + CSS, no frameworks) for **FixPilot — AnyDesk, but the AI does the fixing.**
Same design system as above (dark navy #0F1722, signal orange #FF6A2B, success green #3DDC84, bold display font + clean sans).
Sections: Hero (headline, one-line subhead, two buttons "Watch demo" and "For software vendors") → The problem (Ramesh's 7 PM story, 3 lines)
→ How it works (5 steps with simple inline SVG icons) → Two modes (2 cards) → Safety (6 tiles) → Pricing (3 cards) → Built with Google
(logos as text chips) → Footer with team names. Include an animated mock of the FixPilot side panel in the hero: a dark 360px panel showing
steps appearing one by one ("Open Settings" → "Click Colors" → "Click Dark") and ending with a green "Fixed in 0:30" card.
Respect prefers-reduced-motion. Mobile-first, works at 375px width.
-----------------------------------------------------------------

## Before using: fill or verify
- Team names on slides 1 and 10.
- Replace "a billing software company" with your friend's company name only if he agrees, and add his WhatsApp quote as proof.
- The ₹150–300 per session and ₹15–25 per fix numbers are estimates. Say "estimated" if a judge asks.
