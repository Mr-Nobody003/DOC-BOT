"""Typed graph state for medical evidence workflows."""

from typing import Any, List, NotRequired, Optional, TypedDict


class EvidenceChunk(TypedDict, total=False):
    """Serialized chunk stored in graph state (checkpoint-safe)."""

    id: str
    text: str
    page_content: NotRequired[str]
    metadata: dict[str, Any]
    score: float


class MedicalGraphState(TypedDict, total=False):
    session_id: str
    trace_id: str
    graph_run_id: str

    query: str
    clarified_query: NotRequired[str]

    intent: NotRequired[str]
    mesh_terms: NotRequired[List[str]]
    search_queries: NotRequired[List[str]]
    retrieval_plan: NotRequired[dict[str, Any]]

    retrieved_docs: NotRequired[List[EvidenceChunk]]
    reranked_docs: NotRequired[List[EvidenceChunk]]

    validated_claims: NotRequired[List[dict[str, Any]]]
    unsupported_claims: NotRequired[List[dict[str, Any]]]
    citations: NotRequired[List[dict[str, Any]]]

    confidence_score: NotRequired[float]
    evidence_quality: NotRequired[str]
    evidence_sufficient: NotRequired[bool]

    requires_clarification: NotRequired[bool]
    clarification_prompt: NotRequired[Optional[str]]

    final_response: NotRequired[str]
    cache_hit: NotRequired[bool]
    skip_to_citations: NotRequired[bool]
    clarification_loop: NotRequired[bool]
    audit_log: NotRequired[dict[str, Any]]


class GroundedGraphState(TypedDict, total=False):
    """Legacy minimal linear graph state."""

    query: str
    retrieved_chunks: List[dict[str, Any]]
    is_valid: bool
    generation: str
    citations: List[dict[str, Any]]
