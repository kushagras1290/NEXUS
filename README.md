# NEXUS

**One enterprise knowledge problem. Two retrieval architectures. One measurable answer.**

NEXUS is a production-oriented enterprise knowledge retrieval platform that benchmarks classical lexical information retrieval against neural vector retrieval on the same corpus, query set, security rules, and user interface.

## What is implemented

- **Classic engine:** OpenSearch + BM25 + field boosts + exact-ID boosts + fuzzy matching + ACL filters.
- **Semantic engine:** BGE embeddings + Qdrant + HNSW ANN + ACL filters.
- **Compare mode:** fan-out to both engines concurrently, return latency/overlap/rank deltas.
- **Cinematic search website:** scroll-driven knowledge constellation, full-screen search workspace, Classic/Semantic/Compare modes.
- **Admin console:** index health, knowledge-domain metrics, ingestion controls, engine status and dataset visibility.
- **Dataset:** EUKB synthetic enterprise corpus generator, manifest, taxonomy, synonyms and labelled evaluation queries.
- **Evaluation:** Recall@K, MRR, nDCG@K and latency benchmark runner.
- **Ops:** Docker Compose, health/readiness probes, structured logs, CI, non-root containers, deterministic configuration.

## Architecture

```text
Cinematic Next.js UI
        |
        v
FastAPI Query Orchestrator
   |                 |
   v                 v
OpenSearch          Qdrant
BM25 / lexical      HNSW / dense
   |                 |
   +--------+--------+
            v
       Compare/Eval
```

The two primary engines are intentionally independent. Hybrid search can be added later as a third experiment without contaminating the BM25-vs-vector benchmark.

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

Then open:

- Web: `http://localhost:3000`
- API docs: `http://localhost:8000/docs`
- API health: `http://localhost:8000/health/live`

## Dataset ingestion

The repository contains the deterministic EUKB generator and sample artifacts. Generate/re-generate the full corpus with:

```bash
python tools/generate_eukb.py --output data/generated --documents 50000 --eval-queries 5000
```

Index it into both engines:

```bash
cd apps/api
python -m nexus_api.cli ingest --dataset ../../data/generated
```

For local smoke testing, ingest a subset:

```bash
python -m nexus_api.cli ingest --dataset ../../data/generated --limit 5000
```

## API examples

Development auth uses explicit headers so ACL behavior remains testable locally:

```bash
curl -s http://localhost:8000/api/v1/search/classic \
  -H 'Content-Type: application/json' \
  -H 'X-Nexus-User-Role: engineer' \
  -H 'X-Nexus-User-Department: Software Engineering' \
  -H 'X-Nexus-User-Country: IN' \
  -d '{"query":"ERR-SRE-1047","limit":10}'
```

Production deployments must switch `NEXUS_AUTH_MODE=oidc` and configure issuer/audience/JWKS.

## Test

```bash
make api-install
make api-lint
make api-test

make web-install
make web-test
make web-build
```

## Security model

- Search-time ACL filtering is enforced in backend queries, never only in the UI.
- Production auth supports OIDC/JWT validation with issuer/audience checks.
- CORS is allow-listed.
- Containers run as non-root.
- No secrets are committed.
- Request IDs and structured logs are emitted.
- Search result cache keys must include user ACL context if Redis caching is enabled.
- Archived/draft content is excluded from normal retrieval.

## Dataset provenance

The EUKB corpus models a fictional multinational technology-services company. It contains synthetic policies, technical standards, runbooks, incidents, support articles and organisational records. It does **not** claim to contain private TCS/Infosys/Accenture or other corporate data.

## Current dependency baseline

The project targets FastAPI 0.141.x, `opensearch-py` 3.2.x, `qdrant-client` 1.19.x, Next.js 16.3.6 and React 19.3.x. Pin updates should be reviewed through Dependabot/CI rather than silently floating in production.
