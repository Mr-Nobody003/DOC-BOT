from backend.graph.state import MedicalGraphState
from backend.validation.evidence_validator import assess_evidence


async def evidence_validation_node(state: MedicalGraphState) -> dict:
    chunks = list(state.get("reranked_docs") or state.get("retrieved_docs") or [])
    result = assess_evidence(chunks)
    return {
        "evidence_sufficient": result["evidence_sufficient"],
        "evidence_quality": result["evidence_quality"],
        "confidence_score": result["confidence_score"],
    }
