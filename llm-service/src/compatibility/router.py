"""FastAPI router for product compatibility evaluation endpoints.

This module provides the compatibility evaluation API endpoints with proper
authentication, request/response validation, error handling, and structured
logging for all compatibility operations.
"""

import logging
import time

from fastapi import APIRouter, Depends, HTTPException

from ..auth import require_api_key
from ..client import LLMService
from ..dependencies import get_llm_service
from .models import CompatibilityRequest, CompatibilityResponse
from .service import CompatibilityService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/compatibility",
    tags=["compatibility"],
    dependencies=[Depends(require_api_key)],
)

logger.debug("compatibility_router_initialized")


def get_service(
    llm_service: LLMService = Depends(get_llm_service),
) -> CompatibilityService:
    """Create compatibility service instance."""
    return CompatibilityService(llm_service)


@router.post(
    "/evaluate",
    response_model=CompatibilityResponse,
)
def evaluate_compatibility(
    request: CompatibilityRequest,
    service: CompatibilityService = Depends(get_service),
):
    """Evaluate compatibility between two products."""
    start_time = time.time()

    logger.info(
        "compatibility_request_started",
        extra={
            "product_a_id": request.product_a.id,
            "product_a_category": request.product_a.category,
            "product_b_id": request.product_b.id,
            "product_b_category": request.product_b.category,
            "provider": service.llm.settings.llm_provider,
        },
    )

    try:
        result = service.evaluate(request)

        latency_ms = int((time.time() - start_time) * 1000)

        logger.info(
            "compatibility_request_completed",
            extra={
                "product_a_id": request.product_a.id,
                "product_b_id": request.product_b.id,
                "compatible": result.compatible,
                "relationship": result.relationship,
                "confidence": result.confidence,
                "latency_ms": latency_ms,
                "provider": service.llm.settings.llm_provider,
            },
        )

        return result

    except ValueError as e:
        latency_ms = int((time.time() - start_time) * 1000)
        logger.warning(
            "compatibility_request_validation_error",
            extra={
                "product_a_id": request.product_a.id,
                "product_b_id": request.product_b.id,
                "error": str(e)[:200],
                "latency_ms": latency_ms,
                "provider": service.llm.settings.llm_provider,
            },
        )
        raise HTTPException(status_code=422, detail=str(e))

    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        logger.error(
            "compatibility_request_unexpected_error",
            extra={
                "product_a_id": request.product_a.id,
                "product_b_id": request.product_b.id,
                "error_type": type(e).__name__,
                "error": str(e)[:200],
                "latency_ms": latency_ms,
                "provider": service.llm.settings.llm_provider,
            },
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Internal server error")
