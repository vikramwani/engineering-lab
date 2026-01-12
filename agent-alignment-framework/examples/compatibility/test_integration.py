#!/usr/bin/env python3
"""Integration test for the compatibility evaluator.

This script tests the end-to-end functionality of the compatibility evaluator
without requiring API keys, using mock responses to validate the framework.
"""

import json
import os
import sys
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from examples.compatibility.evaluator import CompatibilityEvaluator
from agent_alignment.llm.client import LLMProvider


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing without API calls."""
    
    def __init__(self):
        self.call_count = 0
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate mock responses based on agent role in prompt."""
        self.call_count += 1
        
        # Simple mock responses based on prompt content
        if "advocate" in prompt.lower() or "for compatibility" in prompt.lower():
            return """
            {
                "decision": "accessory",
                "confidence": 0.85,
                "reasoning": "The MagSafe charger is specifically designed as an accessory for iPhone devices. It provides wireless charging capability and is fully compatible with iPhone 15 Pro Max through magnetic alignment.",
                "evidence": [
                    "MagSafe technology is Apple's proprietary wireless charging standard",
                    "iPhone 15 Pro Max supports MagSafe charging up to 15W",
                    "Physical magnetic alignment ensures proper connection",
                    "Both products are manufactured by Apple ensuring compatibility"
                ]
            }
            """
        
        elif "skeptic" in prompt.lower() or "against" in prompt.lower():
            return """
            {
                "decision": "accessory", 
                "confidence": 0.75,
                "reasoning": "While generally compatible, there are some limitations to consider. The charging speed may be slower than wired charging, and case compatibility could be an issue with certain protective cases.",
                "evidence": [
                    "MagSafe charging is slower than Lightning cable charging",
                    "Thick cases may interfere with magnetic connection",
                    "Requires precise alignment for optimal charging",
                    "Heat generation during wireless charging may affect battery longevity"
                ]
            }
            """
        
        elif "judge" in prompt.lower():
            return """
            {
                "decision": "accessory",
                "confidence": 0.90,
                "reasoning": "Based on the evidence from both perspectives, the MagSafe charger is clearly designed as a compatible accessory for the iPhone 15 Pro Max. While there are minor limitations regarding charging speed and case compatibility, the fundamental compatibility is strong and well-established.",
                "evidence": [
                    "Apple designed MagSafe specifically for iPhone compatibility",
                    "iPhone 15 Pro Max has built-in MagSafe support",
                    "Widespread successful usage confirms compatibility",
                    "Official Apple accessory with guaranteed compatibility"
                ]
            }
            """
        
        else:
            return """
            {
                "decision": "accessory",
                "confidence": 0.80,
                "reasoning": "General compatibility assessment indicates these products work together as intended.",
                "evidence": ["Compatible design", "Shared standards", "Manufacturer support"]
            }
            """
    
    def get_provider_name(self) -> str:
        return "mock-llm-provider"


def create_sample_products():
    """Create sample product data for testing."""
    return {
        "iphone_15_pro_max": {
            "id": "IPHONE-15-PRO-MAX-256GB",
            "title": "iPhone 15 Pro Max",
            "category": "Smartphone",
            "brand": "Apple",
            "attributes": {
                "screen_size": "6.7 inches",
                "storage": "256GB",
                "charging_ports": ["USB-C", "MagSafe", "Qi Wireless"],
                "operating_system": "iOS 17",
                "processor": "A17 Pro"
            },
            "description": "Latest iPhone with titanium design and A17 Pro chip."
        },
        
        "magsafe_charger": {
            "id": "APPLE-MAGSAFE-CHARGER-15W",
            "title": "Apple MagSafe Charger",
            "category": "Charger",
            "brand": "Apple",
            "attributes": {
                "power_output": "15W",
                "connector_type": "MagSafe magnetic",
                "compatibility": ["iPhone 12 series", "iPhone 13 series", "iPhone 14 series", "iPhone 15 series"],
                "charging_method": "Wireless magnetic"
            },
            "description": "Official Apple MagSafe wireless charger with magnetic alignment."
        }
    }


def test_compatibility_evaluator():
    """Test the compatibility evaluator with mock LLM."""
    print("🧪 Testing Compatibility Evaluator Integration")
    print("=" * 60)
    
    # Create mock LLM client
    mock_provider = MockLLMProvider()
    
    # Patch the LLMClient to use our mock
    with patch('agent_alignment.llm.client.LLMClient') as mock_llm_client_class:
        # Create a mock LLM client instance
        mock_llm_client = Mock()
        mock_llm_client.generate.side_effect = mock_provider.generate
        mock_llm_client_class.return_value = mock_llm_client
        
        # Create evaluator (this will use our mocked LLM client)
        try:
            evaluator = CompatibilityEvaluator(llm_client=mock_llm_client)
            print("✅ Evaluator created successfully")
        except Exception as e:
            print(f"❌ Failed to create evaluator: {e}")
            return False
    
    # Load sample products
    products = create_sample_products()
    print(f"✅ Sample products loaded: {len(products)} products")
    
    # Test compatibility evaluation
    print("\n📱 Testing: iPhone 15 Pro Max + MagSafe Charger")
    print("-" * 40)
    
    try:
        result = evaluator.evaluate_compatibility(
            product_a=products["iphone_15_pro_max"],
            product_b=products["magsafe_charger"],
            task_id="test-integration-001"
        )
        
        print("📊 Evaluation Results:")
        print(f"   🎯 Final Decision: {result['relationship']}")
        print(f"   ✅ Compatible: {result['compatible']}")
        print(f"   📈 Confidence: {result['confidence']:.2f}")
        print(f"   🔍 Alignment State: {result['alignment_summary']['state']}")
        print(f"   ⚠️  Needs Human Review: {result['needs_human_review']}")
        print(f"   ⏱️  Processing Time: {result['processing_time_ms']}ms")
        
        print("\n🤝 Agent Decisions:")
        for i, agent_decision in enumerate(result["agent_decisions"], 1):
            print(f"   {i}. {agent_decision['agent_name']} ({agent_decision['role_type']}):")
            print(f"      Decision: {agent_decision['relationship']}")
            print(f"      Confidence: {agent_decision['confidence']:.2f}")
            print(f"      Evidence: {len(agent_decision['evidence'])} items")
        
        print("\n📈 Alignment Analysis:")
        alignment = result["alignment_summary"]
        print(f"   • Decision Agreement: {alignment['decision_agreement']}")
        print(f"   • Confidence Spread: {alignment['confidence_spread']:.2f}")
        print(f"   • Average Confidence: {alignment['avg_confidence']:.2f}")
        if alignment['disagreement_areas']:
            print(f"   • Disagreement Areas: {', '.join(alignment['disagreement_areas'])}")
        
        # Validate results
        print("\n✅ Validation Checks:")
        
        # Check that we got decisions from all agents
        expected_agents = {"advocate_agent", "skeptic_agent", "judge_agent"}
        actual_agents = {d['agent_name'] for d in result["agent_decisions"]}
        if expected_agents == actual_agents:
            print("   ✅ All expected agents provided decisions")
        else:
            print(f"   ❌ Missing agents: {expected_agents - actual_agents}")
        
        # Check that all decisions are valid
        valid_relationships = {
            "replacement_filter", "replacement_part", "accessory", 
            "consumable", "power_supply", "not_compatible", "insufficient_information"
        }
        all_valid = all(d['relationship'] in valid_relationships for d in result["agent_decisions"])
        if all_valid:
            print("   ✅ All agent decisions use valid relationship types")
        else:
            print("   ❌ Some agent decisions use invalid relationship types")
        
        # Check confidence ranges
        all_valid_confidence = all(0.0 <= d['confidence'] <= 1.0 for d in result["agent_decisions"])
        if all_valid_confidence:
            print("   ✅ All confidence scores are in valid range [0.0, 1.0]")
        else:
            print("   ❌ Some confidence scores are out of range")
        
        # Check that alignment analysis is present
        if result["alignment_summary"]["state"] in ["full_alignment", "soft_disagreement", "hard_disagreement", "insufficient_signal"]:
            print("   ✅ Alignment state is valid")
        else:
            print(f"   ❌ Invalid alignment state: {result['alignment_summary']['state']}")
        
        print("\n🎉 Integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_simple_compatibility():
    """Test simple boolean compatibility evaluation."""
    print("\n" + "=" * 60)
    print("🔄 Testing Simple Boolean Compatibility")
    print("=" * 60)
    
    # Create mock LLM client
    mock_provider = MockLLMProvider()
    
    with patch('agent_alignment.llm.client.LLMClient') as mock_llm_client_class:
        mock_llm_client = Mock()
        mock_llm_client.generate.side_effect = mock_provider.generate
        mock_llm_client_class.return_value = mock_llm_client
        
        evaluator = CompatibilityEvaluator(llm_client=mock_llm_client)
    
    products = create_sample_products()
    
    try:
        result = evaluator.evaluate_simple_compatibility(
            product_a=products["iphone_15_pro_max"],
            product_b=products["magsafe_charger"],
            task_id="test-simple-001"
        )
        
        print(f"   Compatible: {result['compatible']}")
        print(f"   Confidence: {result['confidence']:.2f}")
        print(f"   Explanation: {result['explanation'][:100]}...")
        print(f"   Needs Review: {result['needs_human_review']}")
        
        print("✅ Simple compatibility test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Simple compatibility test failed: {e}")
        return False


def test_json_serialization():
    """Test that results can be properly serialized to JSON."""
    print("\n" + "=" * 60)
    print("🔄 Testing JSON Serialization")
    print("=" * 60)
    
    mock_provider = MockLLMProvider()
    
    with patch('agent_alignment.llm.client.LLMClient') as mock_llm_client_class:
        mock_llm_client = Mock()
        mock_llm_client.generate.side_effect = mock_provider.generate
        mock_llm_client_class.return_value = mock_llm_client
        
        evaluator = CompatibilityEvaluator(llm_client=mock_llm_client)
    
    products = create_sample_products()
    
    try:
        result = evaluator.evaluate_compatibility(
            product_a=products["iphone_15_pro_max"],
            product_b=products["magsafe_charger"],
            task_id="test-json-001"
        )
        
        # Test JSON serialization
        json_str = json.dumps(result, indent=2)
        print(f"✅ Result serialized to JSON ({len(json_str)} characters)")
        
        # Test JSON deserialization
        parsed_result = json.loads(json_str)
        print("✅ JSON successfully parsed back to Python object")
        
        # Verify key fields are preserved
        assert parsed_result["request_id"] == result["request_id"]
        assert parsed_result["compatible"] == result["compatible"]
        assert len(parsed_result["agent_decisions"]) == len(result["agent_decisions"])
        print("✅ Key fields preserved after JSON round-trip")
        
        return True
        
    except Exception as e:
        print(f"❌ JSON serialization test failed: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Starting Compatibility Evaluator Integration Tests")
    print()
    
    tests = [
        test_compatibility_evaluator,
        test_simple_compatibility,
        test_json_serialization,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"📊 Integration Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All integration tests passed! The compatibility evaluator is working correctly.")
        print("\n📋 Next Steps:")
        print("   1. Set OPENAI_API_KEY to test with real LLM")
        print("   2. Run: python examples/compatibility/demo.py")
        print("   3. Start the UI: cd agent-alignment-ui && python backend/main.py")
        print("   4. Test the full end-to-end workflow")
    else:
        print("⚠️  Some integration tests failed. Please check the implementation.")
    
    sys.exit(0 if failed == 0 else 1)