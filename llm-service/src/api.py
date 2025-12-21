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


# --------------------
# App setup
# --------------------

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
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    except LLMTimeoutError:
        raise HTTPException(status_code=504, detail="LLM request timed out")
    except LLMUnavailableError:
        raise HTTPException(status_code=503, detail="LLM temporarily unavailable")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")



    latency_ms = int((time.time() - start) * 1000)

    return GenerateResponse(
        request_id=request.state.request_id,
        output=output,
        latency_ms=latency_ms,
    )
