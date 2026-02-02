import os
import pickle
from typing import List, Tuple
import numpy as np
import faiss
from utils import Document, logger

class VectorStore:
    def __init__(self, dimension: int):
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.documents: List[Document] = []
        self.embeddings: List[List[float]] = []

    def add(self, documents: List[Document], embeddings: List[List[float]]):
        if not documents:
            return
        
        # Convert embeddings to numpy array
        embeddings_np = np.array(embeddings).astype('float32')
        self.index.add(embeddings_np)
        self.documents.extend(documents)
        self.embeddings.extend(embeddings)
        logger.info(f"Added {len(documents)} documents to vector store")

    def query(self, query_embedding: List[float], k: int = 5, allowed_sources: List[str] = None, collection: str = None) -> List[Document]:
        if not self.documents:
            return []
            
        query_np = np.array([query_embedding]).astype('float32')
        
        # If no filter, just do a normal search
        if not allowed_sources and not collection:
            distances, indices = self.index.search(query_np, k)
            results = []
            for idx in indices[0]:
                if idx != -1 and idx < len(self.documents):
                    results.append(self.documents[idx])
            return results

        # If filter is provided, we search for more items and filter them
        search_k = min(len(self.documents), k * 10)
        distances, indices = self.index.search(query_np, search_k)
        
        results = []
        for idx in indices[0]:
            if idx == -1 or idx >= len(self.documents):
                continue
            
            doc = self.documents[idx]
            match = False
            
            # Logic: If collection 'xyz' is active, search 'pdf_upload' OR 'xyz'
            # Base Knowledge (pdf_upload) is ALWAYS queried
            doc_source = doc.metadata.get("source")
            doc_collection = doc.metadata.get("collection")
            
            if doc_source == "pdf_upload":
                match = True
            elif collection and doc_collection == collection:
                match = True
            
            if match:
                results.append(doc)
                if len(results) >= k:
                    break
        
        return results

    def delete_by_metadata(self, key: str, value: str):
        """Remove documents that match a metadata key/value pair and rebuild index."""
        indices_to_keep = [
            i for i, doc in enumerate(self.documents) 
            if doc.metadata.get(key) != value
        ]
        
        if len(indices_to_keep) == len(self.documents):
            return # Nothing to delete

        logger.info(f"Deleting documents where {key}={value}. Total chunks: {len(self.documents)} -> {len(indices_to_keep)}")
        
        # Filter docs and embeddings
        self.documents = [self.documents[i] for i in indices_to_keep]
        self.embeddings = [self.embeddings[i] for i in indices_to_keep]
        
        # Rebuild index
        self.index = faiss.IndexFlatL2(self.dimension)
        if self.embeddings:
            embeddings_np = np.array(self.embeddings).astype('float32')
            self.index.add(embeddings_np)

    def save(self, path: str):
        """Save index, documents, and embeddings to disk."""
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
            
        faiss.write_index(self.index, os.path.join(path, "index.faiss"))
        state = {
            "documents": self.documents,
            "embeddings": self.embeddings,
            "dimension": self.dimension
        }
        with open(os.path.join(path, "store.pkl"), "wb") as f:
            pickle.dump(state, f)
        logger.info(f"Vector store saved to {path}")

    @classmethod
    def load(cls, path: str) -> 'VectorStore':
        """Load from disk."""
        with open(os.path.join(path, "store.pkl"), "rb") as f:
            state = pickle.load(f)
            
        instance = cls(state["dimension"])
        instance.index = faiss.read_index(os.path.join(path, "index.faiss"))
        instance.documents = state["documents"]
        instance.embeddings = state["embeddings"]
        
        logger.info(f"Vector store loaded from {path} with {len(instance.documents)} documents")
        return instance
