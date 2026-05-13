from backend.cache.redis_cache import get_cached_response
from backend.graph.state import MedicalGraphState


async def redis_cache_check_node(state: MedicalGraphState) -> dict:
    q = (state.get("clarified_query") or state.get("query") or "").strip()
    mesh = state.get("mesh_terms") or []
    intent = str(state.get("intent") or "")
    search_queries = state.get("search_queries") or []
    cached = await get_cached_response(
        q, mesh, intent=intent, search_queries=search_queries
    )
    if cached:
        return {
            "cache_hit": True,
            "final_response": cached.get("final_response", ""),
            "citations": cached.get("citations", []),
            "confidence_score": float(cached.get("confidence_score", 0.0)),
            "evidence_quality": cached.get("evidence_quality", "cached"),
        }
    return {"cache_hit": False}
