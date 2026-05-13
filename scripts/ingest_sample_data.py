import asyncio
from backend.ingestion.pubmed import PubMedFetcher
from backend.retrieval.chunking import MedicalChunker
from backend.retrieval.embeddings import EmbeddingService
from backend.retrieval.qdrant_store import QdrantStore

async def ingest_sample_data(query: str = "glioblastoma treatment", max_results: int = 20):
    print(f"Starting ingestion pipeline for query: '{query}'")
    
    # 1. Fetch from PubMed
    print("1. Fetching PMIDs...")
    fetcher = PubMedFetcher()
    pmids = await fetcher.fetch_pmids(query, max_results=max_results)
    print(f"Found {len(pmids)} PMIDs.")
    
    print("2. Fetching abstracts and metadata...")
    articles = await fetcher.fetch_abstracts(pmids)
    print(f"Successfully fetched {len(articles)} articles with abstracts.")
    
    # 2. Chunking
    print("3. Chunking articles with character spans...")
    chunker = MedicalChunker(chunk_size=800, chunk_overlap=100)
    chunks = chunker.chunk_articles(articles)
    print(f"Created {len(chunks)} chunks.")
    
    # 3. Embeddings
    print("4. Generating BAAI/bge-large-en-v1.5 embeddings...")
    embedder = EmbeddingService()
    # Extract texts for embedding
    chunk_texts = [c["chunk_text"] for c in chunks]
    embeddings = await embedder.embed_texts(chunk_texts)
    
    # Attach embeddings back to chunks
    for chunk, emb in zip(chunks, embeddings):
        chunk["embedding"] = emb
        
    # 4. Qdrant Storage
    print("5. Initializing Qdrant collection and storing vectors...")
    store = QdrantStore()
    await store.initialize_collection()
    await store.insert_chunks(chunks)
    
    print("Ingestion complete!")

if __name__ == "__main__":
    asyncio.run(ingest_sample_data())
