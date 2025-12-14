from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.client import LLMService
from src.logging_middleware import LoggingMiddleware

app = FastAPI()

# Add logging middleware
app.add_middleware(LoggingMiddleware)

# Initialize your LLM service
llm_service = LLMService()

# Request model
class ChatRequest(BaseModel):
    query: str

# Health check
@app.get("/")
def root():
    return {"status": "ok", "message": "LLM Service API is running"}

# Versioned chat endpoint
@app.post("/v1/chat")
def chat_v1(req: ChatRequest):
    try:
        response = llm_service.chat(req.query)
        return response
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": "LLM processing failed",
                "details": str(e)
            },
        )
