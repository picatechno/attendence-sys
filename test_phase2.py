"""Phase 2 integration test - Employee Management"""
import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import async_session_factory
from app.seed import init_db


async def test_phase2():
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Login
        r = await client.post("/api/v1/auth/login", json={"email": "admin@attendence.com", "password": "Admin@123456"})
        assert r.status_code == 200
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create department
        r = await client.post("/api/v1/departments", json={"name": "Engineering", "code": "ENG"}, headers=headers)
        assert r.status_code == 201, f"Create dept: {r.text}"
        dept_id = r.json()["id"]
        print(f"[PASS] Created department: {r.json()['name']} ({dept_id})")

        # List departments
        r = await client.get("/api/v1/departments", headers=headers)
        assert r.status_code == 200
        assert len(r.json()) >= 1
        print(f"[PASS] Listed {len(r.json())} departments")

        # Create location
        r = await client.post("/api/v1/locations", json={"name": "Main Office", "address": "123 Street"}, headers=headers)
        assert r.status_code == 201
        loc_id = r.json()["id"]
        print(f"[PASS] Created location: {r.json()['name']}")

        # Create employee
        emp_data = {
            "employee_code": "EMP001",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "designation": "Developer",
            "date_of_joining": "2026-01-15",
            "department_id": dept_id,
        }
        r = await client.post("/api/v1/employees", json=emp_data, headers=headers)
        assert r.status_code == 201, f"Create emp: {r.text}"
        emp_id = r.json()["id"]
        assert r.json()["employee_code"] == "EMP001"
        print(f"[PASS] Created employee: {r.json()['first_name']} {r.json()['last_name']} ({emp_id})")

        # List employees
        r = await client.get("/api/v1/employees", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 1
        print(f"[PASS] Listed employees: total={data['total']}")

        # Search employees
        r = await client.get("/api/v1/employees?search=john", headers=headers)
        assert r.status_code == 200
        assert r.json()["total"] >= 1
        print(f"[PASS] Search employees: found {r.json()['total']}")

        # Get single employee
        r = await client.get(f"/api/v1/employees/{emp_id}", headers=headers)
        assert r.status_code == 200
        assert r.json()["email"] == "john@example.com"
        print(f"[PASS] Get employee by ID")

        # Update employee
        r = await client.put(f"/api/v1/employees/{emp_id}", json={"designation": "Senior Developer"}, headers=headers)
        assert r.status_code == 200
        assert r.json()["designation"] == "Senior Developer"
        print(f"[PASS] Updated employee designation")

        # Delete (soft) employee
        r = await client.delete(f"/api/v1/employees/{emp_id}", headers=headers)
        assert r.status_code == 204
        print(f"[PASS] Soft-deleted employee")

        # Verify deleted
        r = await client.get(f"/api/v1/employees/{emp_id}", headers=headers)
        assert r.status_code == 404
        print(f"[PASS] Deleted employee not found")

        # Unauthorized access (no token)
        r = await client.get("/api/v1/employees")
        assert r.status_code == 401
        print(f"[PASS] Unauthenticated access blocked")

    print("\n=== ALL PHASE 2 TESTS PASSED ===")


if __name__ == "__main__":
    asyncio.run(test_phase2())
