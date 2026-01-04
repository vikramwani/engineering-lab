"""LLM client abstraction for the agent alignment framework.

This module provides a unified interface for interacting with different LLM providers,
handling retries, timeouts, and error normalization across providers.
"""

import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from ..utils.logging import get_logger

logger = get_logger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers.
    
    Each provider implementation handles the specifics of communicating
    with a particular LLM service (OpenAI, Anthropic, local models, etc.).
    """
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.1,
        **kwargs
    ) -> str:
        """Generate text using the LLM provider.
        
        Args:
            prompt: The input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Provider-specific parameters
            
        Returns:
            str: Generated text response
            
        Raises:
            LLMError: If generation fails
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the name of this provider."""
        pass


class LLMError(Exception):
    """Base exception for LLM-related errors."""
    pass


class LLMTimeoutError(LLMError):
    """Raised when LLM request times out."""
    pass


class LLMRateLimitError(LLMError):
    """Raised when LLM rate limit is exceeded."""
    pass


class LLMUnavailableError(LLMError):
    """Raised when LLM service is unavailable."""
    pass


class LLMClient:
    """Unified client for interacting with LLM providers.
    
    This class provides a consistent interface across different LLM providers,
    handling retries, timeouts, and error normalization.
    """
    
    def __init__(
        self,
        provider: LLMProvider,
        max_retries: int = 3,
        timeout_seconds: int = 30,
        retry_delay: float = 1.0,
    ):
        """Initialize the LLM client.
        
        Args:
            provider: The LLM provider implementation
            max_retries: Maximum number of retries for failed requests
            timeout_seconds: Timeout for individual requests
            retry_delay: Base delay between retries (with exponential backoff)
        """
        self.provider = provider
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.retry_delay = retry_delay
        
        logger.debug(
            "llm_client_initialized",
            extra={
                "provider": provider.get_provider_name(),
                "max_retries": max_retries,
                "timeout_seconds": timeout_seconds,
            }
        )
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.1,
        **kwargs
    ) -> str:
        """Generate text with retry logic and error handling.
        
        Args:
            prompt: The input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Provider-specific parameters
            
        Returns:
            str: Generated text response
            
        Raises:
            LLMError: If generation fails after all retries
        """
        start_time = time.time()
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(
                    "llm_generation_started",
                    extra={
                        "provider": self.provider.get_provider_name(),
                        "prompt_length": len(prompt),
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "attempt": attempt + 1,
                    }
                )
                
                response = self.provider.generate(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **kwargs
                )
                
                generation_time_ms = int((time.time() - start_time) * 1000)
                
                logger.info(
                    "llm_generation_completed",
                    extra={
                        "provider": self.provider.get_provider_name(),
                        "response_length": len(response) if response else 0,
                        "generation_time_ms": generation_time_ms,
                        "attempt": attempt + 1,
                    }
                )
                
                return response
                
            except LLMRateLimitError as e:
                last_error = e
                if attempt < self.max_retries:
                    # Longer delay for rate limits
                    delay = self.retry_delay * (2 ** attempt) * 2
                    logger.warning(
                        "llm_rate_limit_retry",
                        extra={
                            "provider": self.provider.get_provider_name(),
                            "attempt": attempt + 1,
                            "delay_seconds": delay,
                        }
                    )
                    time.sleep(delay)
                else:
                    break
                    
            except (LLMTimeoutError, LLMUnavailableError) as e:
                last_error = e
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(
                        "llm_error_retry",
                        extra={
                            "provider": self.provider.get_provider_name(),
                            "error_type": type(e).__name__,
                            "attempt": attempt + 1,
                            "delay_seconds": delay,
                        }
                    )
                    time.sleep(delay)
                else:
                    break
                    
            except Exception as e:
                # For unexpected errors, don't retry
                logger.error(
                    "llm_generation_unexpected_error",
                    extra={
                        "provider": self.provider.get_provider_name(),
                        "error_type": type(e).__name__,
                        "error": str(e)[:200],
                        "attempt": attempt + 1,
                    },
                    exc_info=True
                )
                raise LLMError(f"Unexpected error during LLM generation: {e}") from e
        
        # All retries exhausted
        generation_time_ms = int((time.time() - start_time) * 1000)
        logger.error(
            "llm_generation_failed",
            extra={
                "provider": self.provider.get_provider_name(),
                "error_type": type(last_error).__name__,
                "error": str(last_error)[:200],
                "attempts": self.max_retries + 1,
                "generation_time_ms": generation_time_ms,
            }
        )
        
        raise last_error
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the current provider.
        
        Returns:
            Dict with provider information
        """
        return {
            "provider_name": self.provider.get_provider_name(),
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds,
        }