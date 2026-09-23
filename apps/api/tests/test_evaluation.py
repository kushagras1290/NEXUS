from nexus_api.evaluation import ndcg_at_k, recall_at_k, reciprocal_rank


def test_retrieval_metrics() -> None:
    judgments = {"A": 3, "B": 2, "C": 0}
    ranked = ["X", "B", "A"]
    assert recall_at_k(ranked, judgments, 3) == 1.0
    assert reciprocal_rank(ranked, judgments) == 0.5
    assert 0 < ndcg_at_k(ranked, judgments, 3) < 1
