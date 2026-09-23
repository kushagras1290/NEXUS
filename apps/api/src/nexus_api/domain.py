from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from pydantic import BaseModel, Field


class SearchMode(StrEnum):
    CLASSIC = "classic"
    SEMANTIC = "semantic"
    COMPARE = "compare"


class UserContext(BaseModel):
    subject: str = "local-user"
    role: str = "employee"
    department: str = "Software Engineering"
    country: str = "GLOBAL"


class SearchFilters(BaseModel):
    department: list[str] = Field(default_factory=list)
    category: list[str] = Field(default_factory=list)
    document_type: list[str] = Field(default_factory=list)
    country: list[str] = Field(default_factory=list)


class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=1000)
    limit: int = Field(default=10, ge=1, le=50)
    filters: SearchFilters = Field(default_factory=SearchFilters)


class SearchHit(BaseModel):
    chunk_id: str
    document_id: str
    title: str
    excerpt: str
    score: float
    department: str
    category: str
    subcategory: str
    document_type: str
    country: str
    version: str
    owner_team: str
    engine: SearchMode
    rank: int


class EngineResult(BaseModel):
    engine: SearchMode
    latency_ms: float
    hits: list[SearchHit]


class CompareResult(BaseModel):
    classic: EngineResult
    semantic: EngineResult
    overlap_document_ids: list[str]
    overlap_ratio: float


@dataclass(slots=True, frozen=True)
class RetrievalQuery:
    text: str
    limit: int
    user: UserContext
    filters: SearchFilters


class Retriever(Protocol):
    async def search(self, query: RetrievalQuery) -> EngineResult: ...

    async def health(self) -> bool: ...
