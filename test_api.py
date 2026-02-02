import requests
import time
import os

BASE_URL = "http://127.0.0.1:8000"
DOC_ID = "sim_studio_test_001"
PDF_PATH = "sample.pdf"

def test_flow():
    print("--- Starting LightRAG API Integration Test ---")
    
    # 1. Health Check
    try:
        r = requests.get(f"{BASE_URL}/health")
        print(f"Health Check: {r.status_code} - {r.json()}")
    except Exception as e:
        print(f"FAILED: Service not running at {BASE_URL}. Start it with 'python api_main.py' first.")
        return

    # 2. Ingest
    print(f"\nIngesting {PDF_PATH}...")
    with open(PDF_PATH, "rb") as f:
        r = requests.post(
            f"{BASE_URL}/ingest",
            files={"file": f},
            data={"document_id": DOC_ID}
        )
    print(f"Ingest Status: {r.status_code} - {r.json()}")

    # 3. Query
    print("\nQuerying: 'What is this document about?'")
    r = requests.post(f"{BASE_URL}/query", json={"query": "What is this document about?"})
    print(f"Query Status: {r.status_code}")
    if r.status_code == 200:
        print(f"Answer: {r.json().get('answer')}")

    # 4. Update (Re-ingest same ID)
    print(f"\nUpdating document {DOC_ID}...")
    with open(PDF_PATH, "rb") as f:
        r = requests.post(
            f"{BASE_URL}/update",
            files={"file": f},
            data={"document_id": DOC_ID}
        )
    print(f"Update Status: {r.status_code} - {r.json()}")

    # 5. Delete
    print(f"\nDeleting document {DOC_ID}...")
    r = requests.post(f"{BASE_URL}/delete", data={"document_id": DOC_ID})
    print(f"Delete Status: {r.status_code} - {r.json()}")

if __name__ == "__main__":
    if not os.path.exists(PDF_PATH):
        print(f"Error: {PDF_PATH} not found. Please run the ingestion test from main.py first to create it.")
    else:
        test_flow()
