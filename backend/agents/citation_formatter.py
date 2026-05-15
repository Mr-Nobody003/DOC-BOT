from backend.core.constants import FALLBACK_NO_EVIDENCE, MEDICAL_DISCLAIMER
from backend.graph.state import MedicalGraphState


async def citation_formatter_node(state: MedicalGraphState) -> dict:
    fr = (state.get("final_response") or "").strip()
    if fr.startswith(FALLBACK_NO_EVIDENCE):
        if state.get("cache_hit") and MEDICAL_DISCLAIMER not in fr:
            fr = fr + "\n\n" + MEDICAL_DISCLAIMER
        return {"citations": [], "final_response": fr}

    citations = list(state.get("citations") or [])
    if not citations:
        for c in state.get("reranked_docs") or []:
            meta = dict(c.get("metadata") or {})
            pmid = meta.get("pmid")
            if not pmid:
                continue
            citations.append(
                {
                    "pmid": str(pmid),
                    "doi": meta.get("doi"),
                    "title": meta.get("title"),
                    "url": meta.get("url")
                    or meta.get("source_url")
                    or f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                }
            )

    seen: set[str] = set()
    uniq = []
    for c in citations:
        key = str(c.get("pmid", c.get("url", "")))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(c)

    if fr and not fr.startswith(FALLBACK_NO_EVIDENCE) and uniq:
        lines = []
        for i, c in enumerate(uniq, start=1):
            title = c.get("title") or ""
            url = c.get("url") or ""
            pmid = c.get("pmid") or ""
            lines.append(f"[{i}] {title} — PMID: {pmid} — {url}")
        fr = fr + "\n\nReferences:\n" + "\n".join(lines)

    if state.get("cache_hit"):
        if MEDICAL_DISCLAIMER not in fr:
            fr = fr + "\n\n" + MEDICAL_DISCLAIMER

    return {"citations": uniq, "final_response": fr}
