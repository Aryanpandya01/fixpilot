Read `CONTEXT_B.md` and `CONTRACT.md` in this workspace first. Don't read the other .md files; they aren't needed.

TASK B1: Session server. Build ONLY what's listed below. The dashboard is the next task.

## 1. Files
- `server/__init__.py` (empty), `server/main.py`, `server/requirements.txt` (fastapi, uvicorn).
- `kb/billing_app.md`: if it does NOT exist yet, create a placeholder with heading `# Demo Billing Software` and one line
  "Knowledge base coming soon." If it exists, don't touch it.
- `dashboard/index.html`: if it does NOT exist yet, create a 1-line placeholder "Dashboard coming soon". If it exists, don't touch it.

## 2. `server/main.py`, implementing CONTRACT.md section 1 EXACTLY
- Pydantic models: `CreateSession{query: str, vendor_id: str = "billing_app"}`,
  `Event{type: str, text: str = "", action: str | None = None, ts: float | None = None}`,
  `Finish{status: Literal["solved","escalated","stopped"], summary: str = ""}`.
- In-memory `SESSIONS: dict[str, dict]`, protected by a `threading.Lock`.
  Session = {code, query, vendor_id, vendor_name, kb_text, status, events: [], summary: None,
  created_at, accepted_at: None, finished_at: None}.
- `POST /sessions`: random unique 6-digit code (string, may start with 0, use `secrets`). Load `kb/<vendor_id>.md`
  (path relative to the repo root, computed from `__file__`). vendor_name = the text of the first line starting with "# ".
  Unknown vendor_id → 404 `{"detail": "unknown vendor"}`. Status = "waiting". Return `{"code": code}`.
- `GET /sessions/{code}` → {code, query, vendor_name, kb_text, status}. Unknown code → 404 `{"detail": "invalid code"}`.
- `POST /sessions/{code}/accept` → status "running", accepted_at = now, `{"ok": true}`.
  If it isn't "waiting" → 409 `{"detail": "session already <status>"}`.
- `POST /sessions/{code}/events` → append the event (fill ts = now if missing). Keep at most 300 events. `{"ok": true}`.
- `GET /sessions/{code}/events` → {status, query, summary, accepted_at, finished_at, events}.
- `POST /sessions/{code}/finish` → set status, summary, finished_at. `{"ok": true}`.
- `GET /health` → `{"ok": true}`.
- Extra (dashboard use only, not in the contract): `GET /sessions` → a list of the last 20 sessions, newest first:
  {code, query, status, created_at}.
- CORS: allow all origins, methods and headers.
- Mount `dashboard/` as StaticFiles at "/" with html=True, AFTER all API routes, so the API paths still work.
- Print every request on one line to the console (method, path, code, status), so we can watch it live during the demo.

## 3. `server/test_flow.ps1` (PowerShell, Invoke-RestMethod, base URL as a param, default http://localhost:9000)
1. GET /health
2. POST /sessions with query "Customer wants to add a new product: Parle-G, Rs 10, GST 18%" → print the code
3. GET /sessions/{code} → print vendor_name, status and the kb_text length
4. POST accept
5. POST 3 events: intent "Click 'Products' in the top menu" (action click), intent "Type product name Parle-G" (action type),
   done "Product Parle-G added with 18% GST"
6. POST finish status solved, summary "Added Parle-G at Rs 10 with 18% GST."
7. GET /sessions/{code}/events → print the status, summary, number of events and the duration (finished_at - accepted_at)
8. Error checks: GET /sessions/000000 → expect 404, and POST accept again on the same code → expect 409. Print PASS/FAIL for each.
Add a `-Pause` switch that waits 2 seconds between events, so it can be watched live on the dashboard later.

## 4. Done when
- `pip install -r server/requirements.txt` works in `.venv`.
- `uvicorn server.main:app --host 0.0.0.0 --port 9000` starts.
- `powershell -ExecutionPolicy Bypass -File server/test_flow.ps1` prints every step, with PASS for both error checks.
- `http://localhost:9000/health` in the browser shows {"ok": true}, and `http://localhost:9000/` shows the dashboard placeholder.
At the end, give me: the files created (one line each), the run command, the test command, and the sample output.
