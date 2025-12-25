import requests
import sys

BASE_URL = "http://localhost:8000"
API_KEY = "dev-secret-key"

HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json",
}

def assert_ok(condition, message):
    if not condition:
        print(f"❌ {message}")
        sys.exit(1)
    print(f"✅ {message}")

def test_health():
    r = requests.get(f"{BASE_URL}/health")
    assert_ok(r.status_code == 200, "Health endpoint returns 200")

def test_auth_failure():
    r = requests.post(
        f"{BASE_URL}/generate",
        headers={"Content-Type": "application/json"},
        json={"prompt": "hello"},
    )
    assert_ok(r.status_code == 401, "Missing API key is rejected")

def test_generate_success():
    r = requests.post(
        f"{BASE_URL}/generate",
        headers=HEADERS,
        json={"prompt": "hello"},
    )
    body = r.json()
    assert_ok(r.status_code == 200, "Generate endpoint returns 200")
    assert_ok("output" in body, "Response contains output")
    assert_ok("request_id" in body, "Response contains request_id")
    assert_ok("latency_ms" in body, "Response contains latency")

def test_validation_error():
    r = requests.post(
        f"{BASE_URL}/generate",
        headers=HEADERS,
        json={},
    )
    assert_ok(r.status_code == 422, "Invalid payload returns 422")

if __name__ == "__main__":
    print("Running service validation...\n")

    test_health()
    test_auth_failure()
    test_generate_success()
    test_validation_error()

    print("\n🎉 All validation checks passed")
