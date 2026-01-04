#!/usr/bin/env python3
"""Example usage of the Agent Alignment Framework.

This script demonstrates how to use the framework for product compatibility
evaluation with a simple mock LLM provider for testing.
"""

import json
import os
import sys
from typing import Any, Dict

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agent_alignment import (
    MultiAgentEvaluator,
    EvaluationTask,
    AgentRole,
    CategoricalDecisionSchema,
    LLMClient,
)
from agent_alignment.core.agent import LLMAgent
from agent_alignment.core.models import AgentDecision
from agent_alignment.llm.client import LLMProvider
from agent_alignment.config import FrameworkSettings
from agent_alignment.utils.logging import setup_logging
from agent_alignment.utils.validation import extract_json_from_text, normalize_confidence, normalize_confidence


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing without API calls."""
    
    def generate(self, prompt: str, max_tokens: int = 500, temperature: float = 0.1, **kwargs) -> str:
        """Generate mock responses based on agent role."""
        
        # Simple mock responses based on prompt content
        if "advocate" in prompt.lower() or "for compatibility" in prompt.lower():
            return """
            {
                "decision": "accessory",
                "confidence": 0.85,
                "reasoning": "The MagSafe charger is specifically designed as an accessory for iPhone devices. It provides wireless charging capability and is fully compatible with iPhone 15 Pro Max.",
                "evidence": [
                    "MagSafe technology is Apple's proprietary wireless charging standard",
                    "iPhone 15 Pro Max supports MagSafe charging up to 15W",
                    "Physical magnetic alignment ensures proper connection"
                ]
            }
            """
        
        elif "skeptic" in prompt.lower() or "against" in prompt.lower():
            return """
            {
                "decision": "accessory", 
                "confidence": 0.75,
                "reasoning": "While generally compatible, there are some limitations to consider. The charging speed may be slower than wired charging, and case compatibility could be an issue.",
                "evidence": [
                    "MagSafe charging is slower than Lightning cable charging",
                    "Thick cases may interfere with magnetic connection",
                    "Requires precise alignment for optimal charging"
                ]
            }
            """
        
        elif "judge" in prompt.lower():
            return """
            {
                "decision": "accessory",
                "confidence": 0.90,
                "reasoning": "Based on the evidence from both perspectives, the MagSafe charger is clearly designed as a compatible accessory for the iPhone 15 Pro Max. While there are minor limitations, the fundamental compatibility is strong.",
                "evidence": [
                    "Apple designed MagSafe specifically for iPhone compatibility",
                    "iPhone 15 Pro Max has built-in MagSafe support",
                    "Widespread successful usage confirms compatibility"
                ]
            }
            """
        
        else:
            return """
            {
                "decision": "accessory",
                "confidence": 0.80,
                "reasoning": "General compatibility assessment indicates these products work together.",
                "evidence": ["Compatible design", "Shared standards"]
            }
            """
    
    def get_provider_name(self) -> str:
        return "mock-llm"


class DemoAgent(LLMAgent):
    """Demo agent implementation for testing."""
    
    def _build_prompt(self, task: EvaluationTask) -> str:
        """Build prompt using external template with strict separation."""
        # Load the prompt template
        template = self._load_prompt_template()
        
        # Extract product information
        product_a = task.context.get("product_a", {})
        product_b = task.context.get("product_b", {})
        
        # Format product information
        product_a_info = self._format_product_info(product_a, "Product A")
        product_b_info = self._format_product_info(product_b, "Product B")
        
        # Get relationship types if available
        relationship_types = task.context.get("relationship_types", [])
        relationship_info = ""
        if relationship_types:
            relationship_info = f"\nValid relationship types: {', '.join(relationship_types)}"
        
        # Format the complete prompt
        prompt = template.format(
            agent_role=self.role.instruction,
            evaluation_criteria=task.evaluation_criteria,
            product_a_info=product_a_info,
            product_b_info=product_b_info,
            relationship_info=relationship_info,
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
                decision_value="accessory",
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
    
    def _format_product_info(self, product: Dict[str, Any], label: str) -> str:
        """Format product information for inclusion in prompts."""
        if not product:
            return f"{label}: No information provided"
        
        info_lines = [f"{label}:"]
        
        # Standard fields
        for field in ["id", "title", "name", "category", "brand", "manufacturer"]:
            if field in product:
                info_lines.append(f"  {field.title()}: {product[field]}")
        
        # Attributes
        if "attributes" in product and isinstance(product["attributes"], dict):
            info_lines.append("  Attributes:")
            for key, value in product["attributes"].items():
                info_lines.append(f"    {key}: {value}")
        
        # Description
        if "description" in product:
            info_lines.append(f"  Description: {product['description']}")
        
        return "\n".join(info_lines)


def main():
    """Demonstrate framework usage."""
    
    # Setup logging
    setup_logging(log_level="INFO", log_to_console=True, use_json_format=False)
    
    print("🤖 Agent Alignment Framework Demo")
    print("=" * 50)
    
    # Create mock LLM client
    provider = MockLLMProvider()
    llm_client = LLMClient(provider, max_retries=1, timeout_seconds=10)
    
    print(f"✅ LLM Client initialized with {provider.get_provider_name()}")
    
    # Example 1: Direct framework usage
    print("\n📋 Example 1: Direct Framework Usage")
    print("-" * 30)
    
    # Define agent roles
    agent_roles = [
        AgentRole(
            name="advocate_agent",
            role_type="advocate",
            instruction="Analyze products and argue FOR compatibility",
            prompt_template="examples/demo/prompts/advocate.txt",
            max_tokens=300,
            temperature=0.1,
        ),
        AgentRole(
            name="skeptic_agent", 
            role_type="skeptic",
            instruction="Analyze products and challenge compatibility assumptions",
            prompt_template="examples/demo/prompts/skeptic.txt",
            max_tokens=300,
            temperature=0.1,
        ),
        AgentRole(
            name="judge_agent",
            role_type="judge",
            instruction="Review both perspectives and make final compatibility decision",
            prompt_template="examples/demo/prompts/judge.txt",
            max_tokens=300,
            temperature=0.1,
        ),
    ]
    
    # Create evaluator with demo agent class
    evaluator = MultiAgentEvaluator.from_roles(
        roles=agent_roles,
        llm_client=llm_client,
        agent_class=DemoAgent,
    )
    
    print(f"✅ Multi-agent evaluator created with {len(agent_roles)} agents")
    
    # Define evaluation task
    task = EvaluationTask(
        task_id="demo-001",
        task_type="product_compatibility",
        decision_schema=CategoricalDecisionSchema(categories=[
            "replacement_filter", "replacement_part", "accessory", 
            "consumable", "power_supply", "not_compatible", "insufficient_information"
        ]),
        context={
            "product_a": {
                "id": "IPHONE-15-PRO-MAX",
                "title": "iPhone 15 Pro Max",
                "category": "Smartphone",
                "brand": "Apple",
                "attributes": {
                    "screen_size": "6.7 inches",
                    "storage": "256GB",
                    "color": "Natural Titanium",
                    "charging": "Lightning, MagSafe, Qi wireless"
                }
            },
            "product_b": {
                "id": "MAGSAFE-CHARGER",
                "title": "MagSafe Charger",
                "category": "Charger",
                "brand": "Apple", 
                "attributes": {
                    "power": "15W",
                    "connector": "MagSafe magnetic",
                    "compatibility": "iPhone 12 and later"
                }
            },
            "domain": "product_compatibility"
        },
        evaluation_criteria="Determine if these products are compatible and classify their relationship type"
    )
    
    print(f"📝 Evaluation task created: {task.task_id}")
    
    # Run evaluation
    print("\n🔄 Running multi-agent evaluation...")
    result = evaluator.evaluate(task)
    
    # Display results
    print(f"\n📊 Evaluation Results:")
    print(f"   Decision: {result.synthesized_decision}")
    print(f"   Confidence: {result.confidence:.2f}")
    print(f"   Alignment: {result.alignment_summary.state.value}")
    print(f"   Needs Review: {result.requires_human_review}")
    print(f"   Processing Time: {result.processing_time_ms}ms")
    
    print(f"\n🤝 Agent Decisions:")
    for output in result.agent_decisions:
        print(f"   {output.agent_name}: {output.decision_value} (confidence: {output.confidence:.2f})")
    
    print(f"\n📈 Alignment Analysis:")
    print(f"   Decision Agreement: {result.alignment_summary.decision_agreement}")
    print(f"   Confidence Spread: {result.alignment_summary.confidence_spread:.2f}")
    print(f"   Average Confidence: {result.alignment_summary.avg_confidence:.2f}")
    print(f"   Consensus Strength: {result.alignment_summary.consensus_strength:.2f}")
    
    if result.alignment_summary.disagreement_areas:
        print(f"   Disagreement Areas: {', '.join(result.alignment_summary.disagreement_areas)}")
    
    # Example 2: Different alignment scenarios
    print(f"\n📋 Example 2: Framework Capabilities")
    print("-" * 35)
    
    capabilities = [
        "✅ Multi-agent orchestration with role-based perspectives",
        "✅ Automatic disagreement detection and alignment analysis", 
        "✅ Flexible decision types (Boolean, Categorical, Scalar, Free-form)",
        "✅ Human-in-the-loop integration for complex cases",
        "✅ Structured logging and request tracing",
        "✅ Multiple LLM provider support (OpenAI, Anthropic, Local)",
        "✅ Production-ready error handling and validation",
        "✅ Extensible architecture for custom use cases"
    ]
    
    for capability in capabilities:
        print(f"   {capability}")
    
    # Example 3: Alignment states demonstration
    print(f"\n📋 Example 3: Alignment States")
    print("-" * 30)
    
    alignment_examples = [
        {
            "scenario": "Full Agreement",
            "state": "FULL_ALIGNMENT",
            "description": "All agents agree on decision and have high confidence"
        },
        {
            "scenario": "Soft Disagreement", 
            "state": "SOFT_DISAGREEMENT",
            "description": "Agents agree on decision but differ on confidence or evidence"
        },
        {
            "scenario": "Hard Disagreement",
            "state": "HARD_DISAGREEMENT", 
            "description": "Agents fundamentally disagree on the decision"
        },
        {
            "scenario": "Insufficient Signal",
            "state": "INSUFFICIENT_SIGNAL",
            "description": "Agents lack confidence or sufficient information"
        }
    ]
    
    for example in alignment_examples:
        print(f"   {example['scenario']}: {example['description']}")
    
    print(f"\n✅ Demo completed successfully!")
    print(f"\nNext steps:")
    print(f"   1. Set up real LLM provider (OpenAI, Anthropic, etc.)")
    print(f"   2. Create domain-specific prompt templates")
    print(f"   3. Implement custom agents for your use case")
    print(f"   4. Configure human-in-the-loop integration")
    print(f"   5. Add monitoring and observability")
    
    print(f"\n📚 Documentation:")
    print(f"   - Architecture: docs/architecture.md")
    print(f"   - Adding Use Cases: docs/adding-a-new-use-case.md")
    print(f"   - Examples: examples/compatibility/")


if __name__ == "__main__":
    main()