from typing import Any, Dict, List
import hashlib

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models

from backend.core.config import get_settings
from backend.db.qdrant import get_qdrant_client


class QdrantStore:
    def __init__(self, collection_name: str | None = None):
        settings = get_settings()
        self.collection_name = collection_name or settings.qdrant_collection
        self._client: AsyncQdrantClient | None = None
        # BAAI/bge-large-en-v1.5 has 1024 dimensions
        self.vector_size = 1024
    
    async def _get_client(self) -> AsyncQdrantClient:
        """Get or lazily initialize the Qdrant client."""
        if self._client is None:
            self._client = await get_qdrant_client()
        return self._client
        
    async def initialize_collection(self):
        """Creates the Qdrant collection if it doesn't exist."""
        client = await self._get_client()
        collections = await client.get_collections()
        exists = any(c.name == self.collection_name for c in collections.collections)
        
        if not exists:
            await client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.vector_size,
                    distance=models.Distance.COSINE
                )
            )
            # Create payload indices for fast filtering
            await client.create_payload_index(
                collection_name=self.collection_name,
                field_name="pmid",
                field_schema=models.PayloadSchemaType.KEYWORD
            )
            await client.create_payload_index(
                collection_name=self.collection_name,
                field_name="evidence_type",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
            await client.create_payload_index(
                collection_name=self.collection_name,
                field_name="publication_year",
                field_schema=models.PayloadSchemaType.INTEGER,
            )

    async def insert_chunks(self, chunks: List[Dict[str, Any]]):
        """Inserts embedded chunks into Qdrant."""
        if not chunks:
            return
        
        client = await self._get_client()
        points = []
        for chunk in chunks:
            # Extract embedding and chunk_id
            embedding = chunk.pop("embedding", [])
            chunk_id = chunk.pop("chunk_id", "")
            
            # Convert chunk_id to deterministic integer ID (fast, efficient)
            # Use first 8 bytes of MD5 hash as unsigned 64-bit integer
            hash_obj = hashlib.md5(chunk_id.encode())
            point_id = int.from_bytes(hash_obj.digest()[:8], byteorder='big', signed=False)
            
            # Keep chunk_id in payload for reference
            chunk["chunk_id"] = chunk_id
            
            points.append(
                models.PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=chunk
                )
            )
            
        await client.upsert(
            collection_name=self.collection_name,
            points=points
        )
