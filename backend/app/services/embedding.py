import os
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Pinecone
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "citation-theme-bot")

if not PINECONE_API_KEY:
    raise RuntimeError("Missing PINECONE_API_KEY")

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)

# Initialize SentenceTransformer model
model = SentenceTransformer("all-mpnet-base-v2")


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Split text into chunks with specified size and overlap.
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunk = text[i:i + chunk_size]
        if len(chunk) >= 100:  # Minimum chunk size to avoid tiny chunks
            chunks.append(chunk)

    return chunks


def embed_text(text: str) -> List[float]:
    """
    Create embeddings for text using SentenceTransformer.
    """
    return model.encode(text).tolist()


def embed_and_store_chunks(text: str, doc_id: str, chunk_size: int = 500) -> int:
    """
    Split text into chunks, embed them, and store in Pinecone.
    Returns number of chunks processed.
    """
    chunks = chunk_text(text, chunk_size)

    vectors = []
    for i, chunk in enumerate(chunks):
        if len(chunk.strip()) < 20:  # Skip very small chunks
            continue

        # Create embedding
        embedding = embed_text(chunk)

        # Create metadata
        metadata = {
            "doc_id": doc_id,
            "ref": f"chunk-{i + 1}",
            "text": chunk
        }

        # Create vector ID
        vector_id = f"{doc_id}_chunk_{i + 1}"

        vectors.append((vector_id, embedding, metadata))

        # Batch upsert to Pinecone
        if len(vectors) >= 100:
            index.upsert(vectors=vectors)
            vectors = []

    # Upsert any remaining vectors
    if vectors:
        index.upsert(vectors=vectors)

    return len(chunks)