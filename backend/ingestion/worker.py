"""ARQ worker for PubMed ingestion and embedding."""

from urllib.parse import urlparse

from arq.connections import RedisSettings

from backend.core.config import get_settings
from backend.ingestion.pubmed import PubMedFetcher
from backend.retrieval.chunking import MedicalChunker
from backend.retrieval.embeddings import EmbeddingService
from backend.retrieval.qdrant_store import QdrantStore


def _redis_settings() -> RedisSettings:
    url = get_settings().redis_url
    u = urlparse(url)
    path = (u.path or "").strip("/")
    database = int(path.split("/")[0]) if path.isdigit() else 0
    return RedisSettings(
        host=u.hostname or "localhost",
        port=u.port or 6379,
        username=u.username,
        password=u.password,
        database=database,
        ssl=(u.scheme == "rediss"),
    )


async def ingest_pubmed_query(ctx, query: str, max_articles: int = 25) -> dict:
    fetcher = PubMedFetcher()
    pmids = await fetcher.fetch_pmids(query, max_results=max_articles)
    articles = await fetcher.fetch_abstracts(pmids)
    chunker = MedicalChunker()
    chunks = chunker.chunk_articles(articles)
    embedder = EmbeddingService()
    texts = [c["chunk_text"] for c in chunks]
    if not texts:
        return {"status": "empty", "query": query}
    vectors = await embedder.embed_texts(texts)
    for c, v in zip(chunks, vectors, strict=True):
        c["embedding"] = v
    store = QdrantStore()
    await store.initialize_collection()
    await store.insert_chunks(chunks)
    return {"status": "ok", "query": query, "chunks": len(chunks)}


class WorkerSettings:
    functions = [ingest_pubmed_query]
    redis_settings = _redis_settings()
