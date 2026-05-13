from backend.core.config import get_settings
from backend.core.constants import FALLBACK_NO_EVIDENCE
from backend.graph.state import MedicalGraphState
from backend.agents.response_generation import ResponseSynthesizer


async def response_generation_node(state: MedicalGraphState) -> dict:
    settings = get_settings()
    chunks = list(state.get("reranked_docs") or [])
    q = (state.get("clarified_query") or state.get("query") or "").strip()
    conf = float(state.get("confidence_score") or 0.0)
    if conf < settings.confidence_min_response:
        return {"final_response": FALLBACK_NO_EVIDENCE, "citations": []}
    synth = ResponseSynthesizer()
    text = await synth.synthesize(q, chunks)
    return {"final_response": text}
