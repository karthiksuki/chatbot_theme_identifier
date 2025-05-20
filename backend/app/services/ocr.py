import os
from pathlib import Path
from PyPDF2 import PdfReader
import pytesseract
from PIL import Image
import docx2txt
from docx import Document

# Try to import pdf2image, but don't fail if it's not available
try:
    from pdf2image import convert_from_path

    HAS_PDF2IMAGE = True
except ImportError:
    HAS_PDF2IMAGE = False


def ocr_pdf(file_path: str) -> str:
    """
    Extract text from PDF using PyPDF2 and OCR if needed.
    """
    try:
        pdf_text = ""
        reader = PdfReader(file_path)

        # First try PyPDF2 text extraction
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pdf_text += text + "\n\n"

        # If we got sufficient text, return it
        if len(pdf_text.strip()) > 100:
            return pdf_text

        # If text extraction failed, try OCR if pdf2image is available
        if HAS_PDF2IMAGE and not pdf_text.strip():
            ocr_text = ""
            images = convert_from_path(file_path)
            for img in images:
                ocr_text += pytesseract.image_to_string(img) + "\n\n"
            return ocr_text

        return pdf_text

    except Exception as e:
        print(f"Error extracting text from PDF: {str(e)}")
        return ""


def ocr_image(file_path: str) -> str:
    """
    Extract text from images using OCR.
    """
    try:
        img = Image.open(file_path)
        text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        print(f"Error extracting text from image: {str(e)}")
        return ""


def extract_text_from_docx(file_path: str) -> str:
    """
    Extract text from DOCX files.
    """
    try:
        # Try docx2txt first
        text = docx2txt.process(file_path)
        if text:
            return text

        # Fallback to python-docx
        doc = Document(file_path)
        text = "\n\n".join([para.text for para in doc.paragraphs if para.text.strip()])
        return text
    except Exception as e:
        print(f"Error extracting text from DOCX: {str(e)}")
        return ""


def extract_text_from_txt(file_path: str) -> str:
    """
    Extract text from plain text files.
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        return text
    except Exception as e:
        print(f"Error extracting text from TXT: {str(e)}")
        return ""


def extract_text(file_path: str) -> str:
    """
    Extract text from various file formats.
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".pdf":
        return ocr_pdf(file_path)
    elif ext in [".docx", ".doc"]:
        return extract_text_from_docx(file_path)
    elif ext in [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]:
        return ocr_image(file_path)
    elif ext == ".txt":
        return extract_text_from_txt(file_path)
    else:
        return ""