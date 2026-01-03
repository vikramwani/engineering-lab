"""Advocate agent that argues FOR product compatibility in the debate system.

This agent takes the position that products are compatible and looks for
evidence to support that conclusion. It provides one side of the debate
that will be resolved by the judge agent.

Design Philosophy:
- Focus on finding compatibility evidence
- Be thorough but honest in analysis
- Provide structured reasoning for the judge
- Fail fast on invalid LLM responses
"""

import json
import logging
from typing import Any, Dict

from ...client import LLMService
from ..config.settings import get_compatibility_settings
from .base import AgentContext, AgentResult, DebateAgent

logger = logging.getLogger(__name__)


class AdvocateAgent(DebateAgent):
    """Agent that argues FOR compatibility between products.

    This agent actively looks for evidence that products are compatible
    and can work together. It provides the positive perspective in the
    multi-agent debate system.
    """

    def __init__(self, llm_service: LLMService):
        """Initialize the advocate agent.

        Args:
            llm_service: LLM service for making evaluations
        """
        super().__init__(
            name="advocate",
            llm_service=llm_service,
            prompt_name="compatibility_agent_for",
        )
        self.settings = get_compatibility_settings()

        logger.info(
            "advocate_agent_ready",
            extra={
                "agent_name": self.name,
                "max_tokens": self.settings.agent_max_tokens,
                "timeout_seconds": self.settings.agent_timeout_seconds,
            },
        )

    def evaluate(self, context: AgentContext) -> AgentResult:
        """Evaluate compatibility by arguing FOR compatibility.

        Args:
            context: Evaluation context with product information

        Returns:
            AgentResult: Structured evaluation arguing for compatibility

        Raises:
            ValueError: If LLM response is invalid or unparseable
            RuntimeError: If evaluation fails due to service issues
        """
        logger.info(
            "advocate_evaluation_started",
            extra={
                "agent_name": self.name,
                "product_summary": context.get_product_summary(),
                "request_id": context.request_id,
            },
        )

        try:
            # Build prompt with product information
            prompt = self._build_prompt(context)

            # Call LLM with configured parameters
            raw_output = self.llm_service.chat(
                prompt=prompt, max_tokens=self.settings.agent_max_tokens
            )

            logger.debug(
                "advocate_llm_response_received",
                extra={
                    "agent_name": self.name,
                    "response_length": len(raw_output),
                    "request_id": context.request_id,
                },
            )

            # Parse and validate response
            parsed_data = self._parse_llm_response(raw_output, context.request_id)
            result = self._create_agent_result(parsed_data)

            # Validate result before returning
            self._validate_result(result)

            logger.info(
                "advocate_evaluation_completed",
                extra={
                    "agent_name": self.name,
                    "compatible": result.compatible,
                    "relationship": result.relationship,
                    "confidence": result.confidence,
                    "evidence_count": len(result.evidence),
                    "request_id": context.request_id,
                },
            )

            return result

        except json.JSONDecodeError as e:
            logger.error(
                "advocate_json_parse_error",
                extra={
                    "agent_name": self.name,
                    "error": str(e),
                    "raw_output_preview": (
                        raw_output[:200] if "raw_output" in locals() else "N/A"
                    ),
                    "request_id": context.request_id,
                },
            )
            raise ValueError(f"Advocate agent returned invalid JSON: {e}") from e

        except Exception as e:
            logger.error(
                "advocate_evaluation_failed",
                extra={
                    "agent_name": self.name,
                    "error_type": type(e).__name__,
                    "error": str(e),
                    "request_id": context.request_id,
                },
                exc_info=True,
            )
            raise RuntimeError(f"Advocate agent evaluation failed: {e}") from e

    def _parse_llm_response(self, raw_output: str, request_id: str) -> Dict[str, Any]:
        """Parse and validate LLM response JSON.

        Args:
            raw_output: Raw response from LLM
            request_id: Request ID for logging

        Returns:
            Dict[str, Any]: Parsed JSON data

        Raises:
            json.JSONDecodeError: If response is not valid JSON
        """
        try:
            parsed = json.loads(raw_output.strip())

            logger.debug(
                "advocate_json_parsed_successfully",
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
                    "advocate_invalid_json_output",
                    extra={
                        "agent_name": self.name,
                        "raw_output": raw_output[: self.settings.log_output_max_length],
                        "json_error": str(e),
                        "request_id": request_id,
                    },
                )
            raise

    def _create_agent_result(self, data: Dict[str, Any]) -> AgentResult:
        """Create AgentResult from parsed LLM response data.

        Args:
            data: Parsed JSON data from LLM

        Returns:
            AgentResult: Validated agent result
        """
        # Normalize confidence (handle percentage format)
        confidence = float(data.get("confidence", 0.0))
        if confidence > 1.0:
            confidence = confidence / 100.0
            logger.debug(
                "advocate_confidence_normalized",
                extra={
                    "agent_name": self.name,
                    "original": data.get("confidence"),
                    "normalized": confidence,
                },
            )

        # Ensure confidence is in valid range
        confidence = max(0.0, min(1.0, confidence))

        # Normalize evidence to list format
        evidence = data.get("evidence", [])
        if isinstance(evidence, str):
            evidence = [evidence]
        elif not isinstance(evidence, list):
            evidence = []
            logger.warning(
                "advocate_evidence_invalid_type",
                extra={
                    "agent_name": self.name,
                    "evidence_type": type(evidence).__name__,
                },
            )

        # Truncate evidence if too long
        if len(evidence) > self.settings.max_evidence_items:
            evidence = evidence[: self.settings.max_evidence_items]
            logger.warning(
                "advocate_evidence_truncated",
                extra={
                    "agent_name": self.name,
                    "original_count": len(data.get("evidence", [])),
                    "truncated_count": len(evidence),
                },
            )

        return AgentResult(
            agent_name=self.name,
            compatible=bool(data.get("compatible", False)),
            relationship=data.get("relationship", self.settings.fallback_relationship),
            confidence=confidence,
            explanation=str(
                data.get("explanation", self.settings.fallback_explanation)
            ),
            evidence=evidence,
            reasoning=str(data.get("reasoning", "")),
        )
