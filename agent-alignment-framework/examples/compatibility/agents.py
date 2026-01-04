"""Compatibility-specific agent implementations.

This module provides agent implementations specialized for product
compatibility evaluation using the generic agent framework.
"""

import json
from typing import Any, Dict

from agent_alignment.core.agent import LLMAgent
from agent_alignment.core.models import AgentDecision, EvaluationTask
from agent_alignment.utils.validation import (
    extract_json_from_text,
    normalize_confidence,
    parse_evidence_list,
    sanitize_text_output,
)


class CompatibilityAgent(LLMAgent):
    """Agent specialized for product compatibility evaluation.
    
    This agent understands product compatibility concepts and can evaluate
    relationships between products using structured prompts and outputs.
    """
    
    def _build_prompt(self, task: EvaluationTask) -> str:
        """Build the prompt for compatibility evaluation.
        
        Args:
            task: The evaluation task
            
        Returns:
            str: Formatted prompt for the LLM
        """
        # Load the base prompt template
        template = self._load_prompt_template()
        
        # Extract product information
        product_a = task.context.get("product_a", {})
        product_b = task.context.get("product_b", {})
        
        # Format product information
        product_a_info = self._format_product_info(product_a, "Product A")
        product_b_info = self._format_product_info(product_b, "Product B")
        
        # Get relationship types if available
        relationship_types = task.context.get("relationship_types", [])
        relationship_info = ""
        if relationship_types:
            relationship_info = f"\nValid relationship types: {', '.join(relationship_types)}"
        
        # Format the complete prompt
        prompt = template.format(
            agent_role=self.role.instruction,
            evaluation_criteria=task.evaluation_criteria,
            product_a_info=product_a_info,
            product_b_info=product_b_info,
            relationship_info=relationship_info,
            task_type=task.task_type,
        )
        
        return prompt
    
    def _parse_response(self, task: EvaluationTask, response: str, request_id: str) -> AgentDecision:
        """Parse the LLM response into structured output.
        
        Args:
            task: The original evaluation task
            response: Raw LLM response
            request_id: Request ID for tracing
            
        Returns:
            AgentOutput: Parsed and validated agent output
        """
        # Extract JSON from response
        json_data = extract_json_from_text(response)
        
        if json_data is None:
            # Fallback: try to parse key information from text
            return self._parse_fallback_response(task, response, request_id)
        
        # Extract required fields
        try:
            decision = json_data.get("decision") or json_data.get("relationship")
            confidence = json_data.get("confidence", 0.5)
            reasoning = json_data.get("reasoning") or json_data.get("explanation", "")
            evidence = json_data.get("evidence", [])
            
            # Validate and normalize
            decision = self._normalize_decision(decision, task)
            confidence = normalize_confidence(confidence)
            reasoning = sanitize_text_output(reasoning, max_length=1000)
            evidence = parse_evidence_list(evidence)
            
            return AgentDecision(
                agent_name=self.role.name,
                role_type=self.role.role_type,
                decision_value=decision,
                confidence=confidence,
                rationale=reasoning,
                evidence=evidence,
                metadata={
                    "request_id": request_id,
                    "task_type": task.task_type,
                    "response_format": "json",
                }
            )
            
        except Exception as e:
            raise ValueError(f"Failed to parse agent response: {e}. Response: {response[:200]}...")
    
    def _parse_fallback_response(self, task: EvaluationTask, response: str, request_id: str) -> AgentDecision:
        """Parse response when JSON extraction fails.
        
        Args:
            task: The evaluation task
            response: Raw response text
            request_id: Request ID for tracing
            
        Returns:
            AgentDecision: Best-effort parsed output
        """
        # Try to extract key information from text
        lines = response.split('\n')
        
        decision = None
        confidence = 0.5
        reasoning = response  # Use full response as reasoning
        evidence = []
        
        # Look for decision indicators
        for line in lines:
            line_lower = line.lower().strip()
            
            # Look for compatibility decisions
            if any(word in line_lower for word in ["compatible", "incompatible", "relationship"]):
                # Extract potential relationship types
                relationship_types = task.context.get("relationship_types", [])
                for rel_type in relationship_types:
                    if rel_type.lower() in line_lower:
                        decision = rel_type
                        break
                
                # Fallback to boolean compatibility
                if decision is None:
                    if "compatible" in line_lower and "incompatible" not in line_lower:
                        decision = True
                    elif "incompatible" in line_lower:
                        decision = False
            
            # Look for confidence indicators
            if "confidence" in line_lower:
                import re
                conf_match = re.search(r'(\d+(?:\.\d+)?)', line)
                if conf_match:
                    confidence = normalize_confidence(float(conf_match.group(1)))
        
        # Default decision if none found
        if decision is None:
            if task.decision_schema.__class__.__name__ == "BooleanDecisionSchema":
                decision = True  # Default to compatible
            else:
                decision = "insufficient_information"
        
        return AgentDecision(
            agent_name=self.role.name,
            role_type=self.role.role_type,
            decision_value=decision,
            confidence=confidence,
            rationale=sanitize_text_output(reasoning, max_length=1000),
            evidence=evidence,
            metadata={
                "request_id": request_id,
                "task_type": task.task_type,
                "response_format": "fallback",
                "parsing_warning": "JSON extraction failed, used fallback parsing",
            }
        )
    
    def _format_product_info(self, product: Dict[str, Any], label: str) -> str:
        """Format product information for inclusion in prompts.
        
        Args:
            product: Product information dictionary
            label: Label for the product (e.g., "Product A")
            
        Returns:
            str: Formatted product information
        """
        if not product:
            return f"{label}: No information provided"
        
        info_lines = [f"{label}:"]
        
        # Standard fields
        for field in ["id", "title", "name", "category", "brand", "manufacturer"]:
            if field in product:
                info_lines.append(f"  {field.title()}: {product[field]}")
        
        # Attributes
        if "attributes" in product and isinstance(product["attributes"], dict):
            info_lines.append("  Attributes:")
            for key, value in product["attributes"].items():
                info_lines.append(f"    {key}: {value}")
        
        # Description
        if "description" in product:
            info_lines.append(f"  Description: {product['description']}")
        
        # Any other fields
        standard_fields = {"id", "title", "name", "category", "brand", "manufacturer", "attributes", "description"}
        for key, value in product.items():
            if key not in standard_fields:
                info_lines.append(f"  {key.title()}: {value}")
        
        return "\n".join(info_lines)
    
    def _normalize_decision(self, decision: Any, task: EvaluationTask) -> Any:
        """Normalize the decision based on the task's decision type.
        
        Args:
            decision: Raw decision value
            task: The evaluation task
            
        Returns:
            Any: Normalized decision value
        """
        decision_schema = task.decision_schema
        
        if decision_schema.__class__.__name__ == "BooleanDecisionSchema":
            # Convert to boolean
            if isinstance(decision, bool):
                return decision
            elif isinstance(decision, str):
                decision_lower = decision.lower().strip()
                if decision_lower in ["true", "yes", "compatible", "1"]:
                    return True
                elif decision_lower in ["false", "no", "incompatible", "0"]:
                    return False
            return True  # Default to compatible
        
        elif decision_schema.__class__.__name__ == "CategoricalDecisionSchema":
            # Validate against allowed categories
            if hasattr(decision_schema, 'categories'):
                if decision in decision_schema.categories:
                    return decision
                
                # Try case-insensitive match
                decision_lower = str(decision).lower()
                for category in decision_schema.categories:
                    if category.lower() == decision_lower:
                        return category
                
                # Default to insufficient information
                return "insufficient_information"
            
            return str(decision)
        
        else:
            # For other decision types, return as-is
            return decision