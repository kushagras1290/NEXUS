from __future__ import annotations

import asyncio
import time
from urllib.parse import urlparse

from opensearchpy import OpenSearch

from ..domain import EngineResult, RetrievalQuery, SearchHit, SearchMode


class OpenSearchRetriever:
    def __init__(
        self,
        *,
        url: str,
        username: str,
        password: str,
        verify_certs: bool,
        index: str,
        timeout_seconds: float,
    ) -> None:
        parsed = urlparse(url)
        self.index = index
        self.client = OpenSearch(
            hosts=[{"host": parsed.hostname or "localhost", "port": parsed.port or 9200}],
            http_auth=(username, password) if username else None,
            use_ssl=parsed.scheme == "https",
            verify_certs=verify_certs,
            ssl_assert_hostname=verify_certs,
            http_compress=True,
            timeout=timeout_seconds,
            max_retries=2,
            retry_on_timeout=True,
        )

    @staticmethod
    def _filters(query: RetrievalQuery) -> list[dict[str, object]]:
        filters: list[dict[str, object]] = [
            {"term": {"status": "ACTIVE"}},
            {"terms": {"allowed_roles": [query.user.role]}},
            {"terms": {"acl_departments": ["*", query.user.department]}},
            {"terms": {"country": ["GLOBAL", query.user.country]}},
        ]
        if query.filters.department:
            filters.append({"terms": {"department": query.filters.department}})
        if query.filters.category:
            filters.append({"terms": {"category": query.filters.category}})
        if query.filters.document_type:
            filters.append({"terms": {"document_type": query.filters.document_type}})
        if query.filters.country:
            filters.append({"terms": {"country": query.filters.country}})
        return filters

    def _search_sync(self, query: RetrievalQuery) -> EngineResult:
        started = time.perf_counter()
        body = {
            "size": query.limit,
            "track_total_hits": False,
            "_source": [
                "chunk_id", "document_id", "title", "text", "department", "category",
                "subcategory", "document_type", "country", "version", "owner_team",
            ],
            "query": {
                "bool": {
                    "filter": self._filters(query),
                    "should": [
                        {"term": {"document_id.keyword": {"value": query.text, "boost": 12.0}}},
                        {"term": {"chunk_id.keyword": {"value": query.text, "boost": 12.0}}},
                        {"term": {"error_code": {"value": query.text, "boost": 14.0}}},
                        {
                            "multi_match": {
                                "query": query.text,
                                "fields": [
                                    "title^4", "subcategory^3", "category^2", "keywords^2", "text"
                                ],
                                "type": "best_fields",
                                "operator": "or",
                                "fuzziness": "AUTO",
                                "prefix_length": 2,
                            }
                        },
                    ],
                    "minimum_should_match": 1,
                }
            },
        }
        response = self.client.search(index=self.index, body=body)
        raw_hits = response.get("hits", {}).get("hits", [])
        hits: list[SearchHit] = []
        for rank, item in enumerate(raw_hits, start=1):
            source = item.get("_source", {})
            text = str(source.get("text", ""))
            hits.append(
                SearchHit(
                    chunk_id=str(source.get("chunk_id", item.get("_id", ""))),
                    document_id=str(source.get("document_id", "")),
                    title=str(source.get("title", "Untitled")),
                    excerpt=text[:520],
                    score=float(item.get("_score") or 0.0),
                    department=str(source.get("department", "")),
                    category=str(source.get("category", "")),
                    subcategory=str(source.get("subcategory", "")),
                    document_type=str(source.get("document_type", "")),
                    country=str(source.get("country", "GLOBAL")),
                    version=str(source.get("version", "")),
                    owner_team=str(source.get("owner_team", "")),
                    engine=SearchMode.CLASSIC,
                    rank=rank,
                )
            )
        return EngineResult(
            engine=SearchMode.CLASSIC,
            latency_ms=(time.perf_counter() - started) * 1000,
            hits=hits,
        )

    async def search(self, query: RetrievalQuery) -> EngineResult:
        return await asyncio.to_thread(self._search_sync, query)

    async def health(self) -> bool:
        try:
            return bool(await asyncio.to_thread(self.client.ping))
        except Exception:
            return False
