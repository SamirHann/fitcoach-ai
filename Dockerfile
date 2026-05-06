FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# PyTorch CPU-only (évite ~3GB de libs CUDA inutiles)
RUN pip install --no-cache-dir \
    --index-url https://download.pytorch.org/whl/cpu \
    torch==2.4.1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pré-charger le modèle d'embeddings (compile ONNX une seule fois au build)
RUN python -c "from langchain_huggingface import HuggingFaceEmbeddings; HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')" 2>/dev/null || true

COPY src ./src
COPY docs ./docs
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
