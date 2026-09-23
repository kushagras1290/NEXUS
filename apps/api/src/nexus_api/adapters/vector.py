from __future__ import annotations

import time

from qdrant_client import AsyncQdrantClient, models

from ..domain import EngineResult, RetrievalQuery, SearchHit, SearchMode
from .embedding import FastEmbedder


class QdrantRetriever:
    def __init__(
        self,
        *,
        url: str,
        api_key: str,
        collection: str,
        embedder: FastEmbedder,
        timeout_seconds: float,
    ) -> None:
        self.collection = collection
        self.embedder = embedder
        self.client = AsyncQdrantClient(
            url=url,
            api_key=api_key or None,
            timeout=timeout_seconds,
        )

    @staticmethod
    def _filter(query: RetrievalQuery) -> models.Filter:
        must: list[models.FieldCondition] = [
            models.FieldCondition(key="status", match=models.MatchValue(value="ACTIVE")),
            models.FieldCondition(key="allowed_roles", match=models.MatchAny(any=[query.user.role])),
            models.FieldCondition(
                key="acl_departments", match=models.MatchAny(any=["*", query.user.department])
            ),
            models.FieldCondition(
                key="country", match=models.MatchAny(any=["GLOBAL", query.user.country])
            ),
        ]
        if query.filters.department:
            must.append(
                models.FieldCondition(
                    key="department", match=models.MatchAny(any=query.filters.department)
                )
            )
        if query.filters.category:
            must.append(
                models.FieldCondition(key="category", match=models.MatchAny(any=query.filters.category))
            )
        if query.filters.document_type:
            must.append(
                models.FieldCondition(
                    key="document_type", match=models.MatchAny(any=query.filters.document_type)
                )
            )
        if query.filters.country:
            must.append(
                models.FieldCondition(key="country", match=models.MatchAny(any=query.filters.country))
            )
        return models.Filter(must=must)

    async def search(self, query: RetrievalQuery) -> EngineResult:
        started = time.perf_counter()
        vector = await self.embedder.embed(query.text)
        response = await self.client.query_points(
            collection_name=self.collection,
            query=vector,
            query_filter=self._filter(query),
            limit=query.limit,
            with_payload=True,
            with_vectors=False,
        )
        hits: list[SearchHit] = []
        for rank, point in enumerate(response.points, start=1):
            payload = point.payload or {}
            text = str(payload.get("text", ""))
            hits.append(
                SearchHit(
                    chunk_id=str(payload.get("chunk_id", point.id)),
                    document_id=str(payload.get("document_id", "")),
                    title=str(payload.get("title", "Untitled")),
                    excerpt=text[:520],
                    score=float(point.score),
                    department=str(payload.get("department", "")),
                    category=str(payload.get("category", "")),
                    subcategory=str(payload.get("subcategory", "")),
                    document_type=str(payload.get("document_type", "")),
                    country=str(payload.get("country", "GLOBAL")),
                    version=str(payload.get("version", "")),
                    owner_team=str(payload.get("owner_team", "")),
                    engine=SearchMode.SEMANTIC,
                    rank=rank,
                )
            )
        return EngineResult(
            engine=SearchMode.SEMANTIC,
            latency_ms=(time.perf_counter() - started) * 1000,
            hits=hits,
        )

    async def health(self) -> bool:
        try:
            await self.client.get_collections()
            return True
        except Exception:
            return False

    async def close(self) -> None:
        await self.client.close()
