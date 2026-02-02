import os
import shutil
import tempfile
import pickle
from typing import Optional, List
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, Header, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from utils import logger, setup_logging
from config import get_settings
from ingestion import DocumentIngestor
from chunking import Chunker
from embeddings import EmbeddingService
from vectorstore import VectorStore
from retrieval import Retriever
from llm import LLMService
from rag import RAGPipeline

app = FastAPI(title="LightRAG API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
setup_logging()

# Shared Services
settings = get_settings()
embed_svc = EmbeddingService(settings.embedding)
llm_svc = LLMService(settings.llm)
_store = None

def get_store() -> Optional[VectorStore]:
    global _store
    if _store is None:
        if os.path.exists(os.path.join(settings.vector_db_path, "store.pkl")):
            try:
                _store = VectorStore.load(settings.vector_db_path)
            except Exception as e:
                logger.error(f"Failed to load store: {e}")
    return _store

def verify_token(authorization: Optional[str] = Header(None)):
    if settings.api_token and authorization != f"Bearer {settings.api_token}":
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.get("/health")
def health():
    return {"status": "ok"}

class QueryRequest(BaseModel):
    query: str
    k: Optional[int] = 5
    collection: Optional[str] = None

@app.post("/query")
async def query_rag(request: Request, auth=Depends(verify_token)):
    # 1. Flexible Input Handling (JSON or Raw Text)
    k = 5
    collection = None
    content_type = request.headers.get("Content-Type", "")
    
    if "application/json" in content_type:
        try:
            data = await request.json()
            query_text = data.get("query", "")
            k = data.get("k", 5)
            collection = data.get("collection")
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON body")
    else:
        # Assume raw text if not JSON
        body = await request.body()
        query_text = body.decode("utf-8").strip()

    if not query_text:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # 2. Automatically wrap in braces if Sim Studio stripped them or sent raw
    processed_query = query_text
    if not (processed_query.startswith("{{") and processed_query.endswith("}}")):
        processed_query = f"{{{{{processed_query}}}}}"
    
    logger.info(f"Processing query: {processed_query} (Collection: {collection})")

    store = get_store()
    if not store:
        raise HTTPException(status_code=400, detail="Vector store is empty. Please ingest documents.")
    
    retriever = Retriever(embed_svc, store)
    pipeline = RAGPipeline(retriever, llm_svc)
    # The pipeline.query now handles the (pdf_upload OR collection) logic internally
    answer = pipeline.query(processed_query, k=k, collection=collection)
    return {"answer": answer}

@app.post("/ingest")
async def ingest_document(
    file: UploadFile = File(...), 
    document_id: str = Form(...),
    collection: Optional[str] = Form(None),
    chunk_size: int = Form(500),
    overlap: int = Form(100),
    auth=Depends(verify_token)
):
    global _store
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        # 1. Ingest
        ingestor = DocumentIngestor()
        
        # User Logic: If not provided, tag as 'pdf_upload'. 
        # If provided 'xyz', it belongs to 'xyz' AND 'pdf_upload' (implied by base layer)
        metadata = {"document_id": document_id, "source": "pdf_upload"}
        if collection:
            metadata["collection"] = collection
            
        docs = ingestor.ingest(tmp_path, extra_metadata=metadata)
        if not docs:
            raise HTTPException(status_code=400, detail="Failed to extract text from PDF.")

        chunker = Chunker(chunk_size=chunk_size, chunk_overlap=overlap)
        chunks = chunker.split(docs)

        texts = [c.text for c in chunks]
        embeddings = embed_svc.embed(texts)

        if _store is None:
            _store = get_store() or VectorStore(len(embeddings[0]))
        
        _store.add(chunks, embeddings)
        _store.save(settings.vector_db_path)
        
        return {"status": "success", "chunks": len(chunks), "document_id": document_id, "collection": collection}
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@app.post("/ingest_text")
async def ingest_text(
    document_id: str = Form(...),
    text: str = Form(...),
    collection: Optional[str] = Form(None),
    chunk_size: int = Form(500),
    overlap: int = Form(100),
    auth=Depends(verify_token)
):
    global _store
    try:
        from utils import Document
        
        metadata = {"document_id": document_id, "source": "pdf_upload"}
        if collection:
            metadata["collection"] = collection
            
        doc = Document(text=text, metadata=metadata)
        chunker = Chunker(chunk_size=chunk_size, chunk_overlap=overlap)
        chunks = chunker.split([doc])
        texts = [c.text for c in chunks]
        if not texts:
            raise HTTPException(status_code=400, detail="No text to embed.")
        embeddings = embed_svc.embed(texts)
        if _store is None:
            _store = get_store() or VectorStore(len(embeddings[0]))
        _store.add(chunks, embeddings)
        _store.save(settings.vector_db_path)
        return {"status": "success", "chunks": len(chunks), "document_id": document_id}
    except Exception as e:
        logger.error(f"Text ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/update")
async def update_document(
    file: UploadFile = File(...), 
    document_id: str = Form(...),
    chunk_size: int = Form(500),
    overlap: int = Form(100),
    auth=Depends(verify_token)
):
    global _store
    store = get_store()
    if store:
        store.delete_by_metadata("document_id", document_id)
    return await ingest_document(file, document_id, chunk_size, overlap, auth)

@app.post("/delete")
async def delete_document(document_id: str = Form(...), auth=Depends(verify_token)):
    global _store
    store = get_store()
    if not store:
        raise HTTPException(status_code=400, detail="Vector store is empty.")
    store.delete_by_metadata("document_id", document_id)
    store.save(settings.vector_db_path)
    return {"status": "success", "message": f"Document {document_id} deleted."}

@app.get("/documents")
async def list_documents(auth=Depends(verify_token)):
    store = get_store()
    if not store:
        return {"documents": []}
    
    # Summarize contents
    docs_summary = {}
    for doc in store.documents:
        did = doc.metadata.get("document_id", "unknown")
        if did not in docs_summary:
            docs_summary[did] = {
                "source": doc.metadata.get("source"),
                "collection": doc.metadata.get("collection"),
                "chunks": 0
            }
        docs_summary[did]["chunks"] += 1
    
    return {"documents": docs_summary}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
