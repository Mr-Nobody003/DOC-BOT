from typing import Dict, Any
from backend.graph.state import GroundedGraphState
from backend.retrieval.hybrid_search import HybridRetriever
from backend.agents.response import ResponseSynthesizer

async def retrieve_node(state: GroundedGraphState) -> Dict[str, Any]:
    """Retrieves chunks from Qdrant using HybridSearch."""
    query = state["query"]
    retriever = HybridRetriever()
    
    # Initialize store connection (this is a no-op if already initialized)
    await retriever.store.initialize_collection()
    
    # Fetch top 5 chunks
    chunks = await retriever.retrieve(query, top_k=5)
    return {"retrieved_chunks": chunks}

async def validate_node(state: GroundedGraphState) -> Dict[str, Any]:
    """Deterministic validation: ensures we have enough good evidence."""
    chunks = state.get("retrieved_chunks", [])
    
    if len(chunks) < 2:
        return {"is_valid": False}
        
    avg_score = sum(c.get("score", 0) for c in chunks) / len(chunks)
    
    # Threshold for bge-large-en is typically around 0.65 for decent semantic similarity
    if avg_score < 0.65:
        return {"is_valid": False}
        
    return {"is_valid": True}

async def generate_node(state: GroundedGraphState) -> Dict[str, Any]:
    """Generates the response using strict grounding rules."""
    query = state["query"]
    chunks = state["retrieved_chunks"]
    
    synthesizer = ResponseSynthesizer()
    response_text = await synthesizer.synthesize(query, chunks)
    
    return {"generation": response_text}

async def citation_node(state: GroundedGraphState) -> Dict[str, Any]:
    """Extracts metadata to map citations to the generation."""
    chunks = state.get("retrieved_chunks", [])
    
    # Simple mapping of citations used (in Phase 4 we just attach them all)
    citations = []
    for chunk in chunks:
        meta = chunk.get("metadata", {})
        citations.append({
            "pmid": meta.get("pmid"),
            "doi": meta.get("doi"),
            "title": meta.get("title")
        })
        
    # Deduplicate citations by PMID
    unique_citations = {c["pmid"]: c for c in citations if c.get("pmid")}.values()
    
    return {"citations": list(unique_citations)}
