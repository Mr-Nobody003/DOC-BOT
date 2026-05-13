from backend.graph.state import MedicalGraphState
from backend.retrieval.reranking import score_pairs


async def reranker_agent_node(state: MedicalGraphState) -> dict:
    plan = state.get("retrieval_plan") or {}
    q = plan.get("primary_query") or state.get("clarified_query") or state.get("query", "")
    docs = list(state.get("retrieved_docs") or [])
    ranked = await score_pairs(q, docs, top_k=8)
    return {"reranked_docs": ranked}
