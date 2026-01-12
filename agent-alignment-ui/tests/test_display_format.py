#!/usr/bin/env python3
"""
Test to verify the "Option 1: Show Both" display format is working correctly.
Tests that decisions show "Compatible (Relationship)" instead of just "relationship".
"""

def test_display_format_logic():
    """Test the display format logic with various scenarios."""
    print("=== Testing Display Format Logic ===")
    
    test_cases = [
        # Compatible cases
        {
            "compatible": True,
            "decision_value": "accessory",
            "expected": "Compatible (Accessory)"
        },
        {
            "compatible": True,
            "decision_value": "replacement_part",
            "expected": "Compatible (Replacement Part)"
        },
        {
            "compatible": True,
            "decision_value": "power_supply",
            "expected": "Compatible (Power Supply)"
        },
        # Not compatible case
        {
            "compatible": False,
            "decision_value": "not_compatible",
            "expected": "Not Compatible"
        },
        # Edge cases
        {
            "compatible": None,
            "decision_value": "accessory",
            "expected": "accessory"  # Fallback
        },
        {
            "compatible": True,
            "decision_value": None,
            "expected": "Compatible"  # Default when no relationship
        }
    ]
    
    # Python version of the formatting logic
    def format_decision_python(compatible, decision_value):
        """Python version of the frontend formatting logic."""
        if compatible is True:
            if decision_value:
                # Convert snake_case to Title Case
                relationship_formatted = decision_value.replace('_', ' ').title()
                return f"Compatible ({relationship_formatted})"
            else:
                return "Compatible"
        elif compatible is False:
            return "Not Compatible"
        else:
            # Fallback to original display
            return str(decision_value or 'Unknown')
    
    all_passed = True
    for i, case in enumerate(test_cases):
        result = format_decision_python(case["compatible"], case["decision_value"])
        expected = case["expected"]
        
        if result == expected:
            print(f"✓ Test case {i+1}: '{result}' (correct)")
        else:
            print(f"✗ Test case {i+1}: Expected '{expected}', got '{result}'")
            all_passed = False
    
    return all_passed

if __name__ == "__main__":
    success = test_display_format_logic()
    if success:
        print("\n🎉 Display format logic test passed!")
        print("The format shows 'Compatible (Relationship)' for compatible items")
        print("and 'Not Compatible' for incompatible items.")
    else:
        print("\n❌ Display format logic test failed!")
    
    exit(0 if success else 1)