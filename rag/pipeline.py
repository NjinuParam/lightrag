from typing import List
from llm import LLMService
from retrieval import Retriever
from utils import logger

DEFAULT_PROMPT_TEMPLATE = """You are a helpful assistant.
Answer the question using ONLY the context below.
If the answer is not present, say you do not know.

Context:
{context}

Question:
{question}
"""

class RAGPipeline:
    def __init__(self, retriever: Retriever, llm_service: LLMService, prompt_template: str = DEFAULT_PROMPT_TEMPLATE):
        self.retriever = retriever
        self.llm_service = llm_service
        self.prompt_template = prompt_template

    def query(self, question: str, k: int = 5, collection: str = None) -> str:
        # 1. Retrieve
        docs = self.retriever.retrieve(question, k=k, collection=collection)
        
        if not docs:
            logger.warning("No relevant context found.")
            return "No relevant context found."
        
        # 2. Format Context
        context_text = "\n\n".join([doc.text for doc in docs])
        
        # 3. Construct Prompt
        prompt = self.prompt_template.format(context=context_text, question=question)
        
        # 4. Generate
        logger.info("Generating answer...")
        return self.llm_service.generate(prompt)
