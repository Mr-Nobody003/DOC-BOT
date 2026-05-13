from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
import hashlib

class MedicalChunker:
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 100):
        # We use a smaller chunk size optimized for dense medical text
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            add_start_index=True,
            separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""]
        )

    def chunk_article(self, article: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Chunks an article's abstract into smaller pieces while preserving metadata
        and calculating exact character offsets for citation mapping.
        """
        chunks = []
        abstract_text = article.get("abstract", "")
        if not abstract_text:
            return chunks

        # Split text into chunks, adding the start index in metadata
        split_docs = self.text_splitter.create_documents([abstract_text])
        
        for i, doc in enumerate(split_docs):
            chunk_text = doc.page_content
            start_char = doc.metadata.get("start_index", 0)
            end_char = start_char + len(chunk_text)
            
            # Generate a deterministic chunk ID
            chunk_id_str = f"{article['pmid']}_{i}_{start_char}"
            chunk_id = hashlib.md5(chunk_id_str.encode()).hexdigest()

            pub_raw = article.get("publication_date", "") or ""
            pub_year: int | None = None
            if len(pub_raw) >= 4 and pub_raw[:4].isdigit():
                pub_year = int(pub_raw[:4])

            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "doc_id": article["pmid"],
                    "pmid": article["pmid"],
                    "title": article["title"],
                    "chunk_text": chunk_text,
                    "journal": article["journal"],
                    "publication_date": article["publication_date"],
                    "publication_year": pub_year,
                    "doi": article["doi"],
                    "source_url": article["source_url"],
                    "evidence_type": article["evidence_type"],
                    "start_char": start_char,
                    "end_char": end_char,
                }
            )
            
        return chunks

    def chunk_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Chunk a list of articles."""
        all_chunks = []
        for article in articles:
            all_chunks.extend(self.chunk_article(article))
        return all_chunks
