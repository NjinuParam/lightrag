# Weaver.ai - LightRAG Documentation

Welcome to the **Weaver.ai** project documentation. This system is a powerful RAG (Retrieval-Augmented Generation) platform integrated with an automated web scraping engine to keep your knowledge base fresh.

## Project Overview

The project consists of two primary microservices and a stunning analytics dashboard:

### 1. Main API Service (`api_main.py`)
This is the core RAG engine.
- **RAG Pipeline:** Handles document ingestion, chunking with overlap, embedding generation, and vector storage.
- **Query Engine:** Supports standard RAG queries and specialized Sim Studio compatible inputs.
- **Direct Ingest:** Supports PDF uploads and raw text ingestion directly to Azure-backed storage.
- **Tech Stack:** FastAPI, FAISS (Vector Store), Mistral/Azure AI (Embeddings/LLM).

### 2. Scraper Service (`scraper/app.py`)
The "Scrapr" engine for web intelligence.
- **Dynamic Crawling:** Uses `scrapy-playwright` to render JavaScript-heavy sites.
- **Sim Studio Integration:** Hooks into Sim Studio workflows for complex scraping tasks.
- **Live Logs:** Provides a `/logs` endpoint for the dashboard to show real-time extraction results.
- **Background Tasks:** Processes crawls asynchronously to maintain speed.

---

## Deployed Instances

The system is live on Azure Container Apps:

| Service | Environment URL |
| :--- | :--- |
| **Main API (RAG)** | `https://light-rag-sandbox.lemongrass-84d35018.westus2.azurecontainerapps.io` |
| **Crawler Service** | `https://crawler-sandbox.lemongrass-84d35018.westus2.azurecontainerapps.io` |
| **Analytics Dashboard** | [Open Dashboard Page](../html/dashboard/dashboard.html) |

---

## 💻 Local Quickstart

To run the entire system locally for development or testing:

1. **Prerequisites:** Ensure Python 3.10+ and [Playwright](https://playwright.dev/) are installed.
2. **Environment:** Copy `.env.example` to `.env` and fill in your API keys.
3. **Launch:** Run the provided batch script:
   ```powershell
   ./run_local.bat
   ```
4. **Access:**
   - **Main API:** `http://localhost:8000`
   - **Scraper:** `http://localhost:8001`
   - **Dashboard:** Open `html/dashboard/dashboard.html` in your browser.

---

## How Deployment Works

### Azure Container Apps
The project is containerized using `Docker` and deployed via **Azure Container Apps**.
- **Continuous Deployment:** Managed via `publish_to_azure.bat` (for local pushing) or GitHub Actions.
- **Environment Variables:**
  - `API_TOKEN`: Used for `Bearer` authentication.
  - `VECTOR_DB_PATH`: Location of the persisted vector store.
  - `x-api-key`: For Sim Studio communication.

### Deployment Commands
To deploy updates manually:
1. Ensure Docker is running.
2. Run the deployment script:
   ```powershell
   ./publish_to_azure.bat
   ```

### ⚠️ Azure Deployment Note
After deploying updates to Azure (especially those involving CORS or Environment Variables), a **Restart** (Revision update) of the Container App in the Azure Portal may be required for the changes to propagate correctly.

---

## Developer Resources

### API Documentation (Postman)
A complete Postman collection is available for testing all endpoints (`/query`, `/ingest`, `/crawl`, `/logs`).
- **File Path:** `postman/LightRag.postman_collection.json`
- **Import:** Open Postman -> Import -> Select File.

### Sim Studio Workflow
- **Workflow ID:** `f78f4c72-fff7-4e3c-ab38-52ad5086e7ae`
- **Platform:** [Sim.ai](https://www.sim.ai)

---

## 📂 Collections & Multi-Tenancy

Weaver.ai supports a "Base + Collection" model for data organization. This allows you to have "Shared Knowledge" and "Project Specific" segments.

### Ingestion Logic
- **Base Knowledge:** If no collection is provided, data is tagged as `source: "pdf_upload"`.
- **Scoped Knowledge:** If a `collection` ID (e.g., `client_alpha`) is provided, data is tagged with that collection.

### Search Strategy
- **Base Search:** Queries without a collection parameter only search the base knowledge.
- **Scoped Search:** Queries with a `collection` ID search **both** the base knowledge **and** the specific collection. This gives the model "Double Vision" (Global Policies + Specific Client Data).

### Example
```json
{
  "query": "What are the project deadlines?",
  "collection": "project_alpha"
}
```

---

## 🕷️ Advanced Scraping (Scrapr)

The Scraper service is optimized for modern web architectures.

- **Dynamic Rendering:** Uses `scrapy-playwright` to handle React/Next.js and other JS-heavy sites.
- **Custom Selectors:** You can override default extraction behavior via the API:
  ```json
  "selectors": {
    "paragraphs": "div.content, p",
    "headings": "h1, h2"
  }
  ```
- **Deduplication:** Automatically removes duplicate content across pages in a single crawl.
- **Direct Pipe:** Successfully crawled text is automatically pushed to the Main API for chunking and embedding.

---

## Frontend Navigation
The UI is organized as follows:
- **📊 Dashboard:** High-level metrics and quick Scrapr launch.
- **📚 Knowledge Base:** Manage files and configure recursive web crawls.
- **🛡️ Audit & Logs:** Inspect AI traces and system health.
- **⚡ Workflows:** Builder for complex automation.

---

## Technical Deep Dive

### 🏗️ Ingestion Architecture
The ingestion lifecycle follows a strictly decoupled pipeline:
1. **Extraction:** The `DocumentIngestor` (facilitated by `pdf_ingestor.py`) extracts raw utf-8 text from source files.
2. **Chunking:** The `Chunker` utilities split text into manageable blocks. Default configuration is **500 characters** with a **100-character overlap** to preserve semantic context across boundaries.
3. **Embedding:** Chunks are sent to the `EmbeddingService`. We use highly efficient 1024-dimensional vectors (or configured dimensions) to represent text meaning.
4. **Indexing:** Vectors are inserted into the **FAISS Index** for ultra-fast O(log n) similarity searches.

### 💾 Vector Storage & Persistence
- **Engine:** [FAISS](https://github.com/facebookresearch/faiss) (Facebook AI Similarity Search).
- **Persistence:** Local state is persisted via Python `pickle` serialization. The system saves the complete vector index and metadata mapping to a `store.pkl` file in the directory defined by `VECTOR_DB_PATH`.
- **Search Strategy:** Uses Euclidean distance (L2) or Inner Product (IP) depending on the normalized state of embeddings to find relevant context for RAG queries.

### 🔌 Sim Studio Integration
The `api_main.py` is specifically optimized for **Sim Studio**. It automatically detects if a query is wrapped in `{{ }}` and processes it accordingly. The scraper also provides a callback-friendly `/logs` endpoint for the studio to monitor long-running crawl success.
