"""Judge agent for resolving compatibility evaluation debates.

This agent reviews arguments from both advocate and skeptic agents, then makes
a final decision based on the strength of evidence presented. It implements
confidence calibration based on agent agreement/disagreement.

Design Philosophy:
- Impartial evaluation of both perspectives
- Confidence calibration based on consensus
- Synthesis of best evidence from all agents
- Clear reasoning for final decisions
"""

import json
import logging
from typing import Any, Dict

from ...client import LLMService
from ..config.settings import get_compatibility_settings
from .base import AgentContext, AgentResult, BaseAgent

logger = logging.getLogger(__name__)


class JudgeAgent(BaseAgent):
    """Agent that resolves debates between advocate and skeptic agents.

    This agent reviews the arguments from both sides of the compatibility debate
    and makes a final decision. It calibrates confidence based on the level of
    agreement between the debating agents.
    """

    def __init__(self, llm_service: LLMService):
        """Initialize the judge agent.

        Args:
            llm_service: LLM service for making evaluations
        """
        super().__init__("judge")
        self.llm_service = llm_service
        self.settings = get_compatibility_settings()

        # Load judge prompt at initialization
        from ..prompts.loader import load_prompt

        self.prompt_template = load_prompt("compatibility_judge")

        logger.info(
            "judge_agent_ready",
            extra={
                "agent_name": self.name,
                "prompt_length": len(self.prompt_template),
                "max_tokens": self.settings.agent_max_tokens,
            },
        )

    def evaluate(self, context: AgentContext) -> AgentResult:
        """Standard evaluate method - not used for judge agent.

        Judge agent requires debate results via evaluate_debate method.

        Raises:
            NotImplementedError: Always, as judge requires debate inputs
        """
        raise NotImplementedError(
            "Judge agent requires debate results via evaluate_debate method"
        )

    def evaluate_debate(
        self,
        context: AgentContext,
        advocate_result: AgentResult,
        skeptic_result: AgentResult,
    ) -> AgentResult:
        """Evaluate compatibility by resolving the debate between agents.

        Args:
            context: Evaluation context with product information
            advocate_result: Result from the advocate agent
            skeptic_result: Result from the skeptic agent

        Returns:
            AgentResult: Final reconciled evaluation

        Raises:
            ValueError: If LLM response is invalid or unparseable
            RuntimeError: If evaluation fails due to service issues
        """
        logger.info(
            "judge_evaluation_started",
            extra={
                "agent_name": self.name,
                "product_summary": context.get_product_summary(),
                "advocate_compatible": advocate_result.compatible,
                "skeptic_compatible": skeptic_result.compatible,
                "request_id": context.request_id,
            },
        )

        # Analyze agreement between agents
        agreement_analysis = self._analyze_agent_agreement(
            advocate_result, skeptic_result, context.request_id
        )

        try:
            # Build prompt with debate results
            prompt = self._build_debate_prompt(context, advocate_result, skeptic_result)

            # Call LLM with configured parameters
            raw_output = self.llm_service.chat(
                prompt=prompt, max_tokens=self.settings.agent_max_tokens
            )

            logger.debug(
                "judge_llm_response_received",
                extra={
                    "agent_name": self.name,
                    "response_length": len(raw_output),
                    "request_id": context.request_id,
                },
            )

            # Parse and validate response
            parsed_data = self._parse_llm_response(raw_output, context.request_id)
            result = self._create_agent_result(parsed_data, agreement_analysis)

            # Validate result before returning
            self._validate_result(result)

            logger.info(
                "judge_evaluation_completed",
                extra={
                    "agent_name": self.name,
                    "compatible": result.compatible,
                    "relationship": result.relationship,
                    "confidence": result.confidence,
                    "evidence_count": len(result.evidence),
                    "agents_agreed": agreement_analysis["compatible_agreement"],
                    "request_id": context.request_id,
                },
            )

            return result

        except json.JSONDecodeError as e:
            logger.error(
                "judge_json_parse_error",
                extra={
                    "agent_name": self.name,
                    "error": str(e),
                    "raw_output_preview": (
                        raw_output[:200] if "raw_output" in locals() else "N/A"
                    ),
                    "request_id": context.request_id,
                },
            )
            raise ValueError(f"Judge agent returned invalid JSON: {e}") from e

        except Exception as e:
            logger.error(
                "judge_evaluation_failed",
                extra={
                    "agent_name": self.name,
                    "error_type": type(e).__name__,
                    "error": str(e),
                    "request_id": context.request_id,
                },
                exc_info=True,
            )
            raise RuntimeError(f"Judge agent evaluation failed: {e}") from e

    def _analyze_agent_agreement(
        self, advocate_result: AgentResult, skeptic_result: AgentResult, request_id: str
    ) -> Dict[str, Any]:
        """Analyze the level of agreement between debating agents.

        Args:
            advocate_result: Advocate agent result
            skeptic_result: Skeptic agent result
            request_id: Request ID for logging

        Returns:
            Dict[str, Any]: Agreement analysis data
        """
        compatible_agreement = advocate_result.compatible == skeptic_result.compatible
        relationship_agreement = (
            advocate_result.relationship == skeptic_result.relationship
        )

        # Calculate confidence spread
        confidence_spread = abs(advocate_result.confidence - skeptic_result.confidence)
        avg_confidence = (advocate_result.confidence + skeptic_result.confidence) / 2

        analysis = {
            "compatible_agreement": compatible_agreement,
            "relationship_agreement": relationship_agreement,
            "confidence_spread": confidence_spread,
            "avg_confidence": avg_confidence,
            "advocate_confidence": advocate_result.confidence,
            "skeptic_confidence": skeptic_result.confidence,
        }

        if compatible_agreement and relationship_agreement:
            logger.info(
                "agents_in_full_agreement",
                extra={
                    "compatible": advocate_result.compatible,
                    "relationship": advocate_result.relationship,
                    "avg_confidence": avg_confidence,
                    "confidence_spread": confidence_spread,
                    "request_id": request_id,
                },
            )
        else:
            logger.warning(
                "agents_in_disagreement",
                extra={
                    "advocate_compatible": advocate_result.compatible,
                    "skeptic_compatible": skeptic_result.compatible,
                    "advocate_relationship": advocate_result.relationship,
                    "skeptic_relationship": skeptic_result.relationship,
                    "compatible_agreement": compatible_agreement,
                    "relationship_agreement": relationship_agreement,
                    "confidence_spread": confidence_spread,
                    "request_id": request_id,
                },
            )

        return analysis

    def _build_debate_prompt(
        self,
        context: AgentContext,
        advocate_result: AgentResult,
        skeptic_result: AgentResult,
    ) -> str:
        """Build judge prompt with debate results.

        Args:
            context: Evaluation context
            advocate_result: Advocate agent result
            skeptic_result: Skeptic agent result

        Returns:
            str: Complete prompt for judge evaluation
        """
        product_a_desc = self._format_product_description(context.product_a)
        product_b_desc = self._format_product_description(context.product_b)

        # Format agent results as structured text (not JSON to avoid f
        # ormatting issues)
        advocate_summary = self._format_agent_result(advocate_result)
        skeptic_summary = self._format_agent_result(skeptic_result)

        prompt = (
            self.prompt_template
            + "\n\n### Product A\n"
            + product_a_desc
            + "\n\n### Product B\n"
            + product_b_desc
            + "\n\nADVOCATE_AGENT: "
            + advocate_summary
            + "\n\nSKEPTIC_AGENT: "
            + skeptic_summary
        )

        logger.debug(
            "judge_prompt_built",
            extra={
                "agent_name": self.name,
                "prompt_length": len(prompt),
                "request_id": context.request_id,
            },
        )

        return prompt

    def _format_product_description(self, product) -> str:
        """Format a product for inclusion in the prompt."""
        return (
            f"ID: {product.id}\n"
            f"Title: {product.title}\n"
            f"Category: {product.category}\n"
            f"Brand: {product.brand}\n"
            f"Attributes: {product.attributes}"
        )

    def _format_agent_result(self, result: AgentResult) -> str:
        """Format an agent result for inclusion in judge prompt.

        Args:
            result: Agent result to format

        Returns:
            str: Formatted agent result
        """
        evidence_str = (
            ", ".join(result.evidence) if result.evidence else "None provided"
        )

        return (
            f"Compatible: {result.compatible}\n"
            f"Relationship: {result.relationship}\n"
            f"Confidence: {result.confidence}\n"
            f"Explanation: {result.explanation}\n"
            f"Evidence: {evidence_str}\n"
            f"Reasoning: {result.reasoning}"
        )

    def _parse_llm_response(self, raw_output: str, request_id: str) -> Dict[str, Any]:
        """Parse and validate LLM response JSON."""
        try:
            parsed = json.loads(raw_output.strip())

            logger.debug(
                "judge_json_parsed_successfully",
                extra={
                    "agent_name": self.name,
                    "parsed_keys": list(parsed.keys()),
                    "request_id": request_id,
                },
            )

            return parsed

        except json.JSONDecodeError as e:
            # Log the problematic output for debugging
            if self.settings.log_agent_outputs:
                logger.error(
                    "judge_invalid_json_output",
                    extra={
                        "agent_name": self.name,
                        "raw_output": raw_output[: self.settings.log_output_max_length],
                        "json_error": str(e),
                        "request_id": request_id,
                    },
                )
            raise

    def _create_agent_result(
        self, data: Dict[str, Any], agreement_analysis: Dict[str, Any]
    ) -> AgentResult:
        """Create AgentResult from parsed LLM response with confidence calibration.

        Args:
            data: Parsed JSON data from LLM
            agreement_analysis: Analysis of agent agreement

        Returns:
            AgentResult: Validated agent result with calibrated confidence
        """
        # Start with LLM's confidence assessment
        base_confidence = float(data.get("confidence", 0.5))
        if base_confidence > 1.0:
            base_confidence = base_confidence / 100.0

        # Calibrate confidence based on agent agreement
        calibrated_confidence = self._calibrate_confidence(
            base_confidence, agreement_analysis
        )

        # Normalize evidence to list format
        evidence = data.get("evidence", [])
        if isinstance(evidence, str):
            evidence = [evidence]
        elif not isinstance(evidence, list):
            evidence = []

        # Truncate evidence if too long
        if len(evidence) > self.settings.max_evidence_items:
            evidence = evidence[: self.settings.max_evidence_items]

        return AgentResult(
            agent_name=self.name,
            compatible=bool(data.get("compatible", False)),
            relationship=data.get("relationship", self.settings.fallback_relationship),
            confidence=calibrated_confidence,
            explanation=str(
                data.get("explanation", self.settings.fallback_explanation)
            ),
            evidence=evidence,
            reasoning=str(data.get("reasoning", "")),
        )

    def _calibrate_confidence(
        self, base_confidence: float, agreement_analysis: Dict[str, Any]
    ) -> float:
        """Calibrate confidence based on agent agreement patterns.

        Args:
            base_confidence: Base confidence from LLM
            agreement_analysis: Agreement analysis data

        Returns:
            float: Calibrated confidence value
        """
        # Start with base confidence
        calibrated = base_confidence

        # Boost confidence when agents agree
        if (
            agreement_analysis["compatible_agreement"]
            and agreement_analysis["relationship_agreement"]
        ):
            # Full agreement - boost confidence
            calibrated = min(1.0, calibrated + 0.1)
            logger.debug(
                "confidence_boosted_for_agreement",
                extra={
                    "base_confidence": base_confidence,
                    "calibrated_confidence": calibrated,
                    "boost_reason": "full_agreement",
                },
            )
        elif agreement_analysis["compatible_agreement"]:
            # Partial agreement - small boost
            calibrated = min(1.0, calibrated + 0.05)
            logger.debug(
                "confidence_boosted_for_partial_agreement",
                extra={
                    "base_confidence": base_confidence,
                    "calibrated_confidence": calibrated,
                    "boost_reason": "compatible_agreement",
                },
            )
        else:
            # Disagreement - reduce confidence
            reduction = min(0.2, agreement_analysis["confidence_spread"] * 0.5)
            calibrated = max(0.1, calibrated - reduction)
            logger.debug(
                "confidence_reduced_for_disagreement",
                extra={
                    "base_confidence": base_confidence,
                    "calibrated_confidence": calibrated,
                    "reduction": reduction,
                    "confidence_spread": agreement_analysis["confidence_spread"],
                },
            )

        # Ensure final confidence is in valid range
        return max(0.0, min(1.0, calibrated))
