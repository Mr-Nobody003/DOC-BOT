import asyncio

from backend.retrieval.hybrid_search import HybridRetriever
from tests.retrieval_eval.metrics import precision_at_k, recall_at_k

# Simple evaluation harness
EVAL_QUERIES = [
    {
        "query": "What are the latest treatments for glioblastoma?",
        "expected_pmids": [] # Would be populated manually after initial ingestion for ground truth
    },
    {
        "query": "Does aspirin prevent cardiovascular events in healthy adults?",
        "expected_pmids": []
    }
]

async def run_evaluation():
    print("Starting Retrieval Evaluation Harness...\n")
    retriever = HybridRetriever()
    
    for idx, test_case in enumerate(EVAL_QUERIES):
        query = test_case["query"]
        expected = set(test_case["expected_pmids"])
        print(f"--- Test Case {idx + 1} ---")
        print(f"Query: {query}")
        
        try:
            # Retrieve top 5 chunks
            results = await retriever.retrieve(query, top_k=5)
            
            retrieved_pmids = [res["metadata"]["pmid"] for res in results]
            retrieved_set = set(retrieved_pmids)

            print("Retrieved PMIDs:")
            for rank, res in enumerate(results, 1):
                pmid = res["metadata"].get("pmid")
                score = res["score"]
                chunk_preview = (res.get("page_content") or "")[:100].replace("\n", " ")
                print(f"  {rank}. PMID: {pmid} | Score: {score:.4f} | Chunk: {chunk_preview}...")

            if expected:
                r5 = recall_at_k(retrieved_pmids, expected, k=5)
                p5 = precision_at_k(retrieved_pmids, expected, k=5)
                print(f"Recall@5: {r5:.2f} | Precision@5: {p5:.2f}")
            else:
                print("No expected PMIDs provided. Please manually verify relevance.")
                
        except Exception as e:
            print(f"Retrieval failed: {str(e)}")
        print("\n")

if __name__ == "__main__":
    asyncio.run(run_evaluation())
