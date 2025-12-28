"""Configuration management for the LLM service.

This module handles loading and validation of configuration settings from
environment variables, supporting multiple LLM providers and comprehensive
logging configuration.
"""
import logging
import os
from dataclasses import dataclass
from typing import Literal

from dotenv import load_dotenv

load_dotenv()  # Load environment variables once at config level

logger = logging.getLogger(__name__)

LLMProvider = Literal["openai", "xai", "local"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR"]


@dataclass
class Settings:
    """Configuration settings for the LLM service."""
    
    openai_api_key: str
    xai_api_key: str
    service_api_key: str
    llm_provider: LLMProvider = "openai"
    model: str = "gpt-4o-mini"
    default_max_tokens: int = 256
    request_timeout_seconds: int = 15
    use_local_llm: bool = False
    local_llm_base_url: str = "http://localhost:11434/v1"
    log_level: LogLevel = "INFO"
    log_file: str = "logs/llm_service.log"
    log_to_console: bool = True


def load_settings() -> Settings:
    """Load and validate configuration settings from environment variables.
    
    Returns:
        Settings: Validated configuration object
        
    Raises:
        RuntimeError: If required environment variables are missing
    """
    logger.debug("settings_loading_started")
    
    llm_provider = os.getenv("LLM_PROVIDER", "openai").lower()
    use_local_llm = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"
    
    # Override provider if using local LLM
    if use_local_llm:
        llm_provider = "local"
        logger.debug("provider_overridden_for_local", extra={"provider": llm_provider})
    
    # Validate provider
    if llm_provider not in ["openai", "xai", "local"]:
        logger.error(
            "invalid_provider_specified",
            extra={"provider": llm_provider, "valid_providers": ["openai", "xai", "local"]}
        )
        raise RuntimeError(f"Invalid LLM_PROVIDER: {llm_provider}. Must be 'openai', 'xai', or 'local'")
    
    # Get API keys
    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    xai_api_key = os.getenv("XAI_API_KEY", "")
    service_api_key = os.getenv("SERVICE_API_KEY")
    
    # Validate required API keys based on provider
    if llm_provider == "openai" and not openai_api_key:
        logger.error("missing_openai_api_key", extra={"provider": llm_provider})
        raise RuntimeError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
    elif llm_provider == "xai" and not xai_api_key:
        logger.error("missing_xai_api_key", extra={"provider": llm_provider})
        raise RuntimeError("XAI_API_KEY is required when LLM_PROVIDER=xai")
    
    if not service_api_key:
        logger.error("missing_service_api_key")
        raise RuntimeError("SERVICE_API_KEY is required")

    # Set default models based on provider
    default_models = {
        "openai": "gpt-4o-mini",
        "xai": "grok-3",  # Updated from deprecated grok-beta
        "local": "llama3.2:3b"
    }
    
    # Get logging configuration
    log_level = os.getenv("LOG_LEVEL", "DEBUG").upper()
    if log_level not in ["DEBUG", "INFO", "WARNING", "ERROR"]:
        log_level = "INFO"
    
    model = os.getenv("MODEL", default_models[llm_provider])
    default_max_tokens = int(os.getenv("DEFAULT_MAX_TOKENS", "256"))
    request_timeout_seconds = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30" if llm_provider == "local" else "15"))
    local_llm_base_url = os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:11434/v1")
    log_file = os.getenv("LOG_FILE", "logs/llm_service.log")
    log_to_console = os.getenv("LOG_TO_CONSOLE", "true").lower() == "true"
    
    settings = Settings(
        openai_api_key=openai_api_key,
        xai_api_key=xai_api_key,
        service_api_key=service_api_key,
        llm_provider=llm_provider,
        model=model,
        default_max_tokens=default_max_tokens,
        request_timeout_seconds=request_timeout_seconds,
        use_local_llm=use_local_llm,
        local_llm_base_url=local_llm_base_url,
        log_level=log_level,
        log_file=log_file,
        log_to_console=log_to_console,
    )
    
    logger.info(
        "settings_loaded_successfully",
        extra={
            "provider": llm_provider,
            "model": model,
            "max_tokens": default_max_tokens,
            "timeout_seconds": request_timeout_seconds,
            "use_local_llm": use_local_llm,
            "log_level": log_level,
            "log_file": log_file,
            "log_to_console": log_to_console,
            "openai_key_present": bool(openai_api_key),
            "xai_key_present": bool(xai_api_key),
            "service_key_present": bool(service_api_key),
        }
    )
    
    return settings
