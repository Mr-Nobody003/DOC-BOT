from langchain_core.messages import HumanMessage, SystemMessage

from backend.core.config import get_settings
from backend.graph.state import MedicalGraphState
from backend.llm.provider import get_llm_provider
from backend.models.schemas import RetrievalPlan


async def retrieval_planner_node(state: MedicalGraphState) -> dict:
    q = (state.get("clarified_query") or state.get("query") or "").strip()
    settings = get_settings()

    if settings.openrouter_api_key:
        try:
            provider = get_llm_provider("openrouter", settings.llm_model_query)
            model = provider.get_model(0.0)
            structured = model.with_structured_output(RetrievalPlan)
            sys = SystemMessage(
                content=(
                    "Plan PubMed/Qdrant retrieval. Prefer precise clinical phrasing. "
                    "Respect evidence policy: no diagnosis, only evidence search planning."
                )
            )
            hum = HumanMessage(
                content=(
                    f"Primary query:\n{q}\n"
                    f"MeSH hints: {', '.join(state.get('mesh_terms') or [])}\n"
                )
            )
            plan: RetrievalPlan = await structured.ainvoke([sys, hum])
            pub_year_min = None
            if plan.temporal_filter_years:
                from datetime import datetime, timezone

                pub_year_min = datetime.now(timezone.utc).year - int(plan.temporal_filter_years)
            return {
                "retrieval_plan": {
                    "primary_query": plan.search_queries[0] if plan.search_queries else q,
                    "search_queries": plan.search_queries or [q],
                    "publication_year_min": pub_year_min,
                    "required_source_types": plan.required_source_types or [],
                }
            }
        except Exception:
            pass

    return {
        "retrieval_plan": {
            "primary_query": q,
            "search_queries": [q],
            "publication_year_min": None,
            "required_source_types": [],
        }
    }
