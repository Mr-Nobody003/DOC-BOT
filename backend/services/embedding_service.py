from backend.retrieval.embeddings import EmbeddingService as _EmbeddingService


class EmbeddingService:
    """Thin facade over fastembed-backed embedding service."""

    def __init__(self) -> None:
        self._inner = _EmbeddingService()

    async def embed_query(self, text: str) -> list[float]:
        return await self._inner.embed_query(text)

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return await self._inner.embed_texts(texts)
