#!/usr/bin/env python3
"""Test script for the Agent Alignment UI backend API."""

import json
import requests
import time

def test_backend_api():
    """Test the backend API endpoints."""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Agent Alignment UI Backend API")
    print("=" * 60)
    
    # Test health endpoint
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/api/health")
        if response.status_code == 200:
            print("   ✅ Health endpoint working")
            print(f"   Response: {response.json()}")
        else:
            print(f"   ❌ Health endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Health endpoint error: {e}")
        return False
    
    # Test root endpoint
    print("\n2. Testing root endpoint...")
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("   ✅ Root endpoint working")
            print(f"   Response: {response.json()}")
        else:
            print(f"   ❌ Root endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Root endpoint error: {e}")
    
    # Test evaluations list endpoint
    print("\n3. Testing evaluations list endpoint...")
    try:
        response = requests.get(f"{base_url}/api/evaluations")
        if response.status_code == 200:
            print("   ✅ Evaluations endpoint working")
            data = response.json()
            print(f"   Total evaluations: {data.get('total', 0)}")
        else:
            print(f"   ❌ Evaluations endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Evaluations endpoint error: {e}")
    
    # Test HITL requests endpoint
    print("\n4. Testing HITL requests endpoint...")
    try:
        response = requests.get(f"{base_url}/api/hitl/requests")
        if response.status_code == 200:
            print("   ✅ HITL requests endpoint working")
            data = response.json()
            print(f"   Total HITL requests: {data.get('total', 0)}")
        else:
            print(f"   ❌ HITL requests endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ HITL requests endpoint error: {e}")
    
    # Test compatibility evaluation endpoint (without API key)
    print("\n5. Testing compatibility evaluation endpoint...")
    try:
        test_data = {
            "product_a": {
                "id": "test-product-a",
                "title": "Test Product A",
                "category": "Electronics",
                "brand": "TestBrand",
                "attributes": {"type": "test"},
                "description": "Test product for API testing"
            },
            "product_b": {
                "id": "test-product-b", 
                "title": "Test Product B",
                "category": "Accessories",
                "brand": "TestBrand",
                "attributes": {"type": "test"},
                "description": "Test accessory for API testing"
            }
        }
        
        response = requests.post(
            f"{base_url}/api/evaluations/compatibility",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 500:
            # Expected if no API key is set
            print("   ⚠️  Compatibility evaluation failed (expected without API key)")
            error_data = response.json()
            if "OPENAI_API_KEY" in str(error_data.get("detail", "")):
                print("   ✅ Correct error message about missing API key")
            else:
                print(f"   ❌ Unexpected error: {error_data}")
        elif response.status_code == 200:
            print("   ✅ Compatibility evaluation succeeded")
            data = response.json()
            print(f"   Result: {data.get('synthesized_decision', 'N/A')}")
        else:
            print(f"   ❌ Unexpected status code: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Compatibility evaluation error: {e}")
    
    print("\n🎉 Backend API test completed!")
    return True

if __name__ == "__main__":
    # Wait a moment for server to be ready
    time.sleep(2)
    test_backend_api()