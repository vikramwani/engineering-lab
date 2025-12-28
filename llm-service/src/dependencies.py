import logging

from .client import LLMService
from .config import load_settings

logger = logging.getLogger(__name__)

# Singleton pattern for settings and service
_settings = None
_llm_service = None


def get_settings():
    """Get cached settings instance."""
    global _settings
    if _settings is None:
        logger.debug("settings_cache_miss")
        _settings = load_settings()
        logger.debug("settings_cached", extra={"provider": _settings.llm_provider})
    else:
        logger.debug("settings_cache_hit", extra={"provider": _settings.llm_provider})
    return _settings


def get_llm_service() -> LLMService:
    """Get cached LLM service instance."""
    global _llm_service
    if _llm_service is None:
        logger.debug("llm_service_cache_miss")
        settings = get_settings()
        _llm_service = LLMService(settings)
        logger.info(
            "llm_service_initialized",
            extra={"provider": settings.llm_provider, "model": settings.model}
        )
    else:
        logger.debug("llm_service_cache_hit")
    return _llm_service
