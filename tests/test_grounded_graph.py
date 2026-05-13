import asyncio

import pytest

from backend.db.qdrant import get_qdrant_client
from backend.graph.state import GroundedGraphState
from backend.graph.workflow import build_grounded_workflow


def _qdrant_reachable() -> bool:
    async def _ping() -> None:
        client = get_qdrant_client()
        await asyncio.wait_for(client.get_collections(), timeout=2.0)

    try:
        asyncio.run(_ping())
        return True
    except Exception:
        return False


def test_workflow_smoke():
    if not _qdrant_reachable():
        pytest.skip("Qdrant is not reachable (start docker-compose for integration smoke test)")

    async def _run() -> list[str]:
        workflow = build_grounded_workflow()
        state: GroundedGraphState = {"query": "glioblastoma treatment"}
        nodes_seen: list[str] = []
        async for output in workflow.astream(state):
            for node_name, node_state in output.items():
                nodes_seen.append(node_name)
                if "generation" in node_state:
                    assert isinstance(node_state["generation"], str)
                if "is_valid" in node_state:
                    assert isinstance(node_state["is_valid"], bool)
                if "retrieved_chunks" in node_state:
                    assert isinstance(node_state["retrieved_chunks"], list)
        return nodes_seen

    nodes_seen = asyncio.run(_run())
    assert nodes_seen, "graph should emit at least one node"
