from backend.core.constants import FALLBACK_NO_EVIDENCE
from backend.graph.state import MedicalGraphState
from backend.validation.hallucination_checks import claims_supported_minimal


async def second_validation_node(state: MedicalGraphState) -> dict:
    text = (state.get("final_response") or "").strip()
    chunks = list(state.get("reranked_docs") or [])
    if text == FALLBACK_NO_EVIDENCE:
        return {"validated_claims": [], "unsupported_claims": []}
    if "no generative model is configured" in text:
        return {
            "validated_claims": [
                {
                    "claim": "extractive_evidence_only",
                    "supported": True,
                    "citation": "",
                    "confidence": 1.0,
                }
            ],
            "unsupported_claims": [],
        }
    ok, claims = claims_supported_minimal(text, chunks)
    if not ok:
        return {
            "final_response": FALLBACK_NO_EVIDENCE,
            "validated_claims": [],
            "unsupported_claims": claims,
            "citations": [],
        }
    return {"validated_claims": claims, "unsupported_claims": []}
