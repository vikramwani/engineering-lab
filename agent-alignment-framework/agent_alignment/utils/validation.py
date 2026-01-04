"""Validation utilities for the agent alignment framework.

This module provides utilities for validating and parsing agent outputs,
JSON responses, and other data structures used throughout the framework.
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple, Union

from ..utils.logging import get_logger

logger = get_logger(__name__)


def validate_json_response(response: str, required_fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """Validate and parse a JSON response from an agent.
    
    Args:
        response: Raw response string that should contain JSON
        required_fields: List of required fields in the JSON object
        
    Returns:
        Dict[str, Any]: Parsed JSON object
        
    Raises:
        ValueError: If JSON is invalid or missing required fields
    """
    # First try to extract JSON from the response
    json_data = extract_json_from_text(response)
    
    if json_data is None:
        raise ValueError(f"No valid JSON found in response: {response[:200]}...")
    
    # Validate required fields
    if required_fields:
        missing_fields = []
        for field in required_fields:
            if field not in json_data:
                missing_fields.append(field)
        
        if missing_fields:
            raise ValueError(
                f"Missing required fields in JSON response: {missing_fields}. "
                f"Available fields: {list(json_data.keys())}"
            )
    
    logger.debug(
        "json_response_validated",
        extra={
            "response_length": len(response),
            "json_fields": list(json_data.keys()),
            "required_fields": required_fields or [],
        }
    )
    
    return json_data


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """Extract JSON object from text that may contain other content.
    
    This function tries multiple strategies to find and parse JSON:
    1. Look for JSON blocks marked with ```json
    2. Look for content between { and }
    3. Try parsing the entire text as JSON
    
    Args:
        text: Text that may contain JSON
        
    Returns:
        Optional[Dict[str, Any]]: Parsed JSON object or None if not found
    """
    if not text or not text.strip():
        return None
    
    # Strategy 1: Look for JSON code blocks
    json_block_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
    matches = re.findall(json_block_pattern, text, re.DOTALL | re.IGNORECASE)
    
    for match in matches:
        try:
            return json.loads(match.strip())
        except json.JSONDecodeError:
            continue
    
    # Strategy 2: Look for JSON objects in the text
    # Find content between outermost { and }
    brace_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.findall(brace_pattern, text, re.DOTALL)
    
    for match in matches:
        try:
            return json.loads(match.strip())
        except json.JSONDecodeError:
            continue
    
    # Strategy 3: Try parsing the entire text
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    
    # Strategy 4: Look for more complex nested JSON
    try:
        # Find the first { and last } and try to parse that
        first_brace = text.find('{')
        last_brace = text.rfind('}')
        
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            json_candidate = text[first_brace:last_brace + 1]
            return json.loads(json_candidate)
    except json.JSONDecodeError:
        pass
    
    logger.warning(
        "json_extraction_failed",
        extra={
            "text_length": len(text),
            "text_preview": text[:200],
        }
    )
    
    return None


def normalize_confidence(confidence: Union[str, int, float]) -> float:
    """Normalize confidence value to [0.0, 1.0] range.
    
    Args:
        confidence: Confidence value in various formats
        
    Returns:
        float: Normalized confidence in [0.0, 1.0] range
    """
    try:
        # Handle string inputs
        if isinstance(confidence, str):
            # Remove percentage signs and convert
            confidence = confidence.replace('%', '').strip()
            confidence = float(confidence)
        
        # Convert to float
        confidence = float(confidence)
        
        # If confidence is > 1, assume it's a percentage
        if confidence > 1.0:
            confidence = confidence / 100.0
        
        # Clamp to [0.0, 1.0] range
        return max(0.0, min(1.0, confidence))
        
    except (ValueError, TypeError):
        logger.warning(
            "confidence_normalization_failed",
            extra={
                "confidence_value": str(confidence),
                "confidence_type": type(confidence).__name__,
            }
        )
        return 0.5  # Default to medium confidence


def validate_decision_format(decision: Any, decision_type: str) -> Tuple[bool, str]:
    """Validate that a decision matches the expected format.
    
    Args:
        decision: The decision value to validate
        decision_type: Expected decision type ("boolean", "categorical", "scalar", "freeform")
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if decision_type == "boolean":
        if isinstance(decision, bool):
            return True, ""
        elif isinstance(decision, str):
            lower_decision = decision.lower().strip()
            if lower_decision in ["true", "false", "yes", "no", "compatible", "incompatible"]:
                return True, ""
        return False, f"Boolean decision expected, got: {type(decision).__name__}"
    
    elif decision_type == "categorical":
        if isinstance(decision, str) and decision.strip():
            return True, ""
        return False, f"Non-empty string expected for categorical decision, got: {type(decision).__name__}"
    
    elif decision_type == "scalar":
        if isinstance(decision, (int, float)):
            return True, ""
        elif isinstance(decision, str):
            try:
                float(decision)
                return True, ""
            except ValueError:
                pass
        return False, f"Numeric value expected for scalar decision, got: {type(decision).__name__}"
    
    elif decision_type == "freeform":
        if isinstance(decision, str):
            return True, ""
        return False, f"String expected for freeform decision, got: {type(decision).__name__}"
    
    else:
        return False, f"Unknown decision type: {decision_type}"


def parse_evidence_list(evidence: Union[str, List[str]]) -> List[str]:
    """Parse evidence from various formats into a list of strings.
    
    Args:
        evidence: Evidence in string or list format
        
    Returns:
        List[str]: Parsed evidence list
    """
    if isinstance(evidence, list):
        # Filter out empty strings and convert all to strings
        return [str(item).strip() for item in evidence if str(item).strip()]
    
    elif isinstance(evidence, str):
        # Try to parse as JSON list first
        try:
            parsed = json.loads(evidence)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except json.JSONDecodeError:
            pass
        
        # Split by common delimiters
        for delimiter in ['\n', ';', '|', ',']:
            if delimiter in evidence:
                items = evidence.split(delimiter)
                parsed_items = [item.strip() for item in items if item.strip()]
                if len(parsed_items) > 1:
                    return parsed_items
        
        # Return as single item if no delimiters found
        if evidence.strip():
            return [evidence.strip()]
    
    return []


def sanitize_text_output(text: str, max_length: int = 1000) -> str:
    """Sanitize text output by removing problematic characters and limiting length.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        str: Sanitized text
    """
    if not isinstance(text, str):
        text = str(text)
    
    # Remove null bytes and other problematic characters
    text = text.replace('\x00', '').replace('\r', '')
    
    # Normalize whitespace
    text = ' '.join(text.split())
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length - 3] + "..."
    
    return text.strip()


def validate_agent_output_structure(output_dict: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate the structure of an agent output dictionary.
    
    Args:
        output_dict: Dictionary containing agent output data
        
    Returns:
        Tuple[bool, List[str]]: (is_valid, list_of_errors)
    """
    required_fields = ["decision", "confidence", "reasoning"]
    optional_fields = ["evidence", "metadata"]
    errors = []
    
    # Check required fields
    for field in required_fields:
        if field not in output_dict:
            errors.append(f"Missing required field: {field}")
    
    # Validate field types and values
    if "confidence" in output_dict:
        try:
            confidence = float(output_dict["confidence"])
            if not (0.0 <= confidence <= 1.0):
                errors.append(f"Confidence must be between 0.0 and 1.0, got: {confidence}")
        except (ValueError, TypeError):
            errors.append(f"Confidence must be numeric, got: {type(output_dict['confidence']).__name__}")
    
    if "reasoning" in output_dict:
        if not isinstance(output_dict["reasoning"], str) or not output_dict["reasoning"].strip():
            errors.append("Reasoning must be a non-empty string")
    
    if "evidence" in output_dict:
        if not isinstance(output_dict["evidence"], list):
            errors.append(f"Evidence must be a list, got: {type(output_dict['evidence']).__name__}")
    
    return len(errors) == 0, errors