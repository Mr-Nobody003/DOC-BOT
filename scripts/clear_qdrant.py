import asyncio
import logging
from qdrant_client import AsyncQdrantClient

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def clear_qdrant_collections():
    # Load configuration
    from backend.core.config import get_settings
    settings = get_settings()

    if not settings.qdrant_client_api_endpoint or not settings.qdrant_client_api_key:
        logger.error("Missing Qdrant Cloud credentials in .env")
        return

    logger.info(f"Connecting to Qdrant Cloud at: {settings.qdrant_client_api_endpoint}")
    
    # Initialize client
    client = AsyncQdrantClient(
        url=settings.qdrant_client_api_endpoint,
        api_key=settings.qdrant_client_api_key,
        timeout=30
    )

    try:
        # Get existing collections
        collections_response = await client.get_collections()
        collections = collections_response.collections
        
        if not collections:
            logger.info("No collections found in Qdrant. It is already clear.")
            return

        for collection in collections:
            logger.info(f"Deleting collection: {collection.name}")
            await client.delete_collection(collection_name=collection.name)
            logger.info(f"Successfully deleted collection: {collection.name}")
            
        logger.info("All collections have been cleared.")
        
    except Exception as e:
        logger.error(f"Failed to clear collections: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(clear_qdrant_collections())
