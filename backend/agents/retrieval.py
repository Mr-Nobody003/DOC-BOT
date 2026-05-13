from backend.graph.state import MedicalGraphState
from backend.retrieval.hybrid_search import HybridRetriever


async def retrieval_agent_node(state: MedicalGraphState) -> dict:
    plan = state.get("retrieval_plan") or {}
    q = plan.get("primary_query") or state.get("clarified_query") or state.get("query", "")
    et = plan.get("required_source_types") or None
    if et == []:
        et = None
    pub_year_min = plan.get("publication_year_min")

    retriever = HybridRetriever()
    await retriever.store.initialize_collection()
    docs = await retriever.retrieve(
        q,
        top_k=24,
        evidence_types=et,
        publication_year_min=pub_year_min,
    )
    return {"retrieved_docs": docs}
