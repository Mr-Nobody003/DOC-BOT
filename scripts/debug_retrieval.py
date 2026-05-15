import asyncio
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.retrieval.hybrid_search import HybridRetriever

async def debug_retrieval(query: str, top_k: int = 5):
    print(f"\n--- Debugging Retrieval for Query: '{query}' ---")
    retriever = HybridRetriever()
    
    # Initialize connection
    await retriever.store.initialize_collection()
    
    results = await retriever.retrieve(query, top_k=top_k)
    
    if not results:
        print("No results found.")
        return
        
    print(f"Found {len(results)} chunks.\n")
    
    for idx, res in enumerate(results):
        score = res.get("score", 0.0)
        metadata = res.get("metadata", {})
        text = res.get("text", "")
        
        pmid = metadata.get("pmid", "N/A")
        doi = metadata.get("doi", "N/A")
        pub_date = metadata.get("pub_date", "N/A")
        title = metadata.get("title", "N/A")
        
        print(f"[{idx+1}] Score: {score:.4f} | PMID: {pmid} | DOI: {doi} | Date: {pub_date}")
        print(f"Title: {title}")
        print(f"Chunk Span: {metadata.get('start_char')} - {metadata.get('end_char')}")
        print(f"Text Preview: {text[:250]}...\n")
        print("-" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Debug Retrieval Quality")
    parser.add_argument("query", type=str, help="Search query")
    parser.add_argument("--top-k", type=int, default=5, help="Number of chunks to retrieve")
    args = parser.parse_args()
    
    asyncio.run(debug_retrieval(args.query, args.top_k))
