from __future__ import annotations

import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.middleware.base import RequestResponseEndpoint

from .config import get_settings
from .dependencies import build_search_service
from .logging import configure_logging
from .routers.admin import router as admin_router
from .routers.health import router as health_router
from .routers.search import router as search_router

settings = get_settings()
configure_logging(settings.log_level)
log = structlog.get_logger("nexus.api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    service = build_search_service(settings)
    app.state.search_service = service
    log.info("nexus_started", env=settings.env)
    try:
        yield
    finally:
        close = getattr(service.semantic, "close", None)
        if close is not None:
            await close()
        log.info("nexus_stopped")


app = FastAPI(
    title="NEXUS Retrieval API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.env != "production" else None,
    redoc_url=None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Nexus-User-Role",
        "X-Nexus-User-Department",
        "X-Nexus-User-Country",
        "X-Request-ID",
    ],
)


@app.middleware("http")
async def request_context(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    started = time.perf_counter()
    structlog.contextvars.bind_contextvars(request_id=request_id, path=request.url.path)
    try:
        response = await call_next(request)
    finally:
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        log.info("request_complete", latency_ms=latency_ms, method=request.method)
        structlog.contextvars.clear_contextvars()
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    return response


@app.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


app.include_router(health_router)
app.include_router(search_router)
app.include_router(admin_router)
