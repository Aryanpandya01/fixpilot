"""app/server.py - Local FixPilot panel server.

Bridges the panel UI (app/panel/index.html, over a WebSocket) and the agent loop (agent.agent.run_session).
Mode 1: the user types a query -> run_session with kb_text="".
Mode 2: the user enters a 6-digit support code -> fetch the query + kb from the session server (CONTRACT.md) ->
        the user clicks Accept -> run_session with kb_text, mirroring every event to the session server.

Run: .venv\\Scripts\\python.exe -m uvicorn app.server:app --host 127.0.0.1 --port 8000
"""
import asyncio
import os
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

from agent import agent as fp_agent

load_dotenv()
APP_DIR = Path(__file__).resolve().parent
SERVER_URL = os.getenv("SERVER_URL", "http://localhost:9000").rstrip("/")
TOKEN = os.getenv("FIXPILOT_TOKEN", "")

app = FastAPI(title="FixPilot panel")


def _headers() -> dict:
    return {"X-FixPilot-Token": TOKEN} if TOKEN else {}


class PanelSession:
    """State for one connected panel (one customer PC runs one panel)."""

    def __init__(self, ws: WebSocket, loop: asyncio.AbstractEventLoop):
        self.ws = ws
        self.loop = loop
        self.running = False
        self.code: str | None = None      # Mode 2 support code, None in Mode 1
        self.offer: dict | None = None    # session fetched from the server, waiting for Accept
        self.reply: str | None = None
        self.reply_evt = threading.Event()
        self.user_turn = False            # next ask is "the user does something" (password, login, UAC), not an approval
        self.overlay: subprocess.Popen | None = None
        self.outbox: "queue.Queue[tuple[str, dict]]" = queue.Queue()
        threading.Thread(target=self._post_worker, daemon=True).start()

    # ---- to the panel -------------------------------------------------
    def send(self, msg: dict) -> None:
        try:
            asyncio.run_coroutine_threadsafe(self.ws.send_json(msg), self.loop)
        except Exception as e:  # panel closed
            print("panel send failed:", e)

    # ---- to the session server (ordered, never blocks the agent) --------
    def post(self, path: str, body: dict) -> None:
        if self.code:
            self.outbox.put((path, body))

    def _post_worker(self) -> None:
        while True:
            path, body = self.outbox.get()
            try:
                requests.post(f"{SERVER_URL}/sessions/{self.code}{path}", json=body,
                              headers=_headers(), timeout=5)
            except Exception as e:
                print("session server post failed:", e)

    # ---- guide-mode highlight -------------------------------------------
    def show_overlay(self, x: int, y: int, text: str) -> None:
        self.hide_overlay()
        try:
            self.overlay = subprocess.Popen(
                [sys.executable, str(APP_DIR / "overlay.py"), str(x), str(y), text],
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except Exception as e:
            print("overlay failed:", e)

    def hide_overlay(self) -> None:
        if self.overlay and self.overlay.poll() is None:
            self.overlay.kill()
        self.overlay = None

    # ---- callbacks handed to run_session ----------------------------------
    def on_event(self, ev: dict) -> None:
        self.send({"kind": "event", **ev})
        if ev.get("type") == "highlight" and "x" in ev:
            self.show_overlay(int(ev["x"]), int(ev["y"]), ev.get("text", ""))
        if ev.get("type") == "approval" and ev.get("action") == "ask_user":
            self.user_turn = True
            if "x" in ev:  # ring the field the user should type into (e.g. the password box)
                self.show_overlay(int(ev["x"]), int(ev["y"]), "Type here")
        if ev.get("action") != "retry":
            self.post("/events", {k: ev.get(k) for k in ("type", "text", "action", "ts")})

    def ask_approval(self, question: str) -> bool:
        ask = "next" if question == "next" else "user" if self.user_turn else "approve"
        self.user_turn = False
        self.reply = None
        self.reply_evt.clear()
        self.send({"kind": "ask", "ask": ask, "text": question})
        self.reply_evt.wait()
        self.hide_overlay()
        self.send({"kind": "ask_done"})
        return self.reply in ("approve", "next")

    # ---- run the agent in a background thread ------------------------------
    def start(self, query: str, kb_text: str, mode: str) -> None:
        if self.running:
            self.send({"kind": "error", "text": "FixPilot is already working on a task."})
            return
        self.running = True

        def _run():
            t0 = time.time()
            self.send({"kind": "started", "query": query, "mode": mode, "mode2": bool(self.code)})
            try:
                result = fp_agent.run_session(query=query, kb_text=kb_text, mode=mode,
                                              on_event=self.on_event, ask_approval=self.ask_approval)
            except Exception as e:
                result = {"status": "escalated", "summary": f"Unexpected error: {e}"}
            secs = round(time.time() - t0, 1)
            self.hide_overlay()
            self.send({"kind": "result", "seconds": secs, **result})
            self.post("/finish", {"status": result.get("status", "escalated"),
                                  "summary": result.get("summary", "")})
            self.running = False

        threading.Thread(target=_run, daemon=True).start()

    def answer(self, reply: str) -> None:
        self.reply = reply
        self.reply_evt.set()

    def stop(self) -> None:
        fp_agent.request_stop()
        self.answer("deny")  # unblock a pending approval
        self.hide_overlay()


@app.get("/")
def panel() -> FileResponse:
    return FileResponse(APP_DIR / "panel" / "index.html")


LOCAL_HOSTS = ("127.0.0.1", "localhost")


def _origin_ok(ws: WebSocket) -> bool:
    """Only the FixPilot panel itself may drive the agent. Without this, ANY website open in the browser
    could connect to ws://127.0.0.1:8000/ws and start a task on this PC. Non-browser clients send no Origin."""
    origin = ws.headers.get("origin")
    if origin is None:
        return True
    host = ws.headers.get("host", "")
    return origin == f"http://{host}" and host.split(":")[0] in LOCAL_HOSTS


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket) -> None:
    if not _origin_ok(ws):
        await ws.close(code=1008)  # policy violation: another website tried to control this PC
        return
    await ws.accept()
    s = PanelSession(ws, asyncio.get_running_loop())
    await ws.send_json({"kind": "hello", "server_url": SERVER_URL, "model": fp_agent.MODEL})
    try:
        while True:
            m = await ws.receive_json()
            t = m.get("type")
            if t == "start":  # Mode 1
                s.code = None
                q = (m.get("query") or "").strip()
                if q:
                    s.start(q, "", m.get("mode", "auto"))
            elif t == "join":  # Mode 2: look up the code
                code = "".join(ch for ch in str(m.get("code", "")) if ch.isdigit())
                await _join(s, code)
            elif t == "accept" and s.offer:
                await _accept(s, m.get("mode", "auto"))
            elif t == "decline":
                s.offer, s.code = None, None
                await ws.send_json({"kind": "declined"})
            elif t in ("approve", "deny", "next"):
                s.answer(t)
            elif t == "stop":
                s.stop()
    except (WebSocketDisconnect, ConnectionResetError, Exception):
        s.stop()


async def _join(s: PanelSession, code: str) -> None:
    if len(code) != 6:
        s.send({"kind": "error", "text": "Please enter the 6-digit code from support."})
        return
    try:
        r = await asyncio.to_thread(requests.get, f"{SERVER_URL}/sessions/{code}", timeout=8)
    except Exception:
        s.send({"kind": "error", "text": f"Can't reach the support server ({SERVER_URL}). Check the internet connection."})
        return
    if r.status_code == 404:
        s.send({"kind": "error", "text": "That code is not valid. Please check it with support."})
        return
    data = r.json()
    if data.get("status") != "waiting":
        s.send({"kind": "error", "text": f"That code was already used ({data.get('status')})."})
        return
    s.code, s.offer = code, data
    s.send({"kind": "offer", "code": code, "vendor_name": data.get("vendor_name", "Support"),
            "query": data.get("query", "")})


async def _accept(s: PanelSession, mode: str) -> None:
    offer, code = s.offer, s.code
    try:
        r = await asyncio.to_thread(requests.post, f"{SERVER_URL}/sessions/{code}/accept",
                                    json={}, headers=_headers(), timeout=8)
        if r.status_code >= 400:
            s.send({"kind": "error", "text": f"Support server refused: {r.text[:120]}"})
            return
    except Exception:
        s.send({"kind": "error", "text": "Can't reach the support server."})
        return
    s.offer = None
    s.start(offer.get("query", ""), offer.get("kb_text", ""), mode)
