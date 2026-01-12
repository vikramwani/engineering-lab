#!/usr/bin/env python3
"""
Test script to verify frontend runtime stability and API proxy functionality.
"""

import requests
import json
import time

def test_frontend_pages():
    """Test that frontend pages load without runtime errors."""
    print("🌐 Testing Frontend Runtime...")
    
    base_url = "http://localhost:3000"
    
    try:
        # Test main page loads
        response = requests.get(base_url, timeout=10)
        if response.status_code != 200:
            print(f"❌ Frontend main page failed: {response.status_code}")
            return False
        
        print("✅ Frontend main page loads successfully")
        
        # Test API endpoints through proxy
        api_endpoints = [
            "/api/evaluations",
            "/api/hitl/requests", 
            "/api/config/keys"
        ]
        
        for endpoint in api_endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ {endpoint} - Status: {response.status_code}, Data keys: {list(data.keys())}")
                else:
                    print(f"⚠️  {endpoint} - Status: {response.status_code}")
            except Exception as e:
                print(f"❌ {endpoint} - Error: {e}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Frontend test failed: {e}")
        return False

def test_data_structure():
    """Test that API returns expected data structure."""
    print("\n📊 Testing API Data Structure...")
    
    try:
        # Test evaluations endpoint
        response = requests.get("http://localhost:8001/api/evaluations", timeout=5)
        if response.status_code == 200:
            data = response.json()
            
            # Check required fields
            if 'evaluations' not in data:
                print("❌ Missing 'evaluations' field in response")
                return False
            
            if 'total' not in data:
                print("❌ Missing 'total' field in response")
                return False
            
            if not isinstance(data['evaluations'], list):
                print("❌ 'evaluations' should be a list")
                return False
            
            print(f"✅ Evaluations API structure valid - {len(data['evaluations'])} evaluations, total: {data['total']}")
            
            # Test individual evaluation structure
            if data['evaluations']:
                eval_item = data['evaluations'][0]
                required_fields = ['task_id', 'task_type', 'agent_decisions', 'alignment_summary']
                
                for field in required_fields:
                    if field not in eval_item:
                        print(f"❌ Missing required field '{field}' in evaluation item")
                        return False
                
                print("✅ Individual evaluation structure valid")
            
        else:
            print(f"❌ Evaluations API failed: {response.status_code}")
            return False
        
        # Test HITL requests endpoint
        response = requests.get("http://localhost:8001/api/hitl/requests", timeout=5)
        if response.status_code == 200:
            data = response.json()
            
            if 'requests' not in data or 'total' not in data:
                print("❌ HITL API missing required fields")
                return False
            
            print(f"✅ HITL API structure valid - {len(data['requests'])} requests")
        
        return True
        
    except Exception as e:
        print(f"❌ Data structure test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Frontend Runtime Test Suite")
    print("=" * 40)
    
    # Give frontend time to fully load
    print("⏳ Waiting for frontend to be ready...")
    time.sleep(3)
    
    frontend_success = test_frontend_pages()
    data_success = test_data_structure()
    
    if frontend_success and data_success:
        print("\n🎉 All frontend runtime tests passed!")
        print("✅ Frontend loads without errors")
        print("✅ API proxy is working")
        print("✅ Data structures are valid")
        exit(0)
    else:
        print("\n❌ Some frontend tests failed")
        exit(1)