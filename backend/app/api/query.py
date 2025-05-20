import os
import openai
import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

load_dotenv()

# === Environment Setup ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "citation-theme-bot")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")

if not PINECONE_API_KEY:
    raise RuntimeError("Missing PINECONE_API_KEY")
if LLM_PROVIDER == "openai" and not OPENAI_API_KEY:
    raise RuntimeError("Missing OPENAI_API_KEY")
if LLM_PROVIDER == "groq" and not GROQ_API_KEY:
    raise RuntimeError("Missing GROQ_API_KEY")

openai.api_key = OPENAI_API_KEY

# === Pinecone Initialization ===
pc = Pinecone(api_key=PINECONE_API_KEY)

# List existing indexes
existing_indexes = pc.list_indexes().names()

if PINECONE_INDEX_NAME not in existing_indexes:
    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=2048,  # use your embedding size
        metric='cosine',  # or 'euclidean' based on your use case
        spec=ServerlessSpec(
            cloud='aws',       # adjust cloud and region as needed
            region='us-east-1'
        )
    )
else:
    print(f"Index '{PINECONE_INDEX_NAME}' already exists, skipping creation.")

index = pc.Index(PINECONE_INDEX_NAME)

# === FastAPI Router ===
router = APIRouter()

# === Request/Response Schemas ===
class QueryRequest(BaseModel):
    q: str
    top_k: int = 5
    model: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    citations: Dict[str, List[str]]

# === Embedding Function ===
def embed_text(text: str) -> List[float]:
    try:
        res = openai.Embedding.create(
            input=text[:1024],
            model="text-embedding-ada-002"
        )
        return res['data'][0]['embedding']
    except Exception as e:
        raise RuntimeError(f"Embedding failed: {e}")

# === LLM Call Wrappers ===
def call_groq_llm(prompt: str, model: str = "llama3-8b-8192") -> str:
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 800
    }
    try:
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=body)
        res.raise_for_status()
        return res.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        raise RuntimeError(f"Groq LLM failed: {e}")

def call_openai_llm(prompt: str, model: str = "gpt-4-turbo") -> str:
    try:
        res = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=800
        )
        return res.choices[0].message.content.strip()
    except Exception as e:
        raise RuntimeError(f"OpenAI LLM failed: {e}")

def call_llm(prompt: str, provider: Optional[str] = None, model: Optional[str] = None) -> str:
    provider = provider or LLM_PROVIDER
    model = model or {"openai": "gpt-4-turbo", "groq": "llama3-8b-8192"}.get(provider)

    if provider == "openai":
        return call_openai_llm(prompt, model)
    elif provider == "groq":
        raise RuntimeError("Groq LLM provider currently disabled due to 404 error.")
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


# === Query Endpoint ===
@router.post("/query", response_model=QueryResponse)
async def query_docs(request: QueryRequest):
    try:
        # 1. Query Pinecone using integrated embedding
        results = index.query(
            top_k=request.top_k,
            include_metadata=True,
            text=request.q.strip()[:1024],
            embed=True
        )
        print(results)

        # 2. Handle no matches & casual greetings
        if not results.matches:
            if request.q.strip().lower() in {"hi", "hello", "hey"}:
                return QueryResponse(
                    answer="Hello! Upload a document and ask a research question to get started.",
                    citations={}
                )
            try:
                answer = call_llm(
                    f"The user asked: '{request.q}'. Respond helpfully, even without documents."
                )
                return QueryResponse(answer=answer, citations={})
            except Exception as e:
                raise HTTPException(status_code=500, detail="LLM fallback failed: " + str(e))

        # 3. Extract context and citations
        chunks = []
        citations_map = {}

        for match in results.matches:
            meta = match.metadata or {}
            doc_id = meta.get("doc_id", "UNKNOWN_DOC")
            ref = meta.get("ref", f"score_{match.score:.2f}")
            text = meta.get("text", "")

            if text:
                chunks.append(text)
                citations_map.setdefault(doc_id, [])
                if ref not in citations_map[doc_id]:
                    citations_map[doc_id].append(ref)

        # 4. Build prompt
        prompt = "You are an AI research assistant helping with document analysis. Use the following excerpts:\n\n"
        for i, chunk in enumerate(chunks):
            prompt += f"Excerpt {i + 1}:\n{chunk}\n\n"
        prompt += f"Question: {request.q}\n\nAnswer based only on the excerpts."

        # 5. Call LLM for answer
        answer = call_llm(prompt, model=request.model)

        return QueryResponse(answer=answer, citations=citations_map)

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")
