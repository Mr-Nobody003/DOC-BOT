from fastembed import TextEmbedding
from typing import List

class EmbeddingService:
    def __init__(self, model_name: str = "BAAI/bge-large-en-v1.5"):
        # We use BAAI/bge-large-en-v1.5 via FastEmbed for lightweight ONNX execution
        self.model = TextEmbedding(model_name=model_name)
        
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Embeds a list of texts into vectors.
        """
        embeddings = list(self.model.embed(texts))
        return [emb.tolist() for emb in embeddings]
        
    async def embed_query(self, query: str) -> List[float]:
        """
        Embeds a search query.
        """
        prefix = "Represent this sentence for searching relevant passages: "
        query_with_prefix = prefix + query
        embedding = list(self.model.embed([query_with_prefix]))[0]
        return embedding.tolist()
