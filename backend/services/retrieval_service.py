from typing import Any, Optional

from backend.retrieval.hybrid_search import HybridRetriever


class RetrievalService:
    def __init__(self) -> None:
        self._retriever = HybridRetriever()

    async def search(
        self,
        query: str,
        top_k: int = 8,
        *,
        evidence_types: Optional[list[str]] = None,
        publication_year_min: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        return await self._retriever.retrieve(
            query,
            top_k=top_k,
            evidence_types=evidence_types,
            publication_year_min=publication_year_min,
        )
