import json
import logging
from typing import Any, Dict

from ..client import LLMService
from .models import CompatibilityRequest, CompatibilityResponse, CompatibilityRelationship
from .prompt import SYSTEM_PROMPT

logger = logging.getLogger("llm_service")


class CompatibilityService:
    def __init__(self, llm: LLMService):
        self.llm = llm

    def _build_prompt(self, request: CompatibilityRequest) -> str:
        """Build the final prompt for compatibility evaluation."""
        base_prompt = (
            SYSTEM_PROMPT
            if isinstance(SYSTEM_PROMPT, str)
            else str(SYSTEM_PROMPT)
        )

        # Build product descriptions from Product objects
        product_a_desc = f"ID: {request.product_a.id}\nTitle: {request.product_a.title}\nCategory: {request.product_a.category}\nBrand: {request.product_a.brand}\nAttributes: {request.product_a.attributes}"
        product_b_desc = f"ID: {request.product_b.id}\nTitle: {request.product_b.title}\nCategory: {request.product_b.category}\nBrand: {request.product_b.brand}\nAttributes: {request.product_b.attributes}"

        prompt = (
            base_prompt
            + "\n\n### Product A\n"
            + product_a_desc
            + "\n\n### Product B\n"
            + product_b_desc
        )

        return prompt

    def _safe_parse_json(self, raw_output: str) -> Dict[str, Any]:
        """Parse LLM output safely and log failures clearly."""
        try:
            parsed = json.loads(raw_output)
            return parsed
        except json.JSONDecodeError as e:
            logger.error(
                "compatibility_invalid_json",
                extra={"raw_output": raw_output[:500]},  # Truncate for safety
            )
            raise ValueError("LLM returned invalid JSON") from e

    def _normalize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize raw LLM JSON into CompatibilityResponse-compatible dict."""
        relationship_raw = data.get("relationship", "insufficient_information")

        # Valid relationship values
        valid_relationships = [
            "replacement_filter",
            "replacement_part",
            "accessory",
            "consumable",
            "power_supply",
            "not_compatible",
            "insufficient_information",
        ]

        # Coerce relationship safely
        if relationship_raw not in valid_relationships:
            logger.warning(
                "compatibility_relationship_invalid",
                extra={"relationship_raw": relationship_raw},
            )
            relationship = "insufficient_information"
        else:
            relationship = relationship_raw

        evidence_raw = data.get("evidence", [])
        if isinstance(evidence_raw, list):
            evidence = evidence_raw
        elif isinstance(evidence_raw, str):
            evidence = [evidence_raw]
        else:
            evidence = []

        # Normalize confidence value (handle both percentage and decimal formats)
        confidence_raw = data.get("confidence", 0.0)
        confidence = float(confidence_raw)

        # If confidence is > 1.0, assume it's a percentage and convert to decimal
        if confidence > 1.0:
            confidence = confidence / 100.0
            logger.info(
                "compatibility_confidence_normalized",
                extra={"original": confidence_raw, "normalized": confidence},
            )

        # Clamp confidence to valid range [0.0, 1.0]
        confidence = max(0.0, min(1.0, confidence))

        normalized = {
            "compatible": bool(data.get("compatible", False)),
            "relationship": relationship,
            "confidence": confidence,
            "explanation": str(data.get("explanation", "")),
            "evidence": evidence,
        }

        return normalized

    def evaluate(self, request: CompatibilityRequest) -> CompatibilityResponse:
        """Evaluate compatibility between two products."""
        logger.info(
            "compatibility_request_received",
            extra={
                "product_a_id": request.product_a.id,
                "product_b_id": request.product_b.id,
            },
        )

        prompt = self._build_prompt(request)
        raw_output = self.llm.chat(prompt=prompt)

        logger.info(
            "compatibility_llm_response",
            extra={"raw_output": raw_output[:500]},  # Truncate for safety
        )

        parsed = self._safe_parse_json(raw_output)
        normalized = self._normalize(parsed)
        response = CompatibilityResponse(**normalized)

        logger.info(
            "compatibility_response_validated",
            extra={
                "compatible": response.compatible,
                "relationship": response.relationship,
                "confidence": response.confidence,
            },
        )

        return response
