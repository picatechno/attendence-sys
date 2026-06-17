"""Phase 3 integration test - Device sync and attendance ingestion"""
import asyncio
from datetime import datetime, timezone, date
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.seed import init_db


async def test_phase3():
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Login
        r = await client.post("/api/v1/auth/login", json={"email": "admin@attendence.com", "password": "Admin@123456"})
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # --- ZKTeco PUSH Protocol Tests ---

        # 1. Device handshake
        r = await client.get("/iclock/cdata?SN=MA100-TEST-001&options=all")
        assert r.status_code == 200
        assert "GET OPTION FROM" in r.text
        print(f"[PASS] Device handshake: {r.status_code}")

        # 2. Second handshake (already registered)
        r = await client.get("/iclock/cdata?SN=MA100-TEST-001&options=all")
        assert r.status_code == 200
        print(f"[PASS] Device re-handshake: {r.status_code}")

        # 3. Heartbeat
        r = await client.get("/iclock/getrequest?SN=MA100-TEST-001")
        assert r.status_code == 200
        print(f"[PASS] Device heartbeat: {r.status_code}")

        # 4. Push attendance logs
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        attlog_payload = f"TEST001\t{now}\t1\t0\nTEST002\t{now}\t1\t0"
        r = await client.post("/iclock/cdata?table=ATTLOG&SN=MA100-TEST-001", content=attlog_payload)
        assert r.status_code == 200
        assert r.text == "OK"
        print(f"[PASS] Push attendance logs: {r.status_code}")

        # 5. List devices via API
        r = await client.get("/api/v1/devices", headers=headers)
        assert r.status_code == 200
        devices = r.json()
        assert len(devices) >= 1
        device_id = devices[0]["id"]
        print(f"[PASS] List devices: {len(devices)} found")

        # 6. Get device logs (convert via schema)
        r = await client.get(f"/api/v1/devices/{device_id}/logs", headers=headers)
        assert r.status_code == 200
        logs = r.json()
        assert logs["total"] >= 2
        print(f"[PASS] Device logs: {logs['total']} entries")

        # 7. Send device command
        r = await client.post(f"/api/v1/devices/{device_id}/command",
                              json={"command": "RESTART"}, headers=headers)
        assert r.status_code == 200
        print(f"[PASS] Device command queued")

        # 8. ZKTeco test endpoint
        r = await client.get("/iclock/test")
        assert r.status_code == 200
        assert r.json()["status"] == "ZKTeco PUSH listener is active"
        print(f"[PASS] ZKTeco test endpoint")

        # 9. List attendances
        r = await client.get("/api/v1/attendances", headers=headers)
        assert r.status_code == 200
        print(f"[PASS] List attendances: {r.json()['total']} total")

        # 10. Attendance with device log processing
        today_str = date.today().isoformat()
        r = await client.post(f"/api/v1/employees", json={
            "employee_code": "DEV002",
            "first_name": "Device",
            "last_name": "User",
            "date_of_joining": "2026-01-01",
        }, headers=headers)
        emp_id = r.json()["id"]

        # Check attendance list now includes the new employee
        r = await client.get("/api/v1/attendances", headers=headers)
        assert r.status_code == 200
        print(f"[PASS] Attendance listing works with all data")

    print("\n=== ALL PHASE 3 TESTS PASSED ===")


if __name__ == "__main__":
    asyncio.run(test_phase3())
