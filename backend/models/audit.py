from datetime import datetime, timezone
from typing import Any, List

from pydantic import BaseModel, Field


class MedicalAuditLog(BaseModel):
    session_id: str = ""
    trace_id: str = ""
    graph_run_id: str = ""
    query: str = ""
    retrieved_doc_ids: List[str] = Field(default_factory=list)
    retrieval_scores: List[float] = Field(default_factory=list)
    validation_result: str = ""
    confidence_score: float = 0.0
    citations: List[dict[str, Any]] = Field(default_factory=list)
    response_hash: str = ""
    timestamp: str = ""

    @classmethod
    def build(
        cls,
        *,
        session_id: str,
        trace_id: str,
        graph_run_id: str,
        query: str,
        chunks: list[dict[str, Any]],
        validation_result: str,
        confidence_score: float,
        citations: list[dict[str, Any]],
        response_hash: str,
    ) -> "MedicalAuditLog":
        ids: list[str] = []
        scores: list[float] = []
        for c in chunks:
            ids.append(str(c.get("id", "")))
            scores.append(float(c.get("score", 0.0)))
        return cls(
            session_id=session_id,
            trace_id=trace_id,
            graph_run_id=graph_run_id,
            query=query,
            retrieved_doc_ids=ids,
            retrieval_scores=scores,
            validation_result=validation_result,
            confidence_score=confidence_score,
            citations=citations,
            response_hash=response_hash,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
