# FixPilot — CONTRACT (shared by Person A and Person B)

Agree on this together, then it is FROZEN. Change it only when both people agree.
Paste this file into Antigravity first on both laptops: "Follow this contract exactly."

---

## 1. Server API (Person B builds, Person A's app calls)

Base URL: `SERVER_URL` (from .env), default `http://<laptopB-ip>:9000`. CORS: allow all. Storage: in-memory dict.

| Method + path | Called by | Request body → Response |
|---|---|---|
| `POST /sessions` | dashboard | `{"query": str, "vendor_id": "billing_app"}` → `{"code": "482913"}` (random 6 digits) |
| `GET /sessions/{code}` | app | → `{"code", "query", "vendor_name", "kb_text", "status"}` · 404 if code not found |
| `POST /sessions/{code}/accept` | app | `{}` → `{"ok": true}` · status → `running` |
| `POST /sessions/{code}/events` | app | one **Event** → `{"ok": true}` |
| `GET /sessions/{code}/events` | dashboard (polls every 2s) | → `{"status": str, "query": str, "summary": str\|null, "accepted_at": float\|null, "finished_at": float\|null, "events": [Event, ...]}` (times are unix seconds) |
| `POST /sessions/{code}/finish` | app | `{"status": "solved" \| "escalated" \| "stopped", "summary": str}` → `{"ok": true}` |
| `GET /health` | anyone | → `{"ok": true}` |

Session status: `waiting` → `running` → `solved` / `escalated` / `stopped`.
`kb_text` = full contents of `kb/billing_app.md`, read when the session is created.

## 2. Event (Person A sends, Person B displays)

```json
{"type": "intent", "text": "Click 'Products' in the left menu", "action": "click", "ts": 1732080000}
```
`type` is one of: `intent` (AI step), `approval` (waiting for the customer), `done`, `escalate`, `error`, `stopped`.

## 3. Engine function (Person A, agent/agent.py)

```python
run_session(query: str, kb_text: str, mode: str,            # mode: "guide" | "assist" | "auto"
            on_event: callable, ask_approval: callable) -> dict  # returns {"status", "summary"}
```
- Mode 1 (personal Windows help): `kb_text = ""`
- Mode 2 (business support): `kb_text` comes from `GET /sessions/{code}`

## 4. Folders (who owns what)

| Folder | Owner |
|---|---|
| `agent/`, `app/` | Person A |
| `server/`, `dashboard/`, `demo_app/`, `kb/`, `pitch/` | Person B |
| `CONTRACT.md` | both, together only |

`.env` (never commit): `GEMINI_API_KEY=...` and `SERVER_URL=http://<laptopB-ip>:9000`
