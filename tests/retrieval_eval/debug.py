import asyncio
print("Debug start")
from backend.retrieval.hybrid_search import HybridRetriever
print("Imports done")

async def main():
    print("Initializing retriever...")
    retriever = HybridRetriever()
    print("Retriever initialized. Embedding query...")
    q = await retriever.embedder.embed_query("test query")
    print(f"Query embedded, len: {len(q)}. Querying qdrant...")
    results = await retriever.store.client.query_points(
        collection_name=retriever.store.collection_name,
        query=q,
        limit=1
    )
    print("Qdrant responded!")
    print(results)

if __name__ == "__main__":
    asyncio.run(main())
