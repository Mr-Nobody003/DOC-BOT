import asyncio
import os
from backend.graph.state import MedicalGraphState
from backend.retrieval.live_search import search_wikipedia, search_pubmed_journals


def _dense_retrieval_enabled() -> bool:
    enabled = os.getenv("DOCBOT_ENABLE_DENSE_RETRIEVAL", "").lower()
    if enabled in {"1", "true", "yes", "on"}:
        return True
    if os.getenv("VERCEL"):
        return False
    return True


async def _safe_dense_retrieve(
    query: str,
    *,
    evidence_types: list[str] | None,
    publication_year_min: int | None,
) -> tuple[list[dict], str | None]:
    if not _dense_retrieval_enabled():
        return [], "Dense retrieval disabled in Vercel serverless runtime"

    try:
        from backend.retrieval.hybrid_search import HybridRetriever

        retriever = HybridRetriever()
        await asyncio.wait_for(retriever.store.initialize_collection(), timeout=5)
        docs = await asyncio.wait_for(
            retriever.retrieve(
                query,
                top_k=24,
                evidence_types=evidence_types,
                publication_year_min=publication_year_min,
            ),
            timeout=10,
        )
        return docs, None
    except Exception as exc:
        return [], f"Dense retrieval failed: {type(exc).__name__}: {exc}"


async def _safe_live_retrieve(name: str, coro, timeout: int) -> tuple[list[dict], str | None]:
    try:
        docs = await asyncio.wait_for(coro, timeout=timeout)
        return docs if isinstance(docs, list) else [], None
    except Exception as exc:
        return [], f"{name} retrieval failed: {type(exc).__name__}: {exc}"


async def retrieval_agent_node(state: MedicalGraphState) -> dict:
    plan = state.get("retrieval_plan") or {}
    q = plan.get("primary_query") or state.get("clarified_query") or state.get("query", "")
    et = plan.get("required_source_types") or None
    if et == []:
        et = None
    pub_year_min = plan.get("publication_year_min")
    
    # Launch all retrievals concurrently
    qdrant_task = _safe_dense_retrieve(
        q,
        evidence_types=et,
        publication_year_min=pub_year_min,
    )
    wiki_task = _safe_live_retrieve("Wikipedia", search_wikipedia(q, max_results=2), 6)
    pubmed_task = _safe_live_retrieve("PubMed", search_pubmed_journals(q, max_results=4), 8)
    
    results = await asyncio.gather(qdrant_task, wiki_task, pubmed_task)
    
    docs = []
    errors = []
    for source_docs, source_error in results:
        docs.extend(source_docs)
        if source_error:
            errors.append(source_error)
        
    patch = {"retrieved_docs": docs}
    if errors:
        patch["retrieval_errors"] = errors
    return patch
