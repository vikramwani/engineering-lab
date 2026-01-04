"""Multi-agent evaluation orchestrator for the alignment framework.

This module provides the main orchestrator that coordinates multiple agents,
manages the evaluation process, and synthesizes final results with alignment analysis.
"""

import logging
import time
import uuid
from typing import List, Optional, Callable, Dict, Any

from ..llm.client import LLMClient
from ..utils.logging import get_logger
from .agent import BaseAgent
from .resolution import AlignmentEngine, AlignmentThresholds
from .models import (
    AgentDecision,
    AgentRole,
    EvaluationResult,
    EvaluationTask,
)
from .hitl import build_hitl_request, HITLRequest

logger = get_logger(__name__)


class MultiAgentEvaluator:
    """Main orchestrator for multi-agent evaluation processes.
    
    This class coordinates multiple agents to evaluate tasks, analyzes their
    alignment, detects disagreements, and synthesizes final decisions. It also
    provides extension points for human-in-the-loop review when needed.
    """
    
    def __init__(
        self,
        agents: List[BaseAgent],
        alignment_engine: Optional[AlignmentEngine] = None,
        alignment_thresholds: Optional[AlignmentThresholds] = None,
        enable_hitl: bool = True,
        max_retries: int = 3,
        timeout_seconds: int = 30,
    ):
        """Initialize the multi-agent evaluator.
        
        Creates an orchestrator that coordinates multiple agents for evaluation tasks,
        with configurable alignment analysis and error handling.
        
        Args:
            agents: List of agents to participate in evaluations (minimum 1 required)
            alignment_engine: Engine for alignment analysis (creates default if None)
            alignment_thresholds: Thresholds for alignment analysis (uses defaults if None)
            enable_hitl: Whether to enable human-in-the-loop functionality
            max_retries: Maximum retries for failed agent evaluations (1-10)
            timeout_seconds: Timeout for individual agent evaluations (1-300)
            
        Raises:
            ValueError: If no agents are provided or parameters are invalid
        """
        if not agents:
            raise ValueError("At least one agent must be provided")
        
        self.agents = agents
        
        # Create alignment engine with thresholds
        if alignment_engine is None:
            thresholds = alignment_thresholds or AlignmentThresholds()
            alignment_engine = AlignmentEngine(
                thresholds=thresholds,
                event_callback=self._log_alignment_event
            )
        
        self.alignment_engine = alignment_engine
        self.enable_hitl = enable_hitl
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        
        logger.info(
            "multi_agent_evaluator_initialized",
            extra={
                "agent_count": len(agents),
                "agent_roles": [agent.role.role_type for agent in agents],
                "enable_hitl": enable_hitl,
                "max_retries": max_retries,
                "timeout_seconds": timeout_seconds,
                "alignment_engine_type": type(self.alignment_engine).__name__,
            }
        )
    
    @classmethod
    def from_roles(
        cls,
        roles: List[AgentRole],
        llm_client: LLMClient,
        agent_class: type = None,
        alignment_thresholds: Optional[AlignmentThresholds] = None,
        **kwargs
    ) -> "MultiAgentEvaluator":
        """Create evaluator from agent roles and LLM client.
        
        Convenience factory method that instantiates agents from role definitions
        and creates a configured evaluator.
        
        Args:
            roles: List of agent role definitions to instantiate
            llm_client: LLM client for agent communication
            agent_class: Agent class to instantiate (uses LLMAgent if None)
            alignment_thresholds: Thresholds for alignment analysis (uses defaults if None)
            **kwargs: Additional arguments passed to evaluator initialization
            
        Returns:
            MultiAgentEvaluator: Configured evaluator instance with instantiated agents
            
        Raises:
            ValueError: If roles list is empty or agent instantiation fails
        """
        from .agent import LLMAgent  # Import here to avoid circular imports
        
        if agent_class is None:
            agent_class = LLMAgent
        
        agents = []
        for role in roles:
            agent = agent_class(role=role, llm_client=llm_client)
            agents.append(agent)
        
        return cls(agents=agents, alignment_thresholds=alignment_thresholds, **kwargs)
    
    def evaluate(self, task: EvaluationTask) -> EvaluationResult:
        """Evaluate a task using multiple agents with alignment analysis.
        
        Args:
            task: The evaluation task to perform
            
        Returns:
            EvaluationResult: Complete evaluation result with alignment analysis
            
        Raises:
            ValueError: If the task is invalid
            RuntimeError: If the evaluation fails
        """
        request_id = self._generate_request_id()
        start_time = time.time()
        
        logger.info(
            "multi_agent_evaluation_started",
            extra={
                "task_id": task.task_id,
                "task_type": task.task_type,
                "agent_count": len(self.agents),
                "request_id": request_id,
            }
        )
        
        try:
            # Validate task
            self._validate_task(task)
            
            # Execute all agents
            agent_decisions = self._execute_agents(task, request_id)
            
            # Analyze alignment between agents
            alignment_summary = self.alignment_engine.analyze_alignment(task, agent_decisions)
            
            # Synthesize final decision
            decision, confidence, reasoning, evidence = self.alignment_engine.synthesize_decision(
                task, agent_decisions, alignment_summary
            )
            
            # Check if human review is needed
            needs_review, review_reason = self.alignment_engine.needs_human_review(alignment_summary)
            
            # Create final result
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            result = EvaluationResult(
                task_id=task.task_id,
                synthesized_decision=decision,
                confidence=confidence,
                reasoning=reasoning,
                evidence=evidence,
                agent_decisions=agent_decisions,
                alignment_summary=alignment_summary,
                requires_human_review=needs_review and self.enable_hitl,
                review_reason=review_reason,
                request_id=request_id,
                processing_time_ms=processing_time_ms,
                metadata={
                    "agent_count": len(agent_decisions),
                    "successful_agents": len([o for o in agent_decisions if o.confidence > 0]),
                    "alignment_state": alignment_summary.state.value,
                }
            )
            
            self._log_evaluation_completion(result)
            
            return result
            
        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            self._log_evaluation_error(task, e, processing_time_ms, request_id)
            raise
    
    def create_hitl_request(self, evaluation_result: EvaluationResult) -> Optional[HITLRequest]:
        """Create a human-in-the-loop review request using the formalized escalation contract.
        
        This method uses the pure, deterministic build_hitl_request function to create
        structured HITL requests when human review is required.
        
        Args:
            evaluation_result: The evaluation result that may need human review
            
        Returns:
            Optional[HITLRequest]: Structured request for human review if required, None otherwise
        """
        return build_hitl_request(evaluation_result, evaluation_result.alignment_summary, self._log_hitl_event)
    
    def _generate_request_id(self) -> str:
        """Generate a unique request ID for tracing."""
        return str(uuid.uuid4())[:8]
    
    def _validate_task(self, task: EvaluationTask) -> None:
        """Validate that the task can be processed.
        
        Args:
            task: The evaluation task to validate
            
        Raises:
            ValueError: If the task is invalid
        """
        if not task.task_id:
            raise ValueError("Task must have a valid task_id")
        
        if not task.task_type:
            raise ValueError("Task must have a task_type")
        
        if not task.evaluation_criteria:
            raise ValueError("Task must have evaluation_criteria")
        
        if not task.context:
            raise ValueError("Task must have context data")
        
        # Validate decision schema compatibility
        for agent in self.agents:
            if hasattr(agent, 'validate_decision_schema'):
                if not agent.validate_decision_schema(task.decision_schema):
                    raise ValueError(
                        f"Agent {agent.role.name} is not compatible with decision schema {type(task.decision_schema).__name__}"
                    )
    
    def _execute_agents(self, task: EvaluationTask, request_id: str) -> List[AgentDecision]:
        """Execute all agents for the given task.
        
        Args:
            task: The evaluation task
            request_id: Request ID for tracing
            
        Returns:
            List[AgentDecision]: Outputs from all successful agent evaluations
        """
        agent_decisions = []
        failed_agents = []
        
        for agent in self.agents:
            try:
                logger.debug(
                    "executing_agent",
                    extra={
                        "agent_name": agent.role.name,
                        "role_type": agent.role.role_type,
                        "task_id": task.task_id,
                        "request_id": request_id,
                    }
                )
                
                output = self._execute_agent_with_retry(agent, task)
                agent_decisions.append(output)
                
            except Exception as e:
                logger.error(
                    "agent_execution_failed",
                    extra={
                        "agent_name": agent.role.name,
                        "role_type": agent.role.role_type,
                        "task_id": task.task_id,
                        "error_type": type(e).__name__,
                        "error": str(e)[:200],
                        "request_id": request_id,
                    },
                    exc_info=True
                )
                failed_agents.append((agent.role.name, str(e)))
        
        if not agent_decisions:
            raise RuntimeError(
                f"All agents failed to execute. Failures: {failed_agents}"
            )
        
        if failed_agents:
            logger.warning(
                "partial_agent_failure",
                extra={
                    "task_id": task.task_id,
                    "successful_agents": len(agent_decisions),
                    "failed_agents": len(failed_agents),
                    "failures": failed_agents,
                    "request_id": request_id,
                }
            )
        
        return agent_decisions
    
    def _execute_agent_with_retry(self, agent: BaseAgent, task: EvaluationTask) -> AgentDecision:
        """Execute an agent with retry logic.
        
        Args:
            agent: The agent to execute
            task: The evaluation task
            
        Returns:
            AgentDecision: The agent's output
            
        Raises:
            RuntimeError: If all retries are exhausted
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                return agent.evaluate(task)
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    logger.debug(
                        "agent_retry",
                        extra={
                            "agent_name": agent.role.name,
                            "attempt": attempt + 1,
                            "max_retries": self.max_retries,
                            "error": str(e)[:100],
                        }
                    )
                    time.sleep(0.5 * (attempt + 1))  # Exponential backoff
        
        raise RuntimeError(
            f"Agent {agent.role.name} failed after {self.max_retries} attempts: {last_error}"
        )
    
    def _log_evaluation_completion(self, result: EvaluationResult) -> None:
        """Log the completion of a multi-agent evaluation."""
        logger.info(
            "multi_agent_evaluation_completed",
            extra={
                "task_id": result.task_id,
                "synthesized_decision": str(result.synthesized_decision),
                "confidence": result.confidence,
                "alignment_state": result.alignment_summary.state.value,
                "requires_human_review": result.requires_human_review,
                "agent_count": len(result.agent_decisions),
                "processing_time_ms": result.processing_time_ms,
                "request_id": result.request_id,
            }
        )
    
    def _log_evaluation_error(
        self,
        task: EvaluationTask,
        error: Exception,
        processing_time_ms: int,
        request_id: str
    ) -> None:
        """Log an evaluation error."""
        logger.error(
            "multi_agent_evaluation_failed",
            extra={
                "task_id": task.task_id,
                "task_type": task.task_type,
                "error_type": type(error).__name__,
                "error": str(error)[:200],
                "processing_time_ms": processing_time_ms,
                "request_id": request_id,
            },
            exc_info=True
        )
    
    def _generate_disagreement_summary(self, result: EvaluationResult) -> str:
        """Generate a human-readable summary of agent disagreements."""
        summary_parts = []
        
        # Overall alignment state
        summary_parts.append(
            f"Alignment State: {result.alignment_summary.state.value.replace('_', ' ').title()}"
        )
        
        # Decision agreement
        if not result.alignment_summary.decision_agreement:
            decisions = {}
            for output in result.agent_decisions:
                decision_str = str(output.decision_value)
                if decision_str not in decisions:
                    decisions[decision_str] = []
                decisions[decision_str].append(output.agent_name)
            
            summary_parts.append("Decision Disagreement:")
            for decision, agents in decisions.items():
                summary_parts.append(f"  - {decision}: {', '.join(agents)}")
        
        # Confidence spread
        if result.alignment_summary.confidence_spread > 0.2:
            confidences = [(o.agent_name, o.confidence) for o in result.agent_decisions]
            confidences.sort(key=lambda x: x[1], reverse=True)
            summary_parts.append("Confidence Spread:")
            for agent_name, confidence in confidences:
                summary_parts.append(f"  - {agent_name}: {confidence:.2f}")
        
        # Disagreement areas
        if result.alignment_summary.disagreement_areas:
            summary_parts.append(
                f"Disagreement Areas: {', '.join(result.alignment_summary.disagreement_areas)}"
            )
        
        return "\n".join(summary_parts)
    
    def _generate_reviewer_instructions(self, result: EvaluationResult) -> str:
        """Generate instructions for human reviewers."""
        instructions = [
            "Please review the agent evaluations and provide your assessment.",
            "",
            "Consider the following:",
            "1. Review each agent's decision, confidence, and reasoning",
            "2. Identify which agent(s) provide the most compelling evidence",
            "3. Consider any factors the agents may have missed",
            "4. Make your own independent assessment",
            "",
            f"Task: {result.task_id}",
            f"Current disagreement: {result.review_reason}",
            "",
            "Agent Summaries:"
        ]
        
        for output in result.agent_decisions:
            instructions.append(
                f"- {output.agent_name} ({output.role_type}): "
                f"{output.decision_value} (confidence: {output.confidence:.2f})"
            )
        
        return "\n".join(instructions)
    
    def _log_alignment_event(self, event: str, data: Dict[str, Any]) -> None:
        """Log alignment engine events with structured metadata."""
        logger.info(event, extra=data)
    
    def _log_hitl_event(self, event: str, data: Dict[str, Any]) -> None:
        """Log HITL escalation events with structured metadata."""
        if event == "hitl_escalation_not_required":
            logger.debug(event, extra=data)
        else:
            logger.info(event, extra=data)