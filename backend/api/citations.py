from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["citations"])


@router.get("/citations/{pmid}")
async def get_citation(pmid: str):
    if not pmid.isdigit():
        raise HTTPException(status_code=400, detail="pmid must be numeric")
    url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
    return {
        "pmid": pmid,
        "pubmed_url": url,
        "eutils_link": f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={pmid}&retmode=xml",
    }
