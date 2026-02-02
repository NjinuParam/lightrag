import os
import multiprocessing
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
from loguru import logger
from dotenv import load_dotenv

# We don't import ANY scrapy/twisted stuff here to avoid reactor initialization in the main process

load_dotenv()

app = FastAPI(title="LightRAG Scraper Service")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScrapeRequest(BaseModel):
    document_id: str
    urls: List[str]
    collection: Optional[str] = None
    selectors: Dict[str, str] = {
        "paragraphs": "p",
        "headings": "h1, h2, h3"
    }

def verify_token(authorization: Optional[str] = Header(None)):
    token = os.getenv("API_TOKEN")
    if not token:
        logger.warning("API_TOKEN not set in environment. Skipping auth.")
        return
        
    expected = f"Bearer {token.strip()}"
    if authorization != expected:
        logger.error(f"Auth failed. Header: {authorization}, Expected: {expected}")
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.get("/health")
def health():
    return {"status": "ok", "service": "scraper"}

def run_spider_sync(req_dict):
    # LATE IMPORT to ensure reactor is fresh in this process
    from scrapy.crawler import CrawlerProcess
    from spiders.generic import GenericSpider
    
    # Force the Asyncio reactor for scrapy-playwright
    process = CrawlerProcess({
        'ITEM_PIPELINES': {
            'pipelines.MarkdownPipeline': 300,
        },
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'LOG_LEVEL': 'INFO',
        'TWISTED_REACTOR': 'twisted.internet.asyncioreactor.AsyncioSelectorReactor',
        'DOWNLOAD_HANDLERS': {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {'headless': True},
    })
    
    process.crawl(GenericSpider, 
        urls=req_dict['urls'], 
        selectors=req_dict['selectors'], 
        document_id=req_dict['document_id'],
        collection=req_dict.get('collection')
    )
    process.start()

async def crawl_in_process(req: ScrapeRequest):
    req_dict = req.dict()
    p = multiprocessing.Process(target=run_spider_sync, args=(req_dict,))
    p.start()
    logger.info(f"Spawned crawl process {p.pid} for {req.document_id}")

@app.get("/logs")
async def get_crawler_logs(auth=Depends(verify_token)):
    log_path = os.path.join(os.getcwd(), "crawler-logs.md")
    if not os.path.exists(log_path):
        return {"message": "No logs found yet. Start a crawl first!"}
    
    with open(log_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Return as plain text for easy reading in browser
    return PlainTextResponse(content)

@app.post("/crawl")
async def start_crawl(req: ScrapeRequest, background_tasks: BackgroundTasks, auth=Depends(verify_token)):
    logger.info(f"Accepted crawl request for doc_id: {req.document_id}")
    background_tasks.add_task(crawl_in_process, req)
    return {"status": "accepted", "document_id": req.document_id, "message": "Crawl started in background"}

if __name__ == "__main__":
    multiprocessing.freeze_support()
    uvicorn.run(app, host="0.0.0.0", port=8001)
