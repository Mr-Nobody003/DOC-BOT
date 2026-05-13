import httpx


class MeshService:
    async def suggest_mesh(self, text: str, max_terms: int = 8) -> list[str]:
        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        terms: list[str] = []
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.get(
                url,
                params={"db": "mesh", "term": text, "retmax": str(max_terms), "retmode": "json"},
            )
            r.raise_for_status()
            data = r.json()
            for uid in (data.get("esearchresult", {}).get("idlist", []) or []):
                terms.append(f"MESH:{uid}")
        return terms
