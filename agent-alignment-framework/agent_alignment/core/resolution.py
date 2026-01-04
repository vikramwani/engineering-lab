"""Hardened alignment and disagreement detection engine for multi-agent evaluations.

This module provides deterministic, explainable, and extensible alignment analysis
and disagreement resolution for any evaluation domain. All alignment states are
derived using configurable thresholds and produce consistent, serializable results.

Key Features:
- Deterministic alignment scoring with no randomness
- Explicit alignment state modeling with clear thresholds
- Schema-aware decision similarity analysis
- Configurable disagreement detection rules
- HITL-ready escalation triggers
- Pure functions with comprehensive type hints
"""

import statistics
from typing import Any, Dict, List, Optional, Tuple, Callable

from .models import (
    AgentDecision,
    AlignmentState,
    AlignmentSummary,
    BooleanDecisionSchema,
    CategoricalDecisionSchema,
    DecisionSchema,
    EvaluationTask,
    FreeFormDecisionSchema,
    ScalarDecisionSchema,
)


class AlignmentThresholds:
    """Configurable thresholds for alignment state detection.
    
    This class encapsulates all threshold values used to determine alignment states,
    making the system configurable while maintaining deterministic behavior.
    """
    
    def __init__(
        self,
        soft_disagreement_confidence_spread: float = 0.2,
        hard_disagreement_confidence_spread: float = 0.4,
        insufficient_signal_avg_confidence: float = 0.5,
        min_confidence_for_consensus: float = 0.7,
        scalar_decision_tolerance_ratio: float = 0.1,
        reasoning_overlap_threshold: float = 0.3,
        minority_dominance_threshold: float = 0.4,
    ):
        """Initialize alignment thresholds.
        
        Args:
            soft_disagreement_confidence_spread: Confidence spread threshold for soft disagreement
            hard_disagreement_confidence_spread: Confidence spread threshold for hard disagreement  
            insufficient_signal_avg_confidence: Average confidence threshold for insufficient signal
            min_confidence_for_consensus: Minimum confidence required for strong consensus
            scalar_decision_tolerance_ratio: Tolerance ratio for scalar decision agreement (as % of range)
            reasoning_overlap_threshold: Minimum reasoning keyword overlap for agreement
            minority_dominance_threshold: Threshold for minority agent influence
        """
        self.soft_disagreement_confidence_spread = soft_disagreement_confidence_spread
        self.hard_disagreement_confidence_spread = hard_disagreement_confidence_spread
        self.insufficient_signal_avg_confidence = insufficient_signal_avg_confidence
        self.min_confidence_for_consensus = min_confidence_for_consensus
        self.scalar_decision_tolerance_ratio = scalar_decision_tolerance_ratio
        self.reasoning_overlap_threshold = reasoning_overlap_threshold
        self.minority_dominance_threshold = minority_dominance_threshold
    
    @classmethod
    def from_config(cls, config: Dict[str, float]) -> "AlignmentThresholds":
        """Create thresholds from configuration dictionary.
        
        Args:
            config: Configuration dictionary with threshold values
            
        Returns:
            AlignmentThresholds: Configured thresholds instance
        """
        return cls(
            soft_disagreement_confidence_spread=config.get("soft_disagreement_confidence_spread", 0.2),
            hard_disagreement_confidence_spread=config.get("hard_disagreement_confidence_spread", 0.4),
            insufficient_signal_avg_confidence=config.get("insufficient_signal_avg_confidence", 0.5),
            min_confidence_for_consensus=config.get("min_confidence_for_consensus", 0.7),
            scalar_decision_tolerance_ratio=config.get("scalar_decision_tolerance_ratio", 0.1),
            reasoning_overlap_threshold=config.get("reasoning_overlap_threshold", 0.3),
            minority_dominance_threshold=config.get("minority_dominance_threshold", 0.4),
        )
    
    def to_dict(self) -> Dict[str, float]:
        """Convert thresholds to dictionary for serialization.
        
        Returns:
            Dict[str, float]: Dictionary mapping threshold names to their values
        """
        return {
            "soft_disagreement_confidence_spread": self.soft_disagreement_confidence_spread,
            "hard_disagreement_confidence_spread": self.hard_disagreement_confidence_spread,
            "insufficient_signal_avg_confidence": self.insufficient_signal_avg_confidence,
            "min_confidence_for_consensus": self.min_confidence_for_consensus,
            "scalar_decision_tolerance_ratio": self.scalar_decision_tolerance_ratio,
            "reasoning_overlap_threshold": self.reasoning_overlap_threshold,
            "minority_dominance_threshold": self.minority_dominance_threshold,
        }


class AlignmentAnalyzer:
    """Deterministic analyzer for multi-agent alignment and disagreement detection.
    
    This class provides pure functions for analyzing agent alignment using configurable
    thresholds. All analysis is deterministic - same inputs always produce same outputs.
    """
    
    def __init__(self, thresholds: Optional[AlignmentThresholds] = None):
        """Initialize alignment analyzer with configurable thresholds.
        
        Args:
            thresholds: Alignment thresholds configuration (uses defaults if None)
        """
        self.thresholds = thresholds or AlignmentThresholds()
    
    def analyze_alignment(
        self,
        task: EvaluationTask,
        agent_decisions: List[AgentDecision],
        event_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None
    ) -> AlignmentSummary:
        """Analyze alignment between multiple agent decisions using deterministic rules.
        
        This method performs comprehensive alignment analysis using configurable thresholds
        to produce consistent, explainable results across all evaluation domains.
        
        Args:
            task: The evaluation task that was performed
            agent_decisions: List of decisions from all participating agents
            event_callback: Optional callback for emitting structured events
            
        Returns:
            AlignmentSummary: Complete alignment analysis with deterministic metrics
            
        Raises:
            ValueError: If insufficient agent decisions are provided (< 2)
        """
        if len(agent_decisions) < 2:
            raise ValueError("At least 2 agent decisions required for alignment analysis")
        
        if event_callback:
            event_callback("alignment_analysis_started", {
                "task_id": task.task_id,
                "agent_count": len(agent_decisions),
                "decision_schema_type": type(task.decision_schema).__name__,
            })
        
        # Step 1: Analyze decision agreement using schema-aware comparison
        decision_agreement = self._analyze_decision_agreement(
            task.decision_schema, agent_decisions
        )
        
        # Step 2: Calculate confidence metrics
        confidence_metrics = self._calculate_confidence_metrics(agent_decisions)
        
        # Step 3: Identify dissenting agents
        dissenting_agents = self._identify_dissenting_agents(
            task.decision_schema, agent_decisions
        )
        
        # Step 4: Detect specific disagreement areas
        disagreement_areas = self._detect_disagreement_areas(
            task.decision_schema, agent_decisions, confidence_metrics
        )
        
        # Step 5: Calculate deterministic alignment score
        alignment_score = self._calculate_alignment_score(
            decision_agreement, confidence_metrics, dissenting_agents
        )
        
        # Step 6: Determine alignment state using thresholds
        alignment_state = self._determine_alignment_state(
            decision_agreement, confidence_metrics, disagreement_areas, dissenting_agents
        )
        
        # Step 7: Generate deterministic resolution rationale
        resolution_rationale = self._generate_resolution_rationale(
            alignment_state, decision_agreement, confidence_metrics, disagreement_areas
        )
        
        # Step 8: Calculate consensus strength
        consensus_strength = self._calculate_consensus_strength(
            decision_agreement, confidence_metrics, alignment_score
        )
        
        summary = AlignmentSummary(
            state=alignment_state,
            alignment_score=alignment_score,
            decision_agreement=decision_agreement,
            confidence_spread=confidence_metrics["spread"],
            confidence_distribution={d.agent_name: d.confidence for d in agent_decisions},
            avg_confidence=confidence_metrics["average"],
            dissenting_agents=dissenting_agents,
            disagreement_areas=disagreement_areas,
            consensus_strength=consensus_strength,
            resolution_rationale=resolution_rationale,
            metadata={
                "agent_count": len(agent_decisions),
                "decision_schema_type": type(task.decision_schema).__name__,
                "thresholds": self.thresholds.to_dict(),
                "analysis_version": "2.0.0",
            }
        )
        
        if event_callback:
            event_callback("alignment_analysis_completed", {
                "task_id": task.task_id,
                "alignment_state": alignment_state.value,
                "alignment_score": alignment_score,
                "decision_agreement": decision_agreement,
                "confidence_spread": confidence_metrics["spread"],
                "avg_confidence": confidence_metrics["average"],
                "dissenting_agent_count": len(dissenting_agents),
                "disagreement_area_count": len(disagreement_areas),
                "consensus_strength": consensus_strength,
            })
        
        return summary
    
    def requires_human_review(self, alignment_summary: AlignmentSummary) -> Tuple[bool, Optional[str]]:
        """Determine if evaluation requires human review based on alignment state.
        
        This method implements the HITL trigger logic using only alignment state analysis.
        Only HARD_DISAGREEMENT triggers human review to maintain clear escalation rules.
        
        Args:
            alignment_summary: The alignment analysis results
            
        Returns:
            Tuple of (requires_review: bool, reason: Optional[str])
        """
        if alignment_summary.state == AlignmentState.HARD_DISAGREEMENT:
            return True, "Agents have fundamental disagreements requiring human review"
        
        return False, None
    
    def _analyze_decision_agreement(
        self, 
        decision_schema: DecisionSchema, 
        agent_decisions: List[AgentDecision]
    ) -> bool:
        """Analyze whether agents agree on their primary decisions using schema-aware comparison.
        
        This method uses the decision schema to determine the appropriate comparison logic
        for different types of decisions (boolean, categorical, scalar, free-form).
        
        Args:
            decision_schema: The decision schema defining decision structure and validation
            agent_decisions: List of agent decisions to analyze for agreement
            
        Returns:
            bool: True if agents agree on primary decision, False otherwise
        """
        decisions = [d.decision_value for d in agent_decisions]
        
        if isinstance(decision_schema, BooleanDecisionSchema):
            # Boolean: All decisions must be identical
            return len(set(decisions)) == 1
        
        elif isinstance(decision_schema, CategoricalDecisionSchema):
            # Categorical: All decisions must be identical (string comparison)
            return len(set(str(d) for d in decisions)) == 1
        
        elif isinstance(decision_schema, ScalarDecisionSchema):
            # Scalar: Decisions within tolerance range are considered agreeing
            if len(decisions) < 2:
                return True
            
            decision_range = decision_schema.max_value - decision_schema.min_value
            tolerance = decision_range * self.thresholds.scalar_decision_tolerance_ratio
            mean_decision = statistics.mean(decisions)
            
            return all(abs(d - mean_decision) <= tolerance for d in decisions)
        
        elif isinstance(decision_schema, FreeFormDecisionSchema):
            # Free-form: Normalized string comparison
            normalized_decisions = set(str(d).lower().strip() for d in decisions)
            return len(normalized_decisions) == 1
        
        else:
            # Unknown schema: Conservative approach - require exact match
            return len(set(str(d) for d in decisions)) == 1
    
    def _calculate_confidence_metrics(self, agent_decisions: List[AgentDecision]) -> Dict[str, float]:
        """Calculate confidence-related metrics for alignment analysis.
        
        Computes statistical measures of confidence distribution across agents
        to assess the reliability and consistency of their decisions.
        
        Args:
            agent_decisions: List of agent decisions with confidence scores
            
        Returns:
            Dict[str, float]: Dictionary containing:
                - average: Mean confidence across all agents
                - spread: Difference between max and min confidence
                - min: Lowest confidence score
                - max: Highest confidence score
        """
        confidences = [d.confidence for d in agent_decisions]
        
        if len(confidences) == 1:
            return {
                "average": confidences[0],
                "spread": 0.0,
                "min": confidences[0],
                "max": confidences[0],
            }
        
        return {
            "average": statistics.mean(confidences),
            "spread": max(confidences) - min(confidences),
            "min": min(confidences),
            "max": max(confidences),
        }
    
    def _identify_dissenting_agents(
        self, 
        decision_schema: DecisionSchema, 
        agent_decisions: List[AgentDecision]
    ) -> List[str]:
        """Identify agents whose decisions differ from the majority.
        
        Uses majority voting to determine the consensus decision, then identifies
        agents whose decisions differ from this consensus.
        
        Args:
            decision_schema: The decision schema (for potential future schema-aware logic)
            agent_decisions: List of agent decisions to analyze
            
        Returns:
            List[str]: Names of agents whose decisions are in the minority
        """
        if len(agent_decisions) < 2:
            return []
        
        # Count decision frequencies
        decision_counts: Dict[str, List[str]] = {}
        for decision in agent_decisions:
            decision_key = str(decision.decision_value)
            if decision_key not in decision_counts:
                decision_counts[decision_key] = []
            decision_counts[decision_key].append(decision.agent_name)
        
        # Find majority decision
        majority_decision = max(decision_counts.items(), key=lambda x: len(x[1]))[0]
        majority_agents = set(decision_counts[majority_decision])
        
        # Return agents not in majority
        return [d.agent_name for d in agent_decisions if d.agent_name not in majority_agents]
    
    def _detect_disagreement_areas(
        self,
        decision_schema: DecisionSchema,
        agent_decisions: List[AgentDecision],
        confidence_metrics: Dict[str, float]
    ) -> List[str]:
        """Detect specific areas where agents disagree using deterministic rules.
        
        Args:
            decision_schema: The decision schema
            agent_decisions: List of agent decisions
            confidence_metrics: Pre-calculated confidence metrics
            
        Returns:
            List of disagreement area identifiers
        """
        disagreement_areas = []
        
        # Check primary decision disagreement
        decisions = [str(d.decision_value) for d in agent_decisions]
        if len(set(decisions)) > 1:
            disagreement_areas.append("primary_decision")
        
        # Check confidence level disagreement
        if confidence_metrics["spread"] > self.thresholds.soft_disagreement_confidence_spread:
            disagreement_areas.append("confidence_levels")
        
        # Check reasoning approach disagreement
        reasoning_overlap = self._calculate_reasoning_overlap(agent_decisions)
        if reasoning_overlap < self.thresholds.reasoning_overlap_threshold:
            disagreement_areas.append("reasoning_approach")
        
        # Check evidence quality disagreement
        evidence_consistency = self._calculate_evidence_consistency(agent_decisions)
        evidence_threshold = 0.5  # This should be configurable but kept as constant for now
        if evidence_consistency < evidence_threshold:
            disagreement_areas.append("evidence_quality")
        
        return disagreement_areas
    
    def _calculate_reasoning_overlap(self, agent_decisions: List[AgentDecision]) -> float:
        """Calculate overlap in reasoning approaches between agents.
        
        Args:
            agent_decisions: List of agent decisions
            
        Returns:
            Float between 0.0 and 1.0 representing reasoning overlap
        """
        if len(agent_decisions) < 2:
            return 1.0
        
        # Extract keywords from each agent's rationale
        reasoning_keywords = []
        for decision in agent_decisions:
            # Simple keyword extraction (split and normalize)
            keywords = set(
                word.lower().strip() 
                for word in decision.rationale.split() 
                if len(word) > 3  # Filter short words
            )
            reasoning_keywords.append(keywords)
        
        if not reasoning_keywords:
            return 0.0
        
        # Calculate intersection over union
        common_keywords = set.intersection(*reasoning_keywords)
        all_keywords = set.union(*reasoning_keywords)
        
        if not all_keywords:
            return 0.0
        
        return len(common_keywords) / len(all_keywords)
    
    def _calculate_evidence_consistency(self, agent_decisions: List[AgentDecision]) -> float:
        """Calculate consistency in evidence quality across agents.
        
        Args:
            agent_decisions: List of agent decisions
            
        Returns:
            Float between 0.0 and 1.0 representing evidence consistency
        """
        if len(agent_decisions) < 2:
            return 1.0
        
        evidence_lengths = [len(d.evidence) for d in agent_decisions]
        
        if not evidence_lengths:
            return 0.0
        
        # Calculate coefficient of variation (normalized standard deviation)
        mean_length = statistics.mean(evidence_lengths)
        if mean_length == 0:
            return 1.0 if all(l == 0 for l in evidence_lengths) else 0.0
        
        std_dev = statistics.stdev(evidence_lengths) if len(evidence_lengths) > 1 else 0.0
        coefficient_of_variation = std_dev / mean_length
        
        # Convert to consistency score (lower variation = higher consistency)
        return max(0.0, 1.0 - coefficient_of_variation)
    
    def _calculate_alignment_score(
        self,
        decision_agreement: bool,
        confidence_metrics: Dict[str, float],
        dissenting_agents: List[str]
    ) -> float:
        """Calculate deterministic alignment score using weighted components.
        
        The alignment score is a single metric in [0.0, 1.0] that combines:
        - Decision agreement (40% weight)
        - Confidence consistency (30% weight) 
        - Consensus breadth (30% weight)
        
        Args:
            decision_agreement: Whether agents agree on primary decision
            confidence_metrics: Confidence-related metrics
            dissenting_agents: List of dissenting agent names
            
        Returns:
            Float between 0.0 and 1.0 representing overall alignment
        """
        score = 0.0
        
        # Component 1: Decision agreement (40% weight)
        if decision_agreement:
            score += 0.4
        
        # Component 2: Confidence consistency (30% weight)
        # Higher consistency = lower spread
        confidence_consistency = max(0.0, 1.0 - (confidence_metrics["spread"] / 1.0))
        score += 0.3 * confidence_consistency
        
        # Component 3: Consensus breadth (30% weight)
        # Fewer dissenting agents = higher consensus
        total_agents = len(dissenting_agents) + 1  # Assume at least one non-dissenting agent
        consensus_breadth = 1.0 - (len(dissenting_agents) / total_agents)
        score += 0.3 * consensus_breadth
        
        return min(1.0, max(0.0, score))
    
    def _determine_alignment_state(
        self,
        decision_agreement: bool,
        confidence_metrics: Dict[str, float],
        disagreement_areas: List[str],
        dissenting_agents: List[str]
    ) -> AlignmentState:
        """Determine alignment state using deterministic threshold-based rules.
        
        State determination follows this priority order:
        1. INSUFFICIENT_SIGNAL: Low average confidence
        2. HARD_DISAGREEMENT: Decision disagreement OR high confidence spread OR many disagreement areas
        3. SOFT_DISAGREEMENT: Some disagreement areas OR moderate confidence spread
        4. FULL_ALIGNMENT: All other cases
        
        Args:
            decision_agreement: Whether agents agree on primary decision
            confidence_metrics: Confidence-related metrics
            disagreement_areas: List of disagreement areas
            dissenting_agents: List of dissenting agent names
            
        Returns:
            AlignmentState: The determined alignment state
        """
        # Priority 1: Insufficient signal (low confidence)
        if confidence_metrics["average"] < self.thresholds.insufficient_signal_avg_confidence:
            return AlignmentState.INSUFFICIENT_SIGNAL
        
        # Priority 2: Hard disagreement (fundamental conflicts)
        if (not decision_agreement or 
            confidence_metrics["spread"] > self.thresholds.hard_disagreement_confidence_spread or
            len(disagreement_areas) >= 3):
            return AlignmentState.HARD_DISAGREEMENT
        
        # Priority 3: Soft disagreement (minor conflicts)
        if (confidence_metrics["spread"] > self.thresholds.soft_disagreement_confidence_spread or
            len(disagreement_areas) >= 1):
            return AlignmentState.SOFT_DISAGREEMENT
        
        # Priority 4: Full alignment (no significant conflicts)
        return AlignmentState.FULL_ALIGNMENT
    
    def _generate_resolution_rationale(
        self,
        alignment_state: AlignmentState,
        decision_agreement: bool,
        confidence_metrics: Dict[str, float],
        disagreement_areas: List[str]
    ) -> str:
        """Generate deterministic, short explanation of alignment state.
        
        Args:
            alignment_state: The determined alignment state
            decision_agreement: Whether agents agree on primary decision
            confidence_metrics: Confidence-related metrics
            disagreement_areas: List of disagreement areas
            
        Returns:
            String: Short, deterministic explanation of alignment state
        """
        if alignment_state == AlignmentState.FULL_ALIGNMENT:
            return f"Full alignment: agents agree on decision with avg confidence {confidence_metrics['average']:.2f}"
        
        elif alignment_state == AlignmentState.SOFT_DISAGREEMENT:
            areas = ", ".join(disagreement_areas) if disagreement_areas else "confidence levels"
            return f"Soft disagreement in {areas} (spread: {confidence_metrics['spread']:.2f})"
        
        elif alignment_state == AlignmentState.HARD_DISAGREEMENT:
            if not decision_agreement:
                return "Hard disagreement: agents disagree on primary decision"
            else:
                return f"Hard disagreement: high confidence spread ({confidence_metrics['spread']:.2f}) or multiple conflict areas"
        
        elif alignment_state == AlignmentState.INSUFFICIENT_SIGNAL:
            return f"Insufficient signal: low average confidence ({confidence_metrics['average']:.2f})"
        
        else:
            return f"Unknown alignment state: {alignment_state.value}"
    
    def _calculate_consensus_strength(
        self,
        decision_agreement: bool,
        confidence_metrics: Dict[str, float],
        alignment_score: float
    ) -> float:
        """Calculate consensus strength as a combination of agreement and confidence.
        
        Args:
            decision_agreement: Whether agents agree on primary decision
            confidence_metrics: Confidence-related metrics
            alignment_score: Pre-calculated alignment score
            
        Returns:
            Float between 0.0 and 1.0 representing consensus strength
        """
        # Consensus strength is the product of alignment score and average confidence
        # This ensures both agreement AND confidence contribute to consensus
        return alignment_score * confidence_metrics["average"]


class DisagreementResolver:
    """Deterministic resolver for synthesizing decisions from agent disagreements.
    
    This class provides schema-aware decision synthesis using configurable strategies.
    All resolution is deterministic and produces explainable results.
    """
    
    def __init__(self, analyzer: Optional[AlignmentAnalyzer] = None):
        """Initialize disagreement resolver.
        
        Args:
            analyzer: Alignment analyzer for consistency (uses default if None)
        """
        self.analyzer = analyzer or AlignmentAnalyzer()
    
    def resolve_disagreement(
        self,
        task: EvaluationTask,
        agent_decisions: List[AgentDecision],
        alignment_summary: AlignmentSummary,
        event_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None
    ) -> Tuple[Any, float, str, List[str]]:
        """Resolve disagreement and synthesize final decision using schema-aware logic.
        
        Args:
            task: The evaluation task
            agent_decisions: All agent decisions
            alignment_summary: Alignment analysis results
            event_callback: Optional callback for emitting structured events
            
        Returns:
            Tuple of (decision, confidence, reasoning, evidence)
        """
        if event_callback:
            event_callback("disagreement_resolution_started", {
                "task_id": task.task_id,
                "agent_count": len(agent_decisions),
                "alignment_state": alignment_summary.state.value,
                "decision_schema_type": type(task.decision_schema).__name__,
            })
        
        # Route to schema-specific resolution
        if isinstance(task.decision_schema, BooleanDecisionSchema):
            result = self._resolve_boolean_decision(agent_decisions, alignment_summary)
        elif isinstance(task.decision_schema, CategoricalDecisionSchema):
            result = self._resolve_categorical_decision(agent_decisions, alignment_summary)
        elif isinstance(task.decision_schema, ScalarDecisionSchema):
            result = self._resolve_scalar_decision(agent_decisions, alignment_summary)
        elif isinstance(task.decision_schema, FreeFormDecisionSchema):
            result = self._resolve_freeform_decision(agent_decisions, alignment_summary)
        else:
            # Fallback for unknown schemas
            result = self._resolve_highest_confidence_decision(agent_decisions, alignment_summary)
        
        decision, confidence, reasoning, evidence = result
        
        if event_callback:
            event_callback("disagreement_resolution_completed", {
                "task_id": task.task_id,
                "final_decision": str(decision),
                "final_confidence": confidence,
                "alignment_state": alignment_summary.state.value,
                "evidence_count": len(evidence),
            })
        
        return decision, confidence, reasoning, evidence
    
    def _resolve_boolean_decision(
        self, 
        agent_decisions: List[AgentDecision], 
        alignment_summary: AlignmentSummary
    ) -> Tuple[bool, float, str, List[str]]:
        """Resolve boolean decision using confidence-weighted majority vote.
        
        Args:
            agent_decisions: List of agent decisions
            alignment_summary: Alignment analysis results
            
        Returns:
            Tuple of (decision, confidence, reasoning, evidence)
        """
        # Calculate confidence-weighted votes
        weighted_true = sum(d.confidence for d in agent_decisions if d.decision_value is True)
        weighted_false = sum(d.confidence for d in agent_decisions if d.decision_value is False)
        
        decision = weighted_true > weighted_false
        
        # Confidence based on alignment strength and consensus
        confidence = alignment_summary.consensus_strength
        
        # Generate reasoning
        supporting_decisions = [d for d in agent_decisions if d.decision_value == decision]
        reasoning = (
            f"Boolean decision: {decision} based on confidence-weighted majority "
            f"({len(supporting_decisions)}/{len(agent_decisions)} agents, "
            f"weighted score: {weighted_true if decision else weighted_false:.2f})"
        )
        
        # Collect evidence from supporting agents
        evidence = []
        for decision_obj in supporting_decisions[:3]:  # Top 3 supporting agents
            evidence.extend(decision_obj.evidence[:2])  # Top 2 evidence per agent
        
        return decision, confidence, reasoning, evidence[:5]
    
    def _resolve_categorical_decision(
        self, 
        agent_decisions: List[AgentDecision], 
        alignment_summary: AlignmentSummary
    ) -> Tuple[str, float, str, List[str]]:
        """Resolve categorical decision using confidence-weighted voting.
        
        Args:
            agent_decisions: List of agent decisions
            alignment_summary: Alignment analysis results
            
        Returns:
            Tuple of (decision, confidence, reasoning, evidence)
        """
        # Calculate confidence-weighted scores for each category
        category_scores: Dict[str, float] = {}
        for decision_obj in agent_decisions:
            category = str(decision_obj.decision_value)
            category_scores[category] = category_scores.get(category, 0.0) + decision_obj.confidence
        
        # Select category with highest weighted score
        decision = max(category_scores.items(), key=lambda x: x[1])[0]
        
        # Confidence based on alignment strength
        confidence = alignment_summary.consensus_strength
        
        # Generate reasoning
        supporting_decisions = [d for d in agent_decisions if str(d.decision_value) == decision]
        reasoning = (
            f"Categorical decision: '{decision}' selected by confidence-weighted vote "
            f"({len(supporting_decisions)}/{len(agent_decisions)} agents, "
            f"weighted score: {category_scores[decision]:.2f})"
        )
        
        # Collect evidence from supporting agents
        evidence = []
        for decision_obj in supporting_decisions:
            evidence.extend(decision_obj.evidence[:2])
        
        return decision, confidence, reasoning, evidence[:5]
    
    def _resolve_scalar_decision(
        self, 
        agent_decisions: List[AgentDecision], 
        alignment_summary: AlignmentSummary
    ) -> Tuple[float, float, str, List[str]]:
        """Resolve scalar decision using confidence-weighted average.
        
        Args:
            agent_decisions: List of agent decisions
            alignment_summary: Alignment analysis results
            
        Returns:
            Tuple of (decision, confidence, reasoning, evidence)
        """
        # Calculate confidence-weighted average
        total_weight = sum(d.confidence for d in agent_decisions)
        if total_weight == 0:
            decision = statistics.mean(d.decision_value for d in agent_decisions)
        else:
            decision = sum(
                d.decision_value * d.confidence for d in agent_decisions
            ) / total_weight
        
        # Confidence based on alignment strength
        confidence = alignment_summary.consensus_strength
        
        # Generate reasoning
        decision_values = [d.decision_value for d in agent_decisions]
        reasoning = (
            f"Scalar decision: {decision:.3f} from confidence-weighted average "
            f"(range: {min(decision_values):.3f}-{max(decision_values):.3f}, "
            f"total weight: {total_weight:.2f})"
        )
        
        # Collect evidence from highest confidence agents
        sorted_decisions = sorted(agent_decisions, key=lambda x: x.confidence, reverse=True)
        evidence = []
        for decision_obj in sorted_decisions[:3]:  # Top 3 most confident agents
            evidence.extend(decision_obj.evidence[:2])
        
        return decision, confidence, reasoning, evidence[:5]
    
    def _resolve_freeform_decision(
        self, 
        agent_decisions: List[AgentDecision], 
        alignment_summary: AlignmentSummary
    ) -> Tuple[str, float, str, List[str]]:
        """Resolve free-form decision using highest confidence agent.
        
        Args:
            agent_decisions: List of agent decisions
            alignment_summary: Alignment analysis results
            
        Returns:
            Tuple of (decision, confidence, reasoning, evidence)
        """
        # Use highest confidence agent's decision as primary
        highest_confidence_decision = max(agent_decisions, key=lambda x: x.confidence)
        decision = str(highest_confidence_decision.decision_value)
        
        # Confidence based on alignment strength
        confidence = alignment_summary.consensus_strength
        
        # Generate reasoning with multiple perspectives
        reasoning = (
            f"Free-form decision from highest confidence agent "
            f"({highest_confidence_decision.agent_name}: {highest_confidence_decision.confidence:.2f}): "
            f"{decision[:100]}..."
        )
        
        # Add other perspectives if available
        other_decisions = [d for d in agent_decisions if d != highest_confidence_decision]
        if other_decisions:
            other_summaries = [
                f"{d.agent_name}: {str(d.decision_value)[:30]}..." 
                for d in other_decisions[:2]
            ]
            reasoning += f" Other perspectives: {'; '.join(other_summaries)}"
        
        # Collect evidence from all agents
        evidence = []
        for decision_obj in agent_decisions:
            evidence.extend(decision_obj.evidence[:2])
        
        return decision, confidence, reasoning, evidence[:5]
    
    def _resolve_highest_confidence_decision(
        self, 
        agent_decisions: List[AgentDecision], 
        alignment_summary: AlignmentSummary
    ) -> Tuple[Any, float, str, List[str]]:
        """Fallback resolver using highest confidence agent's decision.
        
        Args:
            agent_decisions: List of agent decisions
            alignment_summary: Alignment analysis results
            
        Returns:
            Tuple of (decision, confidence, reasoning, evidence)
        """
        highest_confidence_decision = max(agent_decisions, key=lambda x: x.confidence)
        
        decision = highest_confidence_decision.decision_value
        confidence = alignment_summary.consensus_strength
        
        reasoning = (
            f"Fallback resolution using highest confidence agent "
            f"({highest_confidence_decision.agent_name}: {highest_confidence_decision.confidence:.2f})"
        )
        
        return decision, confidence, reasoning, highest_confidence_decision.evidence


class AlignmentEngine:
    """Hardened engine for alignment analysis and disagreement resolution.
    
    This class provides the main interface for analyzing agent alignment and resolving
    disagreements using deterministic, configurable, and extensible algorithms.
    """
    
    def __init__(
        self, 
        thresholds: Optional[AlignmentThresholds] = None,
        analyzer: Optional[AlignmentAnalyzer] = None,
        resolver: Optional[DisagreementResolver] = None,
        event_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None
    ):
        """Initialize alignment engine with configurable components.
        
        Args:
            thresholds: Alignment thresholds configuration
            analyzer: Alignment analyzer (uses default if None)
            resolver: Disagreement resolver (uses default if None)
            event_callback: Optional callback for emitting structured events
        """
        self.thresholds = thresholds or AlignmentThresholds()
        self.analyzer = analyzer or AlignmentAnalyzer(self.thresholds)
        self.resolver = resolver or DisagreementResolver(self.analyzer)
        self.event_callback = event_callback
        
        if event_callback:
            event_callback("alignment_engine_initialized", {
                "thresholds": self.thresholds.to_dict(),
                "analyzer_type": type(self.analyzer).__name__,
                "resolver_type": type(self.resolver).__name__,
            })
    
    def analyze_alignment(
        self,
        task: EvaluationTask,
        agent_decisions: List[AgentDecision]
    ) -> AlignmentSummary:
        """Analyze alignment between agent decisions.
        
        Args:
            task: The evaluation task
            agent_decisions: List of agent decisions
            
        Returns:
            AlignmentSummary: Complete alignment analysis
        """
        return self.analyzer.analyze_alignment(task, agent_decisions, self.event_callback)
    
    def needs_human_review(self, alignment_summary: AlignmentSummary) -> Tuple[bool, Optional[str]]:
        """Determine if evaluation needs human review.
        
        Args:
            alignment_summary: Alignment analysis results
            
        Returns:
            Tuple of (needs_review: bool, reason: Optional[str])
        """
        return self.analyzer.requires_human_review(alignment_summary)
    
    def synthesize_decision(
        self,
        task: EvaluationTask,
        agent_decisions: List[AgentDecision],
        alignment_summary: AlignmentSummary
    ) -> Tuple[Any, float, str, List[str]]:
        """Synthesize final decision from agent disagreements.
        
        Args:
            task: The evaluation task
            agent_decisions: List of agent decisions
            alignment_summary: Alignment analysis results
            
        Returns:
            Tuple of (decision, confidence, reasoning, evidence)
        """
        return self.resolver.resolve_disagreement(task, agent_decisions, alignment_summary, self.event_callback)