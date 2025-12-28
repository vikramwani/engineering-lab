"""API key authentication middleware for the LLM service.

This module provides authentication functions that validate API keys from
request headers, ensuring secure access to protected endpoints with proper
error handling and logging.
"""
import logging
from typing import Optional

from fastapi import Header, HTTPException

from .dependencies import get_settings

logger = logging.getLogger(__name__)


def require_api_key(x_api_key: Optional[str] = Header(default=None)):
    """Validate API key from request header.
    
    Args:
        x_api_key: API key from X-API-Key header
        
    Raises:
        HTTPException: If API key is invalid (401 Unauthorized)
    """
    settings = get_settings()  # Use cached settings

    if not x_api_key:
        logger.warning("auth_failed_missing_key")
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    if x_api_key != settings.service_api_key:
        logger.warning(
            "auth_failed_invalid_key",
            extra={"key_length": len(x_api_key) if x_api_key else 0}
        )
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    logger.debug("auth_successful")
