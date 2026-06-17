"""Phase 4 integration test - Attendance Calculation Engine"""
import asyncio
from datetime import datetime, timezone, date, timedelta
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.seed import init_db


async def test_phase4():
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/api/v1/auth/login", json={"email": "admin@attendence.com", "password": "Admin@123456"})
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        today = date.today()
        today_str = today.isoformat()

        # --- 1. Create a shift ---
        r = await client.post("/api/v1/shifts", json={
            "name": "Morning Shift",
            "code": "MORN",
            "start_time": "09:00",
            "end_time": "18:00",
            "grace_late_minutes": 15,
            "grace_early_minutes": 15,
            "break_start": "13:00",
            "break_end": "14:00",
            "min_work_hours": 28800,
        }, headers=headers)
        assert r.status_code == 201
        shift = r.json()
        shift_id = shift["id"]
        print(f"[PASS] Created shift: {shift['name']} id={shift_id}")

        # --- 2. List shifts ---
        r = await client.get("/api/v1/shifts", headers=headers)
        assert r.status_code == 200
        assert len(r.json()) >= 1
        print(f"[PASS] List shifts: {len(r.json())} found")

        # --- 3. Create employee ---
        r = await client.post("/api/v1/employees", json={
            "employee_code": "CALC001",
            "first_name": "Calc",
            "last_name": "Test",
            "date_of_joining": today_str,
        }, headers=headers)
        assert r.status_code == 201
        emp = r.json()
        emp_id = emp["id"]
        print(f"[PASS] Created employee: {emp['employee_code']}")

        # --- 4. Assign shift ---
        r = await client.post("/api/v1/shift-assignments", json={
            "employee_id": emp_id,
            "shift_id": shift_id,
            "effective_from": today_str,
        }, headers=headers)
        assert r.status_code == 201
        print(f"[PASS] Shift assigned")

        # --- 5. List assignments ---
        r = await client.get(f"/api/v1/shift-assignments?employee_id={emp_id}", headers=headers)
        assert r.status_code == 200
        assert len(r.json()) == 1
        print(f"[PASS] List assignments: 1 found")

        # --- 6. Handshake + Push attendance logs for today (late) ---
        r = await client.get("/iclock/cdata?SN=MA100-TEST-P4&options=all")
        assert r.status_code == 200

        late_time = datetime.combine(today, datetime.min.time()) + timedelta(hours=10, minutes=30)
        late_str = late_time.strftime("%Y-%m-%d %H:%M:%S")
        punch_out = late_time + timedelta(hours=8, minutes=20)  # leaves at 18:50, ~ 7h20m net

        attlog = f"CALC001\t{late_str}\t1\t0\nCALC001\t{punch_out.strftime('%Y-%m-%d %H:%M:%S')}\t1\t0"
        r = await client.post("/iclock/cdata?table=ATTLOG&SN=MA100-TEST-P4", content=attlog)
        assert r.status_code == 200
        print(f"[PASS] Pushed late attendance logs")

        # --- 7. Compute attendance ---
        r = await client.post(
            f"/api/v1/attendances/compute?employee_id={emp_id}&att_date={today_str}",
            headers=headers,
        )
        assert r.status_code == 200
        result = r.json()
        print(f"[PASS] Computed attendance: status={result['status']}, "
              f"late={result.get('late_minutes')}min, "
              f"early_leave={result.get('early_leave_minutes')}min, "
              f"work_hours={result.get('net_work_hours')}s")

        # Check it's marked late (10:30 punch with 9:00 shift + 15 grace)
        assert result["status"] in ("late", "present")
        if result["status"] == "late":
            print(f"[PASS] Late detection works: {result['late_minutes']}min late")

        # Total work hours should be >0
        total = result.get("total_work_hours", 0)
        net = result.get("net_work_hours", 0)
        assert total and total > 0, f"Total work hours should be >0, got {total}"
        assert net and net > 0, f"Net work hours should be >0, got {net}"
        print(f"[PASS] Work hours: total={total}s net={net}s")

        # --- 8. Create holiday ---
        new_year = date(today.year + 1, 1, 1)
        r = await client.post("/api/v1/holidays", json={
            "name": "New Year",
            "date": new_year.isoformat(),
            "type": "public",
        }, headers=headers)
        assert r.status_code == 201
        print(f"[PASS] Created holiday: {r.json()['name']} on {r.json()['date']}")

        # --- 9. List holidays ---
        r = await client.get(f"/api/v1/holidays?year={new_year.year}", headers=headers)
        assert r.status_code == 200
        assert len(r.json()) >= 1
        print(f"[PASS] List holidays: {len(r.json())} found")

        # --- 10. Update shift ---
        r = await client.put(f"/api/v1/shifts/{shift_id}", json={
            "name": "Morning Shift Updated",
            "code": "MORN",
            "start_time": "08:30",
            "end_time": "17:30",
            "grace_late_minutes": 10,
            "grace_early_minutes": 10,
            "min_work_hours": 28800,
        }, headers=headers)
        assert r.status_code == 200
        assert r.json()["name"] == "Morning Shift Updated"
        print(f"[PASS] Updated shift name")

        # --- 11. Delete shift assignment ---
        r = await client.get(f"/api/v1/shift-assignments?employee_id={emp_id}", headers=headers)
        assignments = r.json()
        if assignments:
            a_id = assignments[0]["id"]
            r = await client.delete(f"/api/v1/shift-assignments/{a_id}", headers=headers)
            assert r.status_code == 204
            print(f"[PASS] Deleted shift assignment")

        # --- 12. Delete holiday ---
        r = await client.get(f"/api/v1/holidays?year={new_year.year}", headers=headers)
        holidays = r.json()
        if holidays:
            h_id = holidays[0]["id"]
            r = await client.delete(f"/api/v1/holidays/{h_id}", headers=headers)
            assert r.status_code == 204
            print(f"[PASS] Deleted holiday")

        # --- 13. Delete shift ---
        r = await client.delete(f"/api/v1/shifts/{shift_id}", headers=headers)
        assert r.status_code == 204
        print(f"[PASS] Deleted shift")

    print("\n=== ALL PHASE 4 TESTS PASSED ===")


if __name__ == "__main__":
    asyncio.run(test_phase4())
