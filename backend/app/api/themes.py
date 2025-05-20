# backend/app/api/themes.py

import os
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, List
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
import openai
import requests
from dotenv import load_dotenv

load_dotenv()

# Load environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "citation-theme-bot")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")

if not PINECONE_API_KEY:
    raise RuntimeError("Missing PINECONE_API_KEY")
if LLM_PROVIDER == "openai" and not OPENAI_API_KEY:
    raise RuntimeError("Missing OPENAI_API_KEY")
if LLM_PROVIDER == "groq" and not GROQ_API_KEY:
    raise RuntimeError("Missing GROQ_API_KEY")

# Setup clients
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)

router = APIRouter()

# Request model
class ThemeRequest(BaseModel):
    query: Optional[str] = None
    top_k: int = 100
    model: Optional[str] = None

# LLM call: Groq
def call_groq_llm(prompt: str, model: str = "mixtral-8x7b-32768") -> str:
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.4,
        "max_tokens": 1000
    }
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=body)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()

# LLM call: OpenAI
def call_openai_llm(prompt: str, model: str = "gpt-4-turbo") -> str:
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=1000
    )
    return response.choices[0].message.content.strip()

# Unified LLM call
def call_llm(prompt: str, provider: str = None, model: str = None) -> str:
    provider = provider or LLM_PROVIDER
    model = model or {"openai": "gpt-4-turbo", "groq": "mixtral-8x7b-32768"}.get(provider)

    try:
        if provider == "openai":
            return call_openai_llm(prompt, model)
        elif provider == "groq":
            return call_groq_llm(prompt, model)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    except Exception as e:
        print(f"Theme LLM error: {e}")
        raise RuntimeError("Theme extraction failed.")

# Endpoint
@router.post("/themes/")
async def get_themes(request: ThemeRequest):
    try:
        # Load embedding model for dummy query if needed
        embedder = SentenceTransformer("all-MiniLM-L6-v2")

        # Embed query or use [0.0] * 384 to fetch general sample
        if request.query:
            query_vec = embedder.encode(request.query).tolist()
        else:
            query_vec = [0.0] * 384

        # Retrieve top_k document chunks
        res = index.query(
            vector=query_vec,
            top_k=request.top_k,
            include_metadata=True
        )

        # Format chunks
        chunks = [
            (match.metadata.get("text", ""), match.metadata.get("doc_id", "UNKNOWN"))
            for match in res.matches if "text" in match.metadata
        ]

        if not chunks:
            return {"error": "No document excerpts available for theme analysis."}

        # Build prompt for theme extraction
        prompt = (
            "You are an AI assistant specializing in document research. "
            "Identify 2–3 major themes from the following excerpts.\n"
        )
        if request.query:
            prompt += f"User Query: {request.query}\n\n"
        prompt += "Excerpts:\n"

        max_excerpts = 20
        for i, (text, doc_id) in enumerate(chunks[:max_excerpts]):
            prompt += f"Excerpt {i+1} (Doc: {doc_id}): {text.strip()}\n\n"

        prompt += (
            "Extract 2–3 key themes.\n"
            "Each theme should include:\n"
            "- A short title\n"
            "- A 2–3 sentence summary\n"
            "- A list of supporting document IDs\n"
            "Return response in this JSON format:\n"
            "{\n"
            "  \"Theme 1\": {\"summary\": \"...\", \"docs\": [\"DOC001\", \"DOC002\"]},\n"
            "  \"Theme 2\": {\"summary\": \"...\", \"docs\": [\"DOC003\"]}\n"
            "}"
        )

        content = call_llm(prompt, model=request.model)

        # Attempt to parse clean JSON
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Try extracting inner JSON
            try:
                start = content.find('{')
                end = content.rfind('}') + 1
                return json.loads(content[start:end])
            except:
                return {"error": "Failed to parse AI output", "raw_output": content}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
