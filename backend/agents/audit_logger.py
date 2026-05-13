import hashlib

from backend.graph.state import MedicalGraphState
from backend.models.audit import MedicalAuditLog


async def audit_logger_node(state: MedicalGraphState) -> dict:
    chunks = list(state.get("reranked_docs") or state.get("retrieved_docs") or [])
    text = state.get("final_response") or ""
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()
    audit = MedicalAuditLog.build(
        session_id=state.get("session_id", ""),
        trace_id=state.get("trace_id", ""),
        graph_run_id=state.get("graph_run_id", ""),
        query=state.get("clarified_query") or state.get("query", ""),
        chunks=chunks,
        validation_result=str(state.get("evidence_quality", "")),
        confidence_score=float(state.get("confidence_score") or 0.0),
        citations=list(state.get("citations") or []),
        response_hash=h,
    )
    return {"audit_log": audit.model_dump()}
