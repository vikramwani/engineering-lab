import logging
import time
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from .auth import require_api_key
from .client import LLMService
from .config import load_settings
from .llm_errors import LLMRateLimitError, LLMTimeoutError, LLMUnavailableError
from .logging_config import setup_logging
from .logging_middleware import LoggingMiddleware

logger = logging.getLogger("llm_service")

# --------------------
# App setup
# --------------------

setup_logging()

app = FastAPI(title="LLM Service")
app.add_middleware(LoggingMiddleware)

settings = load_settings()
llm_service = LLMService(settings)


# --------------------
# Models
# --------------------


class GenerateRequest(BaseModel):
    """Request model for text generation."""
    
    prompt: str = Field(..., min_length=1)
    max_tokens: Optional[int] = None


class GenerateResponse(BaseModel):
    """Response model for text generation."""
    
    request_id: str
    output: str
    latency_ms: int


# --------------------
# Routes
# --------------------


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/generate", response_model=GenerateResponse)
def generate(
    request_data: GenerateRequest,
    request: Request,
    _: None = Depends(require_api_key),
):
    """Generate text using the LLM service."""
    start_time = time.time()

    try:
        output = llm_service.chat(
            prompt=request_data.prompt,
            max_tokens=request_data.max_tokens,
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

    latency_ms = int((time.time() - start_time) * 1000)

    return GenerateResponse(
        request_id=request.state.request_id,
        output=output,
        latency_ms=latency_ms,
    )
