from typing import cast\n\nfrom fastapi import Request

from .adapters.classic import OpenSearchRetriever
from .adapters.embedding import FastEmbedder
from .adapters.vector import QdrantRetriever
from .config import Settings
from .services.search import SearchService


def build_search_service(settings: Settings) -> SearchService:
    embedder = FastEmbedder(settings.embedding_model)
    classic = OpenSearchRetriever(
        url=str(settings.opensearch_url),
        username=settings.opensearch_username,
        password=settings.opensearch_password,
        verify_certs=settings.opensearch_verify_certs,
        index=settings.opensearch_index,
        timeout_seconds=settings.request_timeout_seconds,
    )
    semantic = QdrantRetriever(
        url=str(settings.qdrant_url),
        api_key=settings.qdrant_api_key,
        collection=settings.qdrant_collection,
        embedder=embedder,
        timeout_seconds=settings.request_timeout_seconds,
    )
    return SearchService(classic=classic, semantic=semantic)


def get_search_service(request: Request) -> SearchService:
    return request.app.state.search_service
