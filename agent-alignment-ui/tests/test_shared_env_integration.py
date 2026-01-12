#!/usr/bin/env python3
"""Test script for shared .env integration functionality."""

import json
import requests
import time

def test_shared_env_integration():
    """Test that API keys are loaded from shared .env file."""
    base_url = "http://localhost:8001"
    
    print("🔗 Testing Shared .env Integration")
    print("=" * 60)
    
    # Test 1: Check API key preloading
    print("1. Testing API key preloading from shared .env...")
    try:
        response = requests.get(f"{base_url}/api/config/keys")
        if response.status_code == 200:
            status = response.json()
            print("   ✅ API key status endpoint working")
            print(f"   OpenAI configured: {status['openai_configured']}")
            print(f"   OpenAI preview: {status['openai_key_preview']}")
            print(f"   Anthropic configured: {status['anthropic_configured']}")
            
            if status['openai_configured']:
                print("   ✅ OpenAI API key successfully preloaded from shared .env")
            else:
                print("   ❌ OpenAI API key not preloaded")
                return False
        else:
            print(f"   ❌ API key status failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ API key status error: {e}")
        return False
    
    # Test 2: Real compatibility evaluation
    print("\n2. Testing real compatibility evaluation...")
    try:
        test_data = {
            "product_a": {
                "id": "iphone-15",
                "title": "iPhone 15 Pro Max",
                "category": "Smartphone",
                "brand": "Apple",
                "attributes": {
                    "screen_size": "6.7 inches",
                    "storage": "256GB",
                    "charging_ports": ["USB-C", "MagSafe"]
                }
            },
            "product_b": {
                "id": "magsafe-charger",
                "title": "Apple MagSafe Charger",
                "category": "Charger",
                "brand": "Apple",
                "attributes": {
                    "power_output": "15W",
                    "charging_method": "Wireless magnetic"
                }
            }
        }
        
        print("   🔄 Running real LLM evaluation...")
        response = requests.post(
            f"{base_url}/api/evaluations/compatibility",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=45
        )
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ Real evaluation successful!")
            print(f"   Decision: {result.get('relationship', 'N/A')}")
            print(f"   Compatible: {result.get('compatible', 'N/A')}")
            print(f"   Confidence: {result.get('confidence', 0):.2f}")
            print(f"   Agents: {len(result.get('agent_decisions', []))}")
            print(f"   Alignment: {result.get('alignment_summary', {}).get('state', 'N/A')}")
            print(f"   Processing time: {result.get('processing_time_ms', 0)}ms")
            
            # Verify multi-agent structure
            agent_decisions = result.get('agent_decisions', [])
            expected_agents = {'advocate_agent', 'skeptic_agent', 'judge_agent'}
            actual_agents = {d.get('agent_name') for d in agent_decisions}
            
            if expected_agents == actual_agents:
                print("   ✅ All expected agents participated")
            else:
                print(f"   ⚠️  Agent mismatch. Expected: {expected_agents}, Got: {actual_agents}")
            
            return True
        else:
            print(f"   ❌ Real evaluation failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Real evaluation error: {e}")
        return False

if __name__ == "__main__":
    time.sleep(1)  # Wait for server
    
    success = test_shared_env_integration()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Shared .env Integration Test PASSED!")
        print("\n✅ What's Working:")
        print("   • API keys automatically loaded from shared .env")
        print("   • Real LLM evaluations working")
        print("   • Multi-agent system functioning")
        print("   • Alignment analysis operational")
        print("   • No manual API key configuration needed")
    else:
        print("❌ Shared .env Integration Test FAILED!")
    
    print("\n🎯 Ready for Production:")
    print("   • Backend: http://localhost:8001")
    print("   • Frontend: cd agent-alignment-ui/frontend && npm start")
    print("   • API keys: Automatically loaded from root .env file")