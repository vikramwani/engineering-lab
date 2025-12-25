import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()  # Load environment variables once at config level


@dataclass
class Settings:
    """Configuration settings for the LLM service."""
    
    openai_api_key: str
    service_api_key: str
    model: str = "gpt-4o-mini"  # Fixed model name
    default_max_tokens: int = 256
    request_timeout_seconds: int = 15


def load_settings() -> Settings:
    """Load and validate configuration settings from environment variables.
    
    Returns:
        Settings: Validated configuration object
        
    Raises:
        RuntimeError: If required environment variables are missing
    """
    openai_api_key = os.getenv("OPENAI_API_KEY")
    service_api_key = os.getenv("SERVICE_API_KEY")

    if not openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required")
    if not service_api_key:
        raise RuntimeError("SERVICE_API_KEY is required")

    return Settings(
        openai_api_key=openai_api_key,
        service_api_key=service_api_key,
        model=os.getenv("MODEL", "gpt-4o-mini"),
        default_max_tokens=int(os.getenv("DEFAULT_MAX_TOKENS", "256")),
        request_timeout_seconds=int(os.getenv("REQUEST_TIMEOUT_SECONDS", "15")),
    )
