import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from server.main import app

async def run_tests():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. GET /health
        res = await client.get("/health")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        assert res.json() == {"ok": True}
        print("[PASS] GET /health")

        # 2. POST /sessions
        res = await client.post("/sessions", json={
            "query": "Customer wants to add a new product: Parle-G, Rs 10, GST 18%",
            "vendor_id": "billing_app"
        })
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()
        assert "code" in data
        code = data["code"]
        assert len(code) == 6 and code.isdigit()
        print(f"[PASS] POST /sessions -> code {code}")

        # 3. GET /sessions/{code}
        res = await client.get(f"/sessions/{code}")
        assert res.status_code == 200
        s_data = res.json()
        assert s_data["code"] == code
        assert "BilliGo" in s_data["vendor_name"]
        assert s_data["status"] == "waiting"
        assert len(s_data["kb_text"]) > 0
        print(f"[PASS] GET /sessions/{code} -> vendor: '{s_data['vendor_name']}', status: {s_data['status']}")

        # 4. POST /sessions/{code}/accept
        res = await client.post(f"/sessions/{code}/accept")
        assert res.status_code == 200
        assert res.json() == {"ok": True}
        print(f"[PASS] POST /sessions/{code}/accept")

        # Check status updated to running
        res = await client.get(f"/sessions/{code}")
        assert res.json()["status"] == "running"

        # 5. POST 3 events
        events = [
            {"type": "intent", "text": "Click 'Products' in the top menu", "action": "click"},
            {"type": "intent", "text": "Type product name Parle-G", "action": "type"},
            {"type": "done", "text": "Product Parle-G added with 18% GST"}
        ]
        for ev in events:
            res = await client.post(f"/sessions/{code}/events", json=ev)
            assert res.status_code == 200
            assert res.json() == {"ok": True}
        print(f"[PASS] Posted {len(events)} events")

        # 6. POST /sessions/{code}/finish
        res = await client.post(f"/sessions/{code}/finish", json={
            "status": "solved",
            "summary": "Added Parle-G at Rs 10 with 18% GST."
        })
        assert res.status_code == 200
        assert res.json() == {"ok": True}
        print(f"[PASS] POST /sessions/{code}/finish")

        # 7. GET /sessions/{code}/events
        res = await client.get(f"/sessions/{code}/events")
        assert res.status_code == 200
        ev_data = res.json()
        assert ev_data["status"] == "solved"
        assert ev_data["summary"] == "Added Parle-G at Rs 10 with 18% GST."
        assert len(ev_data["events"]) == 3
        assert ev_data["accepted_at"] is not None
        assert ev_data["finished_at"] is not None
        duration = ev_data["finished_at"] - ev_data["accepted_at"]
        print(f"[PASS] GET /sessions/{code}/events -> status: {ev_data['status']}, count: {len(ev_data['events'])}, duration: {duration:.4f}s")

        # 8. GET /sessions (dashboard sessions list)
        res = await client.get("/sessions")
        assert res.status_code == 200
        sessions_list = res.json()
        assert len(sessions_list) >= 1
        assert any(s["code"] == code for s in sessions_list)
        print(f"[PASS] GET /sessions -> {len(sessions_list)} sessions listed")

        # 9. Error checks
        # Unknown session code -> 404
        res = await client.get("/sessions/000000")
        assert res.status_code == 404
        print("[PASS] Error check 1: 404 on unknown session code")

        # Re-accepting already finished session -> 409
        res = await client.post(f"/sessions/{code}/accept")
        assert res.status_code == 409
        print("[PASS] Error check 2: 409 on accept when not waiting")

        # Unknown vendor -> 404
        res = await client.post("/sessions", json={"query": "test", "vendor_id": "nonexistent_vendor"})
        assert res.status_code == 404
        print("[PASS] Error check 3: 404 on unknown vendor_id")

        # Dashboard static file root /
        res = await client.get("/")
        assert res.status_code == 200
        print("[PASS] Static root / serves dashboard")

    print("\n==========================================")
    print(" ALL TASK B1 CONTRACT TESTS PASSED!")
    print("==========================================")

if __name__ == "__main__":
    asyncio.run(run_tests())
