import logging
import uuid
import fitz  # PyMuPDF
from fastapi import APIRouter, File, UploadFile, HTTPException, status
from app.services.pdf_extractor import extract_pdf_text, get_extracted_pdf
from app.services.text_chunker import create_chunks, get_chunks

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["Upload"])

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB limit for large PDF support


@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_pdf(file: UploadFile = File(...)):
    """Upload, validate, extract text, and chunk PDF document with enhanced error handling."""
    # 1. Validate extension and MIME type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only PDF files (.pdf) are supported.",
        )
    if file.content_type and file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid content type. Uploaded file must be application/pdf.",
        )

    # 2. Read file content and validate size
    try:
        content = await file.read()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file payload: {str(exc)}",
        )

    file_size = len(content)

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded PDF file is completely empty (0 bytes).",
        )

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size ({file_size // (1024 * 1024)}MB) exceeds maximum limit of {MAX_FILE_SIZE // (1024 * 1024)}MB.",
        )

    # [Stage 1] Upload received
    logger.info(f"[Stage 1] Upload received: filename={file.filename}, size={file_size} bytes")

    # [Stage 2] file_id generated
    file_id = str(uuid.uuid4())
    logger.info(f"[Stage 2] file_id generated: {file_id}")

    # 3. Check for PDF encryption / password protection
    try:
        doc = fitz.open(stream=content, filetype="pdf")
        if doc.is_encrypted:
            doc.close()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded PDF is password-protected or encrypted. Please remove encryption and try again.",
            )
        doc.close()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid or corrupted PDF file structure: {str(exc)}",
        )

    # 4. Extract text preserving page numbers & order using PyMuPDF
    try:
        extracted = extract_pdf_text(file_id=file_id, content=content, filename=file.filename)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to parse and extract PDF text: {str(e)}",
        )

    # [Stage 4] Number of pages extracted & [Stage 5] Total extracted characters
    total_chars = extracted.get("total_characters", 0)
    page_count = extracted.get("total_pages", 0)
    logger.info(f"[Stage 4] Number of pages extracted: {page_count}")
    logger.info(f"[Stage 5] Total extracted characters: {total_chars}")

    if total_chars == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No extractable text found in PDF document. Scanned or image-only PDFs are not supported.",
        )

    # [Stage 6] Chunking started & [Stage 7] Number of chunks created
    logger.info(f"[Stage 6] Chunking started for file_id: {file_id}")
    chunks = create_chunks(file_id=file_id, pages=extracted["pages"])
    logger.info(f"[Stage 7] Number of chunks created: {len(chunks)}")



    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No text chunks created for PDF file_id: {file_id}.",
        )

    return {
        "id": file_id,
        "filename": file.filename,
        "size_bytes": file_size,
        "page_count": page_count,
        "total_characters": total_chars,
        "chunk_count": len(chunks),
        "pages": extracted["pages"],
        "chunks": chunks,
        "message": "PDF uploaded, text extracted, and chunked successfully.",
    }



@router.get("/{file_id}/text")
async def get_pdf_text(file_id: str):
    """Retrieve saved extracted text and page structure for a PDF."""
    data = get_extracted_pdf(file_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Extracted PDF text for ID {file_id} not found.",
        )
    return data


@router.get("/{file_id}/chunks")
async def get_pdf_chunks(file_id: str):
    """Retrieve stored text chunks for a PDF by file ID."""
    chunks = get_chunks(file_id)
    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No chunks found for PDF ID {file_id}.",
        )
    return {"file_id": file_id, "chunk_count": len(chunks), "chunks": chunks}


