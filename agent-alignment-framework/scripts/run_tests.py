#!/usr/bin/env python3
"""Test runner for the Agent Alignment Framework.

This script provides a convenient way to run all framework tests and examples.
"""

import subprocess
import sys
import os


def run_command(cmd, description):
    """Run a command and report results."""
    print(f"\n🔄 {description}")
    print("-" * 50)
    
    try:
        # Run from the repository root (parent of scripts/)
        result = subprocess.run(cmd, shell=True, check=True)
        print(f"✅ {description} - PASSED")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED (exit code: {e.returncode})")
        return False


def main():
    """Run all tests and examples."""
    print("🧪 Agent Alignment Framework - Test Suite")
    print("=" * 60)
    
    # Change to parent directory since we're now in scripts/
    os.chdir(os.path.join(os.path.dirname(__file__), '..'))
    
    tests = [
        ("python3 tests/test_framework_validation.py", "Core Framework Validation"),
        ("python3 examples/example_usage.py", "Example Usage Demo"),
        ("python3 examples/simple_hitl_demo.py", "HITL Contract Demo"),
    ]
    
    passed = 0
    failed = 0
    
    for cmd, description in tests:
        if run_command(cmd, description):
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Framework is ready to use.")
        print("\n📋 Optional Integration Test:")
        print("   python3 scripts/live_llm_smoke_test.py --provider openai")
        print("   (Requires API keys - see scripts/live_llm_smoke_test.py --help)")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())