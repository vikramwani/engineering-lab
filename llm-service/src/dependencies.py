from .client import LLMService
from .config import load_settings

# Singleton pattern for settings and service
_settings = None
_llm_service = None


def get_settings():
    """Get cached settings instance."""
    global _settings
    if _settings is None:
        _settings = load_settings()
    return _settings


def get_llm_service() -> LLMService:
    """Get cached LLM service instance."""
    global _llm_service
    if _llm_service is None:
        settings = get_settings()
        _llm_service = LLMService(settings)
    return _llm_service
