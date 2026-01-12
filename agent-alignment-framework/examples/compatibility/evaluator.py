"""Product compatibility evaluator using the agent alignment framework.

This module demonstrates how to use the generic framework for a specific
use case - evaluating product compatibility relationships.
"""

from typing import Any, Dict, List, Optional

from agent_alignment import (
    MultiAgentEvaluator,
    EvaluationTask,
    AgentRole,
    BooleanDecisionSchema,
    CategoricalDecisionSchema,
    LLMClient,
)
from agent_alignment.core.resolution import AlignmentThresholds
from agent_alignment.llm.providers import OpenAIProvider

from examples.compatibility.agents import CompatibilityAgent


class CompatibilityEvaluator:
    """Specialized evaluator for product compatibility assessment.
    
    This class provides a domain-specific interface for evaluating whether
    two products are compatible and what type of relationship they have.
    """
    
    # Standard compatibility relationships
    COMPATIBILITY_RELATIONSHIPS = [
        "replacement_filter",
        "replacement_part", 
        "accessory",
        "consumable",
        "power_supply",
        "not_compatible",
        "insufficient_information",
    ]
    
    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        alignment_thresholds: Optional[AlignmentThresholds] = None,
    ):
        """Initialize the compatibility evaluator.
        
        Args:
            llm_client: LLM client for agent communication
            alignment_thresholds: Alignment thresholds for disagreement handling (uses defaults if None)
        """
        # Create LLM client if not provided
        if llm_client is None:
            import os
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required")
            
            provider = OpenAIProvider(
                api_key=api_key,
                model="gpt-4o-mini",
            )
            llm_client = LLMClient(
                provider=provider,
                max_retries=3,
                timeout_seconds=30,
            )
        
        self.llm_client = llm_client
        
        # Create agent roles
        agent_roles = self._create_agent_roles()
        
        # Create alignment thresholds if not provided
        if alignment_thresholds is None:
            # Use compatibility-specific thresholds
            alignment_thresholds = AlignmentThresholds(
                soft_disagreement_confidence_spread=0.15,  # More sensitive for compatibility
                hard_disagreement_confidence_spread=0.3,
                insufficient_signal_avg_confidence=0.6,
                min_confidence_for_consensus=0.75,
            )
        
        # Create multi-agent evaluator
        self.evaluator = MultiAgentEvaluator.from_roles(
            roles=agent_roles,
            llm_client=llm_client,
            agent_class=CompatibilityAgent,
            alignment_thresholds=alignment_thresholds,
        )
    
    def evaluate_compatibility(
        self,
        product_a: Dict[str, Any],
        product_b: Dict[str, Any],
        task_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Evaluate compatibility between two products.
        
        Args:
            product_a: First product information
            product_b: Second product information
            task_id: Optional task identifier
            
        Returns:
            Dict with compatibility assessment results
        """
        # Create evaluation task
        task = EvaluationTask(
            task_id=task_id or f"compat_{hash((str(product_a), str(product_b)))}"[:8],
            task_type="product_compatibility",
            decision_schema=CategoricalDecisionSchema(categories=self.COMPATIBILITY_RELATIONSHIPS),
            context={
                "product_a": product_a,
                "product_b": product_b,
                "domain": "product_compatibility",
                "relationship_types": self.COMPATIBILITY_RELATIONSHIPS,
            },
            evaluation_criteria=(
                "Determine if these products are compatible and classify their relationship type. "
                "Consider factors like physical compatibility, functional compatibility, "
                "brand compatibility, and intended use cases."
            ),
        )
        
        # Run evaluation
        result = self.evaluator.evaluate(task)
        
        # Convert to compatibility-specific format
        return {
            "compatible": result.synthesized_decision != "not_compatible",
            "relationship": result.synthesized_decision,
            "synthesized_decision": result.synthesized_decision,  # Add this field
            "confidence": result.confidence,
            "explanation": result.reasoning,
            "evidence": result.evidence,
            "agent_decisions": [
                {
                    "agent_name": output.agent_name,
                    "role_type": output.role_type,
                    "decision_value": output.decision_value,  # Add this field
                    "compatible": output.decision_value != "not_compatible",
                    "relationship": output.decision_value,
                    "confidence": output.confidence,
                    "reasoning": output.rationale,
                    "evidence": output.evidence,
                }
                for output in result.agent_decisions
            ],
            "alignment_summary": {
                "state": result.alignment_summary.state.value,
                "decision_agreement": result.alignment_summary.decision_agreement,
                "confidence_spread": result.alignment_summary.confidence_spread,
                "avg_confidence": result.alignment_summary.avg_confidence,
                "disagreement_areas": result.alignment_summary.disagreement_areas,
            },
            "needs_human_review": result.requires_human_review,
            "review_reason": result.review_reason,
            "request_id": result.request_id,
            "processing_time_ms": result.processing_time_ms,
        }
    
    def evaluate_simple_compatibility(
        self,
        product_a: Dict[str, Any],
        product_b: Dict[str, Any],
        task_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Evaluate simple boolean compatibility between two products.
        
        Args:
            product_a: First product information
            product_b: Second product information
            task_id: Optional task identifier
            
        Returns:
            Dict with simple compatibility results
        """
        # Create evaluation task for boolean decision
        task = EvaluationTask(
            task_id=task_id or f"simple_compat_{hash((str(product_a), str(product_b)))}"[:8],
            task_type="simple_compatibility",
            decision_schema=BooleanDecisionSchema(
                positive_label="compatible",
                negative_label="incompatible"
            ),
            context={
                "product_a": product_a,
                "product_b": product_b,
                "domain": "simple_compatibility",
                "evaluation_type": "boolean",
            },
            evaluation_criteria=(
                "Determine if these products are compatible for use together. "
                "Focus on whether they can work together functionally."
            ),
        )
        
        # Run evaluation
        result = self.evaluator.evaluate(task)
        
        # Convert to simple format
        return {
            "compatible": result.synthesized_decision,
            "confidence": result.confidence,
            "explanation": result.reasoning,
            "evidence": result.evidence,
            "needs_human_review": result.requires_human_review,
            "request_id": result.request_id,
        }
    
    def _create_agent_roles(self) -> List[AgentRole]:
        """Create agent roles for compatibility evaluation."""
        return [
            AgentRole(
                name="advocate_agent",
                role_type="advocate",
                instruction=(
                    "Analyze the products and argue FOR compatibility. "
                    "Look for evidence that the products can work together, "
                    "share common standards, or complement each other's functionality."
                ),
                prompt_template="examples/compatibility/prompts/advocate.txt",
                max_tokens=500,
                temperature=0.1,
            ),
            AgentRole(
                name="skeptic_agent",
                role_type="skeptic",
                instruction=(
                    "Analyze the products and argue AGAINST compatibility. "
                    "Look for evidence of incompatibility, conflicting standards, "
                    "or reasons why the products cannot work together."
                ),
                prompt_template="examples/compatibility/prompts/skeptic.txt",
                max_tokens=500,
                temperature=0.1,
            ),
            AgentRole(
                name="judge_agent",
                role_type="judge",
                instruction=(
                    "Review the arguments from both the advocate and skeptic agents. "
                    "Make a final decision about compatibility and relationship type "
                    "based on the evidence presented."
                ),
                prompt_template="examples/compatibility/prompts/judge.txt",
                max_tokens=600,
                temperature=0.05,
            ),
        ]