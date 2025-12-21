from fastapi import Header, HTTPException
from .config import load_settings


def require_api_key(x_api_key: str = Header(...)):
    settings = load_settings()  #  load at request time

    if x_api_key != settings.service_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
