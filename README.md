# NEXUS

**One enterprise knowledge problem. Two retrieval architectures. One measurable answer.**

NEXUS is a full-stack enterprise knowledge retrieval platform that benchmarks classical lexical information retrieval against neural vector retrieval on the **same corpus, query set, ACL rules and user experience**.

## Implemented

- **Classic:** OpenSearch + BM25 + field boosts + exact identifier/error-code boosts + fuzzy lexical retrieval.
- **Semantic:** BGE embeddings through FastEmbed + Qdrant + HNSW approximate nearest-neighbour retrieval.
- **Compare:** concurrent fan-out to both independent engines with latency and result-overlap reporting.
- **Cinematic frontend:** scroll-driven knowledge constellation, deliberate near-black narrative interludes and a full-screen search workspace.
- **Admin control plane:** engine health, corpus metrics and an ACL-gated single-flight operation that indexes the canonical corpus into both engines.
- **EUKB v1 dataset:** 50,000 synthetic enterprise documents, 402,861 chunks and 5,000 labelled evaluation queries committed under `data/full/`.
- **Evaluation:** Recall@K, MRR, nDCG@K and latency benchmarking.
- **Operations:** Docker Compose, non-root application containers, health/readiness endpoints, structured logs, Prometheus metrics and GitHub Actions quality gates.

## Architecture

```text
                   Cinematic Next.js UI
                           |
                           v
                 FastAPI query orchestrator
                    /               \
                   /                 \
          OpenSearch / BM25      Qdrant / HNSW
          CLASSIC ONLY           SEMANTIC ONLY
                   \                 /
                    \               /
                     Compare / Eval
```

The primary engines are deliberately independent. A future hybrid retriever can be a third experiment without contaminating the classical-vs-vector benchmark.

## Quick start

```bash
cp .env.example .env
docker compose up --build -d

# Practical first bootstrap; remove --limit for the complete corpus.
docker compose exec api nexus-api ingest --dataset /data/full --limit 5000
```

Open:

- Web: `http://localhost:3000`
- Search: `http://localhost:3000/search`
- Admin: `http://localhost:3000/admin`
- API docs: `http://localhost:8000/docs`
- Liveness: `http://localhost:8000/health/live`
- Readiness: `http://localhost:8000/health/ready`
- Metrics: `http://localhost:8000/metrics`

The admin panel can also start a full dual-engine reindex from `data/full/`.

> The first semantic indexing/search operation may download the configured embedding model. Production environments should pre-bake or pre-cache model artifacts rather than depend on an outbound runtime download.

## Dataset

The canonical corpus is committed under `data/full/` and is reproducible:

```bash
python tools/generate_eukb.py \
  --output data/full \
  --documents 50000 \
  --eval-queries 5000
```

The **Materialize EUKB Dataset** workflow regenerates and validates the corpus when the generator changes. Gzip output is deterministic so unchanged corpora do not create meaningless binary diffs.

Dataset domains include software engineering, SRE, cloud, cybersecurity, HR, IT support, delivery, finance, legal/compliance, learning and organisational ownership. It deliberately contains exact identifiers, semantic paraphrases, acronyms, typos, ambiguous requests, ACL-sensitive documents and active-vs-archived version conflicts.

No private TCS, Infosys, Accenture or other corporate material is used.

## Evaluation

```bash
docker compose exec api nexus-api evaluate --dataset /data/full --limit 250 --k 10
```

Do not invent benchmark numbers. Record metrics only after running the same labelled evaluation set against both engines.

## Development checks

```bash
make api-install
make api-lint
make api-test

make web-install
make web-test
make web-build
```

GitHub Actions runs Ruff, formatting, strict Mypy, Pytest, TypeScript, ESLint and the Next.js production build.

## Security model

- ACL filtering is enforced in backend retrieval queries, not merely hidden in the UI.
- Production API mode requires OIDC/JWT issuer, audience and JWKS validation.
- Development role headers are explicitly a local/demo mechanism.
- `NEXT_PUBLIC_NEXUS_DEV_AUTH=true` must not be used as the production identity architecture; production web deployments should sit behind an OIDC-aware BFF or identity proxy that supplies the API bearer token.
- Production startup rejects development auth and the default MinIO secret.
- CORS is allow-listed.
- Application containers run non-root.
- Archived and draft documents are excluded from normal retrieval.
- Request IDs, structured logs and Prometheus metrics are emitted.

## Admin execution model

The included reindex registry is intentionally bounded and single-process for a portfolio/local deployment. A horizontally scaled enterprise deployment should move long-running ingestion/reindex jobs and job state to a durable queue such as Redis/RQ, Dramatiq, Celery or a managed queue.

## Dependency baseline

The project targets FastAPI 0.141.x, `opensearch-py` 3.2.x, `qdrant-client` 1.19.x, Next.js 16.3.6 and React 19.3.x. Version changes should go through CI rather than silently floating.
