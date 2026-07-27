import logging
import time
from typing import Dict, List, Any

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

logger = logging.getLogger(__name__)

# In-memory storage for extracted PDF documents
extracted_pdf_store: Dict[str, Dict[str, Any]] = {}


def extract_pdf_text(file_id: str, content: bytes, filename: str) -> Dict[str, Any]:
    """
    Fast, memory-efficient PDF text extraction using PyMuPDF.
    Context manager guarantees immediate document handle & buffer closure.
    """
    if fitz is None:
        raise RuntimeError("PyMuPDF (fitz) is not installed. Please run pip install -r requirements.txt")

    pages: List[Dict[str, Any]] = []
    total_characters = 0

    with fitz.open(stream=content, filetype="pdf") as doc:
        for index, page in enumerate(doc):
            # Extract plain text directly with PyMuPDF fast text layout flags
            text = page.get_text("text", flags=fitz.TEXT_DEHYPHENATE).strip()
            char_count = len(text)
            total_characters += char_count

            pages.append({
                "page_number": index + 1,
                "text": text,
                "char_count": char_count
            })

    extracted_data = {
        "file_id": file_id,
        "filename": filename,
        "total_pages": len(pages),
        "total_characters": total_characters,
        "created_at": time.time(),
        "pages": pages
    }

    # Memory-efficient storage
    extracted_pdf_store[file_id] = extracted_data
    logger.info(f"[Stage 3] PDF saved in memory store for file_id: {file_id}")
    return extracted_data


def get_extracted_pdf(file_id: str) -> Dict[str, Any]:
    """Retrieve saved extracted pages by file ID."""
    return extracted_pdf_store.get(file_id)
