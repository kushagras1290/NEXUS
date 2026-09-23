from __future__ import annotations

import asyncio

from ..domain import CompareResult, EngineResult, RetrievalQuery, Retriever


class SearchService:
    def __init__(self, classic: Retriever, semantic: Retriever) -> None:
        self.classic = classic
        self.semantic = semantic

    async def search_classic(self, query: RetrievalQuery) -> EngineResult:
        return await self.classic.search(query)

    async def search_semantic(self, query: RetrievalQuery) -> EngineResult:
        return await self.semantic.search(query)

    async def compare(self, query: RetrievalQuery) -> CompareResult:
        classic, semantic = await asyncio.gather(
            self.classic.search(query), self.semantic.search(query)
        )
        classic_docs = {hit.document_id for hit in classic.hits}
        semantic_docs = {hit.document_id for hit in semantic.hits}
        overlap = sorted(classic_docs & semantic_docs)
        denominator = len(classic_docs | semantic_docs)
        ratio = len(overlap) / denominator if denominator else 0.0
        return CompareResult(
            classic=classic,
            semantic=semantic,
            overlap_document_ids=overlap,
            overlap_ratio=ratio,
        )
