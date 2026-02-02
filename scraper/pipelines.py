import os
from loguru import logger
from rag_client import LightRAGClient

class MarkdownPipeline:
    def __init__(self):
        self.rag_client = LightRAGClient()

    def open_spider(self, spider):
        # Overwrite the log file at the start of each crawl
        log_path = os.path.join(os.getcwd(), "crawler-logs.md")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"# Crawler Logs - Last Run: {spider.document_id}\n")
            f.write("This file contains the raw text extracted before embedding.\n\n")
        logger.info(f"Initialized crawler log at {log_path}")
        
        # Initialize deduplication set
        self.seen_texts = set()

    def process_item(self, item, spider):
        url = item.get("url")
        headings = item.get("headings", [])
        paragraphs = item.get("paragraphs", [])
        document_id = getattr(spider, 'document_id', 'scraped_doc')
        collection = item.get("collection")

        # Transform into RAG-ready Markdown
        clean_headings = [h.strip() for h in headings if h.strip()]
        
        # Deduplicate paragraphs across all pages in this crawl
        clean_paragraphs = []
        for p in paragraphs:
            p_stripped = p.strip()
            if p_stripped and p_stripped not in self.seen_texts:
                self.seen_texts.add(p_stripped)
                clean_paragraphs.append(p_stripped)

        markdown = f"## URL: {url}\n\n"
        
        if clean_headings:
            markdown += "### Headings\n"
            markdown += " | ".join(clean_headings) + "\n\n"
        
        if clean_paragraphs:
            markdown += "### Content\n"
            markdown += "\n\n".join(clean_paragraphs) + "\n"
        
        markdown += "\n---\n"
        
        # Log to file for human verification
        log_path = os.path.join(os.getcwd(), "crawler-logs.md")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(markdown)

        # PUSH DIRECTLY from pipeline in this architecture
        logger.info(f"Pipeline pushing content to LightRAG for {document_id}")
        self.rag_client.ingest_text(document_id, markdown, collection=collection)
        
        return item
