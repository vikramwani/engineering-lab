"""Environment-based configuration overrides for compatibility evaluation.

This module provides runtime configuration that can be overridden through
environment variables while maintaining type safety and validation.

Design Philosophy:
- Environment variables override defaults cleanly
- All configuration is validated at startup
- Configuration is immutable once loaded
- Clear error messages for invalid configuration
"""

import logging
import os
from dataclasses import dataclass
from typing import Optional

from .defaults import SYSTEM_DEFAULTS

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CompatibilitySettings:
    """Runtime configuration for the compatibility evaluation system.

    This configuration is loaded once at startup and provides environment-based
    overrides for all system defaults. All values are validated and immutable.
    """

    # Agent configuration
    agent_max_tokens: int
    agent_timeout_seconds: int
    agent_max_retries: int
    agent_temperature: float

    # System configuration
    execution_timeout_seconds: int
    require_all_agents: bool
    min_confidence_threshold: float
    max_evidence_items: int

    # Prompt configuration
    prompt_version: str
    prompt_base_path: str
    cache_prompts: bool

    # Logging configuration
    log_agent_outputs: bool
    log_output_max_length: int

    # Fallback configuration
    fallback_relationship: str
    fallback_confidence: float
    fallback_explanation: str

    def __post_init__(self) -> None:
        """Validate configuration values after initialization."""
        self._validate_configuration()

        logger.info(
            "compatibility_settings_loaded",
            extra={
                "agent_max_tokens": self.agent_max_tokens,
                "agent_timeout_seconds": self.agent_timeout_seconds,
                "execution_timeout_seconds": self.execution_timeout_seconds,
                "prompt_version": self.prompt_version,
                "require_all_agents": self.require_all_agents,
            },
        )

    def _validate_configuration(self) -> None:
        """Validate all configuration values for correctness."""
        if self.agent_max_tokens <= 0:
            raise ValueError(
                f"agent_max_tokens must be positive, got {self.agent_max_tokens}"
            )

        if self.agent_timeout_seconds <= 0:
            raise ValueError(
                f"agent_timeout_seconds must be positive, got {self.agent_timeout_seconds}"
            )

        if not (0.0 <= self.agent_temperature <= 2.0):
            raise ValueError(
                f"agent_temperature must be in [0.0, 2.0], got {self.agent_temperature}"
            )

        if not (0.0 <= self.min_confidence_threshold <= 1.0):
            raise ValueError(
                f"min_confidence_threshold must be in [0.0, 1.0], got {self.min_confidence_threshold}"
            )

        if self.max_evidence_items <= 0:
            raise ValueError(
                f"max_evidence_items must be positive, got {self.max_evidence_items}"
            )

        if not self.prompt_version.strip():
            raise ValueError("prompt_version cannot be empty")

        if not self.fallback_relationship.strip():
            raise ValueError("fallback_relationship cannot be empty")


def load_compatibility_settings() -> CompatibilitySettings:
    """Load compatibility settings from environment variables with defaults.

    Returns:
        CompatibilitySettings: Validated configuration object

    Raises:
        ValueError: If any configuration value is invalid
    """
    logger.debug("loading_compatibility_settings_from_environment")

    # Load with environment overrides
    settings = CompatibilitySettings(
        # Agent configuration
        agent_max_tokens=int(
            os.getenv(
                "COMPATIBILITY_AGENT_MAX_TOKENS", SYSTEM_DEFAULTS.agents.max_tokens
            )
        ),
        agent_timeout_seconds=int(
            os.getenv(
                "COMPATIBILITY_AGENT_TIMEOUT_SECONDS",
                SYSTEM_DEFAULTS.agents.timeout_seconds,
            )
        ),
        agent_max_retries=int(
            os.getenv(
                "COMPATIBILITY_AGENT_MAX_RETRIES", SYSTEM_DEFAULTS.agents.max_retries
            )
        ),
        agent_temperature=float(
            os.getenv(
                "COMPATIBILITY_AGENT_TEMPERATURE", SYSTEM_DEFAULTS.agents.temperature
            )
        ),
        # System configuration
        execution_timeout_seconds=int(
            os.getenv(
                "COMPATIBILITY_EXECUTION_TIMEOUT_SECONDS",
                SYSTEM_DEFAULTS.compatibility.agent_execution_timeout,
            )
        ),
        require_all_agents=os.getenv(
            "COMPATIBILITY_REQUIRE_ALL_AGENTS",
            str(SYSTEM_DEFAULTS.compatibility.require_all_agents),
        ).lower()
        == "true",
        min_confidence_threshold=float(
            os.getenv(
                "COMPATIBILITY_MIN_CONFIDENCE_THRESHOLD",
                SYSTEM_DEFAULTS.compatibility.min_confidence_threshold,
            )
        ),
        max_evidence_items=int(
            os.getenv(
                "COMPATIBILITY_MAX_EVIDENCE_ITEMS",
                SYSTEM_DEFAULTS.compatibility.max_evidence_items,
            )
        ),
        # Prompt configuration
        prompt_version=os.getenv(
            "COMPATIBILITY_PROMPT_VERSION", SYSTEM_DEFAULTS.prompts.prompt_version
        ),
        prompt_base_path=os.getenv(
            "COMPATIBILITY_PROMPT_BASE_PATH", "src/compatibility/prompts"
        ),
        cache_prompts=os.getenv(
            "COMPATIBILITY_CACHE_PROMPTS", str(SYSTEM_DEFAULTS.prompts.cache_prompts)
        ).lower()
        == "true",
        # Logging configuration
        log_agent_outputs=os.getenv(
            "COMPATIBILITY_LOG_AGENT_OUTPUTS",
            str(SYSTEM_DEFAULTS.compatibility.log_agent_outputs),
        ).lower()
        == "true",
        log_output_max_length=int(
            os.getenv(
                "COMPATIBILITY_LOG_OUTPUT_MAX_LENGTH",
                SYSTEM_DEFAULTS.compatibility.log_output_max_length,
            )
        ),
        # Fallback configuration
        fallback_relationship=os.getenv(
            "COMPATIBILITY_FALLBACK_RELATIONSHIP",
            SYSTEM_DEFAULTS.compatibility.fallback_relationship,
        ),
        fallback_confidence=float(
            os.getenv(
                "COMPATIBILITY_FALLBACK_CONFIDENCE",
                SYSTEM_DEFAULTS.compatibility.fallback_confidence,
            )
        ),
        fallback_explanation=os.getenv(
            "COMPATIBILITY_FALLBACK_EXPLANATION",
            SYSTEM_DEFAULTS.compatibility.fallback_explanation,
        ),
    )

    logger.info(
        "compatibility_settings_loaded_successfully",
        extra={
            "source": "environment_with_defaults",
            "agent_max_tokens": settings.agent_max_tokens,
            "prompt_version": settings.prompt_version,
            "require_all_agents": settings.require_all_agents,
        },
    )

    return settings


# Global settings instance - loaded once at module import
_settings: Optional[CompatibilitySettings] = None


def get_compatibility_settings() -> CompatibilitySettings:
    """Get the global compatibility settings instance.

    Settings are loaded once and cached for the lifetime of the application.
    This ensures consistent configuration across all compatibility operations.

    Returns:
        CompatibilitySettings: The global settings instance
    """
    global _settings
    if _settings is None:
        _settings = load_compatibility_settings()
    return _settings
