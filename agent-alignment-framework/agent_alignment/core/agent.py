"""Base agent interface and implementations for the alignment framework.

This module defines the abstract base class for agents and provides common
functionality for agent implementations across different use cases. All agents
operate on generic evaluation tasks and produce structured outputs without
domain-specific assumptions.

Key Principles:
- Domain Agnostic: No hardcoded domain knowledge or assumptions
- Prompt Separation: All prompts loaded from external templates via configuration
- Structured Output: Consistent output format across all agent types
- Extensible Design: Clean extension points for new agent implementations
"""

import logging
import time
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable

from ..config.loader import get_prompt_loader
from ..llm.client import LLMClient
from ..utils.logging import get_logger
from .models import AgentDecision, AgentRole, EvaluationTask

logger = get_logger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all agents in the evaluation framework.
    
    Agents are responsible for analyzing evaluation tasks from their specific
    perspective (advocate, skeptic, judge, domain expert, etc.) and producing
    structured outputs. Each agent implementation must define how it processes
    tasks and generates decisions within its role constraints.
    
    Design Principles:
    - Generic Interface: Works with any evaluation domain or decision type
    - Prompt Declaration: Agents declare required prompts via configuration
    - Structured Logging: All operations logged with structured metadata
    - Error Resilience: Comprehensive error handling and validation
    """
    
    def __init__(
        self,
        role: AgentRole,
        llm_client: Optional[LLMClient] = None,
    ):
        """Initialize the agent with its role configuration.
        
        Args:
            role: The agent's role definition and configuration
            llm_client: Optional LLM client (required for LLM-based agents)
        """
        self.role = role
        self.llm_client = llm_client
        
        # Validate prompt requirements
        self._validate_prompt_requirements()
        
        logger.debug(
            "agent_initialized",
            extra={
                "agent_name": role.name,
                "role_type": role.role_type,
                "prompt_template": role.prompt_template,
                "max_tokens": role.max_tokens,
                "temperature": role.temperature,
                "has_llm_client": llm_client is not None,
            }
        )
    
    @abstractmethod
    def evaluate(self, task: EvaluationTask) -> AgentDecision:
        """Evaluate the given task from this agent's perspective.
        
        This is the core method that each agent implementation must define.
        It should analyze the task according to the agent's role and return
        a structured output with decision, confidence, reasoning, and evidence.
        
        Args:
            task: The evaluation task to analyze
            
        Returns:
            AgentDecision: Structured output with decision and reasoning
            
        Raises:
            ValueError: If the task cannot be processed by this agent
            RuntimeError: If the evaluation fails due to system issues
        """
        pass
    
    @abstractmethod
    def get_required_prompts(self) -> List[str]:
        """Declare the prompt templates required by this agent.
        
        This method allows agents to declare their prompt dependencies,
        enabling validation and ensuring all required templates are available.
        
        Returns:
            List[str]: List of required prompt template paths
        """
        pass
    
    def _validate_prompt_requirements(self) -> None:
        """Validate that all required prompts are available.
        
        This method checks that all declared prompt templates exist and
        can be loaded, failing fast if configuration is incomplete.
        
        Raises:
            ValueError: If required prompts are missing or invalid
        """
        required_prompts = self.get_required_prompts()
        
        if not required_prompts:
            # Agent doesn't require prompts (e.g., rule-based agents)
            return
        
        prompt_loader = get_prompt_loader()
        
        for prompt_path in required_prompts:
            try:
                # Validate that prompt exists and can be loaded
                prompt_loader.validate_template(prompt_path)
            except Exception as e:
                logger.error(
                    "agent_prompt_validation_failed",
                    extra={
                        "agent_name": self.role.name,
                        "prompt_path": prompt_path,
                        "error": str(e),
                    }
                )
                raise ValueError(
                    f"Agent {self.role.name} requires prompt template '{prompt_path}' "
                    f"which is not available: {e}"
                )
    
    def _generate_request_id(self) -> str:
        """Generate a unique request ID for tracing."""
        return str(uuid.uuid4())[:8]
    
    def _validate_task(self, task: EvaluationTask) -> None:
        """Validate that the task can be processed by this agent.
        
        Args:
            task: The evaluation task to validate
            
        Raises:
            ValueError: If the task is invalid or incompatible
        """
        if not task.task_id:
            raise ValueError("Task must have a valid task_id")
        
        if not task.evaluation_criteria:
            raise ValueError("Task must have evaluation criteria")
        
        if not task.context:
            raise ValueError("Task must have context data")
        
        # Allow agents to add custom validation
        self._validate_task_compatibility(task)
    
    def _validate_task_compatibility(self, task: EvaluationTask) -> None:
        """Hook for agents to add custom task validation.
        
        Subclasses can override this method to add domain-specific
        or role-specific task validation logic.
        
        Args:
            task: The evaluation task to validate
            
        Raises:
            ValueError: If the task is incompatible with this agent
        """
        pass
    
    def _log_evaluation_start(self, task: EvaluationTask, request_id: str) -> None:
        """Log the start of an evaluation process."""
        logger.info(
            "agent_evaluation_started",
            extra={
                "agent_name": self.role.name,
                "role_type": self.role.role_type,
                "task_id": task.task_id,
                "task_type": task.task_type,
                "decision_schema": type(task.decision_schema).__name__,
                "request_id": request_id,
            }
        )
    
    def _log_evaluation_completion(
        self,
        task: EvaluationTask,
        output: AgentDecision,
        processing_time_ms: int,
        request_id: str
    ) -> None:
        """Log the completion of an evaluation process."""
        logger.info(
            "agent_evaluation_completed",
            extra={
                "agent_name": self.role.name,
                "role_type": self.role.role_type,
                "task_id": task.task_id,
                "decision": str(output.decision_value),
                "confidence": output.confidence,
                "evidence_count": len(output.evidence),
                "processing_time_ms": processing_time_ms,
                "request_id": request_id,
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
            "agent_evaluation_failed",
            extra={
                "agent_name": self.role.name,
                "role_type": self.role.role_type,
                "task_id": task.task_id,
                "error_type": type(error).__name__,
                "error": str(error)[:200],  # Truncate long error messages
                "processing_time_ms": processing_time_ms,
                "request_id": request_id,
            },
            exc_info=True
        )


class LLMAgent(BaseAgent):
    """Base implementation for agents that use LLM providers.
    
    This class provides common functionality for agents that generate their
    outputs by prompting Large Language Models. It enforces strict prompt
    separation and provides structured prompt loading and response parsing.
    
    Key Features:
    - Strict Prompt Separation: All prompts loaded from external templates
    - Generic Task Processing: Works with any evaluation domain
    - Structured Output Parsing: Consistent response format validation
    - Comprehensive Error Handling: Robust error recovery and logging
    """
    
    def __init__(
        self,
        role: AgentRole,
        llm_client: LLMClient,
    ):
        """Initialize LLM-based agent with role and client.
        
        Args:
            role: Agent role configuration with prompt template path
            llm_client: LLM client for generating responses
            
        Raises:
            ValueError: If LLM client is not provided or prompts are missing
        """
        if llm_client is None:
            raise ValueError("LLMAgent requires an LLM client")
        
        super().__init__(role, llm_client)
    
    def get_required_prompts(self) -> List[str]:
        """Declare required prompt templates for this LLM agent.
        
        Returns:
            List[str]: List containing the agent's prompt template path
        """
        if self.role.prompt_template:
            return [self.role.prompt_template]
        else:
            # Agent must declare its prompt requirements
            raise ValueError(
                f"LLMAgent {self.role.name} must specify prompt_template in role configuration"
            )
    
    def evaluate(self, task: EvaluationTask) -> AgentDecision:
        """Evaluate the task using LLM-based analysis with strict prompt separation.
        
        Args:
            task: The evaluation task to analyze
            
        Returns:
            AgentDecision: Structured output from LLM analysis
        """
        request_id = self._generate_request_id()
        start_time = time.time()
        
        try:
            self._validate_task(task)
            self._log_evaluation_start(task, request_id)
            
            # Build prompt using external template (no embedded prompts)
            prompt = self._build_prompt(task)
            
            # Get LLM response
            response = self.llm_client.generate(
                prompt=prompt,
                max_tokens=self.role.max_tokens,
                temperature=self.role.temperature
            )
            
            # Parse response into structured output
            output = self._parse_response(task, response, request_id)
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            output.processing_time_ms = processing_time_ms
            
            self._log_evaluation_completion(task, output, processing_time_ms, request_id)
            
            return output
            
        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            self._log_evaluation_error(task, e, processing_time_ms, request_id)
            raise
    
    @abstractmethod
    def _build_prompt(self, task: EvaluationTask) -> str:
        """Build the prompt for this agent's evaluation using external templates.
        
        This method must load prompts from external template files and format
        them with task-specific data. No prompt strings should be embedded
        in the code.
        
        Args:
            task: The evaluation task
            
        Returns:
            str: Formatted prompt for the LLM
            
        Raises:
            ValueError: If prompt template cannot be loaded or formatted
        """
        pass
    
    @abstractmethod
    def _parse_response(self, task: EvaluationTask, response: str, request_id: str) -> AgentDecision:
        """Parse the LLM response into structured output.
        
        Args:
            task: The original evaluation task
            response: Raw LLM response
            request_id: Request ID for tracing
            
        Returns:
            AgentDecision: Parsed and validated agent output
            
        Raises:
            ValueError: If response cannot be parsed or is invalid
        """
        pass
    
    def _load_prompt_template(self, template_path: Optional[str] = None) -> str:
        """Load prompt template from external file with strict separation enforcement.
        
        Args:
            template_path: Optional override for template path
            
        Returns:
            str: The prompt template content
            
        Raises:
            ValueError: If template path is not configured or file not found
        """
        path = template_path or self.role.prompt_template
        
        if not path:
            raise ValueError(
                f"Agent {self.role.name} must specify prompt_template in role configuration. "
                "No embedded prompts allowed."
            )
        
        try:
            prompt_loader = get_prompt_loader()
            return prompt_loader.load_template(path)
        except FileNotFoundError:
            logger.error(
                "prompt_template_not_found",
                extra={
                    "agent_name": self.role.name,
                    "template_path": path,
                }
            )
            raise ValueError(
                f"Prompt template not found: {path}. "
                "Ensure template file exists and path is correct."
            )
    
    def _format_prompt_template(
        self, 
        template_variables: Dict[str, Any],
        template_path: Optional[str] = None
    ) -> str:
        """Format prompt template with variables using external template loader.
        
        Args:
            template_variables: Variables to substitute in template
            template_path: Optional override for template path
            
        Returns:
            str: Formatted prompt ready for LLM
            
        Raises:
            ValueError: If template formatting fails
        """
        path = template_path or self.role.prompt_template
        
        if not path:
            raise ValueError(
                f"Agent {self.role.name} must specify prompt_template. "
                "No embedded prompts allowed."
            )
        
        try:
            prompt_loader = get_prompt_loader()
            return prompt_loader.format_template(path, template_variables)
        except Exception as e:
            logger.error(
                "prompt_template_format_error",
                extra={
                    "agent_name": self.role.name,
                    "template_path": path,
                    "error": str(e),
                    "available_variables": list(template_variables.keys()),
                }
            )
            raise ValueError(
                f"Failed to format prompt template {path}: {e}"
            )
    
    def _format_task_inputs(self, task: EvaluationTask) -> str:
        """Format task context for inclusion in prompts in a generic way.
        
        This method formats task context without making domain-specific
        assumptions, ensuring the agent remains generic.
        
        Args:
            task: The evaluation task
            
        Returns:
            str: Formatted context data suitable for any domain
        """
        formatted_inputs = []
        
        for key, value in task.context.items():
            if isinstance(value, dict):
                # Format nested dictionaries
                nested_items = []
                for nested_key, nested_value in value.items():
                    nested_items.append(f"  {nested_key}: {nested_value}")
                formatted_inputs.append(f"{key}:\n" + "\n".join(nested_items))
            elif isinstance(value, list):
                # Format lists
                list_items = [f"  - {item}" for item in value]
                formatted_inputs.append(f"{key}:\n" + "\n".join(list_items))
            else:
                # Simple key-value pairs
                formatted_inputs.append(f"{key}: {value}")
        
        return "\n\n".join(formatted_inputs)
    
    def _validate_confidence(self, confidence: float) -> float:
        """Validate and normalize confidence score.
        
        Args:
            confidence: Raw confidence score
            
        Returns:
            float: Normalized confidence in [0.0, 1.0] range
        """
        if not isinstance(confidence, (int, float)):
            logger.warning(
                "invalid_confidence_type",
                extra={
                    "agent_name": self.role.name,
                    "confidence_type": type(confidence).__name__,
                    "confidence_value": str(confidence),
                }
            )
            return 0.5  # Default to medium confidence
        
        # Normalize to [0.0, 1.0] range
        normalized = max(0.0, min(1.0, float(confidence)))
        
        if normalized != confidence:
            logger.debug(
                "confidence_normalized",
                extra={
                    "agent_name": self.role.name,
                    "original_confidence": confidence,
                    "normalized_confidence": normalized,
                }
            )
        
        return normalized