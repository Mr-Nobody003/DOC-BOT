"""Health endpoints for API and dependencies."""

from fastapi import APIRouter

from backend.db.postgres import check_postgres
from backend.db.minio import check_minio
from backend.db.qdrant import get_qdrant_client

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    return {"status": "healthy"}


@router.get("/health/db")
async def health_db():
    ok = await check_postgres()
    return {"postgres": "ok" if ok else "error"}


@router.get("/health/vector")
async def health_vector():
    try:
        client = get_qdrant_client()
        await client.get_collections()
        return {"qdrant": "ok"}
    except Exception as e:
        return {"qdrant": "error", "detail": str(e)}


@router.get("/health/object")
async def health_object():
    ok = await check_minio()
    return {"minio": "ok" if ok else "error"}
