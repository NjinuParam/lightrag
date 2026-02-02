FROM python:3.11-slim

WORKDIR /app

# Install build dependencies for FAISS if needed
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Install torch cpu first and skip SSL verification due to network environment issues
RUN pip install --no-cache-dir \
    --default-timeout=100 \
    --trusted-host download.pytorch.org \
    --trusted-host pypi.org \
    --trusted-host files.pythonhosted.org \
    torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir \
    --default-timeout=100 \
    --trusted-host download.pytorch.org \
    --trusted-host pypi.org \
    --trusted-host files.pythonhosted.org \
    -r requirements.txt

COPY . .

# Ensure data directory exists
RUN mkdir -p /data/vectorstore

# Set environment variables defaults
ENV LLM_PROVIDER=openai
ENV VECTOR_DB_PATH=/data/vectorstore

EXPOSE 8000

CMD ["uvicorn", "api_main:app", "--host", "0.0.0.0", "--port", "8000"]
