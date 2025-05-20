import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from pathlib import Path
from typing import List, Optional
from uuid import uuid4
from PyPDF2 import PdfReader
from PIL import Image
import pytesseract
from docx import Document
import docx2txt
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer

try:
    from pdf2image import convert_from_path
except ImportError:
    convert_from_path = None  # Optional

# Load environment
load_dotenv()

# Pinecone setup
pinecone_api_key = os.getenv("PINECONE_API_KEY")
pinecone_index_name = os.getenv("PINECONE_INDEX_NAME", "citation-theme-bot")

if not pinecone_api_key:
    raise RuntimeError("Missing PINECONE_API_KEY")

pc = Pinecone(api_key=pinecone_api_key)
if pinecone_index_name not in pc.list_indexes().names():
    pc.create_index(
        name=pinecone_index_name,
        dimension=2048,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
index = pc.Index(pinecone_index_name)

# Embedding model
embedder = SentenceTransformer("all-mpnet-base-v2")

# Upload path
DATA_DIR = Path(__file__).parent.parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Router
router = APIRouter()


# ========== File Handling & Text Extraction ==========

def save_upload_file(file: UploadFile) -> Path:
    """Save uploaded file to server and return the file path."""
    file_path = Path("uploads") / file.filename
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    return file_path

def extract_text_from_pdf(pdf_path: Path) -> List[dict]:
    try:
        reader = PdfReader(str(pdf_path))
        texts = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and text.strip():
                texts.append({"text": text.strip(), "ref": f"page-{i+1}"})
            elif convert_from_path:
                images = convert_from_path(str(pdf_path), first_page=i+1, last_page=i+1)
                if images:
                    ocr_text = pytesseract.image_to_string(images[0])
                    if ocr_text.strip():
                        texts.append({"text": ocr_text.strip(), "ref": f"page-{i+1}-ocr"})
        return texts
    except Exception as e:
        raise RuntimeError(f"PDF extraction failed: {e}")


def extract_text_from_docx(file_path: Path) -> List[dict]:
    try:
        text = docx2txt.process(str(file_path))
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        result = [{"text": p, "ref": f"para-{i+1}"} for i, p in enumerate(paragraphs)]
        if result:
            return result
        # Fallback
        doc = Document(file_path)
        return [{"text": p.text.strip(), "ref": f"para-{i+1}"} for i, p in enumerate(doc.paragraphs) if p.text.strip()]
    except Exception as e:
        raise RuntimeError(f"DOCX extraction failed: {e}")


def extract_text_from_image(file_path: Path) -> List[dict]:
    try:
        img = Image.open(file_path)
        text = pytesseract.image_to_string(img)
        if text.strip():
            return [{"text": text.strip(), "ref": "image-ocr"}]
        return []
    except Exception as e:
        raise RuntimeError(f"Image OCR failed: {e}")


def extract_text_from_txt(file_path: str) -> List[dict]:
    """Extract text from a plain text file."""
    with open(file_path, "r", encoding="utf-8") as file:
        text = file.read()
    return [{"text": text, "ref": file_path}]


# ========== Text Chunking & Embedding ==========


def chunk_text(text: str, max_length: int = 500) -> List[str]:
    if len(text) <= max_length:
        return [text]

    sentences = text.split(". ")
    chunks, current_chunk, length = [], [], 0

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence.endswith("."):
            sentence += "."
        if length + len(sentence) <= max_length:
            current_chunk.append(sentence)
            length += len(sentence)
        else:
            chunks.append(" ".join(current_chunk))
            current_chunk = [sentence]
            length = len(sentence)

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def embed_text(text: str) -> List[float]:
    return embedder.encode(text).tolist()


# ========== Upload Endpoint ==========
@router.post("/upload/")
async def upload_files(
    files: List[UploadFile] = File(...),
    chunk_size: Optional[int] = Form(500)
):
    saved_files = []
    embeddings = []
    total_chunks = 0
    processed_files = []

    try:
        for file in files:
            file_path = save_upload_file(file)
            saved_files.append(file_path)
            filename = file.filename

            # Extract text based on file type
            if filename.lower().endswith(".pdf"):
                texts = extract_text_from_pdf(file_path)
            elif filename.lower().endswith((".docx", ".doc")):
                texts = extract_text_from_docx(file_path)
            elif filename.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".tiff")):
                texts = extract_text_from_image(file_path)
            elif filename.lower().endswith(".txt"):
                texts = extract_text_from_txt(file_path)
            else:
                continue  # Unsupported file type

            if not texts:
                continue

            processed_files.append(filename)

            # Chunk the extracted text and embed it
            for text_item in texts:
                raw_text = text_item["text"]
                ref = text_item["ref"]

                chunks = chunk_text(raw_text, chunk_size)
                for i, chunk in enumerate(chunks):
                    if len(chunk.strip()) < 20:
                        continue
                    chunk_ref = f"{ref}-chunk-{i+1}" if len(chunks) > 1 else ref
                    embedding = embed_text(chunk)  # This will call the embed function
                    meta = {
                        "doc_id": filename,
                        "ref": chunk_ref,
                        "text": chunk
                    }
                    vector_id = f"{filename}_{chunk_ref}".replace(" ", "_")
                    embeddings.append((vector_id, embedding, meta))
                    total_chunks += 1

        # Upsert the embeddings to Pinecone (or your vector DB)
        if embeddings:
            batch_size = 100
            for i in range(0, len(embeddings), batch_size):
                # Assuming `index` is already initialized
                index.upsert(vectors=embeddings[i:i + batch_size])

        return {
            "message": f"Uploaded {len(processed_files)} files. {total_chunks} chunks embedded.",
            "processed_files": processed_files,
            "total_chunks": total_chunks,
        }

    except Exception as e:
        # Clean up saved files in case of error
        for f in saved_files:
            try:
                if f.exists():
                    f.unlink()
            except:
                pass
        raise HTTPException(status_code=500, detail=str(e))
