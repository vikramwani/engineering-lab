"""LLM client service with multi-provider support and retry logic.

This module provides the LLMService class that handles communication with
various LLM providers (OpenAI, XAI, local) with built-in retry logic,
timeout handling, and comprehensive logging.
"""
import logging
import time
from typing import Optional

from openai import OpenAI

from .config import Settings
from .llm_errors import LLMUnavailableError

logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with LLM APIs (OpenAI, XAI, or local) with retry logic."""
    
    def __init__(self, settings: Settings):
        """Initialize the LLM service with configuration settings.
        
        Args:
            settings: Configuration object containing API keys and model settings
        """
        self.settings = settings
        
        logger.info(
            "llm_service_initializing",
            extra={
                "provider": settings.llm_provider,
                "model": settings.model,
                "timeout_seconds": settings.request_timeout_seconds,
            }
        )
        
        # Configure client based on provider
        if settings.llm_provider == "openai":
            self.client = OpenAI(api_key=settings.openai_api_key)
            logger.debug("openai_client_configured")
        elif settings.llm_provider == "xai":
            self.client = OpenAI(
                api_key=settings.xai_api_key,
                base_url="https://api.x.ai/v1"
            )
            logger.debug("xai_client_configured", extra={"base_url": "https://api.x.ai/v1"})
        elif settings.llm_provider == "local":
            self.client = OpenAI(
                base_url=settings.local_llm_base_url,
                api_key="ollama",  # Local LLMs don't need real API key
            )
            logger.debug("local_client_configured", extra={"base_url": settings.local_llm_base_url})
        else:
            logger.error("unsupported_provider", extra={"provider": settings.llm_provider})
            raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
        
        logger.info("llm_service_initialized", extra={"provider": settings.llm_provider})

    def chat(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """Send a chat completion request to the LLM with retry logic.
        
        Args:
            prompt: The user prompt to send to the LLM
            max_tokens: Maximum tokens to generate (uses default if None)
            
        Returns:
            The generated text response from the LLM
            
        Raises:
            LLMUnavailableError: If all retry attempts fail
        """
        max_tokens_to_use = max_tokens or self.settings.default_max_tokens
        
        # Log the final prompt and parameters before API call
        logger.info(
            "llm_request_starting",
            extra={
                "provider": self.settings.llm_provider,
                "model": self.settings.model,
                "max_tokens": max_tokens_to_use,
                "timeout": self.settings.request_timeout_seconds,
                "prompt_length": len(prompt),
            }
        )
        
        # Log full prompt at debug level for troubleshooting
        logger.debug("llm_request_prompt", extra={"prompt": prompt})
        
        last_exception = None
        max_attempts = 3

        for attempt in range(1, max_attempts + 1):
            try:
                logger.debug(
                    "llm_api_call_attempt",
                    extra={
                        "attempt": attempt,
                        "max_attempts": max_attempts,
                        "provider": self.settings.llm_provider,
                        "model": self.settings.model,
                    },
                )
                
                response = self.client.chat.completions.create(
                    model=self.settings.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens_to_use,
                    timeout=self.settings.request_timeout_seconds,
                )

                result = response.choices[0].message.content
                
                logger.info(
                    "llm_request_successful",
                    extra={
                        "attempt": attempt,
                        "provider": self.settings.llm_provider,
                        "response_length": len(result) if result else 0,
                        "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
                        "completion_tokens": response.usage.completion_tokens if response.usage else None,
                        "total_tokens": response.usage.total_tokens if response.usage else None,
                    },
                )
                
                return result

            except Exception as e:
                last_exception = e
                
                logger.warning(
                    "llm_request_failed",
                    extra={
                        "attempt": attempt,
                        "max_attempts": max_attempts,
                        "provider": self.settings.llm_provider,
                        "error_type": type(e).__name__,
                        "error_message": str(e)[:200],  # Truncate long error messages
                        "is_rate_limit": "rate" in str(e).lower(),
                        "is_timeout": "timeout" in str(e).lower(),
                        "is_not_found": "404" in str(e),
                    },
                )

                # Simple exponential backoff: 0.5s, 1s
                if attempt < max_attempts:
                    backoff_time = 0.5 * attempt
                    logger.info(
                        "llm_request_retrying",
                        extra={
                            "backoff_seconds": backoff_time,
                            "next_attempt": attempt + 1,
                            "provider": self.settings.llm_provider,
                        },
                    )
                    time.sleep(backoff_time)
                else:
                    break

        # After retries exhausted
        logger.error(
            "llm_request_exhausted",
            extra={
                "provider": self.settings.llm_provider,
                "model": self.settings.model,
                "total_attempts": max_attempts,
                "final_error_type": type(last_exception).__name__,
                "final_error": str(last_exception)[:200],
            },
        )
        raise LLMUnavailableError("LLM unavailable after retries") from last_exception
