"""Prompt loading and management system for compatibility evaluation.

This module provides a robust system for loading, validating, and caching
prompts from disk. It ensures prompts are available at runtime and provides
clear error messages when prompts are missing or invalid.

Design Philosophy:
- Fail fast on missing or invalid prompts
- Cache prompts for performance
- Validate prompt structure to prevent runtime issues
- Clear separation between prompt content and business logic
"""

import logging
from pathlib import Path
from typing import Dict, Optional

from ..config.settings import get_compatibility_settings

logger = logging.getLogger(__name__)


class PromptLoadError(Exception):
    """Raised when a prompt cannot be loaded or is invalid."""

    pass


class PromptLoader:
    """Manages loading and caching of compatibility evaluation prompts.

    This class handles the loading of prompt templates from disk, validates
    their content, and provides caching for performance. It ensures that
    all required prompts are available before any evaluation begins.
    """

    def __init__(self) -> None:
        """Initialize the prompt loader with configuration."""
        self.settings = get_compatibility_settings()
        self._prompt_cache: Dict[str, str] = {}
        self._base_path = Path(self.settings.prompt_base_path)

        logger.debug(
            "prompt_loader_initialized",
            extra={
                "base_path": str(self._base_path),
                "prompt_version": self.settings.prompt_version,
                "cache_enabled": self.settings.cache_prompts,
            },
        )

    def load_prompt(self, prompt_name: str) -> str:
        """Load a prompt by name with caching and validation.

        Args:
            prompt_name: Name of the prompt file (without extension)

        Returns:
            str: The loaded prompt content

        Raises:
            PromptLoadError: If prompt cannot be loaded or is invalid
        """
        # Check cache first if caching is enabled
        if self.settings.cache_prompts and prompt_name in self._prompt_cache:
            logger.debug("prompt_cache_hit", extra={"prompt_name": prompt_name})
            return self._prompt_cache[prompt_name]

        # Load from disk
        prompt_content = self._load_from_disk(prompt_name)

        # Validate prompt content
        self._validate_prompt(prompt_name, prompt_content)

        # Cache if enabled
        if self.settings.cache_prompts:
            self._prompt_cache[prompt_name] = prompt_content
            logger.debug(
                "prompt_cached",
                extra={
                    "prompt_name": prompt_name,
                    "content_length": len(prompt_content),
                },
            )

        logger.info(
            "prompt_loaded_successfully",
            extra={
                "prompt_name": prompt_name,
                "content_length": len(prompt_content),
                "from_cache": False,
            },
        )

        return prompt_content

    def _load_from_disk(self, prompt_name: str) -> str:
        """Load prompt content from disk."""
        prompt_file = self._base_path / f"{prompt_name}.txt"

        if not prompt_file.exists():
            logger.error(
                "prompt_file_not_found",
                extra={
                    "prompt_name": prompt_name,
                    "expected_path": str(prompt_file),
                    "base_path": str(self._base_path),
                },
            )
            raise PromptLoadError(f"Prompt file not found: {prompt_file}")

        try:
            with open(prompt_file, "r", encoding="utf-8") as f:
                content = f.read().strip()

            if not content:
                raise PromptLoadError(f"Prompt file is empty: {prompt_file}")

            logger.debug(
                "prompt_file_read_successfully",
                extra={
                    "prompt_name": prompt_name,
                    "file_path": str(prompt_file),
                    "content_length": len(content),
                },
            )

            return content

        except IOError as e:
            logger.error(
                "prompt_file_read_error",
                extra={
                    "prompt_name": prompt_name,
                    "file_path": str(prompt_file),
                    "error": str(e),
                },
            )
            raise PromptLoadError(
                f"Failed to read prompt file {prompt_file}: {e}"
            ) from e

    def _validate_prompt(self, prompt_name: str, content: str) -> None:
        """Validate prompt content for required elements."""
        if not content.strip():
            raise PromptLoadError(f"Prompt {prompt_name} is empty")

        # Check for required JSON schema mention (basic validation)
        if "JSON" not in content.upper():
            logger.warning(
                "prompt_missing_json_reference",
                extra={
                    "prompt_name": prompt_name,
                    "content_preview": content[:100],
                },
            )

        # Check for reasonable length (not too short or too long)
        if len(content) < 50:
            logger.warning(
                "prompt_suspiciously_short",
                extra={
                    "prompt_name": prompt_name,
                    "content_length": len(content),
                },
            )
        elif len(content) > 10000:
            logger.warning(
                "prompt_very_long",
                extra={
                    "prompt_name": prompt_name,
                    "content_length": len(content),
                },
            )

        logger.debug(
            "prompt_validation_completed",
            extra={
                "prompt_name": prompt_name,
                "content_length": len(content),
                "validation_passed": True,
            },
        )

    def preload_all_prompts(self) -> None:
        """Preload all required prompts to validate availability at startup.

        This method should be called during application startup to ensure
        all required prompts are available and valid before serving requests.

        Raises:
            PromptLoadError: If any required prompt is missing or invalid
        """
        required_prompts = [
            "compatibility_agent_for",
            "compatibility_agent_against",
            "compatibility_judge",
        ]

        logger.info(
            "preloading_prompts_started",
            extra={
                "required_prompts": required_prompts,
                "prompt_version": self.settings.prompt_version,
            },
        )

        for prompt_name in required_prompts:
            try:
                self.load_prompt(prompt_name)
                logger.debug(
                    "prompt_preload_success", extra={"prompt_name": prompt_name}
                )
            except PromptLoadError as e:
                logger.error(
                    "prompt_preload_failed",
                    extra={
                        "prompt_name": prompt_name,
                        "error": str(e),
                    },
                )
                raise

        logger.info(
            "preloading_prompts_completed",
            extra={
                "loaded_count": len(required_prompts),
                "cache_size": len(self._prompt_cache),
            },
        )


# Global prompt loader instance
_prompt_loader: Optional[PromptLoader] = None


def get_prompt_loader() -> PromptLoader:
    """Get the global prompt loader instance.

    Returns:
        PromptLoader: The global prompt loader instance
    """
    global _prompt_loader
    if _prompt_loader is None:
        _prompt_loader = PromptLoader()
    return _prompt_loader


def load_prompt(prompt_name: str) -> str:
    """Convenience function to load a prompt by name.

    Args:
        prompt_name: Name of the prompt to load

    Returns:
        str: The loaded prompt content
    """
    return get_prompt_loader().load_prompt(prompt_name)
