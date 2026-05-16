#!/usr/bin/env python3
"""
Ingestion script for Qdrant Cloud.
Handles batch embedding, chunking, and efficient cloud insertion.
"""
import asyncio
import sys
import os
from pathlib import Path
from typing import List, Dict, Any
import uuid
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from backend.ingestion.pubmed import PubMedFetcher
from backend.retrieval.chunking import MedicalChunker
from backend.retrieval.embeddings import EmbeddingService
from backend.retrieval.qdrant_store import QdrantStore
from backend.core.config import get_settings


async def ingest_pubmed_to_qdrant_cloud(
    query: str = "clinical trials cancer treatment",
    max_pmids: int = 50,
    batch_size: int = 10,
) -> None:
    """
    Ingest PubMed articles into Qdrant Cloud with batch processing.
    
    Args:
        query: Search query for PubMed
        max_pmids: Maximum number of articles to fetch
        batch_size: Number of chunks to embed/insert at once
    """
    settings = get_settings()
    
    # Verify Qdrant Cloud credentials
    if not settings.qdrant_client_api_endpoint or not settings.qdrant_client_api_key:
        logger.error("❌ Missing Qdrant Cloud credentials!")
        logger.error("   Set QDRANT_CLIENT_API_ENDPOINT and QDRANT_CLIENT_API_KEY in .env")
        sys.exit(1)
    
    logger.info(f"🔍 Qdrant Cloud Endpoint: {settings.qdrant_client_api_endpoint}")
    
    # Initialize services
    fetcher = PubMedFetcher()
    store = QdrantStore()
    embedder = EmbeddingService()
    chunker = MedicalChunker(chunk_size=800, chunk_overlap=100)
    
    try:
        # Step 1: Create collection on Qdrant Cloud
        logger.info("📋 Creating/initializing collection...")
        await store.initialize_collection()
        logger.info(f"✅ Collection '{store.collection_name}' ready")
        
        # Step 2: Fetch articles from PubMed
        logger.info(f"📚 Fetching articles for query: '{query}'")
        pmids = await fetcher.fetch_pmids(query, max_results=max_pmids)
        logger.info(f"✅ Found {len(pmids)} articles")
        
        if not pmids:
            logger.warning("⚠️  No articles found. Skipping ingestion.")
            return
        
        # Step 3: Fetch full articles
        logger.info("📖 Fetching full articles with abstracts...")
        articles = await fetcher.fetch_abstracts(pmids)
        logger.info(f"✅ Retrieved {len(articles)} full articles")
        
        # Step 4: Chunk articles
        logger.info("✂️  Chunking articles...")
        chunks = chunker.chunk_articles(articles)
        logger.info(f"✅ Created {len(chunks)} chunks")
        
        if not chunks:
            logger.warning("⚠️  No chunks created. Exiting.")
            return
        
        # Step 5: Batch embed and insert
        logger.info(f"🧠 Batch embedding and inserting (batch_size={batch_size})...")
        total_inserted = 0
        
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i : i + batch_size]
            batch_num = i // batch_size + 1
            
            try:
                # Extract texts and embed
                texts = [chunk["chunk_text"] for chunk in batch_chunks]
                logger.info(f"   Batch {batch_num}: Embedding {len(texts)} chunks...")
                embeddings = await embedder.embed_texts(texts)
                
                # Prepare points for Qdrant (use deterministic integer IDs)
                for chunk, embedding in zip(batch_chunks, embeddings):
                    chunk["embedding"] = embedding
                
                # Insert batch
                logger.info(f"   Batch {batch_num}: Inserting to Qdrant Cloud...")
                await store.insert_chunks(batch_chunks)
                total_inserted += len(batch_chunks)
                logger.info(f"   ✅ Batch {batch_num} done ({total_inserted}/{len(chunks)} total)")
                
            except Exception as e:
                logger.error(f"   ❌ Batch {batch_num} failed: {e}")
                raise
        
        logger.info(f"\n✨ Ingestion complete! {total_inserted} chunks inserted to Qdrant Cloud")
        
    except Exception as e:
        logger.error(f"❌ Ingestion failed: {e}", exc_info=True)
        sys.exit(1)


async def ingest_multiple_queries(queries: List[str], max_pmids_per_query: int = 30) -> None:
    """
    Ingest articles from multiple search queries.
    """
    for query in queries:
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing query: {query}")
        logger.info(f"{'='*60}")
        await ingest_pubmed_to_qdrant_cloud(query=query, max_pmids=max_pmids_per_query)
        await asyncio.sleep(1)  # Small delay between queries to avoid rate limiting


# Comprehensive medical queries covering ~80% of common medical questions
# Optimized for 1GB Qdrant Cloud storage (20-25 articles per query)
MEDICAL_QUERIES_COMPREHENSIVE = [
    # Oncology (6 queries)
    "cancer treatment clinical trials",
    "chemotherapy adverse effects",
    "immunotherapy cancer",
    "radiation therapy side effects",
    "glioblastoma multiforme therapy",
    "lung cancer treatment",
    
    # Cardiology (6 queries)
    "cardiovascular disease prevention",
    "heart failure management",
    "hypertension treatment",
    "atrial fibrillation therapy",
    "coronary artery disease",
    "myocardial infarction management",
    
    # Endocrinology (5 queries)
    "diabetes management therapy",
    "type 2 diabetes treatment",
    "insulin resistance",
    "thyroid disease treatment",
    "obesity management interventions",
    
    # Infectious Diseases (5 queries)
    "bacterial infection antibiotics",
    "viral infection treatment",
    "antibiotic resistance management",
    "COVID-19 clinical management",
    "sepsis treatment protocols",
    
    # Neurology (5 queries)
    "Alzheimer's disease treatment",
    "Parkinson's disease management",
    "migraine prevention therapy",
    "epilepsy seizure control",
    "stroke rehabilitation therapy",
    
    # Rheumatology (4 queries)
    "rheumatoid arthritis treatment",
    "systemic lupus erythematosus management",
    "osteoarthritis therapy",
    "gout management treatment",
    
    # Gastroenterology (4 queries)
    "inflammatory bowel disease treatment",
    "Crohn's disease management",
    "ulcerative colitis therapy",
    "gastric ulcer treatment",
    
    # Pulmonology (4 queries)
    "chronic obstructive pulmonary disease",
    "asthma control therapy",
    "pulmonary fibrosis treatment",
    "sleep apnea management",
    
    # Nephrology (3 queries)
    "chronic kidney disease management",
    "acute kidney injury treatment",
    "hypertension in renal disease",
    
    # Psychiatry (4 queries)
    "depression treatment therapy",
    "anxiety disorder management",
    "bipolar disorder treatment",
    "schizophrenia antipsychotic therapy",
    
    # Pain Management (3 queries)
    "chronic pain management",
    "fibromyalgia treatment",
    "neuropathic pain therapy",
    
    # General (2 queries)
    "fever management treatment",
    "antibiotic prophylaxis guidelines",
]


if __name__ == "__main__":
    import os
    
    # Single query from command line
    if len(sys.argv) > 1:
        if sys.argv[1].lower() == "all":
            # Ingest all comprehensive queries
            logger.info(f"🚀 Starting comprehensive ingestion ({len(MEDICAL_QUERIES_COMPREHENSIVE)} queries)...")
            asyncio.run(ingest_multiple_queries(MEDICAL_QUERIES_COMPREHENSIVE, max_pmids_per_query=20))
        elif sys.argv[1].lower() == "core":
            # Ingest only core queries (faster)
            core_queries = MEDICAL_QUERIES_COMPREHENSIVE[:15]
            logger.info(f"🚀 Starting core ingestion ({len(core_queries)} queries)...")
            asyncio.run(ingest_multiple_queries(core_queries, max_pmids_per_query=20))
        else:
            # Single custom query
            query = " ".join(sys.argv[1:])
            asyncio.run(ingest_pubmed_to_qdrant_cloud(query=query, max_pmids=50))
    else:
        # Default: ingest comprehensive queries
        logger.info(f"🚀 Starting comprehensive ingestion ({len(MEDICAL_QUERIES_COMPREHENSIVE)} queries)...")
        logger.info("💡 Usage:")
        logger.info("  python ingest_qdrant_cloud.py all          # Ingest all medical queries")
        logger.info("  python ingest_qdrant_cloud.py core         # Ingest core queries only")
        logger.info("  python ingest_qdrant_cloud.py 'your query' # Ingest custom query")
        logger.info("")
        asyncio.run(ingest_multiple_queries(MEDICAL_QUERIES_COMPREHENSIVE, max_pmids_per_query=20))
