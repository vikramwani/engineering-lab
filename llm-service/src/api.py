from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import Optional
import uuid
import time


from .logging_middleware import LoggingMiddleware
from .config import load_settings
from .client import LLMService
from .llm_errors import (
    LLMTimeoutError,
    LLMRateLimitError,
    LLMUnavailableError,
)
from .auth import require_api_key

import logging

logger = logging.getLogger("llm_service")



# --------------------
# App setup
# --------------------


from .logging_config import setup_logging

setup_logging()

app = FastAPI(title="LLM Service")

app.add_middleware(LoggingMiddleware)



settings = load_settings()
llm = LLMService(settings)

# --------------------
# Models
# --------------------

class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    max_tokens: Optional[int] = None


class GenerateResponse(BaseModel):
    request_id: str
    output: str
    latency_ms: int

# --------------------
# Routes
# --------------------

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/generate", response_model=GenerateResponse)
def generate(
    req: GenerateRequest,
    request: Request,
    _: None = Depends(require_api_key),
):
    start = time.time()

    try:
        output = llm.chat(
            prompt=req.prompt,
            max_tokens=req.max_tokens,
        )
    except LLMRateLimitError:
        logger.warning(
            "llm_rate_limited",
            extra={
                "event": "llm_rate_limited",
                "request_id": request.state.request_id,
            },
        )
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    except LLMTimeoutError:
        logger.warning(
            "llm_timeout",
            extra={
                "event": "llm_timeout",
                "request_id": request.state.request_id,
            },
        )
        raise HTTPException(status_code=504, detail="LLM request timed out")

    except LLMUnavailableError:
        logger.error(
            "llm_unavailable",
            extra={
                "event": "llm_unavailable",
                "request_id": request.state.request_id,
            },
        )
        raise HTTPException(status_code=503, detail="LLM temporarily unavailable")

    except ValueError as e:
        logger.info(
            "bad_request",
            extra={
                "event": "bad_request",
                "request_id": request.state.request_id,
                "error": str(e),
            },
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")



    latency_ms = int((time.time() - start) * 1000)

    return GenerateResponse(
        request_id=request.state.request_id,
        output=output,
        latency_ms=latency_ms,
    )
