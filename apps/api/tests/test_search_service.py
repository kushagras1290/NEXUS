from nexus_api.domain import (
    EngineResult,
    RetrievalQuery,
    SearchFilters,
    SearchHit,
    SearchMode,
    UserContext,
)
from nexus_api.services.search import SearchService


class FakeRetriever:
    def __init__(self, engine: SearchMode, docs: list[str]) -> None:
        self.engine = engine
        self.docs = docs

    async def health(self) -> bool:
        return True

    async def search(self, query: RetrievalQuery) -> EngineResult:
        return EngineResult(
            engine=self.engine,
            latency_ms=1.0,
            hits=[
                SearchHit(
                    chunk_id=f"{doc}-C00",
                    document_id=doc,
                    title=doc,
                    excerpt="x",
                    score=1.0,
                    department="Engineering",
                    category="API",
                    subcategory="REST",
                    document_type="guide",
                    country="GLOBAL",
                    version="1.0",
                    owner_team="Platform",
                    engine=self.engine,
                    rank=i,
                )
                for i, doc in enumerate(self.docs, start=1)
            ],
        )


async def test_compare_overlap() -> None:
    service = SearchService(
        FakeRetriever(SearchMode.CLASSIC, ["A", "B"]),
        FakeRetriever(SearchMode.SEMANTIC, ["B", "C"]),
    )
    result = await service.compare(
        RetrievalQuery(
            text="query",
            limit=10,
            user=UserContext(),
            filters=SearchFilters(),
        )
    )
    assert result.overlap_document_ids == ["B"]
    assert result.overlap_ratio == 1 / 3
