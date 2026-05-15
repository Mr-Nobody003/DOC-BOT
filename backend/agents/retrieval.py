import asyncio
from backend.graph.state import MedicalGraphState
from backend.retrieval.hybrid_search import HybridRetriever
from backend.retrieval.live_search import search_wikipedia, search_pubmed_journals

async def retrieval_agent_node(state: MedicalGraphState) -> dict:
    plan = state.get("retrieval_plan") or {}
    q = plan.get("primary_query") or state.get("clarified_query") or state.get("query", "")
    et = plan.get("required_source_types") or None
    if et == []:
        et = None
    pub_year_min = plan.get("publication_year_min")

    retriever = HybridRetriever()
    await retriever.store.initialize_collection()
    
    # Launch all retrievals concurrently
    qdrant_task = retriever.retrieve(
        q,
        top_k=24,
        evidence_types=et,
        publication_year_min=pub_year_min,
    )
    wiki_task = search_wikipedia(q, max_results=2)
    pubmed_task = search_pubmed_journals(q, max_results=4)
    
    results = await asyncio.gather(qdrant_task, wiki_task, pubmed_task, return_exceptions=True)
    
    docs = []
    # Qdrant docs
    if isinstance(results[0], list):
        docs.extend(results[0])
    # Wikipedia docs
    if isinstance(results[1], list):
        docs.extend(results[1])
    # PubMed docs
    if isinstance(results[2], list):
        docs.extend(results[2])
        
    return {"retrieved_docs": docs}
