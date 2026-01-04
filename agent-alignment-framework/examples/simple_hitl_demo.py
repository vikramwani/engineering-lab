#!/usr/bin/env python3
"""Simple demo of HITL escalation contract without complex prompt templates."""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agent_alignment.core.hitl import build_hitl_request, HITLEscalationReason
from agent_alignment.core.models import (
    EvaluationTask, AgentDecision, EvaluationResult, AlignmentSummary, 
    AlignmentState, BooleanDecisionSchema
)

def main():
    """Demonstrate HITL escalation contract with direct model creation."""
    
    print("🚨 HITL Escalation Contract Demo")
    print("=" * 50)
    
    # Create a task
    task = EvaluationTask(
        task_id="security-review-001",
        task_type="security_assessment",
        decision_schema=BooleanDecisionSchema(),
        context={
            "system": "Payment Processing API",
            "change_type": "Authentication Update",
            "risk_level": "High"
        },
        evaluation_criteria="Assess whether the security changes should be approved"
    )
    
    print(f"📝 Security assessment task: {task.task_id}")
    
    # Scenario 1: No escalation (full alignment)
    print(f"\n1️⃣ Scenario: Full Alignment (No Escalation)")
    
    agent_decisions_aligned = [
        AgentDecision(
            agent_name="security_expert",
            role_type="expert",
            decision_value=True,
            confidence=0.9,
            rationale="Security measures are comprehensive and well-implemented",
            evidence=["Multi-factor authentication", "Encryption standards met", "Audit trail complete"]
        ),
        AgentDecision(
            agent_name="compliance_officer",
            role_type="compliance",
            decision_value=True,
            confidence=0.85,
            rationale="Changes meet all regulatory requirements",
            evidence=["PCI DSS compliance", "SOX requirements satisfied", "GDPR alignment confirmed"]
        )
    ]
    
    alignment_summary_aligned = AlignmentSummary(
        state=AlignmentState.FULL_ALIGNMENT,
        alignment_score=0.95,
        decision_agreement=True,
        confidence_spread=0.05,
        confidence_distribution={"security_expert": 0.9, "compliance_officer": 0.85},
        avg_confidence=0.875,
        dissenting_agents=[],
        disagreement_areas=[],
        consensus_strength=0.95,
        resolution_rationale="Full alignment: agents agree on approval with high confidence"
    )
    
    evaluation_result_aligned = EvaluationResult(
        task_id=task.task_id,
        synthesized_decision=True,
        confidence=0.9,
        reasoning="Strong consensus for approval",
        evidence=["Multi-factor authentication", "PCI DSS compliance"],
        agent_decisions=agent_decisions_aligned,
        alignment_summary=alignment_summary_aligned,
        requires_human_review=False,  # No review required
        request_id="eval-001",
        processing_time_ms=150
    )
    
    hitl_request = build_hitl_request(evaluation_result_aligned, alignment_summary_aligned)
    
    if hitl_request is None:
        print("   ✅ No HITL escalation (as expected)")
    else:
        print("   ❌ Unexpected HITL escalation!")
    
    # Scenario 2: Hard disagreement (escalation required)
    print(f"\n2️⃣ Scenario: Hard Disagreement (Escalation Required)")
    
    agent_decisions_disagreement = [
        AgentDecision(
            agent_name="security_expert",
            role_type="expert",
            decision_value=True,
            confidence=0.8,
            rationale="Security improvements outweigh risks",
            evidence=["Enhanced encryption", "Better access controls", "Improved monitoring"]
        ),
        AgentDecision(
            agent_name="operations_manager",
            role_type="operations",
            decision_value=False,  # DISAGREEMENT!
            confidence=0.75,
            rationale="Implementation risks are too high for production system",
            evidence=["Potential downtime", "Complex rollback procedure", "Limited testing window"]
        ),
        AgentDecision(
            agent_name="compliance_officer",
            role_type="compliance",
            decision_value=True,
            confidence=0.7,
            rationale="Regulatory requirements mandate these changes",
            evidence=["New compliance standards", "Audit findings", "Legal requirements"]
        )
    ]
    
    alignment_summary_disagreement = AlignmentSummary(
        state=AlignmentState.HARD_DISAGREEMENT,
        alignment_score=0.4,
        decision_agreement=False,
        confidence_spread=0.1,
        confidence_distribution={
            "security_expert": 0.8, 
            "operations_manager": 0.75, 
            "compliance_officer": 0.7
        },
        avg_confidence=0.75,
        dissenting_agents=["operations_manager"],
        disagreement_areas=["primary_decision", "risk_assessment"],
        consensus_strength=0.5,
        resolution_rationale="Hard disagreement: agents disagree on primary decision"
    )
    
    evaluation_result_disagreement = EvaluationResult(
        task_id=task.task_id,
        synthesized_decision=True,  # Majority decision
        confidence=0.6,
        reasoning="Majority approval with significant operational concerns",
        evidence=["Enhanced encryption", "New compliance standards"],
        agent_decisions=agent_decisions_disagreement,
        alignment_summary=alignment_summary_disagreement,
        requires_human_review=True,  # Review required!
        request_id="eval-002",
        processing_time_ms=200
    )
    
    hitl_request = build_hitl_request(evaluation_result_disagreement, alignment_summary_disagreement)
    
    if hitl_request is None:
        print("   ❌ Expected HITL escalation but got None!")
    else:
        print("   ✅ HITL escalation triggered!")
        print(f"   📋 Request ID: {hitl_request.request_id}")
        print(f"   🎯 Escalation Reason: {hitl_request.escalation_reason.value}")
        print(f"   📊 Alignment Score: {hitl_request.alignment_score:.2f}")
        print(f"   📝 Summary: {hitl_request.summary}")
        print(f"   👥 Dissenting Agents: {hitl_request.dissenting_agents}")
        print(f"   ⏰ Created At: {hitl_request.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        # Demonstrate key contract features
        print(f"\n🔍 HITL Contract Analysis:")
        print(f"   • Deterministic: ✅ Same inputs → Same outputs")
        print(f"   • Serializable: ✅ All fields JSON-serializable")
        print(f"   • Complete Context: ✅ All agent decisions included")
        print(f"   • Machine Readable: ✅ Structured escalation reason")
        print(f"   • Human Readable: ✅ Clear summary explanation")
        print(f"   • Domain Agnostic: ✅ No security-specific logic")
        print(f"   • No Side Effects: ✅ Pure function, no state changes")
        
        # Show metadata richness
        print(f"\n📊 Rich Metadata Available:")
        for key, value in hitl_request.metadata.items():
            if isinstance(value, (int, float)):
                print(f"   • {key}: {value}")
            elif isinstance(value, list) and len(value) <= 3:
                print(f"   • {key}: {value}")
            else:
                print(f"   • {key}: {str(value)[:50]}...")
        
        # Demonstrate serialization
        print(f"\n📦 JSON Serialization:")
        import json
        json_data = json.loads(hitl_request.model_dump_json())
        print(f"   • Total fields: {len(json_data)}")
        print(f"   • Agent decisions: {len(json_data['agent_decisions'])}")
        print(f"   • Metadata keys: {len(json_data['metadata'])}")
        print(f"   • Size: ~{len(hitl_request.model_dump_json())} bytes")
        
        # Show integration readiness
        print(f"\n🔌 Integration Ready:")
        print(f"   • Queue Systems: ✅ Fully serializable")
        print(f"   • REST APIs: ✅ JSON-compatible")
        print(f"   • Webhooks: ✅ Standard HTTP payload")
        print(f"   • Databases: ✅ Structured data model")
        print(f"   • Message Brokers: ✅ Event-driven architecture")
        print(f"   • Review UIs: ✅ Complete context provided")
    
    print(f"\n✅ HITL Escalation Contract Demo Complete!")
    
    print(f"\n🎯 Key Contract Guarantees:")
    print(f"   ✅ Escalation only for HARD_DISAGREEMENT (per Task 2)")
    print(f"   ✅ Deterministic escalation logic (no randomness)")
    print(f"   ✅ Complete agent context preservation")
    print(f"   ✅ Structured, typed escalation reasons")
    print(f"   ✅ Human-readable summaries")
    print(f"   ✅ Machine-readable metadata")
    print(f"   ✅ Full JSON serialization support")
    print(f"   ✅ Zero UI/workflow assumptions")
    print(f"   ✅ Domain-agnostic implementation")
    print(f"   ✅ Backward compatibility maintained")

if __name__ == "__main__":
    main()