from typing import List
from utils import Document, logger

class Chunker:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into overlapping chunks.
        """
        all_chunks = []
        for doc in documents:
            text = doc.text
            metadata = doc.metadata
            
            # Simple character-based splitting
            start = 0
            while start < len(text):
                end = start + self.chunk_size
                chunk_text = text[start:end]
                
                chunk_doc = Document(
                    text=chunk_text,
                    metadata=metadata.copy() # Inherit metadata
                )
                all_chunks.append(chunk_doc)
                
                if end >= len(text):
                    break
                start += (self.chunk_size - self.chunk_overlap)
        
        logger.info(f"Split {len(documents)} docs into {len(all_chunks)} chunks")
        return all_chunks
