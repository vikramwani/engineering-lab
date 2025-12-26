import logging

from fastapi import APIRouter, Depends, HTTPException

from ..auth import require_api_key
from ..client import LLMService
from ..dependencies import get_llm_service
from .models import CompatibilityRequest, CompatibilityResponse
from .service import CompatibilityService

logger = logging.getLogger("llm_service")



router = APIRouter(
    prefix="/compatibility",
    tags=["compatibility"],
    dependencies=[Depends(require_api_key)],
)



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
    try:
        return service.evaluate(request)
    except ValueError as e:
        # LLM parsing errors (invalid JSON, etc.)
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        # Log internal errors without exposing details
        logger.error(
            "compatibility_evaluation_failed",
            extra={"error": str(e)},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Internal server error")

