"""Core compatibility evaluation service using LLM reasoning.

This module provides the CompatibilityService class that evaluates product
compatibility relationships using structured LLM prompts, with robust JSON
parsing, confidence normalization, and comprehensive error handling.
"""
import json
import logging
from typing import Any, Dict

from ..client import LLMService
from .models import CompatibilityRequest, CompatibilityResponse, CompatibilityRelationship
from .prompt import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class CompatibilityService:
    """Service for evaluating product compatibility using LLM reasoning.
    
    This service takes two products and uses an LLM to determine their compatibility
    relationship, providing structured analysis with confidence scores and evidence.
    """
    
    def __init__(self, llm: LLMService):
        """Initialize the compatibility service with an LLM client.
        
        Args:
            llm: LLM service instance for making compatibility evaluations
        """
        self.llm = llm
        logger.debug("compatibility_service_initialized", extra={"provider": llm.settings.llm_provider})

    def _build_prompt(self, request: CompatibilityRequest) -> str:
        """Build the final prompt for compatibility evaluation."""
        logger.debug("compatibility_prompt_building_started")
        
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

        logger.debug(
            "compatibility_prompt_built",
            extra={
                "prompt_length": len(prompt),
                "product_a_id": request.product_a.id,
                "product_b_id": request.product_b.id,
            }
        )

        return prompt

    def _safe_parse_json(self, raw_output: str) -> Dict[str, Any]:
        """Parse LLM output safely and log failures clearly."""
        logger.debug("compatibility_json_parsing_started", extra={"output_length": len(raw_output)})
        
        try:
            parsed = json.loads(raw_output)
            logger.debug("compatibility_json_parsing_successful", extra={"parsed_keys": list(parsed.keys())})
            return parsed
        except json.JSONDecodeError as e:
            logger.error(
                "compatibility_json_parsing_failed",
                extra={
                    "raw_output": raw_output[:500],  # Truncate for safety
                    "error": str(e),
                    "error_position": getattr(e, 'pos', None),
                }
            )
            raise ValueError("LLM returned invalid JSON") from e

    def _normalize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize raw LLM JSON into CompatibilityResponse-compatible dict."""
        logger.debug("compatibility_normalization_started", extra={"input_keys": list(data.keys())})
        
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
                extra={
                    "relationship_raw": relationship_raw,
                    "valid_relationships": valid_relationships,
                }
            )
            relationship = "insufficient_information"
        else:
            relationship = relationship_raw

        evidence_raw = data.get("evidence", [])
        if isinstance(evidence_raw, list):
            evidence = evidence_raw
        elif isinstance(evidence_raw, str):
            evidence = [evidence_raw]
            logger.debug("compatibility_evidence_converted_from_string")
        else:
            evidence = []
            logger.warning("compatibility_evidence_invalid_type", extra={"evidence_type": type(evidence_raw).__name__})

        # Normalize confidence value (handle both percentage and decimal formats)
        confidence_raw = data.get("confidence", 0.0)
        confidence = float(confidence_raw)

        # If confidence is > 1.0, assume it's a percentage and convert to decimal
        if confidence > 1.0:
            confidence = confidence / 100.0
            logger.info(
                "compatibility_confidence_normalized",
                extra={"original": confidence_raw, "normalized": confidence}
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

        logger.debug(
            "compatibility_normalization_completed",
            extra={
                "compatible": normalized["compatible"],
                "relationship": normalized["relationship"],
                "confidence": normalized["confidence"],
                "evidence_count": len(normalized["evidence"]),
            }
        )

        return normalized

    def evaluate(self, request: CompatibilityRequest) -> CompatibilityResponse:
        """Evaluate compatibility between two products."""
        logger.info(
            "compatibility_evaluation_started",
            extra={
                "product_a_id": request.product_a.id,
                "product_a_category": request.product_a.category,
                "product_a_brand": request.product_a.brand,
                "product_b_id": request.product_b.id,
                "product_b_category": request.product_b.category,
                "product_b_brand": request.product_b.brand,
                "provider": self.llm.settings.llm_provider,
                "model": self.llm.settings.model,
            }
        )

        prompt = self._build_prompt(request)
        
        # Log the final prompt at debug level
        logger.debug("compatibility_final_prompt", extra={"prompt": prompt})

        raw_output = self.llm.chat(prompt=prompt)

        logger.info(
            "compatibility_llm_response_received",
            extra={"raw_output": raw_output[:500]}  # Truncate for safety
        )

        parsed = self._safe_parse_json(raw_output)
        normalized = self._normalize(parsed)
        response = CompatibilityResponse(**normalized)

        logger.info(
            "compatibility_evaluation_completed",
            extra={
                "product_a_id": request.product_a.id,
                "product_b_id": request.product_b.id,
                "compatible": response.compatible,
                "relationship": response.relationship,
                "confidence": response.confidence,
                "evidence_count": len(response.evidence),
                "provider": self.llm.settings.llm_provider,
            }
        )

        return response
