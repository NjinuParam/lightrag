import os
import requests
from loguru import logger

class LightRAGClient:
    def __init__(self):
        self.base_url = os.getenv("LIGHTRAG_API_URL", "http://localhost:8000")
        self.api_token = os.getenv("API_TOKEN")

    def ingest_text(self, document_id: str, text: str, collection: str = None):
        url = f"{self.base_url}/ingest_text"
        headers = {}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        
        data = {
            "document_id": document_id,
            "text": text
        }
        if collection:
            data["collection"] = collection
        
        try:
            logger.info(f"Pushing crawled content to LightRAG: {document_id}")
            response = requests.post(url, data=data, headers=headers, timeout=60)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to push to LightRAG: {e}")
            return None
