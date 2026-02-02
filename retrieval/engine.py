from typing import List
from embeddings import EmbeddingService
from vectorstore.faiss_store import VectorStore
from utils import Document, logger

class Retriever:
    def __init__(self, embedding_service: EmbeddingService, vector_store: VectorStore):
        self.embedding_service = embedding_service
        self.vector_store = vector_store

    def retrieve(self, query: str, k: int = 5, collection: str = None) -> List[Document]:
        logger.info(f"Retrieving context for query: {query} with collection: {collection}")
        query_embedding = self.embedding_service.embed([query])[0]
        return self.vector_store.query(query_embedding, k=k, collection=collection)
