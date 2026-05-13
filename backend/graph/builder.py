"""Production LangGraph: medical evidence workflow with checkpointing."""

from langgraph.graph import END, StateGraph

from backend.agents.audit_logger import audit_logger_node
from backend.agents.cache_check import redis_cache_check_node
from backend.agents.citation_formatter import citation_formatter_node
from backend.agents.clarification import clarification_node
from backend.agents.finalization import append_disclaimer_node, cache_store_node
from backend.agents.generation_node import response_generation_node
from backend.agents.insufficient_evidence import insufficient_evidence_node
from backend.agents.mesh_translation import mesh_translation_node
from backend.agents.post_validation import second_validation_node
from backend.agents.query_understanding import query_understanding_node
from backend.agents.reranker import reranker_agent_node
from backend.agents.retrieval import retrieval_agent_node
from backend.agents.retrieval_planner import retrieval_planner_node
from backend.agents.validation import evidence_validation_node
from backend.graph.checkpoints import get_checkpointer
from backend.graph.state import MedicalGraphState


def _route_cache(state: MedicalGraphState) -> str:
    return "hit" if state.get("cache_hit") else "miss"


def _route_clarification(state: MedicalGraphState) -> str:
    return "loop" if state.get("clarification_loop") else "planner"


def _route_evidence(state: MedicalGraphState) -> str:
    return "sufficient" if state.get("evidence_sufficient") else "insufficient"


def _route_post_citation(state: MedicalGraphState) -> str:
    return "short_circuit" if state.get("cache_hit") else "full_tail"


def build_medical_evidence_graph():
    g = StateGraph(MedicalGraphState)

    g.add_node("query_understanding", query_understanding_node)
    g.add_node("mesh_translation", mesh_translation_node)
    g.add_node("redis_cache_check", redis_cache_check_node)
    g.add_node("clarification", clarification_node)
    g.add_node("retrieval_planner", retrieval_planner_node)
    g.add_node("retrieval", retrieval_agent_node)
    g.add_node("reranker", reranker_agent_node)
    g.add_node("evidence_validation", evidence_validation_node)
    g.add_node("insufficient_evidence", insufficient_evidence_node)
    g.add_node("response_generation", response_generation_node)
    g.add_node("second_validation", second_validation_node)
    g.add_node("citation_formatter", citation_formatter_node)
    g.add_node("audit_logging", audit_logger_node)
    g.add_node("append_disclaimer", append_disclaimer_node)
    g.add_node("cache_store", cache_store_node)

    g.set_entry_point("query_understanding")
    g.add_edge("query_understanding", "mesh_translation")
    g.add_edge("mesh_translation", "redis_cache_check")

    g.add_conditional_edges(
        "redis_cache_check",
        _route_cache,
        {"hit": "citation_formatter", "miss": "clarification"},
    )

    g.add_conditional_edges(
        "clarification",
        _route_clarification,
        {"loop": "query_understanding", "planner": "retrieval_planner"},
    )

    g.add_edge("retrieval_planner", "retrieval")
    g.add_edge("retrieval", "reranker")
    g.add_edge("reranker", "evidence_validation")

    g.add_conditional_edges(
        "evidence_validation",
        _route_evidence,
        {
            "sufficient": "response_generation",
            "insufficient": "insufficient_evidence",
        },
    )

    g.add_edge("insufficient_evidence", "citation_formatter")
    g.add_edge("response_generation", "second_validation")
    g.add_edge("second_validation", "citation_formatter")

    g.add_conditional_edges(
        "citation_formatter",
        _route_post_citation,
        {"short_circuit": END, "full_tail": "audit_logging"},
    )

    g.add_edge("audit_logging", "append_disclaimer")
    g.add_edge("append_disclaimer", "cache_store")
    g.add_edge("cache_store", END)

    checkpointer = get_checkpointer()
    return g.compile(checkpointer=checkpointer)


def build_graph():
    """Backwards-compatible alias."""
    return build_medical_evidence_graph()
