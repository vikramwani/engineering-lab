#!/usr/bin/env python3
"""Demo script showing HITL escalation contract in action."""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agent_alignment import (
    MultiAgentEvaluator, EvaluationTask, AgentRole, CategoricalDecisionSchema, LLMClient
)
from agent_alignment.core.hitl import build_hitl_request
from agent_alignment.core.agent import LLMAgent
from agent_alignment.core.models import AgentDecision
from agent_alignment.llm.providers import LLMProvider
from agent_alignment.utils.logging import setup_logging
from agent_alignment.utils.validation import extract_json_from_text, normalize_confidence

class MockLLMProvider(LLMProvider):
    """Mock LLM provider that creates disagreement."""
    
    def generate(self, prompt: str, max_tokens: int = 500, temperature: float = 0.1, **kwargs) -> str:
        """Generate responses that will create hard disagreement."""
        
        if "advocate" in prompt.lower():
            return """
            {
                "decision": "high_risk",
                "confidence": 0.85,
                "reasoning": "This proposal has significant potential for positive impact and should be approved.",
                "evidence": [
                    "Strong market demand indicators",
                    "Positive stakeholder feedback",
                    "Alignment with strategic objectives"
                ]
            }
            """
        
        elif "skeptic" in prompt.lower():
            return """
            {
                "decision": "low_risk", 
                "confidence": 0.80,
                "reasoning": "This proposal carries substantial risks that outweigh potential benefits.",
                "evidence": [
                    "Significant regulatory compliance concerns",
                    "High implementation costs",
                    "Uncertain market conditions"
                ]
            }
            """
        
        else:  # judge
            return """
            {
                "decision": "medium_risk",
                "confidence": 0.70,
                "reasoning": "Mixed signals from the analysis require careful consideration of both perspectives.",
                "evidence": [
                    "Balanced assessment of risks and benefits",
                    "Need for additional stakeholder input"
                ]
            }
            """
    
    def get_provider_name(self) -> str:
        return "mock-disagreement-llm"

class DemoAgent(LLMAgent):
    """Demo agent implementation for HITL escalation testing."""
    
    def _build_prompt(self, task: EvaluationTask) -> str:
        """Build prompt using external template with strict separation."""
        # Load the prompt template
        template = self._load_prompt_template()
        
        # Extract proposal information
        proposal = task.context.get("proposal", {})
        criteria = task.context.get("evaluation_criteria", [])
        
        # Format proposal information
        proposal_info = self._format_proposal_info(proposal)
        criteria_info = "\n".join(f"- {criterion}" for criterion in criteria)
        
        # Format the complete prompt
        prompt = template.format(
            agent_role=self.role.instruction,
            evaluation_criteria=task.evaluation_criteria,
            proposal_info=proposal_info,
            criteria_info=criteria_info,
            task_type=task.task_type,
        )
        
        return prompt
    
    def _parse_response(self, task: EvaluationTask, response: str, request_id: str) -> AgentDecision:
        """Parse the LLM response into structured output."""
        json_data = extract_json_from_text(response)
        
        if json_data is None:
            # Fallback for demo purposes
            return AgentDecision(
                agent_name=self.role.name,
                role_type=self.role.role_type,
                decision_value="medium_risk",
                confidence=0.75,
                rationale="Demo fallback response",
                evidence=["Demo evidence"],
                metadata={"request_id": request_id, "response_format": "fallback"}
            )
        
        # Extract required fields
        decision = json_data.get("decision", "insufficient_information")
        confidence = normalize_confidence(json_data.get("confidence", 0.5))
        reasoning = json_data.get("reasoning", "No reasoning provided")
        evidence = json_data.get("evidence", [])
        
        return AgentDecision(
            agent_name=self.role.name,
            role_type=self.role.role_type,
            decision_value=decision,
            confidence=confidence,
            rationale=reasoning,
            evidence=evidence if isinstance(evidence, list) else [str(evidence)],
            metadata={"request_id": request_id, "response_format": "json"}
        )
    
    def _format_proposal_info(self, proposal: dict) -> str:
        """Format proposal information for inclusion in prompts."""
        if not proposal:
            return "No proposal information provided"
        
        info_lines = ["Proposal Details:"]
        
        # Standard fields
        for field in ["id", "title", "description", "budget", "timeline"]:
            if field in proposal:
                info_lines.append(f"  {field.title()}: {proposal[field]}")
        
        # Stakeholders
        if "stakeholders" in proposal and isinstance(proposal["stakeholders"], list):
            info_lines.append("  Stakeholders:")
            for stakeholder in proposal["stakeholders"]:
                info_lines.append(f"    - {stakeholder}")
        
        return "\n".join(info_lines)


def main():
    """Demonstrate HITL escalation contract."""
    
    # Setup logging
    setup_logging(log_level="INFO", log_to_console=True, use_json_format=False)
    
    print("🚨 HITL Escalation Contract Demo")
    print("=" * 50)
    
    # Create LLM client that will generate disagreement
    provider = MockLLMProvider()
    llm_client = LLMClient(provider, max_retries=1, timeout_seconds=10)
    
    print(f"✅ LLM Client initialized with {provider.get_provider_name()}")
    
    # Define agent roles for risk assessment
    agent_roles = [
        AgentRole(
            name="risk_advocate",
            role_type="advocate",
            instruction="Analyze the proposal and argue for its approval, focusing on benefits and opportunities",
            prompt_template="examples/demo/prompts/advocate.txt",
            max_tokens=300,
            temperature=0.1,
        ),
        AgentRole(
            name="risk_skeptic", 
            role_type="skeptic",
            instruction="Analyze the proposal and identify risks, concerns, and reasons for rejection",
            prompt_template="examples/demo/prompts/skeptic.txt",
            max_tokens=300,
            temperature=0.1,
        ),
        AgentRole(
            name="risk_judge",
            role_type="judge",
            instruction="Review both perspectives and make a balanced risk assessment",
            prompt_template="examples/demo/prompts/judge.txt",
            max_tokens=300,
            temperature=0.1,
        ),
    ]
    
    # Create evaluator
    evaluator = MultiAgentEvaluator.from_roles(
        roles=agent_roles,
        llm_client=llm_client,
        agent_class=DemoAgent,
    )
    
    print(f"✅ Multi-agent evaluator created with {len(agent_roles)} agents")
    
    # Define evaluation task that will trigger disagreement
    task = EvaluationTask(
        task_id="risk-assessment-001",
        task_type="risk_assessment",
        decision_schema=CategoricalDecisionSchema(categories=[
            "low_risk", "medium_risk", "high_risk", "insufficient_information"
        ]),
        context={
            "proposal": {
                "id": "PROP-2026-001",
                "title": "New Market Expansion Initiative",
                "description": "Proposal to expand operations into emerging markets",
                "budget": "$2.5M",
                "timeline": "18 months",
                "stakeholders": ["Product", "Marketing", "Legal", "Finance"]
            },
            "evaluation_criteria": [
                "Market opportunity assessment",
                "Regulatory compliance requirements", 
                "Financial risk analysis",
                "Implementation feasibility"
            ]
        },
        evaluation_criteria="Assess the risk level of this market expansion proposal"
    )
    
    print(f"📝 Risk assessment task created: {task.task_id}")
    
    # Run evaluation (this will create disagreement)
    print("\n🔄 Running multi-agent risk assessment...")
    result = evaluator.evaluate(task)
    
    # Display results
    print(f"\n📊 Evaluation Results:")
    print(f"   Decision: {result.synthesized_decision}")
    print(f"   Confidence: {result.confidence:.2f}")
    print(f"   Alignment: {result.alignment_summary.state.value}")
    print(f"   Needs Review: {result.requires_human_review}")
    
    print(f"\n🤝 Agent Risk Assessments:")
    for decision in result.agent_decisions:
        print(f"   {decision.agent_name}: {decision.decision_value} (confidence: {decision.confidence:.2f})")
    
    print(f"\n📈 Alignment Analysis:")
    print(f"   Decision Agreement: {result.alignment_summary.decision_agreement}")
    print(f"   Confidence Spread: {result.alignment_summary.confidence_spread:.2f}")
    print(f"   Dissenting Agents: {result.alignment_summary.dissenting_agents}")
    print(f"   Disagreement Areas: {result.alignment_summary.disagreement_areas}")
    
    # Test HITL escalation contract
    print(f"\n🚨 HITL Escalation Contract:")
    
    hitl_request = build_hitl_request(result, result.alignment_summary)
    
    if hitl_request is None:
        print("   ❌ No HITL escalation triggered")
    else:
        print("   ✅ HITL escalation triggered!")
        print(f"   📋 Request ID: {hitl_request.request_id}")
        print(f"   🎯 Escalation Reason: {hitl_request.escalation_reason.value}")
        print(f"   📊 Alignment Score: {hitl_request.alignment_score:.2f}")
        print(f"   📝 Summary: {hitl_request.summary}")
        print(f"   👥 Dissenting Agents: {hitl_request.dissenting_agents}")
        print(f"   ⏰ Created At: {hitl_request.created_at.isoformat()}")
        
        # Show serialization capability
        print(f"\n📦 Serialized HITL Request (JSON):")
        import json
        serialized = json.loads(hitl_request.model_dump_json())
        print(json.dumps(serialized, indent=2)[:500] + "...")
        
        print(f"\n🔌 Integration Points:")
        print(f"   • Request can be sent to any review system")
        print(f"   • Contains all context needed for human reviewer")
        print(f"   • Deterministic and reproducible")
        print(f"   • No UI or workflow assumptions")
        print(f"   • Fully serializable for queues/APIs")
    
    print(f"\n✅ HITL Escalation Contract Demo completed!")
    print(f"\n📚 Key Features Demonstrated:")
    print(f"   ✅ Pure, deterministic escalation logic")
    print(f"   ✅ Structured, serializable HITL requests")
    print(f"   ✅ Clear escalation reasons and summaries")
    print(f"   ✅ Complete agent context preservation")
    print(f"   ✅ Domain-agnostic escalation contract")
    print(f"   ✅ Zero UI/workflow assumptions")

if __name__ == "__main__":
    main()