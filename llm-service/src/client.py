import time
from typing import Optional

from openai import OpenAI

from .config import Settings
from .llm_errors import LLMUnavailableError


class LLMService:
    """Service for interacting with OpenAI's LLM API with retry logic."""
    
    def __init__(self, settings: Settings):
        """Initialize the LLM service with configuration settings.
        
        Args:
            settings: Configuration object containing API keys and model settings
        """
        self.settings = settings
        self.client = OpenAI(api_key=settings.openai_api_key)

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
        last_exception = None
        max_attempts = 3

        for attempt in range(1, max_attempts + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.settings.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens or self.settings.default_max_tokens,
                    timeout=self.settings.request_timeout_seconds,
                )

                return response.choices[0].message.content

            except Exception as e:
                last_exception = e

                # Simple exponential backoff: 0.5s, 1s
                if attempt < max_attempts:
                    time.sleep(0.5 * attempt)
                else:
                    break

        # After retries exhausted
        raise LLMUnavailableError("LLM unavailable after retries") from last_exception
