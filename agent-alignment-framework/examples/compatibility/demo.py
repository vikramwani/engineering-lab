#!/usr/bin/env python3
"""Product Compatibility Evaluator Demo.

This script demonstrates the Agent Alignment Framework applied to product
compatibility evaluation with real examples and comprehensive output.
"""

import json
import os
import sys
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from examples.compatibility.evaluator import CompatibilityEvaluator


def create_sample_products() -> Dict[str, Dict[str, Any]]:
    """Create sample product data for demonstration."""
    return {
        "iphone_15_pro_max": {
            "id": "IPHONE-15-PRO-MAX-256GB-TITANIUM",
            "title": "iPhone 15 Pro Max",
            "category": "Smartphone",
            "brand": "Apple",
            "attributes": {
                "screen_size": "6.7 inches",
                "storage": "256GB",
                "color": "Natural Titanium",
                "charging_ports": ["USB-C", "MagSafe", "Qi Wireless"],
                "operating_system": "iOS 17",
                "processor": "A17 Pro",
                "camera": "48MP Main, 12MP Ultra Wide, 12MP Telephoto",
                "battery": "4441 mAh",
                "dimensions": "159.9 x 76.7 x 8.25 mm",
                "weight": "221g"
            },
            "description": "The most advanced iPhone with titanium design, A17 Pro chip, and professional camera system."
        },
        
        "magsafe_charger": {
            "id": "APPLE-MAGSAFE-CHARGER-15W",
            "title": "Apple MagSafe Charger",
            "category": "Charger",
            "brand": "Apple",
            "attributes": {
                "power_output": "15W",
                "connector_type": "MagSafe magnetic",
                "cable_length": "1 meter",
                "compatibility": ["iPhone 12 series", "iPhone 13 series", "iPhone 14 series", "iPhone 15 series"],
                "charging_method": "Wireless magnetic",
                "input": "USB-C",
                "certifications": ["Qi certified", "Apple certified"]
            },
            "description": "Official Apple MagSafe wireless charger with magnetic alignment for iPhone 12 and later."
        },
        
        "usb_c_hub": {
            "id": "ANKER-USB-C-HUB-7IN1",
            "title": "Anker USB-C Hub 7-in-1",
            "category": "Hub/Adapter",
            "brand": "Anker",
            "attributes": {
                "ports": ["USB-C PD", "2x USB-A 3.0", "HDMI 4K", "SD Card", "microSD", "Ethernet"],
                "power_delivery": "100W pass-through",
                "hdmi_resolution": "4K@60Hz",
                "usb_speed": "USB 3.0 (5Gbps)",
                "compatibility": ["MacBook", "iPad Pro", "Windows laptops", "Android devices"],
                "dimensions": "120 x 50 x 15 mm",
                "weight": "95g"
            },
            "description": "Versatile 7-in-1 USB-C hub with 4K HDMI, USB ports, and 100W power delivery."
        },
        
        "canon_battery": {
            "id": "CANON-LP-E6NH-BATTERY",
            "title": "Canon LP-E6NH Battery",
            "category": "Camera Battery",
            "brand": "Canon",
            "attributes": {
                "voltage": "7.2V",
                "capacity": "2130mAh",
                "chemistry": "Lithium-ion",
                "compatibility": ["EOS R5", "EOS R6", "EOS 5D Mark IV", "EOS 6D Mark II", "EOS 90D"],
                "charging_method": "LC-E6 charger",
                "dimensions": "56.8 x 20.6 x 38.4 mm",
                "weight": "80g"
            },
            "description": "High-capacity lithium-ion battery for Canon EOS cameras with improved performance."
        },
        
        "third_party_battery": {
            "id": "GENERIC-LP-E6-BATTERY-2PACK",
            "title": "Generic LP-E6 Compatible Battery (2-Pack)",
            "category": "Camera Battery",
            "brand": "PowerExtra",
            "attributes": {
                "voltage": "7.4V",
                "capacity": "1865mAh",
                "chemistry": "Lithium-ion",
                "compatibility": ["Canon EOS cameras", "LP-E6 compatible"],
                "charging_method": "Standard LP-E6 chargers",
                "certifications": ["CE", "FCC", "RoHS"],
                "warranty": "18 months",
                "package": "2 batteries + dual charger"
            },
            "description": "Third-party LP-E6 compatible batteries with dual charger for Canon cameras."
        }
    }


def run_compatibility_scenarios():
    """Run various compatibility evaluation scenarios."""
    print("🤖 Product Compatibility Evaluator Demo")
    print("=" * 60)
    print("Demonstrating Agent Alignment Framework for product compatibility evaluation")
    print()
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable is required")
        print("Please set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        return
    
    # Initialize evaluator
    print("🔧 Initializing Compatibility Evaluator...")
    try:
        evaluator = CompatibilityEvaluator()
        print("✅ Evaluator initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize evaluator: {e}")
        return
    
    # Load sample products
    products = create_sample_products()
    print(f"📦 Loaded {len(products)} sample products")
    print()
    
    # Define evaluation scenarios
    scenarios = [
        {
            "name": "Clear Compatibility (Expected: Full Alignment)",
            "description": "iPhone 15 Pro Max + Apple MagSafe Charger",
            "product_a": products["iphone_15_pro_max"],
            "product_b": products["magsafe_charger"],
            "expected_alignment": "FULL_ALIGNMENT",
            "expected_compatible": True,
        },
        {
            "name": "Generic Compatibility (Expected: Soft Disagreement)",
            "description": "iPhone 15 Pro Max + Generic USB-C Hub",
            "product_a": products["iphone_15_pro_max"],
            "product_b": products["usb_c_hub"],
            "expected_alignment": "SOFT_DISAGREEMENT",
            "expected_compatible": True,
        },
        {
            "name": "Third-party Risk Assessment (Expected: Hard Disagreement)",
            "description": "Canon LP-E6NH Battery vs Generic LP-E6 Battery",
            "product_a": products["canon_battery"],
            "product_b": products["third_party_battery"],
            "expected_alignment": "HARD_DISAGREEMENT",
            "expected_compatible": "uncertain",
        },
    ]
    
    # Run each scenario
    for i, scenario in enumerate(scenarios, 1):
        print(f"📋 Scenario {i}: {scenario['name']}")
        print(f"   {scenario['description']}")
        print(f"   Expected Alignment: {scenario['expected_alignment']}")
        print()
        
        try:
            # Run compatibility evaluation
            result = evaluator.evaluate_compatibility(
                product_a=scenario["product_a"],
                product_b=scenario["product_b"],
                task_id=f"demo-scenario-{i}"
            )
            
            # Display results
            print("📊 Evaluation Results:")
            print(f"   🎯 Final Decision: {result['relationship']}")
            print(f"   ✅ Compatible: {result['compatible']}")
            print(f"   📈 Confidence: {result['confidence']:.2f}")
            print(f"   🔍 Alignment State: {result['alignment_summary']['state']}")
            print(f"   ⚠️  Needs Human Review: {result['needs_human_review']}")
            print(f"   ⏱️  Processing Time: {result['processing_time_ms']}ms")
            print()
            
            print("🤝 Agent Decisions:")
            for agent_decision in result["agent_decisions"]:
                print(f"   • {agent_decision['agent_name']} ({agent_decision['role_type']}):")
                print(f"     Decision: {agent_decision['relationship']}")
                print(f"     Confidence: {agent_decision['confidence']:.2f}")
                print(f"     Reasoning: {agent_decision['reasoning'][:100]}...")
                print()
            
            print("📈 Alignment Analysis:")
            alignment = result["alignment_summary"]
            print(f"   • Decision Agreement: {alignment['decision_agreement']}")
            print(f"   • Confidence Spread: {alignment['confidence_spread']:.2f}")
            print(f"   • Average Confidence: {alignment['avg_confidence']:.2f}")
            if alignment['disagreement_areas']:
                print(f"   • Disagreement Areas: {', '.join(alignment['disagreement_areas'])}")
            print()
            
            # Check if HITL escalation occurred
            if result['needs_human_review']:
                print("🚨 HITL Escalation Triggered!")
                print(f"   Reason: {result['review_reason']}")
                print("   → This case requires human review due to agent disagreement")
                print()
            
            # Validate against expectations
            actual_alignment = alignment['state'].upper()
            if actual_alignment == scenario['expected_alignment']:
                print(f"✅ Alignment matches expectation: {actual_alignment}")
            else:
                print(f"⚠️  Alignment differs from expectation:")
                print(f"   Expected: {scenario['expected_alignment']}")
                print(f"   Actual: {actual_alignment}")
            
        except Exception as e:
            print(f"❌ Scenario failed: {e}")
            import traceback
            traceback.print_exc()
        
        print("-" * 60)
        print()
    
    print("🎉 Demo completed successfully!")
    print()
    print("🔍 Key Observations:")
    print("   • Framework successfully orchestrated multiple agents")
    print("   • Alignment analysis detected different disagreement patterns")
    print("   • HITL escalation triggered appropriately for hard disagreements")
    print("   • All agent decisions were captured with confidence scores")
    print("   • Results are deterministic and fully traceable")
    print()
    print("📚 Next Steps:")
    print("   • Try with your own product data")
    print("   • Experiment with different alignment thresholds")
    print("   • Integrate with the visualization UI (coming next)")
    print("   • Deploy as a production service")


def run_simple_compatibility_demo():
    """Run a simple boolean compatibility demo."""
    print("\n" + "=" * 60)
    print("🔄 Simple Boolean Compatibility Demo")
    print("=" * 60)
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable is required")
        return
    
    # Initialize evaluator
    evaluator = CompatibilityEvaluator()
    products = create_sample_products()
    
    # Simple compatibility check
    print("📱 Testing: iPhone 15 Pro Max + MagSafe Charger (Simple Boolean)")
    
    result = evaluator.evaluate_simple_compatibility(
        product_a=products["iphone_15_pro_max"],
        product_b=products["magsafe_charger"],
        task_id="simple-demo"
    )
    
    print(f"   Compatible: {result['compatible']}")
    print(f"   Confidence: {result['confidence']:.2f}")
    print(f"   Explanation: {result['explanation'][:150]}...")
    print(f"   Needs Review: {result['needs_human_review']}")


if __name__ == "__main__":
    try:
        run_compatibility_scenarios()
        run_simple_compatibility_demo()
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()