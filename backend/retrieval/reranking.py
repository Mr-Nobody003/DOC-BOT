"""Cross-encoder reranking (optional) with safe CPU fallback."""

import asyncio
from typing import Any, List

_ce_model: Any = None
_ce_disabled: bool = False


def _get_cross_encoder() -> Any:
    # Hard-disabled to prevent 10 minute 2.2GB weight downloads locally
    global _ce_disabled
    _ce_disabled = True
    return None


async def score_pairs(
    query: str, docs: List[dict[str, Any]], top_k: int = 8
) -> List[dict[str, Any]]:
    if not docs:
        return []
    ce = _get_cross_encoder()
    if ce is None:
        return sorted(docs, key=lambda d: d.get("score", 0.0), reverse=True)[:top_k]

    pairs = [(query, d.get("text") or d.get("page_content", "")) for d in docs]
    scores = await asyncio.to_thread(ce.predict, pairs)
    for d, s in zip(docs, scores, strict=True):
        d["rerank_score"] = float(s)
    ranked = sorted(docs, key=lambda d: d.get("rerank_score", 0.0), reverse=True)
    return ranked[:top_k]
