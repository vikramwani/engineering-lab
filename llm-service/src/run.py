"""Simple CLI script to test the LLM service."""

import logging

from .client import LLMService
from .config import load_settings

logger = logging.getLogger(__name__)


def main():
    """Test the LLM service with a simple prompt."""
    settings = load_settings()
    llm_service = LLMService(settings)
    reply = llm_service.chat(
        "Write a 1-sentence fun fact about software engineering."
    )

    # Use logging instead of print for consistency
    logger.info("llm_test_completed", extra={"response": reply})


if __name__ == "__main__":
    main()
