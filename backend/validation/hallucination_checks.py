"""Lightweight post-generation checks (deterministic)."""

from typing import Any

from backend.core.constants import FALLBACK_NO_EVIDENCE


def claims_supported_minimal(
    response_text: str, chunks: list[dict[str, Any]]
) -> tuple[bool, list[dict[str, Any]]]:
    """Heuristic: ensure non-trivial overlap between response tokens and evidence."""
    if not response_text or response_text.strip() == FALLBACK_NO_EVIDENCE:
        return True, []
    blob = " ".join(
        (c.get("text") or c.get("page_content", "")).lower() for c in chunks
    )
    words = [w for w in response_text.lower().split() if len(w) > 6]
    hits = 0
    for w in words[:40]:
        if w in blob:
            hits += 1
    ok = hits >= max(2, min(4, len(words) // 8 + 1))
    detail = [
        {"claim": "lexical_overlap", "supported": ok, "citation": "", "confidence": hits / max(len(words), 1)}
    ]
    return ok, detail


def second_pass_ok(
    response_text: str, validated_claims: list[dict[str, Any]], min_conf: float
) -> bool:
    if not validated_claims:
        return True
    for c in validated_claims:
        if not c.get("supported", False):
            return False
        if float(c.get("confidence", 0.0)) < min_conf:
            return False
    return True
