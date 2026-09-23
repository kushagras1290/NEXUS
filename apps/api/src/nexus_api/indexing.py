from __future__ import annotations

import gzip
import json
import uuid
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import urlparse

from opensearchpy import OpenSearch, helpers
from qdrant_client import QdrantClient, models

from .adapters.embedding import FastEmbedder
from .config import Settings

NAMESPACE = uuid.UUID("d1392f69-98f2-4fdc-b8c7-e89b8246e990")


def read_jsonl_gz(path: Path, limit: int | None = None) -> Iterator[dict[str, object]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for index, line in enumerate(handle):
            if limit is not None and index >= limit:
                return
            yield json.loads(line)


def opensearch_client(settings: Settings) -> OpenSearch:
    parsed = urlparse(str(settings.opensearch_url))
    return OpenSearch(
        hosts=[{"host": parsed.hostname or "localhost", "port": parsed.port or 9200}],
        http_auth=(settings.opensearch_username, settings.opensearch_password),
        use_ssl=parsed.scheme == "https",
        verify_certs=settings.opensearch_verify_certs,
        ssl_assert_hostname=settings.opensearch_verify_certs,
        http_compress=True,
        timeout=30,
    )


def ensure_classic_index(client: OpenSearch, index: str) -> None:
    if client.indices.exists(index=index):
        return
    body = {
        "settings": {"number_of_shards": 1, "number_of_replicas": 0},
        "mappings": {
            "properties": {
                "chunk_id": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                "document_id": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                "title": {"type": "text"},
                "text": {"type": "text"},
                "keywords": {"type": "text"},
                "error_code": {"type": "keyword"},
                "department": {"type": "keyword"},
                "category": {"type": "keyword"},
                "subcategory": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                "document_type": {"type": "keyword"},
                "country": {"type": "keyword"},
                "classification": {"type": "keyword"},
                "allowed_roles": {"type": "keyword"},
                "acl_departments": {"type": "keyword"},
                "status": {"type": "keyword"},
                "version": {"type": "keyword"},
                "owner_team": {"type": "keyword"},
                "updated_at": {"type": "date"},
            }
        },
    }
    client.indices.create(index=index, body=body)


def _normalized_payload(chunk: dict[str, object], document: dict[str, object]) -> dict[str, object]:
    allowed_departments = chunk.get("allowed_departments") or ["*"]
    return {
        **chunk,
        "title": document.get("title", "Untitled"),
        "keywords": document.get("keywords", []),
        "error_code": document.get("error_code"),
        "acl_departments": allowed_departments,
    }


def index_dataset(
    settings: Settings, dataset: Path, limit: int | None = None, batch_size: int = 256
) -> dict[str, int]:
    documents = {
        str(item["document_id"]): item
        for item in read_jsonl_gz(dataset / "documents.jsonl.gz", limit=None)
    }
    chunks = read_jsonl_gz(dataset / "chunks.jsonl.gz", limit=limit)

    os_client = opensearch_client(settings)
    ensure_classic_index(os_client, settings.opensearch_index)

    qdrant = QdrantClient(
        url=str(settings.qdrant_url), api_key=settings.qdrant_api_key or None, timeout=60
    )
    if not qdrant.collection_exists(settings.qdrant_collection):
        qdrant.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=models.VectorParams(
                size=settings.vector_size, distance=models.Distance.COSINE
            ),
            hnsw_config=models.HnswConfigDiff(m=16, ef_construct=128),
        )
    embedder = FastEmbedder(settings.embedding_model)

    classic_actions: list[dict[str, object]] = []
    vector_payloads: list[dict[str, object]] = []
    vector_ids: list[str] = []
    vector_texts: list[str] = []
    indexed = 0

    def flush() -> None:
        nonlocal indexed
        if not classic_actions:
            return
        helpers.bulk(os_client, classic_actions, request_timeout=60)
        vectors = embedder.embed_batch_sync(vector_texts)
        points = [
            models.PointStruct(id=point_id, vector=vector, payload=payload)
            for point_id, vector, payload in zip(vector_ids, vectors, vector_payloads, strict=True)
        ]
        qdrant.upsert(collection_name=settings.qdrant_collection, points=points, wait=True)
        indexed += len(classic_actions)
        classic_actions.clear()
        vector_payloads.clear()
        vector_ids.clear()
        vector_texts.clear()

    for chunk in chunks:
        doc = documents[str(chunk["document_id"])]
        payload = _normalized_payload(chunk, doc)
        classic_actions.append(
            {
                "_op_type": "index",
                "_index": settings.opensearch_index,
                "_id": chunk["chunk_id"],
                "_source": payload,
            }
        )
        vector_ids.append(str(uuid.uuid5(NAMESPACE, str(chunk["chunk_id"]))))
        vector_payloads.append(payload)
        vector_texts.append(str(payload["text"]))
        if len(classic_actions) >= batch_size:
            flush()
    flush()
    os_client.indices.refresh(index=settings.opensearch_index)
    return {"indexed_chunks": indexed, "documents_loaded": len(documents)}
