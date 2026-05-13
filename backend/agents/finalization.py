from backend.cache.redis_cache import set_cached_response
from backend.core.constants import MEDICAL_DISCLAIMER
from backend.graph.state import MedicalGraphState


async def append_disclaimer_node(state: MedicalGraphState) -> dict:
    text = state.get("final_response") or ""
    if MEDICAL_DISCLAIMER not in text:
        text = text + "\n\n" + MEDICAL_DISCLAIMER
    return {"final_response": text}


async def cache_store_node(state: MedicalGraphState) -> dict:
    if state.get("cache_hit"):
        return {}

    # Skip caching if we fell back to "I don't know" or evidence was insufficient
    final_response = state.get("final_response", "")
    if "I don't know based on the available evidence" in final_response:
        return {}
    if not state.get("evidence_sufficient", True):
        return {}

    q = (state.get("clarified_query") or state.get("query") or "").strip()
    mesh = state.get("mesh_terms") or []
    intent = str(state.get("intent") or "")
    search_queries = state.get("search_queries") or []
    payload = {
        "final_response": state.get("final_response", ""),
        "citations": state.get("citations", []),
        "confidence_score": float(state.get("confidence_score") or 0.0),
        "evidence_quality": state.get("evidence_quality", ""),
    }
    await set_cached_response(
        q,
        mesh,
        payload,
        intent=intent,
        search_queries=search_queries,
        ttl_seconds=7200,
    )
    return {}
