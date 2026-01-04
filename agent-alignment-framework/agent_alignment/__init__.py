"""Agent Alignment Framework - Multi-Agent Evaluation System.

A production-ready framework for building multi-agent evaluation systems
with disagreement detection, alignment analysis, and human-in-the-loop capabilities.

Public API Surface:
- Core evaluation classes: MultiAgentEvaluator, EvaluationTask, AgentRole
- Decision models: AgentDecision, EvaluationResult, AlignmentSummary
- Decision schemas: BooleanDecisionSchema, CategoricalDecisionSchema, etc.
- Alignment engine: AlignmentEngine, AlignmentThresholds, AlignmentState
- HITL contract: HITLRequest, HITLEscalationReason, build_hitl_request
- Agent base classes: BaseAgent
- LLM integration: LLMClient

Internal implementation details are not part of the public API.
"""

# Core evaluation classes (public API)
from .core.evaluator import MultiAgentEvaluator
from .core.models import (
    # Primary models
    EvaluationTask,
    AgentRole,
    AgentDecision,
    EvaluationResult,
    AlignmentSummary,
    AlignmentState,
    
    # Decision schemas
    DecisionSchema,
    BooleanDecisionSchema,
    CategoricalDecisionSchema,
    ScalarDecisionSchema,
    FreeFormDecisionSchema,
    
    # Legacy aliases for backward compatibility (deprecated)
    AgentOutput,  # -> AgentDecision
    DecisionType,  # -> DecisionSchema
    BooleanDecision,  # -> BooleanDecisionSchema
    CategoricalDecision,  # -> CategoricalDecisionSchema
    ScalarDecision,  # -> ScalarDecisionSchema
    FreeFormDecision,  # -> FreeFormDecisionSchema
    
    # Legacy HITL models (deprecated - use core.hitl instead)
    HumanReviewRequest,
    HumanReviewDecision,
    HumanReviewStatus,
    HITLRequest as LegacyHITLRequest,  # Legacy alias
    HITLResponse,  # Legacy alias
)

# Agent base classes (public API)
from .core.agent import BaseAgent

# Alignment engine (public API)
from .core.resolution import AlignmentEngine, AlignmentThresholds

# HITL escalation contract (public API)
from .core.hitl import HITLRequest, HITLEscalationReason, build_hitl_request

# LLM integration (public API)
from .llm.client import LLMClient

__version__ = "0.1.0"

# Explicit public API definition
__all__ = [
    # Core evaluation
    "MultiAgentEvaluator",
    "EvaluationTask", 
    "AgentRole",
    "AgentDecision",
    "EvaluationResult",
    "AlignmentSummary",
    "AlignmentState",
    
    # Decision schemas
    "DecisionSchema",
    "BooleanDecisionSchema",
    "CategoricalDecisionSchema", 
    "ScalarDecisionSchema",
    "FreeFormDecisionSchema",
    
    # Agent base classes
    "BaseAgent",
    
    # Alignment engine
    "AlignmentEngine",
    "AlignmentThresholds",
    
    # LLM integration
    "LLMClient",
    
    # HITL escalation contract
    "HITLRequest",
    "HITLEscalationReason", 
    "build_hitl_request",
    
    # Legacy aliases (deprecated)
    "AgentOutput",
    "DecisionType",
    "BooleanDecision",
    "CategoricalDecision",
    "ScalarDecision",
    "FreeFormDecision",
    "HumanReviewRequest",
    "HumanReviewDecision", 
    "HumanReviewStatus",
    "LegacyHITLRequest",
    "HITLResponse",
]