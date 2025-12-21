from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import uuid
import time

from src.client import LLMService

from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="LLM Service")
llm = LLMService()


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    max_tokens: Optional[int] = 256


class GenerateResponse(BaseModel):
    request_id: str
    output: str
    latency_ms: int


@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest):
    request_id = str(uuid.uuid4())
    start = time.time()

    try:
        output = llm.chat(
            prompt=req.prompt,
            max_tokens=req.max_tokens,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    latency_ms = int((time.time() - start) * 1000)

    return GenerateResponse(
        request_id=request_id,
        output=output,
        latency_ms=latency_ms,
    )

