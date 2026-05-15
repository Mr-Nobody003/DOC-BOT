import asyncio
import logging

from qdrant_client import AsyncQdrantClient

from backend.core.config import get_settings

logger = logging.getLogger(__name__)

# Global client cache per event loop
_clients: dict[int | None, AsyncQdrantClient] = {}
_lock = asyncio.Lock()


def _current_loop_id() -> int | None:
    """Get current event loop ID for per-loop client pooling."""
    try:
        return id(asyncio.get_running_loop())
    except RuntimeError:
        return None


async def get_qdrant_client() -> AsyncQdrantClient:
    """
    Get or create Qdrant client with connection pooling.
    Reuses client per event loop to avoid connection overhead.
    """
    loop_id = _current_loop_id()
    
    # Fast path: return cached client if available
    if loop_id in _clients:
        return _clients[loop_id]
    
    # Slow path: create new client (with lock to avoid duplicate creation)
    async with _lock:
        # Double-check after acquiring lock
        if loop_id in _clients:
            return _clients[loop_id]
        
        settings = get_settings()
        
        try:
            if settings.qdrant_client_api_endpoint and settings.qdrant_client_api_key:
                logger.info(f"Creating Qdrant Cloud client: {settings.qdrant_client_api_endpoint}")
                client = AsyncQdrantClient(
                    url=settings.qdrant_client_api_endpoint,
                    api_key=settings.qdrant_client_api_key,
                    timeout=30,
                    prefer_grpc=True,  # Use gRPC for better performance
                )
            else:
                logger.info(f"Creating local Qdrant client: {settings.qdrant_host}:{settings.qdrant_port}")
                client = AsyncQdrantClient(
                    host=settings.qdrant_host,
                    port=settings.qdrant_port,
                    timeout=30,
                    prefer_grpc=False,
                )
            
            _clients[loop_id] = client
            logger.info("Qdrant client created and cached")
            return client
            
        except Exception as e:
            logger.error(f"Failed to create Qdrant client: {e}")
            raise

