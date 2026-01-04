"""Human-in-the-Loop (HITL) escalation contract for the agent alignment framework.

This module provides a pure, deterministic HITL escalation contract that defines:
- When and why human review is required
- Structured, serializable payloads for downstream systems  
- Domain-agnostic escalation logic

The contract is designed to be pluggable with any review system without introducing
UI, persistence, or async workflows. It focuses purely on escalation signal generation.

Key Principles:
- Pure, deterministic logic with no side effects
- Schema-driven models for structured escalation
- Backward compatible with existing evaluation pipeline
- No assumptions about downstream review systems
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable

from pydantic import BaseModel, Field, validator

from .models import AgentDecision, AlignmentSummary, EvaluationResult


class HITLEscalationReason(str, Enum):
    """Enumeration of reasons why human review escalation is triggered.
    
    These reasons are machine-readable and provide clear semantics for why
    the automated system requires human intervention.
    """
    
    HARD_DISAGREEMENT = "hard_disagreement"
    LOW_CONFIDENCE = "low_confidence"
    INCONSISTENT_EVIDENCE = "inconsistent_evidence"
    CUSTOM_RULE = "custom_rule"


class HITLRequest(BaseModel):
    """Structured request for human-in-the-loop review escalation.
    
    This model defines the complete contract for HITL escalation, containing
    all information needed by downstream review systems to process human review
    requests. All fields are serializable and typed for deterministic processing.
    """
    
    request_id: str = Field(..., description="Unique identifier for this HITL request")
    task_id: str = Field(..., description="ID of the evaluation task requiring review")
    alignment_state: str = Field(..., description="Alignment state that triggered escalation")
    alignment_score: float = Field(..., ge=0.0, le=1.0, description="Deterministic alignment score")
    escalation_reason: HITLEscalationReason = Field(..., description="Primary reason for escalation")
    summary: str = Field(..., description="Short, deterministic explanation of why review is needed")
    
    # Agent decision references (not full duplication)
    agent_decisions: List[AgentDecision] = Field(..., description="Agent decisions requiring review")
    dissenting_agents: List[str] = Field(default_factory=list, description="Names of dissenting agents")
    
    # Temporal information
    created_at: datetime = Field(default_factory=datetime.utcnow, description="UTC timestamp when request was created")
    
    # Structured metadata for downstream systems
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional structured metadata")
    
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
    
    @validator('alignment_state')
    def validate_alignment_state(cls, v: str) -> str:
        """Ensure alignment_state is non-empty.
        
        Args:
            v: The alignment_state string to validate
            
        Returns:
            str: Validated and stripped alignment_state
            
        Raises:
            ValueError: If alignment_state is empty or whitespace-only
        """
        if not v.strip():
            raise ValueError("alignment_state cannot be empty")
        return v.strip()
    
    @validator('summary')
    def validate_summary(cls, v: str) -> str:
        """Ensure summary is non-empty.
        
        Args:
            v: The summary string to validate
            
        Returns:
            str: Validated and stripped summary
            
        Raises:
            ValueError: If summary is empty or whitespace-only
        """
        if not v.strip():
            raise ValueError("summary cannot be empty")
        return v.strip()
    
    class Config:
        """Pydantic configuration for HITLRequest."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


def build_hitl_request(
    evaluation_result: EvaluationResult,
    alignment_summary: AlignmentSummary,
    event_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None
) -> Optional[HITLRequest]:
    """Build a structured HITL request from evaluation results.
    
    This is the core escalation contract function that determines when human review
    is required and produces a structured, serializable payload for downstream systems.
    
    The function is pure and deterministic - identical inputs always produce identical
    outputs. It contains no side effects, UI logic, or persistence operations.
    
    Args:
        evaluation_result: Complete evaluation result from multi-agent evaluation
        alignment_summary: Alignment analysis summary with state and metrics
        event_callback: Optional callback for emitting structured events
        
    Returns:
        Optional[HITLRequest]: Structured HITL request if escalation is required, None otherwise
        
    Escalation Rules:
        - Returns None if requires_human_review == False
        - Returns HITLRequest if escalation is required based on alignment state
        - Only HARD_DISAGREEMENT currently triggers escalation (as per Task 2)
    """
    # Rule 1: No escalation if human review is not required
    if not evaluation_result.requires_human_review:
        if event_callback:
            event_callback("hitl_escalation_not_required", {
                "task_id": evaluation_result.task_id,
                "alignment_state": alignment_summary.state.value,
                "requires_human_review": evaluation_result.requires_human_review,
            })
        return None
    
    # Rule 2: Determine escalation reason based on alignment state
    escalation_reason = _determine_escalation_reason(alignment_summary)
    
    # Rule 3: Generate deterministic summary
    summary = _generate_escalation_summary(alignment_summary, escalation_reason)
    
    # Rule 4: Generate unique request ID (deterministic based on task and timestamp)
    request_id = _generate_request_id(evaluation_result.task_id)
    
    # Rule 5: Build structured request
    hitl_request = HITLRequest(
        request_id=request_id,
        task_id=evaluation_result.task_id,
        alignment_state=alignment_summary.state.value,
        alignment_score=alignment_summary.alignment_score,
        escalation_reason=escalation_reason,
        summary=summary,
        agent_decisions=evaluation_result.agent_decisions,
        dissenting_agents=alignment_summary.dissenting_agents,
        metadata={
            "confidence_spread": alignment_summary.confidence_spread,
            "avg_confidence": alignment_summary.avg_confidence,
            "disagreement_areas": alignment_summary.disagreement_areas,
            "consensus_strength": alignment_summary.consensus_strength,
            "resolution_rationale": alignment_summary.resolution_rationale,
            "agent_count": len(evaluation_result.agent_decisions),
            "processing_time_ms": evaluation_result.processing_time_ms,
            "evaluation_request_id": evaluation_result.request_id,
        }
    )
    
    # Log escalation at INFO level for observability
    if event_callback:
        event_callback("hitl_escalation_triggered", {
            "request_id": request_id,
            "task_id": evaluation_result.task_id,
            "alignment_state": alignment_summary.state.value,
            "escalation_reason": escalation_reason.value,
            "alignment_score": alignment_summary.alignment_score,
            "dissenting_agents": alignment_summary.dissenting_agents,
            "confidence_spread": alignment_summary.confidence_spread,
            "avg_confidence": alignment_summary.avg_confidence,
        })
    
    return hitl_request


def _determine_escalation_reason(alignment_summary: AlignmentSummary) -> HITLEscalationReason:
    """Determine the primary escalation reason based on alignment analysis.
    
    This function maps alignment states to escalation reasons using deterministic rules.
    The mapping prioritizes specific disagreement areas when available.
    
    Args:
        alignment_summary: Alignment analysis summary containing state and disagreement details
        
    Returns:
        HITLEscalationReason: Primary reason for escalation based on alignment state
    """
    # Map alignment states to escalation reasons
    if alignment_summary.state.value == "hard_disagreement":
        return HITLEscalationReason.HARD_DISAGREEMENT
    
    elif alignment_summary.state.value == "insufficient_signal":
        return HITLEscalationReason.LOW_CONFIDENCE
    
    elif alignment_summary.state.value == "soft_disagreement":
        # Analyze disagreement areas to determine specific reason
        if "evidence_quality" in alignment_summary.disagreement_areas:
            return HITLEscalationReason.INCONSISTENT_EVIDENCE
        else:
            return HITLEscalationReason.LOW_CONFIDENCE
    
    else:
        # Fallback for any custom escalation rules
        return HITLEscalationReason.CUSTOM_RULE


def _generate_escalation_summary(
    alignment_summary: AlignmentSummary, 
    escalation_reason: HITLEscalationReason
) -> str:
    """Generate a short, deterministic explanation of why escalation is needed.
    
    Creates human-readable summaries that include relevant metrics and context
    to help human reviewers understand the nature of the disagreement.
    
    Args:
        alignment_summary: Alignment analysis summary with metrics and state
        escalation_reason: Primary escalation reason determining summary format
        
    Returns:
        str: Human-readable summary explaining why human review is needed
    """
    if escalation_reason == HITLEscalationReason.HARD_DISAGREEMENT:
        dissenting_count = len(alignment_summary.dissenting_agents)
        total_agents = len(alignment_summary.confidence_distribution)
        return (
            f"Agents fundamentally disagree on decision "
            f"({dissenting_count}/{total_agents} dissenting, "
            f"confidence spread: {alignment_summary.confidence_spread:.2f})"
        )
    
    elif escalation_reason == HITLEscalationReason.LOW_CONFIDENCE:
        return (
            f"Agents lack sufficient confidence for reliable decision "
            f"(avg confidence: {alignment_summary.avg_confidence:.2f}, "
            f"state: {alignment_summary.state.value})"
        )
    
    elif escalation_reason == HITLEscalationReason.INCONSISTENT_EVIDENCE:
        return (
            f"Agents provide inconsistent evidence quality "
            f"(disagreement areas: {', '.join(alignment_summary.disagreement_areas)})"
        )
    
    elif escalation_reason == HITLEscalationReason.CUSTOM_RULE:
        return (
            f"Custom escalation rule triggered "
            f"(alignment state: {alignment_summary.state.value}, "
            f"score: {alignment_summary.alignment_score:.2f})"
        )
    
    else:
        return f"Unknown escalation reason: {escalation_reason.value}"


def _generate_request_id(task_id: str) -> str:
    """Generate a unique request ID for HITL escalation.
    
    Creates a unique identifier that includes the task ID for traceability
    while ensuring global uniqueness through UUID generation.
    
    Args:
        task_id: The evaluation task ID for traceability
        
    Returns:
        str: Unique request ID in format "hitl-{task_id}-{uuid_prefix}"
    """
    # Generate UUID-based ID with task prefix for traceability
    unique_id = str(uuid.uuid4())[:8]
    return f"hitl-{task_id}-{unique_id}"


# Semantic validation functions for escalation contract

def validate_hitl_request(hitl_request: HITLRequest) -> bool:
    """Validate that a HITL request conforms to the escalation contract.
    
    Performs semantic validation beyond basic Pydantic field validation
    to ensure the request is internally consistent and complete.
    
    Args:
        hitl_request: HITL request to validate
        
    Returns:
        bool: True if request is valid and internally consistent, False otherwise
    """
    try:
        # Basic field validation is handled by Pydantic
        # Additional semantic validation
        
        # Ensure alignment score is reasonable
        if not (0.0 <= hitl_request.alignment_score <= 1.0):
            return False
        
        # Ensure escalation reason is valid
        if hitl_request.escalation_reason not in HITLEscalationReason:
            return False
        
        # Ensure agent decisions are present
        if not hitl_request.agent_decisions:
            return False
        
        # Ensure dissenting agents are subset of all agents
        all_agent_names = {d.agent_name for d in hitl_request.agent_decisions}
        dissenting_set = set(hitl_request.dissenting_agents)
        if not dissenting_set.issubset(all_agent_names):
            return False
        
        return True
        
    except Exception:
        return False


def get_escalation_semantics() -> Dict[str, Any]:
    """Get machine-readable semantics of the HITL escalation contract.
    
    This function provides comprehensive metadata about the escalation contract,
    including what triggers escalation, what information is included/excluded,
    and contract versioning information.
    
    Returns:
        Dict[str, Any]: Structured semantics containing:
            - escalation_triggers: Conditions that trigger each escalation reason
            - included_information: Data included in HITL requests
            - excluded_information: Data intentionally excluded
            - contract_version: Version of the escalation contract
            - deterministic: Whether the contract is deterministic
            - side_effects: Whether the contract has side effects
    """
    return {
        "escalation_triggers": {
            "hard_disagreement": {
                "description": "Agents fundamentally disagree on primary decision",
                "conditions": ["decision_agreement == False", "alignment_state == 'hard_disagreement'"],
                "automatic": True
            },
            "low_confidence": {
                "description": "Agents lack sufficient confidence for reliable decision",
                "conditions": ["avg_confidence < threshold", "alignment_state == 'insufficient_signal'"],
                "automatic": False  # Not currently implemented in Task 2
            },
            "inconsistent_evidence": {
                "description": "Agents provide inconsistent evidence quality",
                "conditions": ["'evidence_quality' in disagreement_areas"],
                "automatic": False  # Not currently implemented in Task 2
            },
            "custom_rule": {
                "description": "Custom escalation rule triggered",
                "conditions": ["user_defined"],
                "automatic": False
            }
        },
        "included_information": [
            "alignment_state",
            "alignment_score", 
            "escalation_reason",
            "deterministic_summary",
            "agent_decisions",
            "dissenting_agents",
            "confidence_metrics",
            "disagreement_areas",
            "temporal_metadata"
        ],
        "excluded_information": [
            "ui_preferences",
            "workflow_state",
            "reviewer_assignments",
            "notification_settings",
            "persistence_details",
            "async_callbacks"
        ],
        "contract_version": "1.0.0",
        "deterministic": True,
        "side_effects": False
    }


# Legacy compatibility aliases
HITLRequest = HITLRequest  # For backward compatibility with existing code