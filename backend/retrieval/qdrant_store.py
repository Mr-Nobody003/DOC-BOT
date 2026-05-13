from typing import Any, Dict, List

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models

from backend.core.config import get_settings
from backend.db.qdrant import get_qdrant_client


class QdrantStore:
    def __init__(self, collection_name: str | None = None):
        settings = get_settings()
        self.collection_name = collection_name or settings.qdrant_collection
        self.client: AsyncQdrantClient = get_qdrant_client()
        # BAAI/bge-large-en-v1.5 has 1024 dimensions
        self.vector_size = 1024
        
    async def initialize_collection(self):
        """Creates the Qdrant collection if it doesn't exist."""
        collections = await self.client.get_collections()
        exists = any(c.name == self.collection_name for c in collections.collections)
        
        if not exists:
            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.vector_size,
                    distance=models.Distance.COSINE
                )
            )
            # Create payload indices for fast filtering
            await self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="pmid",
                field_schema=models.PayloadSchemaType.KEYWORD
            )
            await self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="evidence_type",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
            await self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="publication_year",
                field_schema=models.PayloadSchemaType.INTEGER,
            )

    async def insert_chunks(self, chunks: List[Dict[str, Any]]):
        """Inserts embedded chunks into Qdrant."""
        if not chunks:
            return
            
        points = []
        for chunk in chunks:
            # We assume embedding is already added to the chunk dict
            embedding = chunk.pop("embedding", [])
            chunk_id = chunk.pop("chunk_id") # We'll use this as the ID or generate a UUID
            
            # Qdrant requires IDs to be integers or UUIDs.
            # We'll generate a UUID based on the chunk_id hash
            import uuid
            point_id = str(uuid.uuid5(uuid.NAMESPACE_OID, chunk_id))
            
            points.append(
                models.PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=chunk
                )
            )
            
        await self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
