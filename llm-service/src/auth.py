from typing import Optional
from fastapi import Header, HTTPException
from .dependencies import get_settings


def require_api_key(x_api_key: Optional[str] = Header(default=None)):
    """
    Validate API key from request header.
    """
    settings = get_settings()  # Use cached settings

    if not x_api_key or x_api_key != settings.service_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
