from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException, status

from ..auth import get_user_context
from ..config import Settings, get_settings
from ..dependencies import get_search_service
from ..domain import UserContext
from ..services.search import SearchService

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


def require_admin(user: UserContext = Depends(get_user_context)) -> UserContext:
    if user.role not in {"admin", "manager", "hr", "security"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return user


@router.get("/overview")
async def overview(
    _: UserContext = Depends(require_admin),
    settings: Settings = Depends(get_settings),
    service: SearchService = Depends(get_search_service),
) -> dict[str, object]:
    classic, semantic = await asyncio.gather(service.classic.health(), service.semantic.health())
    return {
        "engines": {
            "classic": {
                "status": "healthy" if classic else "unavailable",
                "index": settings.opensearch_index,
            },
            "semantic": {
                "status": "healthy" if semantic else "unavailable",
                "collection": settings.qdrant_collection,
            },
        },
        "dataset": {
            "name": "EUKB v1",
            "source_documents": 50000,
            "search_chunks": 402861,
            "evaluation_queries": 5000,
        },
    }
