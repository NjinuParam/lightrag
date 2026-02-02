# deployment.md

## LightRAG Python Services Deployment Spec (Sim Studio Integration)

---

## 1. Purpose

This document specifies **how to deploy the LightRAG Python services** so they can be consumed by **Sim Studio (already deployed)** via HTTP APIs.

The deployed service will:

* Expose ingestion, update, delete, and query endpoints
* Persist vector data across restarts
* Be callable as a Sim Studio tool
* Support configurable LLM providers

---

## 2. Deployment Model (Authoritative)

### Chosen Model

**Containerized FastAPI service deployed to Azure Container Apps**

### Non-Goals

* Deploying Sim Studio (already handled)
* Running vector DB inside Sim Studio
* Serverless-only deployments (e.g. Azure Functions)

---

## 3. Runtime Architecture

```
Sim Studio (Managed)
     │
     │ HTTPS (tool calls)
     ▼
LightRAG API (Azure Container App)
     ├── FastAPI
     ├── Embeddings
     ├── FAISS Vector Store (disk-backed)
     └── LLM Client (configurable)
     │
     ▼
LLM Provider (OpenAI / OpenAI-compatible)
```

---

## 4. Service Responsibilities

### LightRAG Service MUST:

* Accept PDF uploads
* Handle document updates via document_id
* Persist embeddings to disk
* Provide a stable public HTTPS endpoint
* Return grounded answers only

### Sim Studio MUST:

* Manage document lifecycle (upload/update/delete)
* Call LightRAG APIs when documents change
* Use LightRAG as a tool for answering questions

---

## 5. Required API Endpoints

The deployed service **must expose** the following endpoints:

| Endpoint  | Method | Purpose                   |
| --------- | ------ | ------------------------- |
| `/health` | GET    | Liveness check            |
| `/ingest` | POST   | New document ingestion    |
| `/update` | POST   | Replace existing document |
| `/delete` | POST   | Remove document           |
| `/query`  | POST   | Full RAG query            |

---

## 6. Container Requirements

### Base Image

* `python:3.11-slim`

### Required Python Packages

* `fastapi`
* `uvicorn`
* `faiss-cpu`
* `langchain`
* `pypdf`
* `python-dotenv`

---

## 7. Filesystem & Persistence

### Persistent Storage Requirement (CRITICAL)

The vector store **must persist across restarts**.

| Path                | Purpose                |
| ------------------- | ---------------------- |
| `/data/vectorstore` | FAISS index + metadata |

### Rules

* Service must load vector store on startup if present
* Service must write updates synchronously
* No in-memory-only vector storage allowed

---

## 8. Environment Variables (Required)

### LLM Configuration

```env
LLM_PROVIDER=openai | openai_compatible | ollama
LLM_MODEL=gpt-4o-mini
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=********
LLM_TEMPERATURE=0.0
```

### Storage Configuration

```env
VECTOR_DB_PATH=/data/vectorstore
```

### Security (Recommended)

```env
API_TOKEN=<shared-secret>
```

---

## 9. Dockerfile Specification

The service **must be containerized**.

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api_main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 10. Azure Deployment Requirements

### Azure Services Used

* Azure Container Apps
* Azure Container Registry (ACR)
* Azure Files (persistent volume)

### Deployment Constraints

* External HTTPS ingress enabled
* Port: `8000`
* Minimum 1 replica (recommended for low latency)
* CPU ≥ 1 vCPU
* Memory ≥ 2 GiB

---

## 11. Public Endpoint Contract

After deployment, the service **must expose**:

```
https://<service-name>.<region>.azurecontainerapps.io
```

Sim Studio tools will call:

* `/query`
* `/ingest`
* `/update`
* `/delete`

---

## 12. Sim Studio Tool Integration

### Tool Example: `query_knowledge`

* Method: `POST`
* URL: `https://<service-url>/query`
* Headers:

  ```http
  Content-Type: application/json
  Authorization: Bearer <API_TOKEN>
  ```

### Expected Behavior

* Sim Studio sends question
* LightRAG returns grounded answer + sources
* Sim Studio presents answer to user

---

## 13. Document Update Flow (Authoritative)

### Replace PDF in Sim Studio

1. User replaces document in Sim Knowledge
2. Sim Studio calls:

```http
POST /update
document_id=<stable-id>
file=@new.pdf
```

3. LightRAG:

   * Deletes old vectors
   * Re-ingests PDF
   * Persists new vectors

4. Subsequent queries use updated content only

---

## 14. Health & Observability

### Health Endpoint

```http
GET /health
```

Expected response:

```json
{ "status": "ok" }
```

### Required Logs

* Ingestion count
* Update/delete operations
* Retrieval latency
* LLM latency

---

## 15. Failure Handling Rules

| Scenario        | Required Behavior                     |
| --------------- | ------------------------------------- |
| Ingest fails    | Do not write partial vectors          |
| Update fails    | Roll back to previous vectors         |
| Query fails     | Return error, not hallucinated answer |
| LLM unavailable | Return explicit failure               |

---

## 16. Acceptance Criteria

Deployment is considered successful when:

* ✅ Service is reachable via HTTPS
* ✅ `/health` returns OK
* ✅ PDFs can be ingested and updated
* ✅ Vector data survives restarts
* ✅ Sim Studio can query and receive grounded answers
* ✅ No stale content after document replacement

---

## 17. Explicit Non-Goals

* No embedding inside Sim Studio
* No multi-region replication (v1)
* No partial PDF updates
* No UI served from this service

---

## 18. Ownership Summary

| Component            | Owner      |
| -------------------- | ---------- |
| Document lifecycle   | Sim Studio |
| Vector storage       | LightRAG   |
| Retrieval logic      | LightRAG   |
| Prompt orchestration | LightRAG   |
| User experience      | Sim Studio |
