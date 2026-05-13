import httpx
import asyncio
from typing import List, Dict, Any
import xml.etree.ElementTree as ET
from datetime import datetime

class PubMedFetcher:
    def __init__(self):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        
    async def fetch_pmids(self, query: str, max_results: int = 50) -> List[str]:
        """Search PubMed for a query and return a list of PMIDs."""
        url = f"{self.base_url}/esearch.fcgi"
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("esearchresult", {}).get("idlist", [])

    async def fetch_abstracts(self, pmids: List[str]) -> List[Dict[str, Any]]:
        """Fetch full details (including abstracts) for a list of PMIDs."""
        if not pmids:
            return []
            
        url = f"{self.base_url}/efetch.fcgi"
        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return self._parse_pubmed_xml(response.text)

    def _parse_pubmed_xml(self, xml_string: str) -> List[Dict[str, Any]]:
        """Parse PubMed XML to extract relevant metadata and abstract text."""
        root = ET.fromstring(xml_string)
        articles = []
        
        for article in root.findall(".//PubmedArticle"):
            pmid_elem = article.find(".//PMID")
            pmid = pmid_elem.text if pmid_elem is not None else ""
            
            title_elem = article.find(".//ArticleTitle")
            title = title_elem.text if title_elem is not None else ""
            
            # Abstract might have multiple sections (Background, Methods, etc.)
            abstract_texts = []
            for abstract_text in article.findall(".//AbstractText"):
                if abstract_text.text:
                    label = abstract_text.get("Label", "")
                    text = abstract_text.text
                    if label:
                        abstract_texts.append(f"{label}: {text}")
                    else:
                        abstract_texts.append(text)
            
            abstract = " ".join(abstract_texts)
            
            # Journal info
            journal_elem = article.find(".//Journal/Title")
            journal = journal_elem.text if journal_elem is not None else ""
            
            # DOI
            doi = ""
            for eloc in article.findall(".//ELocationID"):
                if eloc.get("EIdType") == "doi":
                    doi = eloc.text
                    break
                    
            # Publication Date (Fallback to Year if full date not available)
            pub_date = ""
            pub_date_elem = article.find(".//PubDate")
            if pub_date_elem is not None:
                year = pub_date_elem.find("Year")
                month = pub_date_elem.find("Month")
                if year is not None:
                    pub_date = year.text
                    if month is not None:
                        pub_date += f"-{month.text}"
                        
            # If there's no abstract, we might skip it or keep it for title-only retrieval.
            # For this medical RAG, we prefer abstracts.
            if abstract:
                articles.append({
                    "pmid": pmid,
                    "title": title,
                    "abstract": abstract,
                    "journal": journal,
                    "publication_date": pub_date,
                    "doi": doi,
                    "source_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    "evidence_type": "pubmed_abstract" # Defaulting for now
                })
                
        return articles
