import asyncio

from qdrant_client import AsyncQdrantClient

from backend.core.config import get_settings

_clients: dict[int | None, AsyncQdrantClient] = {}


def _current_loop_id() -> int | None:
    try:
        return id(asyncio.get_running_loop())
    except RuntimeError:
        return None


def get_qdrant_client() -> AsyncQdrantClient:
    loop_id = _current_loop_id()
    client = _clients.get(loop_id)
    if client is None:
        settings = get_settings()
        if settings.qdrant_client_api_endpoint and settings.qdrant_client_api_key:
            client = AsyncQdrantClient(
                url=settings.qdrant_client_api_endpoint,
                api_key=settings.qdrant_client_api_key,
                timeout=30,
            )
        else:
            client = AsyncQdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port,
                timeout=30,
            )
        _clients[loop_id] = client
    return client
