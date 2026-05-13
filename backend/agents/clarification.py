from langgraph.types import interrupt

from backend.graph.state import MedicalGraphState


async def clarification_node(state: MedicalGraphState) -> dict:
    if not state.get("requires_clarification"):
        return {"clarification_loop": False}

    prompt = state.get("clarification_prompt") or (
        "Your question looks underspecified for safe evidence retrieval. "
        "Please restate it with condition, intervention, and outcome if possible."
    )
    user_reply = interrupt({"type": "clarification", "prompt": prompt})
    if isinstance(user_reply, dict):
        text = str(user_reply.get("text") or user_reply.get("message") or user_reply).strip()
    else:
        text = str(user_reply).strip()
    return {
        "query": text,
        "clarified_query": text,
        "requires_clarification": False,
        "clarification_loop": True,
    }
