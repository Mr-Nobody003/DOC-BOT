import httpx

from backend.graph.state import MedicalGraphState


async def mesh_translation_node(state: MedicalGraphState) -> dict:
    terms: list[str] = []
    queries = state.get("search_queries") or [state.get("query", "")]
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

    async with httpx.AsyncClient(timeout=30.0) as client:
        for q in queries[:3]:
            if not q:
                continue
            try:
                r = await client.get(
                    url,
                    params={
                        "db": "mesh",
                        "term": q,
                        "retmax": "8",
                        "retmode": "json",
                    },
                )
                r.raise_for_status()
                data = r.json()
                idlist = data.get("esearchresult", {}).get("idlist", []) or []
                for uid in idlist[:5]:
                    terms.append(f"MESH:{uid}")
            except Exception:
                continue

    if not terms:
        terms = [f"TEXT:{q}" for q in queries if q][:5]

    return {"mesh_terms": terms[:12]}
