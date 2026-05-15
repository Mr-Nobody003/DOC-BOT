from qdrant_client import AsyncQdrantClient

from backend.core.config import get_settings

_client: AsyncQdrantClient | None = None


def get_qdrant_client() -> AsyncQdrantClient:
    global _client
    if _client is None:
        settings = get_settings()
        if settings.qdrant_client_api_endpoint and settings.qdrant_client_api_key:
            _client = AsyncQdrantClient(
                url=settings.qdrant_client_api_endpoint,
                api_key=settings.qdrant_client_api_key,
                timeout=30,
            )
        else:
            _client = AsyncQdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port,
                timeout=30,
            )
    return _client
