import requests
import sys

BASE_URL = "http://localhost:8000"
API_KEY = "dev-secret-key"

HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json",
}


def assert_true(condition, message):
    if not condition:
        print(f"❌ {message}")
        sys.exit(1)
    print(f"✅ {message}")


def main():
    print("Running compatibility service validation...")

    # Health check
    r = requests.get(f"{BASE_URL}/health")
    assert_true(r.status_code == 200, "Health endpoint returns 200")

    # Compatibility happy path
    payload = {
        "product_a": {
            "id": "A1",
            "title": "ACME Air Purifier Model X",
            "category": "air_purifier",
            "brand": "ACME",
            "attributes": {"model": "X"},
        },
        "product_b": {
            "id": "B1",
            "title": "ACME HEPA Replacement Filter for Model X",
            "category": "filter",
            "brand": "ACME",
            "attributes": {"compatible_models": ["X"]},
        },
    }

    r = requests.post(
        f"{BASE_URL}/compatibility/evaluate",
        headers=HEADERS,
        json=payload,
    )

    assert_true(r.status_code == 200, "Compatibility endpoint returns 200")

    body = r.json()

    assert_true("compatible" in body, "Response contains 'compatible'")
    assert_true("relationship" in body, "Response contains 'relationship'")
    assert_true("confidence" in body, "Response contains 'confidence'")
    assert_true("explanation" in body, "Response contains 'explanation'")
    assert_true("evidence" in body, "Response contains 'evidence'")

    assert_true(body["compatible"] is True, "Products are marked compatible")
    assert_true(
        body["relationship"] == "replacement_filter",
        "Relationship classified correctly",
    )
    assert_true(
        0.0 <= body["confidence"] <= 1.0,
        "Confidence is within bounds",
    )

    # Invalid payload
    r = requests.post(
        f"{BASE_URL}/compatibility/evaluate",
        headers=HEADERS,
        json={},
    )
    assert_true(r.status_code == 422, "Invalid payload returns 422")

    print("\n🎉 All compatibility validation checks passed")


if __name__ == "__main__":
    main()
