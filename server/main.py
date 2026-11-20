from __future__ import annotations

import os
import secrets
import threading
import time
from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Root directory of fixpilot repo
REPO_ROOT = Path(__file__).resolve().parent.parent
KB_DIR = REPO_ROOT / "kb"
DASHBOARD_DIR = REPO_ROOT / "dashboard"

try:  # local runs read FIXPILOT_TOKEN from .env; on Cloud Run it comes from the service env vars
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

app = FastAPI(title="FixPilot Session Server")
STARTED_AT = time.time()
VERSION = os.getenv("FIXPILOT_VERSION", "dev")
# Optional shared secret. When set (cloud), accept/events/finish need the X-FixPilot-Token header, which the
# FixPilot app sends from its .env. Creating a session (the dashboard) stays open. Unset locally = no check.
TOKEN = os.getenv("FIXPILOT_TOKEN", "")
MAX_SESSIONS = 500  # sessions live in memory; drop the oldest so a public server can't grow forever


def check_token(x_fixpilot_token: str = Header(default="")) -> None:
    if TOKEN and not secrets.compare_digest(x_fixpilot_token, TOKEN):
        raise HTTPException(status_code=401, detail="missing or wrong X-FixPilot-Token")

# Allow all origins, methods, and headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage and lock
SESSIONS_LOCK = threading.Lock()
SESSIONS: dict[str, dict] = {}


# Pydantic models
class CreateSession(BaseModel):
    query: str
    vendor_id: str = "billigo"


class Event(BaseModel):
    type: str
    text: str = ""
    action: str | None = None
    ts: float | None = None


class Finish(BaseModel):
    status: Literal["solved", "escalated", "stopped"]
    summary: str = ""


# Request logging ASGI middleware: prints method, path, session code (if present), and status code
class RequestLoggerMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        status_code = [200]

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_code[0] = message.get("status", 200)
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            path = scope.get("path", "")
            method = scope.get("method", "")
            path_parts = path.strip("/").split("/")
            code = "-"
            if len(path_parts) >= 2 and path_parts[0] == "sessions":
                code = path_parts[1]
            print(f"[{method}] {path} (code: {code}) -> {status_code[0]}")

app.add_middleware(RequestLoggerMiddleware)


def _extract_vendor_name(kb_text: str, default: str) -> str:
    for line in kb_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return default


def _generate_unique_code() -> str:
    for _ in range(1000):
        c = f"{secrets.randbelow(1_000_000):06d}"
        if c not in SESSIONS:
            return c
    raise HTTPException(status_code=500, detail="unable to generate unique session code")


@app.get("/health")
def get_health():
    return {"ok": True}


@app.get("/version")
def get_version():
    return {"version": VERSION, "started_at": STARTED_AT, "token_required": bool(TOKEN)}


@app.post("/sessions")
def create_session(req: CreateSession):
    kb_path = KB_DIR / f"{req.vendor_id}.md"
    if not kb_path.is_file():
        raise HTTPException(status_code=404, detail="unknown vendor")

    try:
        kb_text = kb_path.read_text(encoding="utf-8")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"failed to read kb file: {exc}")

    vendor_name = _extract_vendor_name(kb_text, req.vendor_id)

    with SESSIONS_LOCK:
        code = _generate_unique_code()
        session_data = {
            "code": code,
            "query": req.query,
            "vendor_id": req.vendor_id,
            "vendor_name": vendor_name,
            "kb_text": kb_text,
            "status": "waiting",
            "events": [],
            "summary": None,
            "created_at": time.time(),
            "accepted_at": None,
            "finished_at": None,
        }
        SESSIONS[code] = session_data
        if len(SESSIONS) > MAX_SESSIONS:
            for old in sorted(SESSIONS, key=lambda c: SESSIONS[c]["created_at"])[: len(SESSIONS) - MAX_SESSIONS]:
                del SESSIONS[old]

    return {"code": code}


@app.get("/sessions")
def list_sessions():
    """Returns the last 20 sessions, newest first."""
    with SESSIONS_LOCK:
        sessions_sorted = sorted(
            SESSIONS.values(), key=lambda s: s["created_at"], reverse=True
        )[:20]
        return [
            {
                "code": s["code"],
                "query": s["query"],
                "status": s["status"],
                "created_at": s["created_at"],
            }
            for s in sessions_sorted
        ]


@app.get("/sessions/{code}")
def get_session(code: str):
    with SESSIONS_LOCK:
        session = SESSIONS.get(code)
        if not session:
            raise HTTPException(status_code=404, detail="invalid code")
        return {
            "code": session["code"],
            "query": session["query"],
            "vendor_name": session["vendor_name"],
            "kb_text": session["kb_text"],
            "status": session["status"],
        }


@app.post("/sessions/{code}/accept", dependencies=[Depends(check_token)])
def accept_session(code: str):
    with SESSIONS_LOCK:
        session = SESSIONS.get(code)
        if not session:
            raise HTTPException(status_code=404, detail="invalid code")
        if session["status"] != "waiting":
            raise HTTPException(
                status_code=409,
                detail=f"session already {session['status']}",
            )
        session["status"] = "running"
        session["accepted_at"] = time.time()
    return {"ok": True}


@app.post("/sessions/{code}/events", dependencies=[Depends(check_token)])
def post_event(code: str, req: Event):
    with SESSIONS_LOCK:
        session = SESSIONS.get(code)
        if not session:
            raise HTTPException(status_code=404, detail="invalid code")

        ev_dict = req.model_dump()
        if ev_dict.get("ts") is None:
            ev_dict["ts"] = time.time()

        session["events"].append(ev_dict)
        if len(session["events"]) > 300:
            session["events"] = session["events"][-300:]

    return {"ok": True}


@app.get("/sessions/{code}/events")
def get_session_events(code: str):
    with SESSIONS_LOCK:
        session = SESSIONS.get(code)
        if not session:
            raise HTTPException(status_code=404, detail="invalid code")
        return {
            "status": session["status"],
            "query": session["query"],
            "summary": session["summary"],
            "accepted_at": session["accepted_at"],
            "finished_at": session["finished_at"],
            "events": list(session["events"]),
        }


@app.post("/sessions/{code}/finish", dependencies=[Depends(check_token)])
def finish_session(code: str, req: Finish):
    with SESSIONS_LOCK:
        session = SESSIONS.get(code)
        if not session:
            raise HTTPException(status_code=404, detail="invalid code")
        session["status"] = req.status
        session["summary"] = req.summary
        session["finished_at"] = time.time()
    return {"ok": True}


DEMO_APP_DIR = REPO_ROOT / "demo_app"
PITCH_DIR = REPO_ROOT / "pitch"
EXPLAINER_DIR = REPO_ROOT / "explainer"

@app.get("/demo", include_in_schema=False)
def get_demo():
    demo_index = DEMO_APP_DIR / "index.html"
    if demo_index.is_file():
        return FileResponse(str(demo_index))
    return RedirectResponse(url="/demo/")

@app.get("/pitch", include_in_schema=False)
def get_pitch():
    pitch_index = PITCH_DIR / "index.html"
    if pitch_index.is_file():
        return FileResponse(str(pitch_index))
    return RedirectResponse(url="/pitch/")

@app.get("/explainer", include_in_schema=False)
def get_explainer():
    explainer_index = EXPLAINER_DIR / "index.html"
    if explainer_index.is_file():
        return FileResponse(str(explainer_index))
    return RedirectResponse(url="/explainer/")

# Mount demo_app/ static files at "/demo" if present
if DEMO_APP_DIR.exists():
    app.mount("/demo", StaticFiles(directory=str(DEMO_APP_DIR), html=True), name="demo_app")

# Mount pitch/ static files at "/pitch" if present
if PITCH_DIR.exists():
    app.mount("/pitch", StaticFiles(directory=str(PITCH_DIR), html=True), name="pitch")

# Mount explainer/ static files at "/explainer" if present
if EXPLAINER_DIR.exists():
    app.mount("/explainer", StaticFiles(directory=str(EXPLAINER_DIR), html=True), name="explainer")

# Mount dashboard/ static files at "/" AFTER all API routes
if not DASHBOARD_DIR.exists():
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/", StaticFiles(directory=str(DASHBOARD_DIR), html=True), name="dashboard")
