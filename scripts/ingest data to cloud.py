# scripts/ingest_to_qdrant_cloud.py
import asyncio
from backend.ingestion.pubmed import PubMedFetcher
from backend.retrieval.qdrant_store import QdrantStore
from backend.retrieval.embeddings import EmbeddingService

async def ingest_pubmed_to_cloud():
    # Initialize
    fetcher = PubMedFetcher()
    store = QdrantStore()
    embedder = EmbeddingService()
    
    # Create collection on cloud
    await store.initialize_collection()
    
    # Search and ingest
    query = "cancer treatment clinical trials"
    pmids = await fetcher.fetch_pmids(query, max_results=100)
    articles = await fetcher.fetch_abstracts(pmids)
    
    # Chunk and embed
    chunks = []
    for article in articles:
        text = f"{article.get('title', '')} {article.get('abstract', '')}"
        # Split into chunks (implement chunking logic)
        embedded = await embedder.embed_text(text)
        chunks.append({
            "text": text,
            "embedding": embedded,
            "metadata": article
        })
    
    # Insert to cloud
    await store.insert_chunks(chunks)
    print(f"Ingested {len(chunks)} chunks to Qdrant Cloud")

if __name__ == "__main__":
    asyncio.run(ingest_pubmed_to_cloud())