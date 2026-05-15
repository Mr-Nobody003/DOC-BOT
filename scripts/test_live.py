import asyncio
from backend.retrieval.live_search import search_wikipedia, search_pubmed_journals
import json

async def test():
    q = "Does low-dose aspirin reduce major cardiovascular events in primary prevention cohorts?"
    
    print("Fetching Wikipedia...")
    wiki = await search_wikipedia(q)
    print(f"Wiki returned {len(wiki)} docs")
    
    print("Fetching PubMed Journals...")
    pubmed = await search_pubmed_journals(q)
    print(f"PubMed returned {len(pubmed)} docs")
    
    print("\nPubMed Abstract snippet:")
    if pubmed:
        print(pubmed[0]['metadata']['title'])
        print(pubmed[0]['text'][:300] + "...")
        print(pubmed[0]['metadata']['url'])

if __name__ == "__main__":
    asyncio.run(test())
