"""LangGraph checkpointer factory (memory or Redis)."""

from typing import Any

from backend.core.config import get_settings


def get_checkpointer() -> Any:
    settings = get_settings()
    backend = (settings.checkpoint_backend or "memory").lower()
    if backend == "redis":
        from langgraph.checkpoint.redis import RedisSaver

        return RedisSaver(redis_url=settings.redis_url)
    from langgraph.checkpoint.memory import MemorySaver

    return MemorySaver()
