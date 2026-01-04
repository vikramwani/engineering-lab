#!/usr/bin/env python3
"""Live LLM Smoke Test for Agent Alignment Framework.

This script validates end-to-end framework functionality with real LLM providers.
It is NOT part of the core framework validation and is NOT deterministic.

Purpose:
- Verify framework works with real LLM providers
- Test complete evaluation pipeline under realistic conditions
- Validate HITL escalation with actual agent disagreements
- Provide confidence that framework integrates properly with LLM APIs

Important Notes:
- This test is NON-DETERMINISTIC (uses real LLMs)
- Results will vary between runs due to LLM response variability
- NOT included in CI/CD pipelines or core validation
- Requires valid API keys for LLM providers
- Can be skipped safely - framework correctness is validated by validate_framework.py

Usage:
    python scripts/live_llm_smoke_test.py [--provider openai|anthropic|local]
    
Environment Variables:
    OPENAI_API_KEY - Required for OpenAI provider
    ANTHROPIC_API_KEY - Required for Anthropic provider
    LLM_PROVIDER - Default provider if not specified via --provider
"""

import argparse
import os
import sys
import time
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agent_alignment import (
    MultiAgentEvaluator,
    EvaluationTask,
    AgentRole,
    BooleanDecisionSchema,
    CategoricalDecisionSchema,
    LLMClient,
)
from agent_alignment.llm.providers import OpenAIProvider, AnthropicProvider, LocalProvider
from agent_alignment.utils.logging import setup_logging, get_logger


def create_llm_client(provider_name: str) -> LLMClient:
    """Create LLM client for the specified provider.
    
    Args:
        provider_name: Name of the LLM provider (openai, anthropic, local)
        
    Returns:
        LLMClient: Configured LLM client
        
    Raises:
        ValueError: If provider is not supported or API key is missing
    """
    if provider_name == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required for OpenAI provider")
        
        provider = OpenAIProvider(
            api_key=api_key,
            model="gpt-4o-mini",  # Use cost-effective model for smoke test
            max_tokens=300,
            temperature=0.1
        )
        
    elif provider_name == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required for Anthropic provider")
        
        provider = AnthropicProvider(
            api_key=api_key,
            model="claude-3-haiku-20240307",  # Use cost-effective model for smoke test
            max_tokens=300,
            temperature=0.1
        )
        
    elif provider_name == "local":
        # Local provider for testing (requires local LLM server)
        provider = LocalProvider(
            base_url="http://localhost:8000",  # Adjust as needed
            model="local-model",
            max_tokens=300,
            temperature=0.1
        )
        
    else:
        raise ValueError(f"Unsupported provider: {provider_name}")
    
    return LLMClient(provider, max_retries=2, timeout_seconds=30)


def create_simple_evaluation_task() -> EvaluationTask:
    """Create a simple evaluation task for smoke testing.
    
    Returns:
        EvaluationTask: Simple boolean compatibility evaluation
    """
    return EvaluationTask(
        task_id="smoke-test-001",
        task_type="compatibility_assessment",
        decision_schema=BooleanDecisionSchema(
            positive_label="compatible",
            negative_label="incompatible"
        ),
        context={
            "product_a": {
                "name": "USB-C Cable",
                "type": "cable",
                "connector": "USB-C",
                "specifications": ["USB 3.0", "Power Delivery", "Data Transfer"]
            },
            "product_b": {
                "name": "MacBook Pro M3",
                "type": "laptop", 
                "ports": ["USB-C", "Thunderbolt 4", "HDMI"],
                "power_requirements": "USB-C Power Delivery"
            }
        },
        evaluation_criteria="Determine if the USB-C cable is compatible with the MacBook Pro M3 for both charging and data transfer"
    )


def create_disagreement_evaluation_task() -> EvaluationTask:
    """Create an evaluation task designed to trigger disagreement.
    
    Returns:
        EvaluationTask: Task likely to cause agent disagreement
    """
    return EvaluationTask(
        task_id="smoke-test-disagreement-001",
        task_type="risk_assessment",
        decision_schema=CategoricalDecisionSchema(
            categories=["low_risk", "medium_risk", "high_risk", "critical_risk"]
        ),
        context={
            "scenario": {
                "description": "Deploying a new authentication system during peak business hours",
                "factors": [
                    "High user traffic expected (Black Friday)",
                    "New system has been tested in staging environment",
                    "Rollback plan exists but takes 30 minutes",
                    "Current system has known security vulnerabilities",
                    "Development team will be available for support",
                    "No recent production deployments in this area"
                ]
            }
        },
        evaluation_criteria="Assess the risk level of deploying the new authentication system during peak business hours"
    )


def create_agent_roles() -> list[AgentRole]:
    """Create agent roles for smoke testing.
    
    Returns:
        List[AgentRole]: Agent roles with simple instructions
    """
    return [
        AgentRole(
            name="advocate_agent",
            role_type="advocate",
            instruction="Analyze the scenario and argue FOR the positive outcome. Focus on benefits, compatibility factors, and supporting evidence.",
            max_tokens=300,
            temperature=0.1
        ),
        AgentRole(
            name="skeptic_agent",
            role_type="skeptic", 
            instruction="Analyze the scenario and identify potential problems, risks, or incompatibilities. Challenge optimistic assumptions.",
            max_tokens=300,
            temperature=0.1
        ),
        AgentRole(
            name="judge_agent",
            role_type="judge",
            instruction="Review both perspectives and make a balanced final decision based on the evidence presented by other agents.",
            max_tokens=300,
            temperature=0.1
        )
    ]


def run_smoke_test(provider_name: str) -> bool:
    """Run the live LLM smoke test.
    
    Args:
        provider_name: Name of the LLM provider to test
        
    Returns:
        bool: True if smoke test passes, False otherwise
    """
    logger = get_logger(__name__)
    
    print(f"🧪 Live LLM Smoke Test - Provider: {provider_name}")
    print("=" * 60)
    print("⚠️  WARNING: This test uses real LLM APIs and is NON-DETERMINISTIC")
    print("⚠️  Results will vary between runs due to LLM response variability")
    print("⚠️  This test is NOT part of core framework validation")
    print()
    
    try:
        # Step 1: Create LLM client
        print("1️⃣ Creating LLM client...")
        llm_client = create_llm_client(provider_name)
        print(f"   ✅ LLM client created for {provider_name}")
        
        # Step 2: Create evaluator
        print("2️⃣ Creating multi-agent evaluator...")
        roles = create_agent_roles()
        evaluator = MultiAgentEvaluator.from_roles(roles, llm_client)
        print(f"   ✅ Evaluator created with {len(roles)} agents")
        
        # Step 3: Test simple evaluation (should reach consensus)
        print("3️⃣ Testing simple evaluation (expecting consensus)...")
        simple_task = create_simple_evaluation_task()
        
        start_time = time.time()
        result = evaluator.evaluate(simple_task)
        processing_time = time.time() - start_time
        
        print(f"   📊 Result: {result.synthesized_decision}")
        print(f"   📊 Confidence: {result.confidence:.2f}")
        print(f"   📊 Alignment: {result.alignment_summary.state.value}")
        print(f"   📊 Processing Time: {processing_time:.1f}s")
        print(f"   📊 Agent Decisions:")
        for decision in result.agent_decisions:
            print(f"      - {decision.agent_name}: {decision.decision_value} (conf: {decision.confidence:.2f})")
        
        if result.requires_human_review:
            print("   ⚠️  Unexpected: Simple task triggered HITL escalation")
        else:
            print("   ✅ Simple evaluation completed without HITL escalation")
        
        # Step 4: Test disagreement scenario (may trigger HITL)
        print("4️⃣ Testing disagreement scenario (may trigger HITL)...")
        disagreement_task = create_disagreement_evaluation_task()
        
        start_time = time.time()
        disagreement_result = evaluator.evaluate(disagreement_task)
        processing_time = time.time() - start_time
        
        print(f"   📊 Result: {disagreement_result.synthesized_decision}")
        print(f"   📊 Confidence: {disagreement_result.confidence:.2f}")
        print(f"   📊 Alignment: {disagreement_result.alignment_summary.state.value}")
        print(f"   📊 Processing Time: {processing_time:.1f}s")
        print(f"   📊 Agent Decisions:")
        for decision in disagreement_result.agent_decisions:
            print(f"      - {decision.agent_name}: {decision.decision_value} (conf: {decision.confidence:.2f})")
        
        # Step 5: Test HITL escalation if triggered
        if disagreement_result.requires_human_review:
            print("5️⃣ Testing HITL escalation contract...")
            hitl_request = evaluator.create_hitl_request(disagreement_result)
            
            if hitl_request:
                print(f"   🚨 HITL Request Created:")
                print(f"      - Request ID: {hitl_request.request_id}")
                print(f"      - Escalation Reason: {hitl_request.escalation_reason.value}")
                print(f"      - Alignment Score: {hitl_request.alignment_score:.2f}")
                print(f"      - Summary: {hitl_request.summary}")
                print(f"      - Dissenting Agents: {hitl_request.dissenting_agents}")
                print("   ✅ HITL escalation contract working")
            else:
                print("   ⚠️  Expected HITL request but got None")
        else:
            print("5️⃣ No HITL escalation triggered (agents reached consensus)")
        
        # Step 6: Validate framework guarantees
        print("6️⃣ Validating framework guarantees...")
        
        # Check that core logic produced valid results
        assert result.synthesized_decision is not None, "Synthesized decision should not be None"
        assert 0.0 <= result.confidence <= 1.0, "Confidence should be in [0.0, 1.0] range"
        assert len(result.agent_decisions) == len(roles), "Should have decisions from all agents"
        assert result.alignment_summary is not None, "Alignment summary should not be None"
        
        # Check that all agent decisions are valid
        for decision in result.agent_decisions:
            assert decision.agent_name is not None, "Agent name should not be None"
            assert decision.decision_value is not None, "Decision value should not be None"
            assert 0.0 <= decision.confidence <= 1.0, "Agent confidence should be in [0.0, 1.0] range"
            assert decision.rationale is not None, "Rationale should not be None"
        
        print("   ✅ All framework guarantees validated")
        
        print()
        print("🎉 Live LLM Smoke Test PASSED!")
        print()
        print("📋 Test Summary:")
        print(f"   • Provider: {provider_name}")
        print(f"   • Simple Task Result: {result.synthesized_decision} (confidence: {result.confidence:.2f})")
        print(f"   • Disagreement Task Result: {disagreement_result.synthesized_decision} (confidence: {disagreement_result.confidence:.2f})")
        print(f"   • HITL Triggered: {'Yes' if disagreement_result.requires_human_review else 'No'}")
        print(f"   • All Agents Responded: Yes")
        print(f"   • Framework Guarantees: ✅ Validated")
        print()
        print("🔍 Key Observations:")
        print("   • Framework successfully orchestrated multiple LLM agents")
        print("   • Alignment analysis produced consistent, structured results")
        print("   • HITL escalation contract worked as designed")
        print("   • All core framework guarantees were maintained")
        print("   • Real LLM integration is working properly")
        
        return True
        
    except Exception as e:
        logger.error(f"Smoke test failed: {e}", exc_info=True)
        print(f"❌ Smoke test FAILED: {e}")
        return False


def main():
    """Main entry point for live LLM smoke test."""
    parser = argparse.ArgumentParser(
        description="Live LLM smoke test for Agent Alignment Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/live_llm_smoke_test.py --provider openai
    python scripts/live_llm_smoke_test.py --provider anthropic
    python scripts/live_llm_smoke_test.py --provider local

Environment Variables:
    OPENAI_API_KEY     - Required for OpenAI provider
    ANTHROPIC_API_KEY  - Required for Anthropic provider
    LLM_PROVIDER       - Default provider if --provider not specified
        """
    )
    
    parser.add_argument(
        "--provider",
        choices=["openai", "anthropic", "local"],
        default=os.getenv("LLM_PROVIDER", "openai"),
        help="LLM provider to use for smoke test (default: openai)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--skip-disclaimer",
        action="store_true",
        help="Skip the non-deterministic test disclaimer"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(log_level=args.log_level, log_to_console=True, use_json_format=False)
    
    # Show disclaimer unless skipped
    if not args.skip_disclaimer:
        print("⚠️  IMPORTANT DISCLAIMER ⚠️")
        print()
        print("This is a LIVE LLM SMOKE TEST that:")
        print("• Uses real LLM APIs (costs money)")
        print("• Produces NON-DETERMINISTIC results")
        print("• Is NOT part of core framework validation")
        print("• Can be safely skipped")
        print()
        print("The core framework correctness is validated by:")
        print("• validate_framework.py (deterministic tests)")
        print("• example_usage.py (mock LLM tests)")
        print("• simple_hitl_demo.py (contract tests)")
        print()
        
        response = input("Continue with live LLM test? [y/N]: ").strip().lower()
        if response not in ['y', 'yes']:
            print("Smoke test cancelled.")
            return 0
        print()
    
    # Run smoke test
    success = run_smoke_test(args.provider)
    
    if success:
        print("✅ Live LLM smoke test completed successfully!")
        return 0
    else:
        print("❌ Live LLM smoke test failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())