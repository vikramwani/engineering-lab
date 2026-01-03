"""Multi-agent compatibility evaluation service with debate architecture.

This module orchestrates a debate-style compatibility evaluation where an advocate
agent argues FOR compatibility, a skeptic agent argues AGAINST, and a judge agent
resolves the debate. This approach provides more robust and explainable evaluations.

Design Philosophy:
- Clean separation of configuration, prompts, and business logic
- Fail fast on configuration or prompt issues
- Comprehensive logging for debugging and monitoring
- Immutable configuration and structured error handling
"""

import logging
import time
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .agents.base import AgentResult

from ..client import LLMService
from .agents.advocate import AdvocateAgent
from .agents.judge import JudgeAgent
from .agents.skeptic import SkepticAgent
from .agents.base import AgentContext
from .config.settings import get_compatibility_settings
from .models import CompatibilityRequest, CompatibilityResponse
from .prompts.loader import get_prompt_loader

logger = logging.getLogger(__name__)


class CompatibilityService:
    """Multi-agent service for evaluating product compatibility through structured debate.

    This service orchestrates a three-agent system:
    1. Advocate Agent: Argues FOR compatibility
    2. Skeptic Agent: Argues AGAINST compatibility
    3. Judge Agent: Resolves the debate and makes final decision

    The debate architecture provides more robust evaluations by considering
    multiple perspectives and calibrating confidence based on agent agreement.
    """

    def __init__(self, llm: LLMService):
        """Initialize the compatibility service with multi-agent architecture.

        Args:
            llm: LLM service instance for making compatibility evaluations

        Raises:
            RuntimeError: If configuration or prompts cannot be loaded
        """
        self.llm = llm
        self.settings = get_compatibility_settings()

        # Validate prompts are available at startup (fail fast)
        try:
            prompt_loader = get_prompt_loader()
            prompt_loader.preload_all_prompts()
        except Exception as e:
            logger.error(
                "compatibility_service_initialization_failed",
                extra={
                    "error_type": type(e).__name__,
                    "error": str(e),
                    "provider": llm.settings.llm_provider,
                },
            )
            raise RuntimeError(
                f"Failed to initialize compatibility service: {e}"
            ) from e

        # Initialize agents
        self.advocate_agent = AdvocateAgent(llm)
        self.skeptic_agent = SkepticAgent(llm)
        self.judge_agent = JudgeAgent(llm)

        logger.info(
            "compatibility_service_initialized",
            extra={
                "provider": llm.settings.llm_provider,
                "model": llm.settings.model,
                "agent_count": 3,
                "prompt_version": self.settings.prompt_version,
                "require_all_agents": self.settings.require_all_agents,
                "execution_timeout": self.settings.execution_timeout_seconds,
            },
        )

    def evaluate(self, request: CompatibilityRequest) -> CompatibilityResponse:
        """Evaluate compatibility using multi-agent debate architecture.

        Args:
            request: Compatibility evaluation request with product information

        Returns:
            CompatibilityResponse: Final compatibility assessment from judge

        Raises:
            ValueError: If request is invalid or agent responses are malformed
            RuntimeError: If evaluation fails due to service issues
            TimeoutError: If evaluation exceeds configured timeout
        """
        # Generate unique request ID for tracing
        request_id = self._generate_request_id()
        start_time = time.time()

        logger.info(
            "multi_agent_evaluation_started",
            extra={
                "product_a_id": request.product_a.id,
                "product_a_category": request.product_a.category,
                "product_a_brand": request.product_a.brand,
                "product_b_id": request.product_b.id,
                "product_b_category": request.product_b.category,
                "product_b_brand": request.product_b.brand,
                "provider": self.llm.settings.llm_provider,
                "model": self.llm.settings.model,
                "request_id": request_id,
            },
        )

        try:
            # Create shared context for all agents
            context = AgentContext(
                product_a=request.product_a,
                product_b=request.product_b,
                request_id=request_id,
            )

            # Execute debate with timeout protection
            with self._execution_timeout_context():
                # Run advocate and skeptic agents (the debate)
                advocate_result = self._run_agent_with_logging(
                    self.advocate_agent, context, "advocate"
                )

                skeptic_result = self._run_agent_with_logging(
                    self.skeptic_agent, context, "skeptic"
                )

                # Judge resolves the debate
                judge_result = self._run_judge_with_logging(
                    context, advocate_result, skeptic_result
                )

            # Convert to API response format
            response = self._create_compatibility_response(judge_result)

            # Log final evaluation metrics
            evaluation_time = time.time() - start_time
            self._log_evaluation_completion(
                request, response, evaluation_time, request_id
            )

            return response

        except Exception as e:
            evaluation_time = time.time() - start_time
            logger.error(
                "multi_agent_evaluation_failed",
                extra={
                    "product_a_id": request.product_a.id,
                    "product_b_id": request.product_b.id,
                    "error_type": type(e).__name__,
                    "error": str(e)[:200],  # Truncate long error messages
                    "provider": self.llm.settings.llm_provider,
                    "evaluation_time_seconds": evaluation_time,
                    "request_id": request_id,
                },
                exc_info=True,
            )

            # Re-raise with appropriate exception type
            if isinstance(e, (ValueError, TimeoutError)):
                raise
            else:
                raise RuntimeError(f"Compatibility evaluation failed: {e}") from e

    def _generate_request_id(self) -> str:
        """Generate a unique request ID for tracing."""
        return str(uuid.uuid4())[:8]

    def _execution_timeout_context(self):
        """Context manager for execution timeout.

        Currently relies on individual agent timeouts. Future enhancement
        could add overall execution timeout if needed.
        """

        class NoOpContext:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                return False

        return NoOpContext()

    def _run_agent_with_logging(
        self, agent, context: AgentContext, agent_type: str
    ) -> "AgentResult":
        """Run an agent with comprehensive logging.

        Args:
            agent: Agent instance to run
            context: Evaluation context
            agent_type: Type of agent for logging

        Returns:
            AgentResult: Result from agent evaluation
        """
        agent_start_time = time.time()

        try:
            result = agent.evaluate(context)
            agent_duration = time.time() - agent_start_time

            logger.info(
                f"{agent_type}_agent_completed",
                extra={
                    "agent_name": agent.name,
                    "compatible": result.compatible,
                    "relationship": result.relationship,
                    "confidence": result.confidence,
                    "evidence_count": len(result.evidence),
                    "duration_seconds": agent_duration,
                    "request_id": context.request_id,
                },
            )

            return result

        except Exception as e:
            agent_duration = time.time() - agent_start_time
            logger.error(
                f"{agent_type}_agent_failed",
                extra={
                    "agent_name": agent.name,
                    "error_type": type(e).__name__,
                    "error": str(e)[:200],
                    "duration_seconds": agent_duration,
                    "request_id": context.request_id,
                },
            )

            if self.settings.require_all_agents:
                raise
            else:
                # If require_all_agents is False, we would implement fallback 
                # behavior here
                # For now, we always require all agents to succeed
                raise

    def _run_judge_with_logging(
        self,
        context: AgentContext,
        advocate_result: "AgentResult",
        skeptic_result: "AgentResult",
    ) -> "AgentResult":
        """Run judge agent with comprehensive logging.

        Args:
            context: Evaluation context
            advocate_result: Result from advocate agent
            skeptic_result: Result from skeptic agent

        Returns:
            AgentResult: Result from judge evaluation
        """
        judge_start_time = time.time()

        try:
            result = self.judge_agent.evaluate_debate(
                context, advocate_result, skeptic_result
            )
            judge_duration = time.time() - judge_start_time

            logger.info(
                "judge_agent_completed",
                extra={
                    "agent_name": self.judge_agent.name,
                    "compatible": result.compatible,
                    "relationship": result.relationship,
                    "confidence": result.confidence,
                    "evidence_count": len(result.evidence),
                    "duration_seconds": judge_duration,
                    "request_id": context.request_id,
                },
            )

            return result

        except Exception as e:
            judge_duration = time.time() - judge_start_time
            logger.error(
                "judge_agent_failed",
                extra={
                    "agent_name": self.judge_agent.name,
                    "error_type": type(e).__name__,
                    "error": str(e)[:200],
                    "duration_seconds": judge_duration,
                    "request_id": context.request_id,
                },
            )
            raise

    def _create_compatibility_response(
        self, judge_result: "AgentResult"
    ) -> CompatibilityResponse:
        """Convert judge result to API response format.

        Args:
            judge_result: Result from judge agent

        Returns:
            CompatibilityResponse: API-compatible response
        """
        return CompatibilityResponse(
            compatible=judge_result.compatible,
            relationship=judge_result.relationship,
            confidence=judge_result.confidence,
            explanation=judge_result.explanation,
            evidence=judge_result.evidence,
        )

    def _log_evaluation_completion(
        self,
        request: CompatibilityRequest,
        response: CompatibilityResponse,
        evaluation_time: float,
        request_id: str,
    ) -> None:
        """Log comprehensive evaluation completion metrics."""
        logger.info(
            "multi_agent_evaluation_completed",
            extra={
                "product_a_id": request.product_a.id,
                "product_b_id": request.product_b.id,
                "compatible": response.compatible,
                "relationship": response.relationship,
                "confidence": response.confidence,
                "evidence_count": len(response.evidence),
                "provider": self.llm.settings.llm_provider,
                "model": self.llm.settings.model,
                "evaluation_time_seconds": evaluation_time,
                "request_id": request_id,
            },
        )
