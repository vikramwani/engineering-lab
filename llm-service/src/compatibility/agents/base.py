"""Base agent interface and shared data structures for debate-style evaluation.

This module provides the foundational abstractions for a multi-agent debate
system where agents argue for and against compatibility, with a judge making
the final decision. The architecture ensures clean separation of concerns and
type safety.

Design Philosophy:
- Each agent has a single, clear responsibility
- All agents produce structured, validated outputs
- The system fails fast on invalid agent responses
- Comprehensive logging enables debugging and monitoring
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from ..models import CompatibilityRelationship, Product

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AgentContext:
    """Immutable context passed to all agents for compatibility evaluation.

    Contains the product pair and metadata needed for evaluation. This context
    is shared across all agents to ensure consistent input data.
    """

    product_a: Product
    product_b: Product
    request_id: str

    def get_product_summary(self) -> str:
        """Generate a concise summary of both products for logging."""
        return (
            f"A:{self.product_a.category}/{self.product_a.brand} "
            f"B:{self.product_b.category}/{self.product_b.brand}"
        )


@dataclass(frozen=True)
class AgentResult:
    """Immutable structured result from an individual agent evaluation.

    Each agent returns this standardized format for consistent processing
    by the judge agent. All fields are validated upon creation.
    """

    agent_name: str
    compatible: bool
    relationship: CompatibilityRelationship
    confidence: float  # Must be in range [0.0, 1.0]
    explanation: str
    evidence: List[str]
    reasoning: str  # Internal reasoning for judge agent

    def __post_init__(self) -> None:
        """Validate agent result fields after creation."""
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(
                f"Agent {self.agent_name} confidence {self.confidence} "
                f"not in [0.0, 1.0]"
            )

        if not self.explanation.strip():
            raise ValueError(
                f"Agent {self.agent_name} provided empty explanation"
            )

        if not isinstance(self.evidence, list):
            raise ValueError(
                f"Agent {self.agent_name} evidence must be a list"
            )

        if len(self.evidence) > 20:  # Reasonable upper bound
            raise ValueError(
                f"Agent {self.agent_name} provided too many evidence items: "
                f"{len(self.evidence)}"
            )


class BaseAgent(ABC):
    """Abstract base class for compatibility evaluation agents.

    All agents in the debate system must implement this interface to ensure
    consistent behavior and enable polymorphic usage by the orchestrator.

    Design Principles:
    - Single responsibility per agent
    - Structured output only
    - Comprehensive logging
    - Fail fast on errors
    """

    def __init__(self, name: str):
        """Initialize the agent with a unique name.

        Args:
            name: Unique identifier for this agent type
        """
        self.name = name
        logger.debug(
            "agent_initialized",
            extra={"agent_name": name, "agent_type": self.__class__.__name__},
        )

    @abstractmethod
    def evaluate(self, context: AgentContext) -> AgentResult:
        """Evaluate product compatibility from this agent's perspective.

        Args:
            context: Shared evaluation context with product information

        Returns:
            AgentResult: Structured evaluation result

        Raises:
            ValueError: If evaluation fails or produces invalid results
            RuntimeError: If agent encounters an unrecoverable error
        """
        pass

    def _validate_result(self, result: AgentResult) -> None:
        """Validate agent result meets all requirements.

        This method is called by concrete agents to ensure their results
        are valid before returning them to the orchestrator.

        Args:
            result: Agent result to validate

        Raises:
            ValueError: If result is invalid
        """
        # AgentResult.__post_init__ handles most validation
        # Additional agent-specific validation can be added here

        logger.debug(
            "agent_result_validated",
            extra={
                "agent_name": self.name,
                "compatible": result.compatible,
                "relationship": result.relationship,
                "confidence": result.confidence,
                "evidence_count": len(result.evidence),
            },
        )


class DebateAgent(BaseAgent):
    """Base class for agents participating in the compatibility debate.

    Debate agents (advocate and skeptic) share common functionality for
    interacting with LLMs and processing structured responses.
    """

    def __init__(self, name: str, llm_service, prompt_name: str):
        """Initialize a debate agent with LLM service and prompt.

        Args:
            name: Unique agent name
            llm_service: LLM service for making API calls
            prompt_name: Name of the prompt file to load
        """
        super().__init__(name)
        self.llm_service = llm_service
        self.prompt_name = prompt_name

        # Load prompt at initialization to fail fast
        from ..prompts.loader import load_prompt

        self.prompt_template = load_prompt(prompt_name)

        logger.info(
            "debate_agent_initialized",
            extra={
                "agent_name": name,
                "prompt_name": prompt_name,
                "prompt_length": len(self.prompt_template),
            },
        )

    def _build_prompt(self, context: AgentContext) -> str:
        """Build the complete prompt with product information.

        Args:
            context: Evaluation context with product data

        Returns:
            str: Complete prompt ready for LLM
        """
        product_a_desc = self._format_product_description(context.product_a)
        product_b_desc = self._format_product_description(context.product_b)

        # Simple concatenation - no string formatting on JSON structures
        prompt = (
            self.prompt_template
            + "\n\n### Product A\n"
            + product_a_desc
            + "\n\n### Product B\n"
            + product_b_desc
        )

        logger.debug(
            "agent_prompt_built",
            extra={
                "agent_name": self.name,
                "prompt_length": len(prompt),
                "request_id": context.request_id,
            },
        )

        return prompt

    def _format_product_description(self, product: Product) -> str:
        """Format a product for inclusion in the prompt.

        Args:
            product: Product to format

        Returns:
            str: Formatted product description
        """
        return (
            f"ID: {product.id}\n"
            f"Title: {product.title}\n"
            f"Category: {product.category}\n"
            f"Brand: {product.brand}\n"
            f"Attributes: {product.attributes}"
        )
