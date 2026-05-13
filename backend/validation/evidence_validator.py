"""Deterministic evidence sufficiency scoring."""

from statistics import mean
from typing import Any

from backend.core.config import get_settings


def assess_evidence(chunks: list[dict[str, Any]]) -> dict[str, Any]:
    settings = get_settings()
    if not chunks:
        return {
            "evidence_sufficient": False,
            "evidence_quality": "insufficient",
            "confidence_score": 0.0,
        }
    scores = [float(c.get("score", 0.0)) for c in chunks]
    avg = mean(scores) if scores else 0.0
    sufficient = len(chunks) >= settings.evidence_min_chunks and avg >= settings.evidence_min_avg_score
    if sufficient and avg >= 0.72:
        quality = "high"
    elif sufficient:
        quality = "moderate"
    elif len(chunks) == 0:
        quality = "insufficient"
    else:
        quality = "low"
    conf = min(1.0, max(0.0, avg * (len(chunks) / max(settings.evidence_min_chunks, 1))))
    return {
        "evidence_sufficient": sufficient,
        "evidence_quality": quality,
        "confidence_score": conf,
    }
