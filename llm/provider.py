from typing import Optional
from openai import OpenAI, AzureOpenAI
import ollama
from config import LLMConfig
from utils import logger

class LLMService:
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = None

        if config.provider in ["openai", "openai_compatible"]:
            self.client = OpenAI(
                api_key=config.api_key or "no-key-needed",
                base_url=config.base_url
            )
        elif config.provider == "azure":
            self.client = AzureOpenAI(
                api_key=config.api_key,
                api_version=config.api_version,
                azure_endpoint=config.base_url
            )
        elif config.provider == "ollama":
            pass
        elif config.provider == "mock":
            logger.info("Using mock LLM service")
        else:
            raise ValueError(f"Unsupported LLM provider: {config.provider}")

    def generate(self, prompt: str, system_prompt: str = "You are a helpful assistant.") -> str:
        try:
            if self.config.provider == "mock":
                return "This is a mock response because LLM_PROVIDER is set to 'mock'."
            
            if self.config.provider in ["openai", "openai_compatible", "azure"]:
                response = self.client.chat.completions.create(
                    model=self.config.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens
                )
                return response.choices[0].message.content
            
            elif self.config.provider == "ollama":
                response = ollama.chat(
                    model=self.config.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    options={
                        "temperature": self.config.temperature,
                        "num_predict": self.config.max_tokens
                    }
                )
                return response['message']['content']
        
        except Exception as e:
            logger.error(f"LLM Generation failed: {e}")
            raise e
        
        return ""
