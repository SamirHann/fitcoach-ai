#!/bin/sh
set -e

OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://ollama:11434}"
OLLAMA_MODEL="${OLLAMA_MODEL:-mistral}"
CHROMA_HOST="${CHROMA_HOST:-chromadb}"
CHROMA_PORT="${CHROMA_PORT:-8000}"

echo "→ Attente d'Ollama ($OLLAMA_BASE_URL)..."
until curl -sf "$OLLAMA_BASE_URL/api/tags" > /dev/null 2>&1; do
    sleep 2
done
echo "✓ Ollama disponible"

echo "→ Vérification du modèle $OLLAMA_MODEL..."
if ! curl -sf "$OLLAMA_BASE_URL/api/tags" | grep -q "\"$OLLAMA_MODEL"; then
    echo "→ Téléchargement du modèle $OLLAMA_MODEL (peut prendre plusieurs minutes)..."
    curl -sf -X POST "$OLLAMA_BASE_URL/api/pull" \
        -H "Content-Type: application/json" \
        -d "{\"name\":\"$OLLAMA_MODEL\",\"stream\":false}" \
        > /dev/null
    echo "✓ Modèle $OLLAMA_MODEL téléchargé"
else
    echo "✓ Modèle $OLLAMA_MODEL déjà présent"
fi

echo "→ Attente de ChromaDB ($CHROMA_HOST:$CHROMA_PORT)..."
until curl -sf "http://$CHROMA_HOST:$CHROMA_PORT/api/v1/heartbeat" > /dev/null 2>&1; do
    sleep 2
done
echo "✓ ChromaDB disponible"

echo "→ Vérification de l'index vectoriel..."
python <<EOF
import chromadb, os, sys, subprocess

client = chromadb.HttpClient(
    host=os.getenv("CHROMA_HOST", "chromadb"),
    port=int(os.getenv("CHROMA_PORT", 8000)),
)

needs_ingest = False
try:
    col = client.get_collection("fitcoach")
    count = col.count()
    if count == 0:
        needs_ingest = True
        print("→ Collection vide, ingestion nécessaire")
    else:
        print(f"✓ Collection fitcoach déjà indexée ({count} chunks)")
except Exception:
    needs_ingest = True
    print("→ Collection inexistante, ingestion nécessaire")

if needs_ingest:
    subprocess.run(["python", "/app/src/ingest.py"], check=True)
EOF

echo ""
echo "✓ Initialisation terminée — lancement de FitCoach AI"
echo ""

exec python /app/src/main.py
