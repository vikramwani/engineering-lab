"""HTTP request/response logging middleware with structured data.

This module provides FastAPI middleware that logs all HTTP requests and responses
with structured JSON data including request IDs, timing information, and error
context for comprehensive observability.
"""

import logging
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses with structured data."""

    def __init__(self, app):
        super().__init__(app)
        logger.debug("logging_middleware_initialized")

    async def dispatch(self, request: Request, call_next):
        """Process HTTP request and log structured data about the request/response cycle."""
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        start_time = time.time()

        logger.info(
            "request_started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": (
                    str(request.query_params) if request.query_params else None
                ),
                "user_agent": request.headers.get("user-agent"),
                "client_ip": request.client.host if request.client else None,
            },
        )

        try:
            response = await call_next(request)

            latency_ms = int((time.time() - start_time) * 1000)

            logger.info(
                "request_completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "latency_ms": latency_ms,
                },
            )

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            logger.error(
                "request_failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "latency_ms": latency_ms,
                    "error_type": type(e).__name__,
                    "error": str(e)[:200],
                },
                exc_info=True,
            )
            raise

        response.headers["X-Request-ID"] = request_id
        return response
