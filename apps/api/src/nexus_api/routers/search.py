from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from ..auth import get_user_context
from ..config import Settings, get_settings
from ..dependencies import get_search_service
from ..domain import CompareResult, EngineResult, RetrievalQuery, SearchRequest, UserContext
from ..metrics import SEARCH_LATENCY, SEARCH_REQUESTS, ZERO_RESULTS
from ..services.search import SearchService

router = APIRouter(prefix="/api/v1/search", tags=["search"])


def _query(req: SearchRequest, user: UserContext, settings: Settings) -> RetrievalQuery:
    return RetrievalQuery(
        text=req.query.strip(),
        limit=min(req.limit, settings.search_limit_max),
        user=user,
        filters=req.filters,
    )


def _record(result: EngineResult) -> None:
    SEARCH_REQUESTS.labels(engine=result.engine.value, status="ok").inc()
    SEARCH_LATENCY.labels(engine=result.engine.value).observe(result.latency_ms / 1000)
    if not result.hits:
        ZERO_RESULTS.labels(engine=result.engine.value).inc()


@router.post("/classic", response_model=EngineResult)
async def classic_search(
    req: SearchRequest,
    user: UserContext = Depends(get_user_context),
    settings: Settings = Depends(get_settings),
    service: SearchService = Depends(get_search_service),
) -> EngineResult:
    try:
        result = await service.search_classic(_query(req, user, settings))
        _record(result)
        return result
    except Exception as exc:
        SEARCH_REQUESTS.labels(engine="classic", status="error").inc()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Classic search unavailable"
        ) from exc


@router.post("/semantic", response_model=EngineResult)
async def semantic_search(
    req: SearchRequest,
    user: UserContext = Depends(get_user_context),
    settings: Settings = Depends(get_settings),
    service: SearchService = Depends(get_search_service),
) -> EngineResult:
    try:
        result = await service.search_semantic(_query(req, user, settings))
        _record(result)
        return result
    except Exception as exc:
        SEARCH_REQUESTS.labels(engine="semantic", status="error").inc()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Semantic search unavailable"
        ) from exc


@router.post("/compare", response_model=CompareResult)
async def compare_search(
    req: SearchRequest,
    user: UserContext = Depends(get_user_context),
    settings: Settings = Depends(get_settings),
    service: SearchService = Depends(get_search_service),
) -> CompareResult:
    try:
        result = await service.compare(_query(req, user, settings))
        _record(result.classic)
        _record(result.semantic)
        return result
    except Exception as exc:
        SEARCH_REQUESTS.labels(engine="compare", status="error").inc()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Compare search unavailable"
        ) from exc
