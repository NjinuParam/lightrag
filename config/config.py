import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

@dataclass
class LLMConfig:
    provider: str               # openai | openai_compatible | ollama | azure
    api_key: Optional[str]
    base_url: Optional[str]
    model: str
    temperature: float
    max_tokens: Optional[int]
    api_version: Optional[str] = None

@dataclass
class EmbeddingConfig:
    provider: str               # openai | huggingface | azure
    model: str
    api_key: Optional[str]
    base_url: Optional[str]
    api_version: Optional[str] = None

@dataclass
class Settings:
    llm: LLMConfig
    embedding: EmbeddingConfig
    vector_db_path: str
    api_token: Optional[str]

def get_settings() -> Settings:
    llm_provider = os.getenv("LLM_PROVIDER", "openai")
    llm_config = LLMConfig(
        provider=llm_provider,
        api_key=os.getenv("LLM_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL") or os.getenv("AZURE_OPENAI_ENDPOINT"),
        model=os.getenv("LLM_MODEL") or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o-mini"),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.0")),
        max_tokens=int(os.getenv("LLM_MAX_TOKENS", "1000")) if os.getenv("LLM_MAX_TOKENS") else None,
        api_version=os.getenv("LLM_API_VERSION") or os.getenv("AZURE_OPENAI_API_VERSION"),
    )

    embed_provider = os.getenv("EMBEDDING_PROVIDER", "openai")
    embedding_config = EmbeddingConfig(
        provider=embed_provider,
        model=os.getenv("EMBEDDING_MODEL") or os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002"),
        api_key=os.getenv("EMBEDDING_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY"),
        base_url=os.getenv("EMBEDDING_BASE_URL") or os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("EMBEDDING_API_VERSION") or os.getenv("AZURE_OPENAI_API_VERSION"),
    )

    return Settings(
        llm=llm_config, 
        embedding=embedding_config,
        vector_db_path=os.getenv("VECTOR_DB_PATH", "storage"),
        api_token=os.getenv("API_TOKEN")
    )
