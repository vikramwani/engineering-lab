import logging
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("llm_service")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses with structured data."""
    
    async def dispatch(self, request: Request, call_next):
        """Process HTTP request and log structured data about the request/response cycle."""
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        start_time = time.time()

        try:
            response = await call_next(request)
        except Exception:
            latency_ms = int((time.time() - start_time) * 1000)
            logger.exception(
                "request_failed",
                extra={
                    "event": "request_failed",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "latency_ms": latency_ms,
                },
            )
            raise

        latency_ms = int((time.time() - start_time) * 1000)

        logger.info(
            "request_completed",
            extra={
                "event": "request_completed",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "latency_ms": latency_ms,
            },
        )

        response.headers["X-Request-ID"] = request_id
        return response
