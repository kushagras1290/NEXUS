from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..admin_jobs import ReindexJobRegistry
from ..auth import get_user_context
from ..config import Settings, get_settings
from ..dependencies import get_search_service
from ..domain import UserContext
from ..services.search import SearchService

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])
job_registry = ReindexJobRegistry()


class ReindexRequest(BaseModel):
    limit: int | None = Field(default=None, ge=1, le=402_861)
    batch_size: int = Field(default=256, ge=16, le=2048)


def require_admin(user: UserContext = Depends(get_user_context)) -> UserContext:
    if user.role not in {"admin", "manager", "hr", "security"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return user


@router.get("/overview")
async def overview(
    _: UserContext = Depends(require_admin),
    settings: Settings = Depends(get_settings),
    service: SearchService = Depends(get_search_service),
) -> dict[str, object]:
    classic, semantic = await asyncio.gather(
        service.classic.health(),
        service.semantic.health(),
    )
    latest = job_registry.latest()
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
            "source_documents": 50_000,
            "search_chunks": 402_861,
            "evaluation_queries": 5_000,
            "path": settings.dataset_path,
        },
        "latest_reindex_job": latest.as_dict() if latest else None,
    }


@router.post("/reindex", status_code=status.HTTP_202_ACCEPTED)
async def start_reindex(
    payload: ReindexRequest,
    _: UserContext = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    dataset = Path(settings.dataset_path).resolve()
    required = {"documents.jsonl.gz", "chunks.jsonl.gz"}
    if not dataset.is_dir() or not required.issubset({path.name for path in dataset.iterdir()}):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Canonical dataset is not materialized on this deployment",
        )

    try:
        job = job_registry.create()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    job_registry.schedule(
        job.id,
        settings=settings,
        dataset=dataset,
        limit=payload.limit,
        batch_size=payload.batch_size,
    )
    return job.as_dict()


@router.get("/reindex/{job_id}")
async def reindex_status(
    job_id: str,
    _: UserContext = Depends(require_admin),
) -> dict[str, object]:
    job = job_registry.get(job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reindex job not found",
        )
    return job.as_dict()
