"""Phase 1 integration test - runs against live server"""
import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import engine, async_session_factory, Base
from app.seed import init_db


async def test_phase1():
    # Re-initialize DB
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test health
        r = await client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
        print("[PASS] Health endpoint")

        # Test login - invalid
        r = await client.post("/api/v1/auth/login", json={"email": "wrong@test.com", "password": "wrong"})
        assert r.status_code == 401
        print("[PASS] Login with wrong credentials returns 401")

        # Test login - valid
        r = await client.post("/api/v1/auth/login", json={"email": "admin@attendence.com", "password": "Admin@123456"})
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert "refresh_token" in data
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]
        print("[PASS] Login with valid credentials")

        # Test access with token
        headers = {"Authorization": f"Bearer {access_token}"}
        r = await client.get("/api/v1/auth/me", headers=headers)
        assert r.status_code == 200
        assert r.json()["email"] == "admin@attendence.com"
        print("[PASS] GET /auth/me with valid token")

        # Test roles
        r = await client.get("/api/v1/auth/me/roles", headers=headers)
        assert r.status_code == 200
        roles = r.json()
        assert any(r["name"] == "super_admin" for r in roles)
        print(f"[PASS] Roles: {[r['name'] for r in roles]}")

        # Test refresh token
        r = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert r.status_code == 200
        new_tokens = r.json()
        assert "access_token" in new_tokens
        print("[PASS] Token refresh")

        # Test change password - wrong old password
        r = await client.post("/api/v1/auth/change-password", json={"old_password": "wrong", "new_password": "NewPass123!"}, headers=headers)
        assert r.status_code == 400
        print("[PASS] Change password with wrong old password returns 400")

        # Test no token
        r = await client.get("/api/v1/auth/me")
        assert r.status_code == 401
        print("[PASS] Unauthenticated request returns 401")

    print("\n=== ALL PHASE 1 TESTS PASSED ===")


if __name__ == "__main__":
    asyncio.run(test_phase1())
