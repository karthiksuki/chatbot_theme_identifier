import os
import json
from typing import List, Dict, Any, Optional
import openai
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")

if LLM_PROVIDER == "openai" and not OPENAI_API_KEY:
    raise RuntimeError("Missing OPENAI_API_KEY")
if LLM_PROVIDER == "groq" and not GROQ_API_KEY:
    raise RuntimeError("Missing GROQ_API_KEY")

# Initialize OpenAI if needed
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY


def call_openai_llm(prompt: str, model: str = "gpt-4-turbo") -> str:
    """Call OpenAI LLM API."""
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI API error: {e}")
        raise RuntimeError(f"OpenAI call failed: {str(e)}")


def call_groq_llm(prompt: str, model: str = "llama3-8b-8192") -> str:
    """Call Groq LLM API."""
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        body = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 1000
        }
        response = requests.post("https://api.groq.com/openai/v1/chat/completions",
                                 headers=headers, json=body)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"Groq API error: {e}")
        raise RuntimeError(f"Groq call failed: {str(e)}")


def call_llm(prompt: str, provider: Optional[str] = None, model: Optional[str] = None) -> str:
    """Unified LLM calling function."""
    provider = provider or LLM_PROVIDER
    model = model or {"openai": "gpt-4-turbo", "groq": "llama3-8b-8192"}.get(provider)

    if provider == "openai":
        return call_openai_llm(prompt, model)
    elif provider == "groq":
        return call_groq_llm(prompt, model)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


def identify_themes(chunks: List[str], doc_ids: List[str], query: Optional[str] = None) -> Dict[str, Any]:
    """
    Identify themes from document chunks using LLM.

    Args:
        chunks: List of text chunks
        doc_ids: List of document IDs corresponding to chunks
        query: Optional query to focus theme extraction

    Returns:
        Dictionary of themes with summaries and associated document IDs
    """
    if not chunks or len(chunks) == 0:
        return {"error": "No document chunks provided for theme analysis"}

    # Build the prompt
    prompt = (
        "You are an AI assistant specializing in document research. "
        "Identify 2-3 major themes from the following excerpts.\n"
    )

    if query:
        prompt += f"User Query: {query}\n\n"

    prompt += "Excerpts:\n"

    # Limit to reasonable number of chunks
    max_chunks = min(20, len(chunks))
    for i in range(max_chunks):
        prompt += f"Excerpt {i + 1} (Doc: {doc_ids[i]}): {chunks[i].strip()}\n\n"

    prompt += (
        "Extract 2-3 key themes.\n"
        "Each theme should include:\n"
        "- A short title\n"
        "- A 2-3 sentence summary\n"
        "- A list of supporting document IDs\n"
        "Return response in this JSON format:\n"
        "{\n"
        "  \"Theme 1\": {\"summary\": \"...\", \"docs\": [\"DOC001\", \"DOC002\"]},\n"
        "  \"Theme 2\": {\"summary\": \"...\", \"docs\": [\"DOC003\"]}\n"
        "}"
    )

    # Call LLM
    try:
        content = call_llm(prompt)

        # Try to parse the JSON response
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Try extracting JSON from the response
            try:
                start = content.find('{')
                end = content.rfind('}') + 1
                if start >= 0 and end > start:
                    return json.loads(content[start:end])
                else:
                    return {"error": "Failed to parse LLM output", "raw_output": content}
            except:
                return {"error": "Failed to parse LLM output", "raw_output": content}

    except Exception as e:
        return {"error": f"Theme identification failed: {str(e)}"}