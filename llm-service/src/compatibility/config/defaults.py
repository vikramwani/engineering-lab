"""Default configuration values for compatibility evaluation system.

This module contains all default values for the compatibility evaluation system.
These defaults are designed for production use and should only be overridden
through environment variables or explicit configuration.

Design Philosophy:
- Conservative defaults that work in production
- No magic numbers scattered throughout the codebase
- Clear documentation of why each default was chosen
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass(frozen=True)
class AgentDefaults:
    """Default configuration for individual agents in the compatibility system.

    These defaults are tuned for reliability and consistency across all agents
    while allowing for agent-specific customization when needed.
    """

    # Token limits - conservative to ensure reliable responses
    max_tokens: int = 512  # Enough for structured JSON with reasoning

    # Timeout settings - balanced for reliability vs responsiveness
    timeout_seconds: int = 30  # Longer than general service for complex reasoning

    # Retry configuration - minimal retries for agent consistency
    max_retries: int = 2  # Avoid cascading delays in multi-agent flow

    # Temperature settings for consistent structured output
    temperature: float = 0.1  # Low temperature for consistent JSON structure


@dataclass(frozen=True)
class CompatibilityDefaults:
    """Default configuration for the overall compatibility evaluation system.

    These settings control the multi-agent orchestration and final response
    generation. They are tuned for production reliability and performance.
    """

    # Agent orchestration
    agent_execution_timeout: int = 120  # Total time for all agents
    require_all_agents: bool = True  # Fail if any agent fails

    # Response validation
    min_confidence_threshold: float = 0.0  # Accept all confidence levels
    max_evidence_items: int = 10  # Prevent excessively long evidence lists

    # Logging and observability
    log_agent_outputs: bool = True  # Log truncated agent responses
    log_output_max_length: int = 500  # Safe truncation length

    # Fallback behavior
    fallback_relationship: str = "insufficient_information"
    fallback_confidence: float = 0.1
    fallback_explanation: str = (
        "Unable to determine compatibility due to evaluation error"
    )


@dataclass(frozen=True)
class PromptDefaults:
    """Default configuration for prompt management and versioning.

    Controls how prompts are loaded, cached, and versioned to ensure
    consistent behavior across deployments and environments.
    """

    # Prompt versioning and caching
    prompt_version: str = "v1"  # Current prompt version
    cache_prompts: bool = True  # Cache loaded prompts in memory

    # Prompt validation
    validate_prompt_syntax: bool = True  # Validate prompts on load
    require_json_schema: bool = True  # Ensure prompts specify JSON output

    # File system settings
    prompt_encoding: str = "utf-8"  # Standard encoding for prompt files
    prompt_file_extension: str = ".txt"  # Standard extension


# Aggregate all defaults for easy access
@dataclass(frozen=True)
class SystemDefaults:
    """Aggregate container for all system defaults.

    Provides a single point of access to all default configuration values
    while maintaining clear separation between different subsystem defaults.
    """

    agents: AgentDefaults = AgentDefaults()
    compatibility: CompatibilityDefaults = CompatibilityDefaults()
    prompts: PromptDefaults = PromptDefaults()

    def to_dict(self) -> Dict[str, Any]:
        """Convert all defaults to a flat dictionary for logging/debugging."""
        return {
            "agent_max_tokens": self.agents.max_tokens,
            "agent_timeout_seconds": self.agents.timeout_seconds,
            "agent_max_retries": self.agents.max_retries,
            "agent_temperature": self.agents.temperature,
            "compatibility_execution_timeout": self.compatibility.agent_execution_timeout,
            "compatibility_require_all_agents": self.compatibility.require_all_agents,
            "compatibility_min_confidence": self.compatibility.min_confidence_threshold,
            "compatibility_max_evidence": self.compatibility.max_evidence_items,
            "prompt_version": self.prompts.prompt_version,
            "prompt_cache_enabled": self.prompts.cache_prompts,
        }


# Global defaults instance - immutable and thread-safe
SYSTEM_DEFAULTS = SystemDefaults()
