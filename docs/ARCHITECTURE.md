# Architecture decisions

## ADR-001: two independent retrieval paths

Classic retrieval uses OpenSearch/BM25 and does not call an embedding model or vector store. Semantic retrieval uses an embedding model and Qdrant/HNSW and does not depend on BM25. Compare mode calls both concurrently. This separation preserves benchmark validity.

## ADR-002: modular monolith before microservices

The API is one deployable FastAPI service with explicit adapter/service boundaries. Ingestion/evaluation can later be split into workers if traffic or ownership justifies it. Premature microservices would add operational cost without improving the experiment.

## ADR-003: ACL at retrieval time

Access controls are encoded into both OpenSearch filters and Qdrant payload filters. The frontend never receives forbidden candidates. Non-confidential documents normalize `acl_departments` to `*`; confidential documents carry explicit department scopes.

## ADR-004: deterministic Qdrant IDs

Qdrant point IDs use UUIDv5 derived from the corpus `chunk_id`, while the human-readable chunk ID remains in payload. This makes repeated ingestion idempotent and avoids relying on arbitrary string IDs.

## ADR-005: generated corpus outside normal Git history

Large synthetic corpus files are reproducible. Git tracks the generator, manifest, taxonomy, validation report and samples. Full archives should use Git LFS, a GitHub Release asset or object storage rather than bloating clone history.
