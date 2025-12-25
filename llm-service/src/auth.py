from fastapi import Header, HTTPException

from .config import load_settings


def require_api_key(x_api_key: str = Header(...)):
    """Validate API key from request header.
    
    Args:
        x_api_key: API key from X-API-Key header
        
    Raises:
        HTTPException: If API key is invalid (401 Unauthorized)
    """
    settings = load_settings()  # Load at request time

    if x_api_key != settings.service_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
