"""Retrieval evaluation metrics."""

from __future__ import annotations

from typing import Iterable


def recall_at_k(retrieved_pmids: Iterable[str], relevant_pmids: set[str], k: int = 5) -> float:
    top = list(retrieved_pmids)[:k]
    hits = relevant_pmids.intersection(top)
    if not relevant_pmids:
        return 0.0
    return len(hits) / len(relevant_pmids)


def precision_at_k(retrieved_pmids: Iterable[str], relevant_pmids: set[str], k: int = 5) -> float:
    top = list(retrieved_pmids)[:k]
    if not top:
        return 0.0
    hits = relevant_pmids.intersection(top)
    return len(hits) / min(k, len(top))
