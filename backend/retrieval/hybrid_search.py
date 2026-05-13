from typing import Any, List, Optional

from qdrant_client.http import models as qmodels

from backend.retrieval.embeddings import EmbeddingService
from backend.retrieval.qdrant_store import QdrantStore
from backend.retrieval.reranking import score_pairs


def _lexical_anchor(
    query: str, docs: list[dict[str, Any]], *, min_hits: int = 2
) -> list[dict[str, Any]]:
    """Prefer chunks that share substantive tokens with the query (reduces off-topic dense hits)."""
    import re

    words = re.findall(r"[a-zA-Z]{4,}", (query or "").lower())
    if len(words) < 2:
        return docs
    keyset = set(words)
    anchored: list[dict[str, Any]] = []
    for d in docs:
        blob = (d.get("text") or d.get("page_content") or "").lower()
        hits = sum(1 for w in keyset if w in blob)
        if hits >= min_hits:
            anchored.append(d)
    if len(anchored) >= max(2, min(4, len(docs) // 2)):
        return anchored
    return docs


class HybridRetriever:
    """Dense retrieval with optional metadata / temporal filters."""

    def __init__(self, collection_name: str | None = None):
        self.store = QdrantStore(collection_name)
        self.embedder = EmbeddingService()

    def _build_filter(
        self,
        *,
        evidence_types: Optional[list[str]] = None,
        publication_year_min: Optional[int] = None,
    ) -> Optional[qmodels.Filter]:
        must: list[qmodels.FieldCondition] = []
        if evidence_types:
            must.append(
                qmodels.FieldCondition(
                    key="evidence_type",
                    match=qmodels.MatchAny(any=evidence_types),
                )
            )
        if publication_year_min is not None:
            must.append(
                qmodels.FieldCondition(
                    key="publication_year",
                    range=qmodels.Range(gte=publication_year_min),
                )
            )
        if not must:
            return None
        return qmodels.Filter(must=must)

    async def retrieve(
        self,
        query: str,
        top_k: int = 8,
        *,
        evidence_types: Optional[list[str]] = None,
        publication_year_min: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        query_vector = await self.embedder.embed_query(query)
        flt = self._build_filter(
            evidence_types=evidence_types, publication_year_min=publication_year_min
        )

        search_result = await self.store.client.query_points(
            collection_name=self.store.collection_name,
            query=query_vector,
            limit=max(top_k * 4, 16),
            with_payload=True,
            query_filter=flt,
        )

        retrieved_docs: list[dict[str, Any]] = []
        for scored_point in search_result.points or []:
            payload = dict(scored_point.payload or {})
            text = payload.get("chunk_text", "")
            retrieved_docs.append(
                {
                    "id": str(scored_point.id),
                    "score": float(scored_point.score or 0.0),
                    "metadata": payload,
                    "page_content": text,
                    "text": text,
                }
            )
        anchored = _lexical_anchor(query, retrieved_docs)
        if len(anchored) >= 2:
            retrieved_docs = anchored
        return retrieved_docs[:top_k]

    async def retrieve_and_rerank(
        self,
        query: str,
        *,
        top_k_dense: int = 20,
        top_k_final: int = 8,
        evidence_types: Optional[list[str]] = None,
        publication_year_min: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        docs = await self.retrieve(
            query,
            top_k=top_k_dense,
            evidence_types=evidence_types,
            publication_year_min=publication_year_min,
        )
        return await score_pairs(query, docs[:top_k_dense], top_k=top_k_final)
