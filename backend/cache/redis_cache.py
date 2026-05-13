"""Redis-backed response cache for identical evidence queries."""

import hashlib
import json
from typing import Any, Optional

from backend.core.config import get_settings
from backend.core.constants import CACHE_KEY_PREFIX
from backend.db.redis import get_redis


def _cache_key(
    query: str,
    mesh_terms: list[str],
    *,
    intent: str = "",
    search_queries: Optional[list[str]] = None,
) -> str:
    sq = "|".join(sorted(s.strip().lower() for s in (search_queries or []) if s))
    mesh = "|".join(sorted(mesh_terms))
    base = f"q:{query.strip().lower()}|intent:{intent}|mesh:{mesh}|sq:{sq}".encode("utf-8")
    digest = hashlib.sha256(base).hexdigest()
    return f"{CACHE_KEY_PREFIX}:{digest}"


async def get_cached_response(
    query: str,
    mesh_terms: list[str],
    *,
    intent: str = "",
    search_queries: Optional[list[str]] = None,
) -> Optional[dict[str, Any]]:
    settings = get_settings()
    if not settings.redis_url:
        return None
    key = _cache_key(query, mesh_terms, intent=intent, search_queries=search_queries)
    r = get_redis()
    raw = await r.get(key)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


async def set_cached_response(
    query: str,
    mesh_terms: list[str],
    payload: dict[str, Any],
    *,
    intent: str = "",
    search_queries: Optional[list[str]] = None,
    ttl_seconds: int = 3600,
) -> None:
    settings = get_settings()
    if not settings.redis_url:
        return
    key = _cache_key(query, mesh_terms, intent=intent, search_queries=search_queries)
    r = get_redis()
    await r.set(key, json.dumps(payload), ex=ttl_seconds)
