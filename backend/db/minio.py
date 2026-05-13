import asyncio

from minio import Minio

from backend.core.config import get_settings

_client: Minio | None = None


def get_minio_client() -> Minio:
    global _client
    if _client is None:
        settings = get_settings()
        _client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_use_ssl,
        )
    return _client


async def check_minio() -> bool:
    try:
        return await asyncio.to_thread(lambda: bool(get_minio_client().list_buckets()))
    except Exception:
        return False
