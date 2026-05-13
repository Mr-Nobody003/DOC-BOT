import json
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.db.postgres import get_postgres_pool

router = APIRouter(tags=["feedback"])


class FeedbackRequest(BaseModel):
    session_id: str = Field(..., min_length=4, max_length=128)
    trace_id: str = Field(..., min_length=4, max_length=128)
    rating: int = Field(ge=-1, le=1, description="-1 negative, 0 neutral, 1 positive")
    comment: str | None = Field(default=None, max_length=4000)


@router.post("/feedback")
async def submit_feedback(body: FeedbackRequest):
    try:
        pool = await get_postgres_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS medical_feedback (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    trace_id TEXT NOT NULL,
                    rating INT NOT NULL,
                    comment TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
                """
            )
            await conn.execute(
                """
                INSERT INTO medical_feedback (session_id, trace_id, rating, comment)
                VALUES ($1, $2, $3, $4);
                """,
                body.session_id,
                body.trace_id,
                body.rating,
                body.comment,
            )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"feedback_unavailable: {e}") from e
    return {"status": "accepted"}
