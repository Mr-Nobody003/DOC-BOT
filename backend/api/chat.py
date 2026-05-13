import json
import uuid
from collections.abc import AsyncGenerator
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field, model_validator
from langgraph.types import Command
from sse_starlette.sse import EventSourceResponse

from backend.core.security import sanitize_user_query
from backend.graph.builder import build_medical_evidence_graph

router = APIRouter(tags=["chat"])

_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_medical_evidence_graph()
    return _graph


class ChatRequest(BaseModel):
    query: str | None = Field(default=None, max_length=8000)
    session_id: str | None = Field(default=None, max_length=128)
    resume: str | dict | None = None

    @model_validator(mode="after")
    def validate_payload(self):
        if self.resume is None:
            if not (self.query or "").strip():
                raise ValueError("query is required unless resuming an interrupted graph")
        return self


async def event_generator(payload: ChatRequest) -> AsyncGenerator[dict, None]:
    graph = get_graph()
    session_id = payload.session_id or str(uuid.uuid4())
    config: dict[str, Any] = {"configurable": {"thread_id": session_id}}

    if payload.resume is not None:
        graph_input: Any = Command(resume=payload.resume)
    else:
        q = sanitize_user_query(payload.query or "")
        graph_input = {
            "session_id": session_id,
            "trace_id": str(uuid.uuid4()),
            "graph_run_id": str(uuid.uuid4()),
            "query": q,
        }

    try:
        async for update in graph.astream(graph_input, config=config):
            if not isinstance(update, dict):
                continue
            for node_name, node_state in update.items():
                if not isinstance(node_state, dict):
                    continue
                yield {
                    "event": "update",
                    "data": json.dumps(
                        {"node": node_name, "patch": node_state}, default=str
                    ),
                }
    except Exception as e:
        yield {"event": "error", "data": json.dumps({"detail": str(e)})}
    yield {"event": "end", "data": "{}"}


@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    return EventSourceResponse(event_generator(request))
