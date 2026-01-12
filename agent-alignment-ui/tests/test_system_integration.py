#!/usr/bin/env python3
"""
Comprehensive integration test for the Agent Alignment UI system.
Tests end-to-end functionality including backend API, frontend proxy, and evaluation pipeline.
"""

import requests
import json
import time

def test_system_health():
    """Test overall system health."""
    print("🏥 Testing System Health...")
    
    # Test backend - use a known working endpoint instead of /health
    try:
        response = requests.get("http://localhost:8001/api/config/keys", timeout=5)
        if response.status_code == 200:
            print("✅ Backend health check passed")
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend not accessible: {e}")
        return False
    
    # Test frontend
    try:
        response = requests.get("http://localhost:3000", timeout=10)
        if response.status_code == 200:
            print("✅ Frontend accessible")
        else:
            print(f"❌ Frontend not accessible: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend not accessible: {e}")
        return False
    
    return True

def test_api_key_management():
    """Test API key management functionality."""
    print("\n🔑 Testing API Key Management...")
    
    # Get current status
    response = requests.get("http://localhost:3000/api/config/keys")
    if response.status_code != 200:
        print(f"❌ Failed to get API key status: {response.status_code}")
        return False
    
    status = response.json()
    print(f"✅ API key status: OpenAI={status['openai_configured']}, Anthropic={status['anthropic_configured']}")
    
    # Verify OpenAI key is preloaded
    if not status['openai_configured']:
        print("❌ OpenAI key should be preloaded from shared .env")
        return False
    
    print("✅ API key preloading from shared .env working")
    return True

def test_evaluation_system():
    """Test the evaluation system end-to-end."""
    print("\n🧠 Testing Evaluation System...")
    
    # Test compatibility evaluation
    test_data = {
        "product_a": {
            "id": "test-phone",
            "title": "Test Smartphone",
            "category": "Smartphone",
            "brand": "TestBrand",
            "attributes": {"charging": "USB-C"}
        },
        "product_b": {
            "id": "test-charger",
            "title": "Test USB-C Charger",
            "category": "Charger", 
            "brand": "TestBrand",
            "attributes": {"connector": "USB-C"}
        }
    }
    
    try:
        response = requests.post(
            "http://localhost:3000/api/evaluations/compatibility",
            headers={"Content-Type": "application/json"},
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            required_fields = ['compatible', 'relationship', 'confidence', 'agent_decisions', 'alignment_summary']
            
            for field in required_fields:
                if field not in result:
                    print(f"❌ Missing field in evaluation result: {field}")
                    return False
            
            print(f"✅ Evaluation completed: {result['relationship']} (confidence: {result['confidence']:.2f})")
            print(f"✅ Agent decisions: {len(result['agent_decisions'])} agents")
            print(f"✅ Alignment state: {result['alignment_summary']['state']}")
            
            return True
        else:
            print(f"❌ Evaluation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Evaluation test failed: {e}")
        return False

def test_data_persistence():
    """Test that evaluations are persisted and retrievable."""
    print("\n💾 Testing Data Persistence...")
    
    # Get evaluations
    response = requests.get("http://localhost:3000/api/evaluations")
    if response.status_code != 200:
        print(f"❌ Failed to get evaluations: {response.status_code}")
        return False
    
    data = response.json()
    
    if 'evaluations' not in data or 'total' not in data:
        print("❌ Invalid evaluations response structure")
        return False
    
    print(f"✅ Found {data['total']} stored evaluations")
    
    if data['evaluations']:
        eval_item = data['evaluations'][0]
        required_fields = ['task_id', 'task_type', 'created_at', 'agent_decisions']
        
        for field in required_fields:
            if field not in eval_item:
                print(f"❌ Missing field in stored evaluation: {field}")
                return False
        
        print("✅ Stored evaluation structure valid")
    
    return True

def test_frontend_components():
    """Test that frontend components are working."""
    print("\n🎨 Testing Frontend Components...")
    
    # Test key API endpoints through frontend proxy
    endpoints = [
        ("/api/evaluations", "evaluations data"),
        ("/api/hitl/requests", "HITL requests"),
        ("/api/config/keys", "API key status")
    ]
    
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"http://localhost:3000{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {description} endpoint working")
            else:
                print(f"❌ {description} endpoint failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ {description} endpoint error: {e}")
            return False
    
    return True

if __name__ == "__main__":
    print("🧪 Agent Alignment UI - System Integration Test")
    print("=" * 60)
    
    tests = [
        ("System Health", test_system_health),
        ("API Key Management", test_api_key_management),
        ("Evaluation System", test_evaluation_system),
        ("Data Persistence", test_data_persistence),
        ("Frontend Components", test_frontend_components),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
    
    print(f"\n{'='*60}")
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        exit(0)
    else:
        print("❌ Some tests failed")
        exit(1)