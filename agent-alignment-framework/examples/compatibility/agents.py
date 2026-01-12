"""Agent implementations for compatibility evaluation.

This module provides specialized agent implementations for product compatibility
evaluation, extending the base LLMAgent class with domain-specific behavior.
"""

import json
from typing import Any, Dict, List

from agent_alignment import BaseAgent, AgentDecision, EvaluationTask, AgentRole, LLMClient
from agent_alignment.core.agent import LLMAgent


class CompatibilityAgent(LLMAgent):
    """Specialized agent for product compatibility evaluation.
    
    This agent extends the LLMAgent class with compatibility-specific
    prompt formatting and response processing.
    """
    
    def __init__(self, role: AgentRole, llm_client: LLMClient):
        """Initialize compatibility agent.
        
        Args:
            role: Agent role configuration
            llm_client: LLM client for generating responses
        """
        super().__init__(role, llm_client)
    
    def _build_prompt(self, task: EvaluationTask) -> str:
        """Build compatibility-specific prompt using external template.
        
        Args:
            task: Evaluation task with product compatibility context
            
        Returns:
            str: Formatted prompt for compatibility evaluation
        """
        # Extract products from context
        product_a = task.context.get("product_a", {})
        product_b = task.context.get("product_b", {})
        relationship_types = task.context.get("relationship_types", [])
        
        # Prepare template variables
        template_variables = {
            "role_type": self.role.role_type,
            "role_instruction": self.role.instruction,
            "evaluation_criteria": task.evaluation_criteria,
            "product_a_info": self._format_product_info(product_a),
            "product_b_info": self._format_product_info(product_b),
            "decision_schema_type": task.decision_schema.get_schema_type(),
            "relationship_types": ", ".join(relationship_types) if relationship_types else "N/A",
            "task_context": self._format_task_inputs(task),
        }
        
        # Use inline template since external templates have path issues
        return self._create_inline_prompt(task, product_a, product_b, relationship_types)
    
    def _parse_response(self, task: EvaluationTask, response: str, request_id: str) -> AgentDecision:
        """Parse LLM response into structured AgentDecision.
        
        Args:
            task: Original evaluation task
            response: Raw LLM response
            request_id: Request ID for tracing
            
        Returns:
            AgentDecision: Parsed agent decision
        """
        try:
            # Try to parse JSON response
            if response.strip().startswith('{'):
                parsed = json.loads(response.strip())
            else:
                # Extract JSON from response if embedded in text
                start_idx = response.find('{')
                end_idx = response.rfind('}') + 1
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = response[start_idx:end_idx]
                    parsed = json.loads(json_str)
                else:
                    raise ValueError("No JSON found in response")
            
            # Extract decision components
            decision_value = parsed.get("decision", "insufficient_information")
            confidence = self._validate_confidence(parsed.get("confidence", 0.5))
            reasoning = parsed.get("reasoning", "No reasoning provided")
            evidence = parsed.get("evidence", [])
            
            # Ensure evidence is a list
            if not isinstance(evidence, list):
                evidence = [str(evidence)] if evidence else []
            
            return AgentDecision(
                agent_name=self.role.name,
                role_type=self.role.role_type,
                decision_value=decision_value,
                confidence=confidence,
                rationale=reasoning,
                evidence=evidence,
                metadata={
                    "request_id": request_id,
                    "task_id": task.task_id,
                    "raw_response_length": len(response),
                }
            )
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # Fallback parsing for non-JSON responses
            return AgentDecision(
                agent_name=self.role.name,
                role_type=self.role.role_type,
                decision_value="insufficient_information",
                confidence=0.3,
                rationale=f"Failed to parse response: {str(e)}. Raw response: {response[:200]}...",
                evidence=[],
                metadata={
                    "request_id": request_id,
                    "task_id": task.task_id,
                    "parse_error": str(e),
                    "raw_response": response[:500],  # Truncated for logging
                }
            )
    
    def _create_inline_prompt(
        self, 
        task: EvaluationTask, 
        product_a: Dict[str, Any], 
        product_b: Dict[str, Any],
        relationship_types: List[str]
    ) -> str:
        """Create compatibility-specific prompt inline (fallback).
        
        Args:
            task: Evaluation task
            product_a: First product information
            product_b: Second product information
            relationship_types: Available relationship types
            
        Returns:
            str: Formatted prompt for compatibility evaluation
        """
        # Format product information
        product_a_info = self._format_product_info(product_a)
        product_b_info = self._format_product_info(product_b)
        
        prompt = f"""
You are evaluating the compatibility between two products. Your role is: {self.role.role_type}

EVALUATION CRITERIA:
{task.evaluation_criteria}

PRODUCT A:
{product_a_info}

PRODUCT B:
{product_b_info}

ROLE INSTRUCTION:
{self.role.instruction}

DECISION SCHEMA:
- Type: {task.decision_schema.get_schema_type()}
"""
        
        if relationship_types:
            prompt += f"""
- Available relationship types: {', '.join(relationship_types)}
"""
        
        prompt += f"""

Please provide your evaluation in the following JSON format:
{{
    "decision": "<your_decision>",
    "confidence": <confidence_score_0_to_1>,
    "reasoning": "<detailed_reasoning>",
    "evidence": ["<evidence_item_1>", "<evidence_item_2>", ...]
}}

Consider the following factors in your evaluation:
- Physical compatibility (connectors, dimensions, power requirements)
- Functional compatibility (intended use cases, feature support)
- Brand compatibility (official support, warranty implications)
- Safety and regulatory compliance
- User experience and usability

Provide a thorough analysis based on your assigned role perspective.
"""
        
        return prompt
    
    def _format_product_info(self, product: Dict[str, Any]) -> str:
        """Format product information for prompt inclusion.
        
        Args:
            product: Product information dictionary
            
        Returns:
            str: Formatted product information
        """
        if not product:
            return "No product information provided"
        
        info_lines = []
        
        # Basic product info
        if "title" in product:
            info_lines.append(f"Title: {product['title']}")
        if "brand" in product:
            info_lines.append(f"Brand: {product['brand']}")
        if "category" in product:
            info_lines.append(f"Category: {product['category']}")
        if "description" in product:
            info_lines.append(f"Description: {product['description']}")
        
        # Product attributes
        if "attributes" in product and product["attributes"]:
            info_lines.append("Attributes:")
            for key, value in product["attributes"].items():
                if isinstance(value, list):
                    value_str = ", ".join(str(v) for v in value)
                else:
                    value_str = str(value)
                info_lines.append(f"  - {key}: {value_str}")
        
        return "\n".join(info_lines)