from backend.core.constants import FALLBACK_NO_EVIDENCE
from backend.graph.state import MedicalGraphState


async def insufficient_evidence_node(state: MedicalGraphState) -> dict:
    return {
        "final_response": FALLBACK_NO_EVIDENCE,
        "citations": [],
        "validated_claims": [],
        "confidence_score": 0.0,
    }
