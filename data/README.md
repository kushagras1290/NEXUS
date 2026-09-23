# NEXUS EUKB v1

Synthetic enterprise knowledge corpus for the NEXUS retrieval platform.

## Purpose

This dataset models a fictional multinational technology-services company, **Northstar Digital Services**.
It is designed to benchmark **classical lexical search (BM25/OpenSearch)** against
**vector/semantic retrieval (Qdrant/HNSW)** on the same enterprise knowledge problem.

No confidential company data is included.

## Corpus

- Source documents: **50,000**
- Search-ready chunks: **402,861**
- Labelled evaluation queries: **5,000**
- Domains: **11**
- Countries/regions: GLOBAL, IN, UK, IE, US, SG, AU

## Files

- `documents.jsonl.gz` — canonical source documents.
- `chunks.jsonl.gz` — search-ready structured chunks.
- `evaluation_queries.jsonl.gz` — labelled retrieval benchmark.
- `documents.parquet` — columnar copy for analytics/ETL (when available).
- `chunks.parquet` — columnar chunk corpus (when available).
- `evaluation_queries.parquet` — evaluation set (when available).
- `synonyms.json` — enterprise synonym dictionary.
- `taxonomy.json` — domain/category/topic taxonomy.
- `manifest.json` — dataset metadata.
- `validation_report.json` — integrity checks and distributions.
- `*_sample_*.csv` — small human-readable previews.

## Retrieval traps intentionally represented

- exact identifiers/error codes
- semantic paraphrases with low lexical overlap
- acronyms
- misspellings
- ambiguous queries
- multi-condition queries
- active vs archived policy/version conflicts
- country-specific documents
- confidential/ACL-sensitive documents
- cross-domain queries

## Ground truth

Every evaluation query contains `relevance_judgments`:

- `3`: highly relevant / intended result
- `2`: relevant alternative
- `0`: deliberately stale/non-relevant result (used for version-conflict tests)

## Recommended benchmark

Evaluate at least:

- Precision@K
- Recall@K
- MRR
- MAP
- nDCG@K
- Hit Rate
- p50/p95/p99 latency

Run the same evaluation set through:

1. OpenSearch BM25
2. Dense vector retrieval in Qdrant
3. Optional hybrid + reranker

## Reproducibility

Random seed: `20260923`

Generated: 2026-09-23
