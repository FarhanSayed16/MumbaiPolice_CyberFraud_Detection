import httpx

try:
    resp = httpx.post(
        "http://localhost:8001/api/v1/auth/login",
        json={"email": "admin.mumbai@maharashtracyber.gov.in", "password": "SecurePolice@2026"}
    )
    print("Status:", resp.status_code)
    print("Response:", resp.text)
except Exception as e:
    print(e)
