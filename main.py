import os
import click
from utils import logger, setup_logging
from config import get_settings
from ingestion import DocumentIngestor
from chunking import Chunker
from embeddings import EmbeddingService
from vectorstore import VectorStore
from retrieval import Retriever
from llm import LLMService
from rag import RAGPipeline

@click.group()
def cli():
    """LightRAG CLI - A lightweight, configurable RAG system."""
    setup_logging()

@cli.command()
@click.option('--path', required=True, help='Path to the PDF file or directory.')
@click.option('--output', default='storage', help='Directory to save the vector store.')
@click.option('--chunk-size', default=500, help='Chunk size in characters.')
@click.option('--overlap', default=100, help='Chunk overlap in characters.')
def ingest(path, output, chunk_size, overlap):
    """Ingest documents and create a vector store."""
    settings = get_settings()
    
    # 1. Ingest
    ingestor = DocumentIngestor()
    docs = ingestor.ingest(path)
    if not docs:
        logger.error("No documents ingested.")
        return

    # 2. Chunk
    chunker = Chunker(chunk_size=chunk_size, chunk_overlap=overlap)
    chunks = chunker.split(docs)

    # 3. Embed
    embed_svc = EmbeddingService(settings.embedding)
    logger.info("Embedding chunks...")
    texts = [c.text for c in chunks]
    embeddings = embed_svc.embed(texts)

    # 4. Store
    dimension = len(embeddings[0])
    store = VectorStore(dimension)
    store.add(chunks, embeddings)
    store.save(output)
    logger.info(f"Ingestion complete. Vector store saved to {output}")

@cli.command()
@click.option('--query', 'question', required=True, help='Question to ask.')
@click.option('--store-path', default='storage', help='Path to the vector store.')
@click.option('--k', default=5, help='Number of chunks to retrieve.')
def query(question, store_path, k):
    """Query the RAG system."""
    settings = get_settings()
    
    if not os.path.exists(store_path):
        logger.error(f"Store path not found: {store_path}")
        return

    # 1. Load Services
    embed_svc = EmbeddingService(settings.embedding)
    store = VectorStore.load(store_path)
    llm_svc = LLMService(settings.llm)
    
    # 2. Setup Pipeline
    retriever = Retriever(embed_svc, store)
    pipeline = RAGPipeline(retriever, llm_svc)
    
    # 3. Run Query
    answer = pipeline.query(question, k=k)
    print("\n--- ANSWER ---")
    print(answer)
    print("--------------\n")

if __name__ == '__main__':
    cli()
