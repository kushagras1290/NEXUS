# Architecture decisions

## ADR-001: two independent retrieval paths

Classic retrieval uses OpenSearch/BM25 and does not call an embedding model or vector store. Semantic retrieval uses BGE/FastEmbed and Qdrant/HNSW and does not depend on BM25. Compare mode calls both concurrently. This separation preserves benchmark validity.

## ADR-002: modular monolith before microservices

The API is one deployable FastAPI service with explicit adapter/service boundaries. Ingestion/evaluation can later be split into workers if traffic, reliability targets or ownership justify it. Premature microservices would add operational cost without improving the experiment.

## ADR-003: ACL at retrieval time

Access controls are encoded into both OpenSearch filters and Qdrant payload filters. The frontend never receives forbidden candidates. Non-confidential documents normalize `acl_departments` to `*`; confidential documents carry explicit department scopes.

## ADR-004: deterministic Qdrant IDs

Qdrant point IDs use UUIDv5 derived from the corpus `chunk_id`, while the human-readable chunk ID remains in payload. Repeated ingestion is idempotent at the point-ID level.

## ADR-005: reproducible portfolio corpus in Git

For this portfolio repository the compressed EUKB corpus is intentionally committed under `data/full/`: each compressed artifact is below GitHub's normal per-file limit and the complete corpus is modest enough for a demonstrator. The generator remains the canonical source and emits deterministic gzip bytes.

A real enterprise deployment should put the large corpus in encrypted object storage or an artifact registry, keep manifests/checksums in source control, and ingest through a controlled data pipeline.

## ADR-006: admin reindex execution

The included reindex job registry is single-process, bounded and single-flight. It prevents accidental parallel full reindexes in the portfolio deployment. Multi-replica production deployments should use a durable external queue and persistent job state.

## ADR-007: production identity boundary

Header-based role simulation exists only for local development. Production API deployments require OIDC. The browser frontend must integrate through an OIDC-aware BFF/identity proxy or equivalent secure token-handling boundary; public build-time environment variables must never contain bearer tokens.
