from __future__ import annotations

import asyncio
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from .config import Settings
from .indexing import index_dataset

JobState = Literal["queued", "running", "succeeded", "failed"]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class ReindexJob:
    id: str
    state: JobState = "queued"
    created_at: str = field(default_factory=utc_now)
    started_at: str | None = None
    finished_at: str | None = None
    indexed_chunks: int | None = None
    documents_loaded: int | None = None
    error: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "state": self.state,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "indexed_chunks": self.indexed_chunks,
            "documents_loaded": self.documents_loaded,
            "error": self.error,
        }


class ReindexJobRegistry:
    """Single-process reindex coordination for the portfolio deployment.

    A multi-replica enterprise deployment should move execution/state into a
    durable queue such as Redis/RQ, Dramatiq, Celery or a managed cloud queue.
    """

    def __init__(self, max_history: int = 20) -> None:
        self._jobs: dict[str, ReindexJob] = {}
        self._order: list[str] = []
        self._lock = threading.Lock()
        self._max_history = max_history
        self._tasks: set[asyncio.Task[None]] = set()

    def latest(self) -> ReindexJob | None:
        with self._lock:
            if not self._order:
                return None
            return self._jobs[self._order[-1]]

    def get(self, job_id: str) -> ReindexJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def create(self) -> ReindexJob:
        with self._lock:
            latest = self._jobs.get(self._order[-1]) if self._order else None
            if latest and latest.state in {"queued", "running"}:
                raise RuntimeError("A reindex job is already running")
            job = ReindexJob(id=str(uuid.uuid4()))
            self._jobs[job.id] = job
            self._order.append(job.id)
            while len(self._order) > self._max_history:
                expired = self._order.pop(0)
                self._jobs.pop(expired, None)
            return job

    def update(self, job_id: str, **changes: object) -> None:
        with self._lock:
            job = self._jobs[job_id]
            for key, value in changes.items():
                if hasattr(job, key):
                    setattr(job, key, value)

    def schedule(
        self,
        job_id: str,
        *,
        settings: Settings,
        dataset: Path,
        limit: int | None,
        batch_size: int,
    ) -> None:
        task = asyncio.create_task(
            self._run(
                job_id,
                settings=settings,
                dataset=dataset,
                limit=limit,
                batch_size=batch_size,
            )
        )
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _run(
        self,
        job_id: str,
        *,
        settings: Settings,
        dataset: Path,
        limit: int | None,
        batch_size: int,
    ) -> None:
        self.update(job_id, state="running", started_at=utc_now())
        try:
            result = await asyncio.to_thread(
                index_dataset,
                settings,
                dataset,
                limit,
                batch_size,
            )
        except Exception as exc:
            self.update(
                job_id,
                state="failed",
                finished_at=utc_now(),
                error=f"{type(exc).__name__}: {exc}",
            )
            return

        self.update(
            job_id,
            state="succeeded",
            finished_at=utc_now(),
            indexed_chunks=result["indexed_chunks"],
            documents_loaded=result["documents_loaded"],
        )
