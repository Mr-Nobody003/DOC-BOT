"""Live web search module for Wikipedia and PubMed Journals."""

import asyncio
from typing import List, Dict

import wikipedia
from Bio import Entrez
import httpx

# Required by NCBI Entrez
Entrez.email = "docbot-research@example.com"
Entrez.tool = "DocBot Medical Evidence Retrieval"

async def search_wikipedia(query: str, max_results: int = 2) -> List[Dict]:
    """Search Wikipedia and return structured document chunks."""
    def _fetch():
        docs = []
        try:
            # Get top search results (truncate query to avoid 300 char limit)
            safe_query = query[:250]
            titles = wikipedia.search(safe_query, results=max_results)
            for title in titles:
                try:
                    page = wikipedia.page(title, auto_suggest=False)
                    # Use the summary as the text chunk
                    summary = page.summary
                    if summary:
                        docs.append({
                            "text": summary,
                            "score": 0.85,
                            "metadata": {
                                "source": "Wikipedia",
                                "title": page.title,
                                "url": page.url,
                                "pmid": "WIKI-" + title.replace(" ", "_")
                            }
                        })
                except wikipedia.exceptions.DisambiguationError as e:
                    # If disambiguation, try the first option
                    try:
                        if e.options:
                            page = wikipedia.page(e.options[0], auto_suggest=False)
                            if page.summary:
                                docs.append({
                                    "text": page.summary,
                                    "score": 0.85,
                                    "metadata": {
                                        "source": "Wikipedia",
                                        "title": page.title,
                                        "url": page.url,
                                        "pmid": "WIKI-" + page.title.replace(" ", "_")
                                    }
                                })
                    except Exception:
                        continue
                except Exception:
                    continue
        except Exception as e:
            print(f"Wikipedia search failed: {e}")
        return docs

    return await asyncio.to_thread(_fetch)

async def search_pubmed_journals(query: str, max_results: int = 5) -> List[Dict]:
    """Search specific elite medical journals on PubMed on the fly."""
    def _fetch():
        docs = []

        def _add_pubmed_docs(search_query: str, remaining: int) -> None:
            if remaining <= 0:
                return

            handle = Entrez.esearch(
                db="pubmed", term=search_query, retmax=remaining, sort="relevance"
            )
            record = Entrez.read(handle)
            handle.close()

            id_list = record.get("IdList", [])
            if not id_list:
                return

            seen_pmids = {
                str(doc.get("metadata", {}).get("pmid", "")) for doc in docs
            }
            new_ids = [pmid for pmid in id_list if str(pmid) not in seen_pmids]
            if not new_ids:
                return

            handle = Entrez.efetch(db="pubmed", id=",".join(new_ids), retmode="xml")
            papers = Entrez.read(handle)
            handle.close()

            for paper in papers.get("PubmedArticle", []):
                medline = paper.get("MedlineCitation", {})
                pmid = str(medline.get("PMID", ""))
                if pmid in seen_pmids:
                    continue
                article = medline.get("Article", {})
                title = article.get("ArticleTitle", "")

                abstract_texts = []
                abstract = article.get("Abstract", {})
                if "AbstractText" in abstract:
                    for text_part in abstract["AbstractText"]:
                        abstract_texts.append(str(text_part))

                abstract_str = " ".join(abstract_texts)
                if not abstract_str:
                    continue

                journal = article.get("Journal", {}).get("Title", "Unknown Journal")
                docs.append({
                    "text": abstract_str,
                    "score": 0.9 if "random" in abstract_str.lower() else 0.85,
                    "metadata": {
                        "source": f"PubMed - {journal}",
                        "title": title,
                        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                        "pmid": pmid
                    }
                })
                seen_pmids.add(pmid)
                if len(docs) >= max_results:
                    break

        try:
            # Construct a strict PubMed query targeting top journals
            elite_journals = [
                '"The Lancet"[Journal]',
                '"British Medical Journal"[Journal]',
                '"Nature"[Journal]',
                '"JAMA"[Journal]',
                '"New England Journal of Medicine"[Journal]'
            ]
            journal_filter = " OR ".join(elite_journals)
            full_query = f"({query}) AND ({journal_filter})"

            _add_pubmed_docs(full_query, max_results)
            if len(docs) < max_results:
                _add_pubmed_docs(query, max_results - len(docs))
        except Exception as e:
            print(f"PubMed live search failed: {e}")
        return docs

    return await asyncio.to_thread(_fetch)
