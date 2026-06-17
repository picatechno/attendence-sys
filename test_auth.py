import httpx
import json

BASE = "http://localhost:8000"

r = httpx.get(f"{BASE}/health")
print("Health:", r.status_code, r.json())

r = httpx.post(f"{BASE}/api/v1/auth/login", json={"email": "admin@attendence.com", "password": "Admin@123456"})
print("Login:", r.status_code)
if r.status_code == 200:
    data = r.json()
    print("Token:", data["access_token"][:30] + "...")
    headers = {"Authorization": f'Bearer {data["access_token"]}'}

    r2 = httpx.get(f"{BASE}/api/v1/auth/me", headers=headers)
    print("Me:", r2.status_code, r2.json().get("email"))

    r3 = httpx.get(f"{BASE}/api/v1/auth/me/roles", headers=headers)
    print("Roles:", r3.status_code, [r.get("name") for r in r3.json()])
else:
    print("Error:", r.text)
