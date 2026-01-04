"""Core framework components for multi-agent evaluation."""

from .models import (
    EvaluationTask,
    AgentRole,
    AgentDecision,
    AgentOutput,  # Legacy alias
    EvaluationResult,
    AlignmentSummary,
    AlignmentState,
    DecisionSchema,
    BooleanDecisionSchema,
    CategoricalDecisionSchema,
    ScalarDecisionSchema,
    FreeFormDecisionSchema,
    # Legacy aliases
    DecisionType,
    BooleanDecision,
    CategoricalDecision,
    ScalarDecision,
    FreeFormDecision,
    # HITL models
    HumanReviewRequest,
    HumanReviewDecision,
    HumanReviewStatus,
)
from .agent import BaseAgent
from .evaluator import MultiAgentEvaluator
from .resolution import AlignmentEngine

__all__ = [
    "EvaluationTask",
    "AgentRole", 
    "AgentDecision",
    "AgentOutput",  # Legacy alias
    "EvaluationResult",
    "AlignmentSummary",
    "AlignmentState",
    "DecisionSchema",
    "BooleanDecisionSchema",
    "CategoricalDecisionSchema",
    "ScalarDecisionSchema", 
    "FreeFormDecisionSchema",
    # Legacy aliases
    "DecisionType",
    "BooleanDecision",
    "CategoricalDecision",
    "ScalarDecision",
    "FreeFormDecision",
    # Core classes
    "BaseAgent",
    "MultiAgentEvaluator",
    "AlignmentEngine",
    # HITL models
    "HumanReviewRequest",
    "HumanReviewDecision",
    "HumanReviewStatus",
]