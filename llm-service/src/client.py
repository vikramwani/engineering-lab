from openai import OpenAI
from typing import Optional
import time

from .config import Settings
from .llm_errors import (
    LLMTimeoutError,
    LLMRateLimitError,
    LLMUnavailableError,
)



class LLMService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = OpenAI(api_key=settings.openai_api_key)

    def chat(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        last_exception = None

        for attempt in range(1, 4):  # 👈 max 3 attempts
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

                # simple backoff: 0.5s, 1s
                if attempt < 3:
                    time.sleep(0.5 * attempt)
                else:
                    break

        # After retries exhausted
        raise LLMUnavailableError("LLM unavailable after retries") from last_exception
