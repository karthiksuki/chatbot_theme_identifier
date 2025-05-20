from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from backend.app.services.theme_identifier import identify_themes

router = APIRouter()

# Define request body schema
class ThemeRequest(BaseModel):
    chunks: List[str]
    doc_ids: List[str]
    query: Optional[str] = None


# Define POST endpoint to handle theme identification
@router.post("/identify-themes")
async def identify_themes_endpoint(request: ThemeRequest):
    """
    Endpoint for identifying themes from document chunks.
    """
    try:
        themes = identify_themes(request.chunks, request.doc_ids, request.query)
        if "error" in themes:
            raise HTTPException(status_code=400, detail=themes["error"])
        return themes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
