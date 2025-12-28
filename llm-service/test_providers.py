#!/usr/bin/env python3
"""
Test script to verify LLM provider configuration.
Run this to test switching between OpenAI, XAI, and local LLMs.
"""

import logging
import os
import sys
sys.path.insert(0, 'src')

from src.config import load_settings
from src.client import LLMService
from src.logging_config import setup_logging

# Configure logging for test script using same settings as main app
try:
    settings = load_settings()
    setup_logging(
        log_level=settings.log_level,
        log_file="logs/test_providers.log",
        log_to_console=True
    )
except Exception:
    # Fallback if settings can't be loaded
    setup_logging(log_level="DEBUG", log_file="logs/test_providers.log", log_to_console=True)

logger = logging.getLogger(__name__)

def test_provider_config():
    """Test the current provider configuration."""
    try:
        settings = load_settings()
        logger.info(
            "configuration_loaded",
            extra={
                "provider": settings.llm_provider,
                "model": settings.model,
                "max_tokens": settings.default_max_tokens,
                "timeout_seconds": settings.request_timeout_seconds,
                "log_level": settings.log_level,
                "log_file": settings.log_file,
                "openai_key_present": bool(settings.openai_api_key),
                "xai_key_present": bool(settings.xai_api_key),
            }
        )
        
        # Test client initialization
        llm_service = LLMService(settings)
        logger.info("llm_service_initialized", extra={"provider": settings.llm_provider})
        
        return True
        
    except Exception as e:
        logger.error(
            "configuration_failed",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True
        )
        return False

def test_simple_request():
    """Test a simple LLM request."""
    try:
        settings = load_settings()
        llm_service = LLMService(settings)
        
        logger.info(
            "test_request_starting",
            extra={"provider": settings.llm_provider, "model": settings.model}
        )
        
        response = llm_service.chat("Say 'Hello from " + settings.llm_provider + "!' in one sentence.")
        
        logger.info(
            "test_request_successful",
            extra={
                "provider": settings.llm_provider,
                "response_length": len(response) if response else 0
            }
        )
        return True
        
    except Exception as e:
        logger.error(
            "test_request_failed",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "is_deprecation_error": "404" in str(e) and "deprecated" in str(e)
            },
            exc_info=True
        )
        return False

if __name__ == "__main__":
    logger.info("test_suite_starting")
    
    # Test configuration
    config_success = test_provider_config()
    if not config_success:
        logger.error("test_suite_failed", extra={"reason": "configuration_invalid"})
        sys.exit(1)
    
    # Test simple request
    request_success = test_simple_request()
    if not request_success:
        logger.warning("test_suite_completed_with_warnings", extra={"reason": "request_failed"})
    else:
        logger.info("test_suite_completed_successfully")
    
    logger.info("test_suite_finished")