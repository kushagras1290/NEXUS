from fastapi import APIRouter, Depends, Response, status

from ..dependencies import get_search_service
from ..services.search import SearchService

router = APIRouter(tags=["health"])


@router.get("/health/live")
async def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
async def ready(
    response: Response,
    service: SearchService = Depends(get_search_service),
) -> dict[str, object]:
    classic = await service.classic.health()
    semantic = await service.semantic.health()
    ready_state = classic and semantic
    if not ready_state:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "ok" if ready_state else "degraded", "classic": classic, "semantic": semantic}
