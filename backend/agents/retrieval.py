import asyncio
import os
import logging
from backend.graph.state import MedicalGraphState
from backend.retrieval.live_search import search_wikipedia, search_pubmed_journals

logger = logging.getLogger(__name__)

def _dense_retrieval_enabled() -> bool:
    """Check if dense (Qdrant) retrieval is enabled."""
    enabled = os.getenv("DOCBOT_ENABLE_DENSE_RETRIEVAL", "").lower()
    if enabled in {"1", "true", "yes", "on"}:
        return True
    if enabled in {"0", "false", "no", "off"}:
        return False
    # Default: enable if not on Vercel (serverless has time constraints)
    return not os.getenv("VERCEL")


async def _safe_dense_retrieve(
    query: str,
    *,
    evidence_types: list[str] | None,
    publication_year_min: int | None,
) -> tuple[list[dict], str | None]:
    """Safely retrieve from Qdrant with shorter timeouts for Vercel compatibility."""
    if not _dense_retrieval_enabled():
        return [], "Dense retrieval disabled"

    try:
        from backend.retrieval.hybrid_search import HybridRetriever

        retriever = HybridRetriever()
        
        # Initialize collection with shorter timeout (Qdrant Cloud may be slow)
        await asyncio.wait_for(retriever.store.initialize_collection(), timeout=8)
        
        # Retrieve with aggressive timeout (leave buffer for other operations)
        docs = await asyncio.wait_for(
            retriever.retrieve(
                query,
                top_k=12,  # Reduced from 24 to save time
                evidence_types=evidence_types,
                publication_year_min=publication_year_min,
            ),
            timeout=50,  # Increased to utilize maximum Vercel limit
        )
        logger.info(f"Dense retrieval: found {len(docs)} docs")
        return docs, None
    except asyncio.TimeoutError:
        logger.warning(f"Dense retrieval timed out (>25s)")
        return [], "Dense retrieval timeout - Qdrant Cloud response slow"
    except Exception as exc:
        logger.warning(f"Dense retrieval failed: {type(exc).__name__}: {exc}")
        return [], f"Dense retrieval failed: {type(exc).__name__}"


async def _safe_live_retrieve(name: str, coro, timeout: int) -> tuple[list[dict], str | None]:
    """Safely retrieve from live sources (Wikipedia, PubMed) with timeout."""
    try:
        docs = await asyncio.wait_for(coro, timeout=timeout)
        result = docs if isinstance(docs, list) else []
        logger.info(f"{name} retrieval: found {len(result)} docs")
        return result, None
    except asyncio.TimeoutError:
        logger.warning(f"{name} retrieval timed out (>{timeout}s)")
        return [], f"{name} retrieval timeout"
    except Exception as exc:
        logger.warning(f"{name} retrieval failed: {type(exc).__name__}: {exc}")
        return [], f"{name} retrieval failed: {type(exc).__name__}"


async def retrieval_agent_node(state: MedicalGraphState) -> dict:
    """Retrieve evidence from multiple sources concurrently."""
    plan = state.get("retrieval_plan") or {}
    q = plan.get("primary_query") or state.get("clarified_query") or state.get("query", "")
    et = plan.get("required_source_types") or None
    if et == []:
        et = None
    pub_year_min = plan.get("publication_year_min")
    
    # Launch all retrievals concurrently (with increased timeouts for comprehensive search)
    qdrant_task = _safe_dense_retrieve(
        q,
        evidence_types=et,
        publication_year_min=pub_year_min,
    )
    wiki_task = _safe_live_retrieve("Wikipedia", search_wikipedia(q, max_results=2), 20)
    pubmed_task = _safe_live_retrieve("PubMed", search_pubmed_journals(q, max_results=8), 45)
    
    results = await asyncio.gather(qdrant_task, wiki_task, pubmed_task)
    
    docs = []
    errors = []
    for source_docs, source_error in results:
        docs.extend(source_docs)
        if source_error:
            errors.append(source_error)
    
    logger.info(f"Total retrieved: {len(docs)} docs from {len(results)} sources")
    
    patch = {"retrieved_docs": docs}
    if errors and not docs:
        patch["retrieval_errors"] = errors
    return patch
