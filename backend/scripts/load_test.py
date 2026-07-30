import asyncio
import time
import httpx

BASE_URL = "http://localhost:8000"

def get_p95(latencies):
    if not latencies:
        return 0
    s = sorted(latencies)
    idx = int(len(s) * 0.95)
    return s[idx]

async def login(client):
    response = await client.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={
            "email": "admin.mumbai@maharashtracyber.gov.in",
            "password": "SecurePolice@2026"
        }
    )
    if response.status_code != 200:
        print("Login failed:", response.text)
        return None
    return response.cookies

async def run_benchmark():
    async with httpx.AsyncClient() as client:
        cookies = await login(client)
        if not cookies:
            return

        csrf = cookies.get("fastapi-csrf-token") or cookies.get("csrf_token") or "dummy"
        headers = {"x-csrf-token": csrf}

        print("Benchmarking GET /api/v1/cases/")
        latencies = []
        for _ in range(20):
            start = time.perf_counter()
            resp = await client.get(f"{BASE_URL}/api/v1/cases", cookies=cookies, headers=headers)
            latencies.append((time.perf_counter() - start) * 1000)
            if resp.status_code != 200:
                print(f"Failed: {resp.status_code} - {resp.text}")
                return
        
        p95_cases = get_p95(latencies)
        print(f"Case List - p95: {p95_cases:.2f} ms")

        print("Benchmarking GET /api/v1/cases")
        resp = await client.get(f"{BASE_URL}/api/v1/cases", cookies=cookies, headers=headers)
        if resp.status_code != 200:
            print(f"Error fetching cases: {resp.status_code} - {resp.text}")
            return
        cases = resp.json().get("items", [])
        if not cases:
            print("No cases found to benchmark trail.")
            return
        
        case_id = cases[0]["id"]

        print(f"Benchmarking POST /api/v1/trail/cases/{case_id}/traverse")
        latencies = []
        for _ in range(20):
            start = time.perf_counter()
            resp = await client.post(f"{BASE_URL}/api/v1/trail/cases/{case_id}/traverse", json={"max_depth": 3}, cookies=cookies, headers=headers)
            latencies.append((time.perf_counter() - start) * 1000)
            if resp.status_code != 200:
                print(f"Failed Trail: {resp.status_code} - {resp.text}")
                break
        
        p95_trail = get_p95(latencies)
        print(f"Trail - p95: {p95_trail:.2f} ms")

        print("Load Test Summary:")
        print(f"Trail retrieval p95 < 500ms? {'YES' if p95_trail < 500 else 'NO'} ({p95_trail:.2f}ms)")
        print(f"Cases list p95: {p95_cases:.2f}ms")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
