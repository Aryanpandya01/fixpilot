"""app/dev_mock_server.py - TEST ONLY stand-in for Person B's session server (CONTRACT.md section 1).

Lets Person A test Mode 2 without the partner's laptop. The real server lives in server/ (Person B).
Run: .venv\\Scripts\\python.exe -m uvicorn app.dev_mock_server:app --port 9000
Create a code: Invoke-RestMethod -Method Post http://localhost:9000/sessions -ContentType application/json -Body '{"query":"..."}'
"""
import random
import time

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="FixPilot MOCK session server")
S: dict[str, dict] = {}
KB = "# Demo Billing Software\n(mock knowledge base - the real one is kb/billing_app.md from Person B)"


class Create(BaseModel):
    query: str
    vendor_id: str = "billing_app"


class Event(BaseModel):
    type: str
    text: str = ""
    action: str | None = None
    ts: float | None = None


class Finish(BaseModel):
    status: str
    summary: str = ""


def _get(code: str) -> dict:
    if code not in S:
        raise HTTPException(404, "invalid code")
    return S[code]


@app.post("/sessions")
def create(b: Create):
    code = f"{random.randint(0, 999999):06d}"
    S[code] = dict(code=code, query=b.query, vendor_name="Demo Billing Software", kb_text=KB, status="waiting",
                   events=[], summary=None, accepted_at=None, finished_at=None)
    return {"code": code}


@app.get("/sessions/{code}")
def get(code: str):
    s = _get(code)
    return {k: s[k] for k in ("code", "query", "vendor_name", "kb_text", "status")}


@app.post("/sessions/{code}/accept")
def accept(code: str):
    s = _get(code)
    if s["status"] != "waiting":
        raise HTTPException(409, f"session already {s['status']}")
    s.update(status="running", accepted_at=time.time())
    return {"ok": True}


@app.post("/sessions/{code}/events")
def event(code: str, e: Event):
    ev = e.model_dump()
    ev["ts"] = ev["ts"] or time.time()
    _get(code)["events"].append(ev)
    print(f"[{code}] {ev['type']}: {ev['text']}", flush=True)
    return {"ok": True}


@app.get("/sessions/{code}/events")
def events(code: str):
    s = _get(code)
    return {k: s[k] for k in ("status", "query", "summary", "accepted_at", "finished_at", "events")}


@app.post("/sessions/{code}/finish")
def finish(code: str, f: Finish):
    _get(code).update(status=f.status, summary=f.summary, finished_at=time.time())
    return {"ok": True}


@app.get("/health")
def health():
    return {"ok": True}
