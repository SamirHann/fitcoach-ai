#!/usr/bin/env python3
"""Ingestion des documents PDF/TXT dans ChromaDB."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import chromadb

load_dotenv()

CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", 8000))
DOCS_DIR = Path(__file__).parent.parent / "docs"
COLLECTION_NAME = "fitcoach"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def load_document(path: Path):
    if path.suffix.lower() == ".pdf":
        loader = PyPDFLoader(str(path))
    else:
        loader = TextLoader(str(path), encoding="utf-8")
    return loader.load()


def ingest():
    print(f"→ Scanning {DOCS_DIR} pour les documents PDF/TXT...")

    docs_paths = list(DOCS_DIR.glob("*.pdf")) + list(DOCS_DIR.glob("*.txt"))
    if not docs_paths:
        print("✗ Aucun document trouvé dans /docs", file=sys.stderr)
        sys.exit(1)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)

    total_chunks = 0
    all_chunks = []

    for doc_path in docs_paths:
        print(f"→ Chargement : {doc_path.name}")
        try:
            raw_docs = load_document(doc_path)
        except Exception as e:
            print(f"✗ Erreur chargement {doc_path.name} : {e}", file=sys.stderr)
            continue

        chunks = splitter.split_documents(raw_docs)
        for i, chunk in enumerate(chunks):
            chunk.metadata["source_file"] = doc_path.name
            chunk.metadata["chunk_index"] = i

        all_chunks.extend(chunks)
        print(f"  ✓ {len(chunks)} chunks extraits depuis {doc_path.name}")
        total_chunks += len(chunks)

    if not all_chunks:
        print("✗ Aucun chunk à indexer.", file=sys.stderr)
        sys.exit(1)

    print(f"\n→ Indexation de {total_chunks} chunks dans ChromaDB...")

    Chroma.from_documents(
        documents=all_chunks,
        embedding=embeddings,
        client=chroma_client,
        collection_name=COLLECTION_NAME,
    )

    print(f"✓ Ingestion terminée : {total_chunks} chunks dans la collection '{COLLECTION_NAME}'")


if __name__ == "__main__":
    ingest()
