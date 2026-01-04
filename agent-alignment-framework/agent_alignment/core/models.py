"""Core data models for the agent alignment framework.

This module defines the fundamental data structures used throughout the framework,
including evaluation tasks, agent decisions, alignment analysis, and decision schemas.
All models are designed to be fully domain-agnostic and support open-ended evaluations.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator


class AlignmentState(str, Enum):
    """Represents the alignment state between multiple agents.
    
    These states are determined by analyzing agent decisions and confidence levels
    according to configurable thresholds in the alignment policy.
    """
    
    FULL_ALIGNMENT = "full_alignment"
    SOFT_DISAGREEMENT = "soft_disagreement"  
    HARD_DISAGREEMENT = "hard_disagreement"
    INSUFFICIENT_SIGNAL = "insufficient_signal"


class DecisionSchema(BaseModel, ABC):
    """Abstract base class for different types of evaluation decision schemas.
    
    Decision schemas define the structure and validation rules for agent decisions.
    They are completely domain-agnostic and can represent any type of decision.
    """
    
    @abstractmethod
    def validate_decision(self, decision: Any) -> bool:
        """Validate that a decision conforms to this schema.
        
        Args:
            decision: The decision value to validate
            
        Returns:
            bool: True if the decision is valid for this schema
        """
        pass
    
    @abstractmethod
    def normalize_confidence(self, confidence: float) -> float:
        """Normalize confidence score to [0.0, 1.0] range.
        
        Args:
            confidence: Raw confidence value
            
        Returns:
            float: Normalized confidence in [0.0, 1.0] range
        """
        pass
    
    @abstractmethod
    def get_schema_type(self) -> str:
        """Get the schema type identifier.
        
        Returns:
            str: Schema type name (e.g., 'boolean', 'categorical', 'scalar', 'freeform')
        """
        pass


class BooleanDecisionSchema(DecisionSchema):
    """Boolean decision schema for binary evaluations.
    
    Supports any binary decision with customizable labels.
    Examples: compatible/incompatible, approve/reject, safe/unsafe.
    """
    
    positive_label: str = Field(default="positive", description="Label for positive/true decisions")
    negative_label: str = Field(default="negative", description="Label for negative/false decisions")
    
    def validate_decision(self, decision: Any) -> bool:
        """Validate that decision is a boolean value.
        
        Args:
            decision: The decision value to validate
            
        Returns:
            bool: True if decision is a boolean, False otherwise
        """
        return isinstance(decision, bool)
    
    def normalize_confidence(self, confidence: float) -> float:
        """Ensure confidence is in [0.0, 1.0] range.
        
        Args:
            confidence: Raw confidence value
            
        Returns:
            float: Confidence clamped to [0.0, 1.0] range
        """
        return max(0.0, min(1.0, float(confidence)))
    
    def get_schema_type(self) -> str:
        """Get schema type identifier.
        
        Returns:
            str: The string "boolean"
        """
        return "boolean"


class CategoricalDecisionSchema(DecisionSchema):
    """Categorical decision schema for classification into predefined categories.
    
    Supports single or multiple category selection from a predefined set.
    Examples: risk levels, content categories, priority classifications.
    """
    
    categories: List[str] = Field(..., min_items=2, description="Valid categories for decisions")
    allow_multiple: bool = Field(default=False, description="Whether multiple categories can be selected")
    
    @validator('categories')
    def validate_categories(cls, v: List[str]) -> List[str]:
        """Ensure categories are unique and non-empty.
        
        Args:
            v: List of category strings to validate
            
        Returns:
            List[str]: Validated list of categories
            
        Raises:
            ValueError: If categories are not unique or contain empty strings
        """
        if len(set(v)) != len(v):
            raise ValueError("Categories must be unique")
        if any(not cat.strip() for cat in v):
            raise ValueError("Categories cannot be empty strings")
        return v
    
    def validate_decision(self, decision: Any) -> bool:
        """Validate that decision is a valid category or list of categories.
        
        Args:
            decision: The decision value to validate (string or list of strings)
            
        Returns:
            bool: True if decision matches schema constraints, False otherwise
        """
        if self.allow_multiple:
            if not isinstance(decision, list):
                return False
            return all(item in self.categories for item in decision)
        else:
            return decision in self.categories
    
    def normalize_confidence(self, confidence: float) -> float:
        """Ensure confidence is in [0.0, 1.0] range.
        
        Args:
            confidence: Raw confidence value
            
        Returns:
            float: Confidence clamped to [0.0, 1.0] range
        """
        return max(0.0, min(1.0, float(confidence)))
    
    def get_schema_type(self) -> str:
        """Get schema type identifier.
        
        Returns:
            str: The string "categorical"
        """
        return "categorical"


class ScalarDecisionSchema(DecisionSchema):
    """Scalar decision schema for numeric evaluations within a defined range.
    
    Supports any numeric decision with configurable min/max bounds.
    Examples: risk scores (0-100), ratings (1-5), probabilities (0.0-1.0).
    """
    
    min_value: float = Field(default=0.0, description="Minimum allowed value")
    max_value: float = Field(default=1.0, description="Maximum allowed value")
    
    @validator('max_value')
    def validate_range(cls, v: float, values: Dict[str, Any]) -> float:
        """Ensure max_value is greater than min_value.
        
        Args:
            v: The max_value to validate
            values: Dictionary of previously validated field values
            
        Returns:
            float: Validated max_value
            
        Raises:
            ValueError: If max_value is not greater than min_value
        """
        if 'min_value' in values and v <= values['min_value']:
            raise ValueError("max_value must be greater than min_value")
        return v
    
    def validate_decision(self, decision: Any) -> bool:
        """Validate that decision is a number within the specified range.
        
        Args:
            decision: The decision value to validate
            
        Returns:
            bool: True if decision is numeric and within [min_value, max_value], False otherwise
        """
        if not isinstance(decision, (int, float)):
            return False
        return self.min_value <= decision <= self.max_value
    
    def normalize_confidence(self, confidence: float) -> float:
        """Ensure confidence is in [0.0, 1.0] range.
        
        Args:
            confidence: Raw confidence value
            
        Returns:
            float: Confidence clamped to [0.0, 1.0] range
        """
        return max(0.0, min(1.0, float(confidence)))
    
    def get_schema_type(self) -> str:
        """Get schema type identifier.
        
        Returns:
            str: The string "scalar"
        """
        return "scalar"


class FreeFormDecisionSchema(DecisionSchema):
    """Free-form decision schema for open-ended text responses.
    
    Supports any text-based decision with optional length constraints.
    Examples: recommendations, explanations, detailed assessments.
    """
    
    max_length: Optional[int] = Field(default=None, description="Maximum allowed text length")
    min_length: Optional[int] = Field(default=None, description="Minimum required text length")
    
    @validator('max_length')
    def validate_length_constraints(cls, v: Optional[int], values: Dict[str, Any]) -> Optional[int]:
        """Ensure max_length is greater than min_length if both are specified.
        
        Args:
            v: The max_length value to validate
            values: Dictionary of previously validated field values
            
        Returns:
            Optional[int]: Validated max_length value
            
        Raises:
            ValueError: If max_length is not greater than min_length
        """
        if v is not None and 'min_length' in values and values['min_length'] is not None:
            if v <= values['min_length']:
                raise ValueError("max_length must be greater than min_length")
        return v
    
    def validate_decision(self, decision: Any) -> bool:
        """Validate that decision is a string within length constraints.
        
        Args:
            decision: The decision value to validate
            
        Returns:
            bool: True if decision is a string within length constraints, False otherwise
        """
        if not isinstance(decision, str):
            return False
        
        if self.min_length is not None and len(decision) < self.min_length:
            return False
        
        if self.max_length is not None and len(decision) > self.max_length:
            return False
        
        return True
    
    def normalize_confidence(self, confidence: float) -> float:
        """Ensure confidence is in [0.0, 1.0] range.
        
        Args:
            confidence: Raw confidence value
            
        Returns:
            float: Confidence clamped to [0.0, 1.0] range
        """
        return max(0.0, min(1.0, float(confidence)))
    
    def get_schema_type(self) -> str:
        """Get schema type identifier.
        
        Returns:
            str: The string "freeform"
        """
        return "freeform"


class EvaluationTask(BaseModel):
    """Defines an evaluation task to be performed by multiple agents.
    
    This is the core input to the multi-agent evaluation system. It is completely
    domain-agnostic and can represent any type of evaluation across any domain.
    """
    
    task_id: str = Field(..., description="Unique identifier for this evaluation task")
    task_type: str = Field(..., description="Type of evaluation (domain-specific identifier)")
    decision_schema: DecisionSchema = Field(..., description="Schema defining the structure of decisions")
    context: Dict[str, Any] = Field(..., description="Opaque context data passed to agents")
    evaluation_criteria: str = Field(..., description="Clear criteria for what should be evaluated")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional task metadata")
    
    @validator('task_id')
    def validate_task_id(cls, v: str) -> str:
        """Ensure task_id is non-empty.
        
        Args:
            v: The task_id string to validate
            
        Returns:
            str: Validated and stripped task_id
            
        Raises:
            ValueError: If task_id is empty or whitespace-only
        """
        if not v.strip():
            raise ValueError("task_id cannot be empty")
        return v.strip()
    
    @validator('task_type')
    def validate_task_type(cls, v: str) -> str:
        """Ensure task_type is non-empty.
        
        Args:
            v: The task_type string to validate
            
        Returns:
            str: Validated and stripped task_type
            
        Raises:
            ValueError: If task_type is empty or whitespace-only
        """
        if not v.strip():
            raise ValueError("task_type cannot be empty")
        return v.strip()
    
    @validator('evaluation_criteria')
    def validate_criteria(cls, v: str) -> str:
        """Ensure evaluation_criteria is non-empty.
        
        Args:
            v: The evaluation_criteria string to validate
            
        Returns:
            str: Validated and stripped evaluation_criteria
            
        Raises:
            ValueError: If evaluation_criteria is empty or whitespace-only
        """
        if not v.strip():
            raise ValueError("evaluation_criteria cannot be empty")
        return v.strip()


class AgentRole(BaseModel):
    """Defines the role and instructions for an agent in the evaluation process.
    
    Each agent takes on a specific role with tailored instructions for how to
    approach the evaluation task. Roles are domain-agnostic.
    """
    
    name: str = Field(..., description="Unique name for this agent role")
    role_type: str = Field(..., description="Type of role (advocate, skeptic, judge, domain_expert, custom)")
    instruction: str = Field(..., description="High-level instruction for this agent's perspective")
    prompt_template: Optional[str] = Field(None, description="Path to prompt template file")
    max_tokens: int = Field(default=500, ge=1, le=4000, description="Maximum tokens for agent response")
    temperature: float = Field(default=0.1, ge=0.0, le=2.0, description="LLM temperature for this agent")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Role-specific metadata")
    
    @validator('name')
    def validate_name(cls, v: str) -> str:
        """Ensure name is non-empty and contains only valid characters.
        
        Args:
            v: The name string to validate
            
        Returns:
            str: Validated and stripped name
            
        Raises:
            ValueError: If name is empty or contains invalid characters
        """
        if not v.strip():
            raise ValueError("name cannot be empty")
        # Allow alphanumeric, underscore, hyphen
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v.strip()):
            raise ValueError("name can only contain alphanumeric characters, underscores, and hyphens")
        return v.strip()
    
    @validator('role_type')
    def validate_role_type(cls, v: str) -> str:
        """Ensure role_type is non-empty.
        
        Args:
            v: The role_type string to validate
            
        Returns:
            str: Validated and stripped role_type
            
        Raises:
            ValueError: If role_type is empty or whitespace-only
        """
        if not v.strip():
            raise ValueError("role_type cannot be empty")
        return v.strip()
    
    @validator('instruction')
    def validate_instruction(cls, v: str) -> str:
        """Ensure instruction is non-empty.
        
        Args:
            v: The instruction string to validate
            
        Returns:
            str: Validated and stripped instruction
            
        Raises:
            ValueError: If instruction is empty or whitespace-only
        """
        if not v.strip():
            raise ValueError("instruction cannot be empty")
        return v.strip()


class AgentDecision(BaseModel):
    """Structured decision from an individual agent's evaluation.
    
    Contains the agent's decision value, confidence, rationale, and supporting evidence.
    This model is schema-aware and validates decisions against the task's decision schema.
    """
    
    agent_name: str = Field(..., description="Name of the agent that produced this decision")
    role_type: str = Field(..., description="Role type of the agent")
    decision_value: Any = Field(..., description="The agent's decision (validated against schema)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in the decision [0.0, 1.0]")
    rationale: str = Field(..., description="Detailed reasoning behind the decision")
    evidence: List[str] = Field(default_factory=list, description="Supporting evidence for the decision")
    processing_time_ms: Optional[int] = Field(None, ge=0, description="Time taken to generate this decision")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Agent-specific metadata")
    
    @validator('agent_name')
    def validate_agent_name(cls, v: str) -> str:
        """Ensure agent_name is non-empty.
        
        Args:
            v: The agent_name string to validate
            
        Returns:
            str: Validated and stripped agent_name
            
        Raises:
            ValueError: If agent_name is empty or whitespace-only
        """
        if not v.strip():
            raise ValueError("agent_name cannot be empty")
        return v.strip()
    
    @validator('role_type')
    def validate_role_type(cls, v: str) -> str:
        """Ensure role_type is non-empty.
        
        Args:
            v: The role_type string to validate
            
        Returns:
            str: Validated and stripped role_type
            
        Raises:
            ValueError: If role_type is empty or whitespace-only
        """
        if not v.strip():
            raise ValueError("role_type cannot be empty")
        return v.strip()
    
    @validator('rationale')
    def validate_rationale(cls, v: str) -> str:
        """Ensure rationale is non-empty.
        
        Args:
            v: The rationale string to validate
            
        Returns:
            str: Validated and stripped rationale
            
        Raises:
            ValueError: If rationale is empty or whitespace-only
        """
        if not v.strip():
            raise ValueError("rationale cannot be empty")
        return v.strip()
    
    @validator('evidence')
    def validate_evidence(cls, v: List[str]) -> List[str]:
        """Ensure evidence items are non-empty strings.
        
        Args:
            v: List of evidence strings to validate
            
        Returns:
            List[str]: List of validated evidence strings with empty items removed
        """
        return [item.strip() for item in v if item.strip()]


class AlignmentSummary(BaseModel):
    """Summary of alignment and disagreement between multiple agents.
    
    Provides deterministic, explainable analysis of how well agents agree on their
    decisions, confidence levels, and reasoning. All metrics are serializable.
    """
    
    state: AlignmentState = Field(..., description="Overall alignment state")
    alignment_score: float = Field(..., ge=0.0, le=1.0, description="Deterministic alignment score [0.0, 1.0]")
    decision_agreement: bool = Field(..., description="Whether agents agree on the primary decision")
    confidence_spread: float = Field(..., ge=0.0, le=1.0, description="Spread in confidence scores")
    confidence_distribution: Dict[str, float] = Field(..., description="Per-agent confidence mapping")
    avg_confidence: float = Field(..., ge=0.0, le=1.0, description="Average confidence across agents")
    dissenting_agents: List[str] = Field(default_factory=list, description="Names of agents with minority decisions")
    disagreement_areas: List[str] = Field(default_factory=list, description="Specific areas of disagreement")
    consensus_strength: float = Field(..., ge=0.0, le=1.0, description="Strength of consensus [0.0, 1.0]")
    resolution_rationale: str = Field(..., description="Short, deterministic explanation of alignment state")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Alignment analysis metadata")
    
    @validator('confidence_distribution')
    def validate_confidence_distribution(cls, v: Dict[str, float]) -> Dict[str, float]:
        """Ensure all confidence values are in valid range.
        
        Args:
            v: Dictionary mapping agent names to confidence values
            
        Returns:
            Dict[str, float]: Validated confidence distribution
            
        Raises:
            ValueError: If any confidence value is outside [0.0, 1.0] range
        """
        for agent_name, confidence in v.items():
            if not (0.0 <= confidence <= 1.0):
                raise ValueError(f"Invalid confidence {confidence} for agent {agent_name}")
        return v


class EvaluationResult(BaseModel):
    """Final result of a multi-agent evaluation process.
    
    Contains the synthesized decision, all agent decisions, alignment analysis,
    and metadata about the evaluation process. Completely domain-agnostic.
    """
    
    task_id: str = Field(..., description="ID of the evaluation task")
    synthesized_decision: Any = Field(..., description="Final synthesized decision")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Final confidence in the decision")
    reasoning: str = Field(..., description="Synthesized reasoning for the final decision")
    evidence: List[str] = Field(default_factory=list, description="Key evidence supporting the decision")
    
    agent_decisions: List[AgentDecision] = Field(..., description="Decisions from all participating agents")
    alignment_summary: AlignmentSummary = Field(..., description="Analysis of agent alignment")
    
    requires_human_review: bool = Field(default=False, description="Whether human review is required")
    review_reason: Optional[str] = Field(None, description="Reason why human review is needed")
    
    request_id: str = Field(..., description="Unique request identifier for tracing")
    processing_time_ms: int = Field(..., ge=0, description="Total processing time in milliseconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Evaluation metadata")
    
    @validator('task_id')
    def validate_task_id(cls, v: str) -> str:
        """Ensure task_id is non-empty.
        
        Args:
            v: The task_id string to validate
            
        Returns:
            str: Validated and stripped task_id
            
        Raises:
            ValueError: If task_id is empty or whitespace-only
        """
        if not v.strip():
            raise ValueError("task_id cannot be empty")
        return v.strip()
    
    @validator('reasoning')
    def validate_reasoning(cls, v: str) -> str:
        """Ensure reasoning is non-empty.
        
        Args:
            v: The reasoning string to validate
            
        Returns:
            str: Validated and stripped reasoning
            
        Raises:
            ValueError: If reasoning is empty or whitespace-only
        """
        if not v.strip():
            raise ValueError("reasoning cannot be empty")
        return v.strip()
    
    @validator('request_id')
    def validate_request_id(cls, v: str) -> str:
        """Ensure request_id is non-empty.
        
        Args:
            v: The request_id string to validate
            
        Returns:
            str: Validated and stripped request_id
            
        Raises:
            ValueError: If request_id is empty or whitespace-only
        """
        if not v.strip():
            raise ValueError("request_id cannot be empty")
        return v.strip()
    
    @validator('evidence')
    def validate_evidence(cls, v: List[str]) -> List[str]:
        """Ensure evidence items are non-empty strings.
        
        Args:
            v: List of evidence strings to validate
            
        Returns:
            List[str]: List of validated evidence strings with empty items removed
        """
        return [item.strip() for item in v if item.strip()]


# HITL Models (to be refactored in Task 3)
class HumanReviewRequest(BaseModel):
    """Request for human review when agents disagree.
    
    Contains all necessary information for a human reviewer to understand
    the disagreement and make an informed decision.
    """
    
    task_id: str = Field(..., description="ID of the evaluation task requiring review")
    evaluation_result: EvaluationResult = Field(..., description="Current evaluation result")
    disagreement_summary: str = Field(..., description="Summary of why human review is needed")
    review_priority: str = Field(default="medium", description="Priority level for review")
    deadline: Optional[str] = Field(None, description="Deadline for human review")
    reviewer_instructions: str = Field(..., description="Instructions for the human reviewer")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Review request metadata")


class HumanReviewDecision(BaseModel):
    """Decision from human reviewer for a disagreement case.
    
    Contains the human decision and rationale that can be integrated
    back into the evaluation system.
    """
    
    task_id: str = Field(..., description="ID of the evaluation task")
    reviewer_id: str = Field(..., description="ID of the human reviewer")
    decision_value: Any = Field(..., description="Human reviewer's decision")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Reviewer's confidence in the decision")
    rationale: str = Field(..., description="Reviewer's reasoning and rationale")
    review_time_ms: int = Field(..., ge=0, description="Time taken for human review")
    feedback: Optional[str] = Field(None, description="Feedback on the agent evaluation process")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Review response metadata")


class HumanReviewStatus(str, Enum):
    """Status of a human review request."""
    
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


# Legacy aliases for backward compatibility (will be deprecated)
DecisionType = DecisionSchema
BooleanDecision = BooleanDecisionSchema
CategoricalDecision = CategoricalDecisionSchema
ScalarDecision = ScalarDecisionSchema
FreeFormDecision = FreeFormDecisionSchema
AgentOutput = AgentDecision
HITLRequest = HumanReviewRequest
HITLResponse = HumanReviewDecision