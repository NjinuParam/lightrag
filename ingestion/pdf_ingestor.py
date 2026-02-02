import os
from typing import List
from pypdf import PdfReader
from utils import logger, Document

class DocumentIngestor:
    def ingest(self, path: str, extra_metadata: dict = None) -> List[Document]:
        """
        Load a PDF and return a list of Documents (one per page or one for entire doc).
        """
        if not os.path.exists(path):
            logger.error(f"File not found: {path}")
            return []

        try:
            reader = PdfReader(path)
            documents = []
            filename = os.path.basename(path)
            
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text.strip():
                    metadata = {
                        "source": filename,
                        "page": i + 1,
                        "total_pages": len(reader.pages)
                    }
                    if extra_metadata:
                        metadata.update(extra_metadata)
                        
                    doc = Document(
                        text=text,
                        metadata=metadata
                    )
                    documents.append(doc)
            
            logger.info(f"Successfully ingested {len(documents)} pages from {filename}")
            return documents
        except Exception as e:
            logger.error(f"Failed to ingest PDF {path}: {e}")
            return []
