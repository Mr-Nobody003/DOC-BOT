import os
import asyncio
from pathlib import Path
from typing import List

from fastembed import TextEmbedding


def _default_cache_dir() -> str | None:
    configured = os.getenv("FASTEMBED_CACHE_DIR")
    if configured:
        Path(configured).mkdir(parents=True, exist_ok=True)
        return configured
    if os.getenv("VERCEL"):
        cache_dir = "/tmp/fastembed-cache"
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        return cache_dir
    return None


class EmbeddingService:
    def __init__(self, model_name: str = "BAAI/bge-large-en-v1.5"):
        # We use BAAI/bge-large-en-v1.5 via FastEmbed for lightweight ONNX execution
        self.model = TextEmbedding(
            model_name=model_name,
            cache_dir=_default_cache_dir(),
            cuda=False,
            threads=1 if os.getenv("VERCEL") else None,
            lazy_load=True,
        )
        
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Embeds a list of texts into vectors.
        """
        embeddings = await asyncio.to_thread(lambda: list(self.model.embed(texts)))
        return [emb.tolist() for emb in embeddings]
        
    async def embed_query(self, query: str) -> List[float]:
        """
        Embeds a search query.
        """
        prefix = "Represent this sentence for searching relevant passages: "
        query_with_prefix = prefix + query
        embedding = await asyncio.to_thread(
            lambda: list(self.model.embed([query_with_prefix]))[0]
        )
        return embedding.tolist()
