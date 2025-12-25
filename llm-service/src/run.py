"""Simple CLI script to test the LLM service."""

from .client import LLMService
from .config import load_settings


def main():
    """Test the LLM service with a simple prompt."""
    settings = load_settings()
    llm_service = LLMService(settings)
    reply = llm_service.chat("Write a 1-sentence fun fact about software engineering.")
    print(reply)


if __name__ == "__main__":
    main()
