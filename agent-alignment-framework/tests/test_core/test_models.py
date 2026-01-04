"""Tests for core data models."""

import pytest
from agent_alignment.core.models import (
    EvaluationTask,
    AgentRole,
    AgentDecision,
    AlignmentSummary,
    AlignmentState,
    BooleanDecisionSchema,
    CategoricalDecisionSchema,
    ScalarDecisionSchema,
    FreeFormDecisionSchema,
)


class TestDecisionTypes:
    """Test decision type validation and normalization."""
    
    def test_boolean_decision_validation(self):
        """Test boolean decision validation."""
        decision_type = BooleanDecisionSchema()
        
        assert decision_type.validate_decision(True)
        assert decision_type.validate_decision(False)
        assert not decision_type.validate_decision("maybe")
        assert not decision_type.validate_decision(1)
    
    def test_categorical_decision_validation(self):
        """Test categorical decision validation."""
        categories = ["low", "medium", "high"]
        decision_type = CategoricalDecisionSchema(categories=categories)
        
        assert decision_type.validate_decision("low")
        assert decision_type.validate_decision("high")
        assert not decision_type.validate_decision("extreme")
        assert not decision_type.validate_decision(True)
    
    def test_scalar_decision_validation(self):
        """Test scalar decision validation."""
        decision_type = ScalarDecisionSchema(min_value=0.0, max_value=10.0)
        
        assert decision_type.validate_decision(5.0)
        assert decision_type.validate_decision(0.0)
        assert decision_type.validate_decision(10.0)
        assert not decision_type.validate_decision(-1.0)
        assert not decision_type.validate_decision(11.0)
        assert not decision_type.validate_decision("five")
    
    def test_confidence_normalization(self):
        """Test confidence normalization."""
        decision_type = BooleanDecisionSchema()
        
        assert decision_type.normalize_confidence(0.5) == 0.5
        assert decision_type.normalize_confidence(-0.1) == 0.0
        assert decision_type.normalize_confidence(1.1) == 1.0
        assert decision_type.normalize_confidence(0.0) == 0.0
        assert decision_type.normalize_confidence(1.0) == 1.0


class TestEvaluationTask:
    """Test evaluation task model."""
    
    def test_basic_task_creation(self):
        """Test creating a basic evaluation task."""
        task = EvaluationTask(
            task_id="test-001",
            task_type="compatibility",
            decision_schema=BooleanDecisionSchema(),
            context={"item_a": "phone", "item_b": "charger"},
            evaluation_criteria="Check if items are compatible"
        )
        
        assert task.task_id == "test-001"
        assert task.task_type == "compatibility"
        assert isinstance(task.decision_schema, BooleanDecisionSchema)
        assert task.context["item_a"] == "phone"
        assert task.evaluation_criteria == "Check if items are compatible"
    
    def test_task_with_custom_decision_type(self):
        """Test task with custom decision type."""
        categories = ["compatible", "incompatible", "unknown"]
        decision_schema = CategoricalDecisionSchema(categories=categories)
        
        task = EvaluationTask(
            task_id="test-002",
            task_type="compatibility",
            decision_schema=decision_schema,
            context={"item_a": "phone", "item_b": "charger"},
            evaluation_criteria="Classify compatibility"
        )
        
        assert isinstance(task.decision_schema, CategoricalDecisionSchema)
        assert task.decision_schema.categories == categories


class TestAgentRole:
    """Test agent role model."""
    
    def test_basic_role_creation(self):
        """Test creating a basic agent role."""
        role = AgentRole(
            name="advocate",
            role_type="advocate",
            instruction="Argue for compatibility",
            max_tokens=500,
            temperature=0.1
        )
        
        assert role.name == "advocate"
        assert role.role_type == "advocate"
        assert role.instruction == "Argue for compatibility"
        assert role.max_tokens == 500
        assert role.temperature == 0.1


class TestAgentDecision:
    """Test agent decision model."""
    
    def test_basic_output_creation(self):
        """Test creating a basic agent decision."""
        output = AgentDecision(
            agent_name="test_agent",
            role_type="advocate",
            decision_value=True,
            confidence=0.85,
            rationale="Strong evidence for compatibility",
            evidence=["Evidence 1", "Evidence 2"]
        )
        
        assert output.agent_name == "test_agent"
        assert output.role_type == "advocate"
        assert output.decision_value is True
        assert output.confidence == 0.85
        assert len(output.evidence) == 2
    
    def test_confidence_validation(self):
        """Test confidence validation in agent decision."""
        # Valid confidence
        output = AgentDecision(
            agent_name="test_agent",
            role_type="advocate",
            decision_value=True,
            confidence=0.5,
            rationale="Test reasoning"
        )
        assert output.confidence == 0.5
        
        # Test boundary values
        with pytest.raises(ValueError):
            AgentDecision(
                agent_name="test_agent",
                role_type="advocate", 
                decision_value=True,
                confidence=1.5,  # Invalid: > 1.0
                rationale="Test reasoning"
            )
        
        with pytest.raises(ValueError):
            AgentDecision(
                agent_name="test_agent",
                role_type="advocate",
                decision_value=True,
                confidence=-0.1,  # Invalid: < 0.0
                rationale="Test reasoning"
            )


class TestAlignmentSummary:
    """Test alignment summary model."""
    
    def test_alignment_summary_creation(self):
        """Test creating alignment summary."""
        summary = AlignmentSummary(
            state=AlignmentState.FULL_ALIGNMENT,
            decision_agreement=True,
            confidence_spread=0.1,
            avg_confidence=0.9,
            disagreement_areas=[],
            consensus_strength=0.95
        )
        
        assert summary.state == AlignmentState.FULL_ALIGNMENT
        assert summary.decision_agreement is True
        assert summary.confidence_spread == 0.1
        assert summary.avg_confidence == 0.9
        assert len(summary.disagreement_areas) == 0
        assert summary.consensus_strength == 0.95
    
    def test_disagreement_state(self):
        """Test disagreement state representation."""
        summary = AlignmentSummary(
            state=AlignmentState.HARD_DISAGREEMENT,
            decision_agreement=False,
            confidence_spread=0.6,
            avg_confidence=0.4,
            disagreement_areas=["decision", "confidence"],
            consensus_strength=0.2
        )
        
        assert summary.state == AlignmentState.HARD_DISAGREEMENT
        assert summary.decision_agreement is False
        assert len(summary.disagreement_areas) == 2
        assert "decision" in summary.disagreement_areas