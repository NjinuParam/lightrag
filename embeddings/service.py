from typing import List
import numpy as np
from openai import OpenAI, AzureOpenAI
from sentence_transformers import SentenceTransformer
from config import EmbeddingConfig
from utils import logger

class EmbeddingService:
    def __init__(self, config: EmbeddingConfig):
        self.config = config
        self.client = None
        self.model = None

        if config.provider == "openai":
            self.client = OpenAI(api_key=config.api_key, base_url=config.base_url)
        elif config.provider == "azure":
            self.client = AzureOpenAI(
                api_key=config.api_key,
                api_version=config.api_version,
                azure_endpoint=config.base_url
            )
        elif config.provider == "huggingface":
            logger.info(f"Loading local embedding model: {config.model}")
            self.model = SentenceTransformer(config.model)
        elif config.provider == "mock":
            logger.info("Using mock embedding service")
        else:
            raise ValueError(f"Unsupported embedding provider: {config.provider}")

    def embed(self, texts: List[str]) -> List[List[float]]:
        if self.config.provider in ["openai", "azure"]:
            response = self.client.embeddings.create(
                input=texts,
                model=self.config.model
            )
            return [data.embedding for data in response.data]
        
        elif self.config.provider == "huggingface":
            embeddings = self.model.encode(texts)
            return embeddings.tolist()
        
        elif self.config.provider == "mock":
            # Return random but consistent-sized embeddings (e.g., 384 dims)
            return [[0.1] * 384 for _ in texts]
        
        return []
