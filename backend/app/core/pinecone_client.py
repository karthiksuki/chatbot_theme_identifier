# backend/app/core/pinecone_client.py

import os
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

load_dotenv()

# Load environment variables
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "citation-theme-bot")
PINECONE_REGION = os.getenv("PINECONE_REGION", "us-east-1")
PINECONE_DIMENSION = int(os.getenv("PINECONE_DIMENSION", 2048))  # match your embedding model

if not PINECONE_API_KEY:
    raise RuntimeError("Missing PINECONE_API_KEY in environment")

# Init Pinecone client
pc = Pinecone(api_key=PINECONE_API_KEY)

# Index accessor
def get_index(index_name: str = PINECONE_INDEX_NAME, dimension: int = PINECONE_DIMENSION) -> pc.Index:
    # Create index if not present
    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region=PINECONE_REGION)
        )
    return pc.Index(index_name)
