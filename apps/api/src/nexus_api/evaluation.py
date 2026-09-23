from __future__ import annotations

import gzip
import json
import math
import statistics
from pathlib import Path
from typing import Any

from .domain import RetrievalQuery, SearchFilters, UserContext
from .services.search import SearchService


def _dcg(grades: list[int]) -> float:
    return float(
        sum((2**grade - 1) / math.log2(index + 2) for index, grade in enumerate(grades))
    )


def ndcg_at_k(ranked_ids: list[str], judgments: dict[str, int], k: int) -> float:
    observed = [judgments.get(doc_id, 0) for doc_id in ranked_ids[:k]]
    ideal = sorted(judgments.values(), reverse=True)[:k]
    denominator = _dcg(ideal)
    return _dcg(observed) / denominator if denominator else 0.0


def recall_at_k(ranked_ids: list[str], judgments: dict[str, int], k: int) -> float:
    relevant = {doc_id for doc_id, grade in judgments.items() if grade > 0}
    if not relevant:
        return 0.0
    return len(set(ranked_ids[:k]) & relevant) / len(relevant)


def reciprocal_rank(ranked_ids: list[str], judgments: dict[str, int]) -> float:
    for rank, doc_id in enumerate(ranked_ids, start=1):
        if judgments.get(doc_id, 0) > 0:
            return 1.0 / rank
    return 0.0


async def evaluate(
    service: SearchService,
    evaluation_file: Path,
    limit: int | None = None,
    k: int = 10,
) -> dict[str, object]:
    per_engine: dict[str, list[dict[str, float]]] = {"classic": [], "semantic": []}
    with gzip.open(evaluation_file, "rt", encoding="utf-8") as handle:
        for idx, line in enumerate(handle):
            if limit is not None and idx >= limit:
                break
            item = json.loads(line)
            if not isinstance(item, dict):
                continue
            raw_item = item
            query = RetrievalQuery(
                text=str(raw_item["query"]),
                limit=k,
                user=UserContext(
                    role=str(raw_item["user_role"]),
                    department=str(raw_item["user_department"]),
                    country=str(raw_item["user_country"]),
                ),
                filters=SearchFilters(),
            )
            raw_judgments = raw_item["relevance_judgments"]
            if not isinstance(raw_judgments, list):
                continue
            judgments: dict[str, int] = {}
            for raw_judgment in raw_judgments:
                if not isinstance(raw_judgment, dict):
                    continue
                judgments[str(raw_judgment["document_id"])] = int(raw_judgment["grade"])

            comparison = await service.compare(query)
            for name, result in (
                ("classic", comparison.classic),
                ("semantic", comparison.semantic),
            ):
                ranked = [hit.document_id for hit in result.hits]
                per_engine[name].append(
                    {
                        "recall": recall_at_k(ranked, judgments, k),
                        "mrr": reciprocal_rank(ranked, judgments),
                        "ndcg": ndcg_at_k(ranked, judgments, k),
                        "latency_ms": result.latency_ms,
                    }
                )

    summary: dict[str, Any] = {}
    for name, rows in per_engine.items():
        summary[name] = {
            "queries": len(rows),
            f"recall@{k}": statistics.fmean(row["recall"] for row in rows) if rows else 0.0,
            "mrr": statistics.fmean(row["mrr"] for row in rows) if rows else 0.0,
            f"ndcg@{k}": statistics.fmean(row["ndcg"] for row in rows) if rows else 0.0,
            "p50_latency_ms": statistics.median(row["latency_ms"] for row in rows)
            if rows
            else 0.0,
            "p95_latency_ms": sorted(row["latency_ms"] for row in rows)[
                max(0, math.ceil(len(rows) * 0.95) - 1)
            ]
            if rows
            else 0.0,
        }
    return summary
