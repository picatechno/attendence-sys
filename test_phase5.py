"""Phase 5 integration test - Reports module (XLSX/PDF)"""
import asyncio
from datetime import date, datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.seed import init_db


async def test_phase5():
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/api/v1/auth/login", json={"email": "admin@attendence.com", "password": "Admin@123456"})
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        today = date.today()
        today_str = today.isoformat()

        # --- Setup: employee + shift + log + compute ---
        r = await client.post("/api/v1/shifts", json={
            "name": "Day Shift", "code": "DAY",
            "start_time": "09:00", "end_time": "18:00",
            "grace_late_minutes": 15, "grace_early_minutes": 15,
        }, headers=headers)
        shift_id = r.json()["id"]

        r = await client.post("/api/v1/employees", json={
            "employee_code": "RPT001", "first_name": "Report", "last_name": "User",
            "date_of_joining": today_str,
        }, headers=headers)
        emp = r.json()
        emp_id = emp["id"]

        r = await client.post("/api/v1/shift-assignments", json={
            "employee_id": emp_id, "shift_id": shift_id, "effective_from": today_str,
        }, headers=headers)
        assert r.status_code == 201

        # Push logs + compute
        r = await client.get("/iclock/cdata?SN=MA100-RPT&options=all")
        assert r.status_code == 200

        punch_time = datetime.combine(today, datetime.min.time()) + timedelta(hours=9, minutes=5)
        punch_out = punch_time + timedelta(hours=8, minutes=30)
        attlog = f"RPT001\t{punch_time.strftime('%Y-%m-%d %H:%M:%S')}\t1\t0\nRPT001\t{punch_out.strftime('%Y-%m-%d %H:%M:%S')}\t1\t0"
        r = await client.post("/iclock/cdata?table=ATTLOG&SN=MA100-RPT", content=attlog)
        assert r.status_code == 200

        r = await client.post(f"/api/v1/attendances/compute?employee_id={emp_id}&att_date={today_str}", headers=headers)
        assert r.status_code == 200

        # --- 1. Daily report (JSON) ---
        r = await client.get(f"/api/v1/reports/daily?report_date={today_str}", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) > 0
        print(f"[PASS] Daily report JSON: {len(data)} entries")

        # --- 2. Daily report (XLSX) ---
        r = await client.get(f"/api/v1/reports/daily?report_date={today_str}&fmt=xlsx", headers=headers)
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert len(r.content) > 100
        print(f"[PASS] Daily report XLSX: {len(r.content)} bytes")

        # --- 3. Daily report (PDF) ---
        r = await client.get(f"/api/v1/reports/daily?report_date={today_str}&fmt=pdf", headers=headers)
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/pdf"
        assert len(r.content) > 1000
        print(f"[PASS] Daily report PDF: {len(r.content)} bytes")

        # --- 4. Monthly report (JSON) ---
        r = await client.get(f"/api/v1/reports/monthly?year={today.year}&month={today.month}", headers=headers)
        assert r.status_code == 200
        monthly = r.json()
        assert isinstance(monthly, list)
        print(f"[PASS] Monthly report JSON: {len(monthly)} entries")

        # --- 5. Monthly report (XLSX) ---
        r = await client.get(f"/api/v1/reports/monthly?year={today.year}&month={today.month}&fmt=xlsx", headers=headers)
        assert r.status_code == 200
        assert len(r.content) > 100
        print(f"[PASS] Monthly report XLSX: {len(r.content)} bytes")

        # --- 6. Monthly report (PDF) ---
        r = await client.get(f"/api/v1/reports/monthly?year={today.year}&month={today.month}&fmt=pdf", headers=headers)
        assert r.status_code == 200
        assert len(r.content) > 1000
        print(f"[PASS] Monthly report PDF: {len(r.content)} bytes")

        # --- 7. Employee report (JSON) ---
        r = await client.get(
            f"/api/v1/reports/employee?employee_id={emp_id}&date_from={today_str}&date_to={today_str}",
            headers=headers,
        )
        assert r.status_code == 200
        emp_report = r.json()
        assert isinstance(emp_report, list)
        print(f"[PASS] Employee report JSON: {len(emp_report)} entries")

        # --- 8. Employee report (XLSX) ---
        r = await client.get(
            f"/api/v1/reports/employee?employee_id={emp_id}&date_from={today_str}&date_to={today_str}&fmt=xlsx",
            headers=headers,
        )
        assert r.status_code == 200
        assert len(r.content) > 100
        print(f"[PASS] Employee report XLSX: {len(r.content)} bytes")

        # --- 9. Employee report (PDF) ---
        r = await client.get(
            f"/api/v1/reports/employee?employee_id={emp_id}&date_from={today_str}&date_to={today_str}&fmt=pdf",
            headers=headers,
        )
        assert r.status_code == 200
        assert len(r.content) > 1000
        print(f"[PASS] Employee report PDF: {len(r.content)} bytes")

    print("\n=== ALL PHASE 5 TESTS PASSED ===")


if __name__ == "__main__":
    asyncio.run(test_phase5())
