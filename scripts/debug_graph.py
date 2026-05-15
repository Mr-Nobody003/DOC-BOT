"""
Run the medical evidence graph against several queries (one checkpoint thread each).

Usage from repo root:
  set PYTHONPATH=%CD%
  python scripts/debug_graph.py
"""

from __future__ import annotations

import asyncio
import uuid

from backend.graph.builder import build_medical_evidence_graph


QUERIES = [
    "What are established first-line treatments for glioblastoma multiforme?",
    "Does low-dose aspirin reduce major cardiovascular events in primary prevention cohorts?",
    "Are there any studies on the efficacy of clofoctol for bacterial infections?",
    "What is the capital of France?",
    "what is the differential diagnostic of a patient complains of fatigue and low energy ?",
    "What are the Symptoms of Malaria ?"
]


async def _stream_until_done(graph, state_input, config):
    last: dict = {}
    async for update in graph.astream(state_input, config=config):
        if not isinstance(update, dict):
            continue
        for _node_name, node_state in update.items():
            if isinstance(node_state, dict):
                last.update(node_state)
    return last


async def run_one(graph, query: str, idx: int, *, timeout_s: float) -> dict:
    """Fresh thread_id per query so checkpoint state does not leak across runs."""
    thread_id = f"debug-{idx}-{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": thread_id}}
    state_input = {
        "query": query,
        "session_id": thread_id,
        "trace_id": f"trace-{idx}",
        "graph_run_id": f"run-{idx}",
    }
    try:
        return await asyncio.wait_for(
            _stream_until_done(graph, state_input, config), timeout=timeout_s
        )
    except asyncio.TimeoutError:
        return {
            "final_response": (
                f"[debug_graph timeout after {timeout_s}s — "
                "try larger timeout, check OpenRouter/network, or resume a clarification interrupt]"
            ),
            "evidence_sufficient": None,
            "cache_hit": None,
            "confidence_score": None,
            "citations": [],
        }


async def main() -> None:
    print("Running medical graph (fresh compile per query to avoid cancelled-stream issues)...\n")

    for i, q in enumerate(QUERIES):
        graph = build_medical_evidence_graph()
        print("=" * 60)
        print(f"QUERY [{i + 1}/{len(QUERIES)}]: {q!r}")
        print("=" * 60)
        try:
            # First cold run can exceed a few minutes (model download + MeSH + retrieval).
            timeout = 900.0 if i == 0 else 420.0
            final = await run_one(graph, q, i, timeout_s=timeout)
            fr = (final.get("final_response") or "").strip()
            print(f"evidence_sufficient: {final.get('evidence_sufficient')}")
            print(f"cache_hit: {final.get('cache_hit')}")
            print(f"confidence_score: {final.get('confidence_score')}")
            print(f"citations (count): {len(final.get('citations') or [])}")
            preview = (fr[:1200] + "…") if len(fr) > 1200 else fr
            print(f"\n--- final_response ({len(fr)} chars) ---\n{preview}\n")
        except Exception as e:
            print(f"ERROR: {type(e).__name__}: {e}\n")


if __name__ == "__main__":
    asyncio.run(main())
