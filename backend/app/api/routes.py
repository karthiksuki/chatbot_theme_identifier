from fastapi import APIRouter, File, UploadFile, Form
from fastapi.responses import JSONResponse
from typing import List
from pathlib import Path
from uuid import uuid4
import os

from backend.app.services.ocr import ocr_pdf
from backend.app.services.embedding import embed_and_store_chunks
from backend.app.services.theme_identifier import identify_themes

# Router init
router = APIRouter()

# Upload and analyze single document
@router.post("/analyze")
async def analyze_document(file: UploadFile = File(...)):
    try:
        # Step 1: Save uploaded file
        upload_dir = Path("data/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        ext = Path(file.filename).suffix
        temp_path = upload_dir / f"{uuid4().hex}{ext}"
        with open(temp_path, "wb") as f:
            f.write(await file.read())

        # Step 2: Extract text from file
        text = ocr_pdf(str(temp_path))

        if not text.strip():
            return JSONResponse(status_code=400, content={"error": "No extractable text found."})

        doc_id = Path(file.filename).stem

        # Step 3: Embed & store in Pinecone
        num_chunks = embed_and_store_chunks(text, doc_id=doc_id)

        # Step 4: Use same text to extract themes
        chunks = [text[i:i+800] for i in range(0, len(text), 800)]
        doc_ids = [doc_id] * len(chunks)
        themes = identify_themes(chunks, doc_ids)

        # Step 5: Return results
        result = {
            "filename": file.filename,
            "num_chunks": num_chunks,
            "themes": themes
        }
        return JSONResponse(content=result)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
