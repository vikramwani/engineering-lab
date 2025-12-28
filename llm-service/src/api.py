"""FastAPI application for LLM-powered compatibility service.

This module provides the main FastAPI application with endpoints for:
- Health checking
- Text generation using LLMs
- Product compatibility evaluation

The service supports multiple LLM providers (OpenAI, XAI, local) and includes
comprehensive logging, authentication, and error handling.
"""
import logging
import time
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from .auth import require_api_key
from .client import LLMService
from .dependencies import get_llm_service, get_settings
from .llm_errors import LLMRateLimitError, LLMTimeoutError, LLMUnavailableError
from .logging_config import setup_logging
from .logging_middleware import LoggingMiddleware
from .compatibility.router import router as compatibility_router


logger = logging.getLogger(__name__)

# --------------------
# App setup
# --------------------

# Load settings first to get logging configuration
settings = get_settings()
setup_logging(
    log_level=settings.log_level,
    log_file=settings.log_file,
    log_to_console=settings.log_to_console
)

app = FastAPI(title="LLM Service", debug=False)  # Set debug=False for production
app.add_middleware(LoggingMiddleware)

# Routers
app.include_router(compatibility_router)

logger.info(
    "application_initialized",
    extra={
        "title": "LLM Service",
        "log_level": settings.log_level,
        "log_file": settings.log_file,
        "provider": settings.llm_provider,
    }
)


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
    logger.debug("health_check_requested")
    return {"status": "ok"}


@app.post("/generate", response_model=GenerateResponse)
def generate(
    request_data: GenerateRequest,
    request: Request,
    llm_service: LLMService = Depends(get_llm_service),
    _: None = Depends(require_api_key),
) -> GenerateResponse:
    """Generate text using the LLM service."""
    start_time = time.time()
    
    logger.info(
        "generate_request_started",
        extra={
            "request_id": request.state.request_id,
            "prompt_length": len(request_data.prompt),
            "max_tokens": request_data.max_tokens,
            "provider": llm_service.settings.llm_provider,
            "model": llm_service.settings.model,
        }
    )

    # Log the prompt at debug level for troubleshooting
    logger.debug(
        "generate_request_prompt",
        extra={
            "request_id": request.state.request_id,
            "prompt": request_data.prompt,
        }
    )

    try:
        output = llm_service.chat(
            prompt=request_data.prompt,
            max_tokens=request_data.max_tokens,
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            "generate_request_completed",
            extra={
                "request_id": request.state.request_id,
                "latency_ms": latency_ms,
                "output_length": len(output) if output else 0,
                "provider": llm_service.settings.llm_provider,
            }
        )
        
        return GenerateResponse(
            request_id=request.state.request_id,
            output=output,
            latency_ms=latency_ms,
        )
    except LLMRateLimitError:
        logger.warning(
            "generate_request_rate_limited",
            extra={
                "request_id": request.state.request_id,
                "provider": llm_service.settings.llm_provider,
                "latency_ms": int((time.time() - start_time) * 1000),
            },
        )
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    except LLMTimeoutError:
        logger.warning(
            "generate_request_timeout",
            extra={
                "request_id": request.state.request_id,
                "provider": llm_service.settings.llm_provider,
                "timeout_seconds": llm_service.settings.request_timeout_seconds,
                "latency_ms": int((time.time() - start_time) * 1000),
            },
        )
        raise HTTPException(status_code=504, detail="LLM request timed out")

    except LLMUnavailableError:
        logger.error(
            "generate_request_llm_unavailable",
            extra={
                "request_id": request.state.request_id,
                "provider": llm_service.settings.llm_provider,
                "latency_ms": int((time.time() - start_time) * 1000),
            },
        )
        raise HTTPException(status_code=503, detail="LLM temporarily unavailable")

    except ValueError as e:
        logger.info(
            "generate_request_validation_error",
            extra={
                "request_id": request.state.request_id,
                "error": str(e)[:200],  # Truncate long error messages
                "latency_ms": int((time.time() - start_time) * 1000),
            },
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(
            "generate_request_unexpected_error",
            extra={
                "request_id": request.state.request_id,
                "error_type": type(e).__name__,
                "error": str(e)[:200],
                "provider": llm_service.settings.llm_provider,
                "latency_ms": int((time.time() - start_time) * 1000),
            },
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Internal server error")
