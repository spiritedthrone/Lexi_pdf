import logging
from fastapi import APIRouter, HTTPException, status, Response
from pydantic import BaseModel
from app.services.simplifier_service import (
    simplify_text_chunk,
    simplify_document,
    get_simplified_document,
)
from app.services.gemini_service import GeminiQuotaExceededError
from app.services.pdf_extractor import get_extracted_pdf
from app.services.pdf_generator import create_simplified_pdf

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/simplify", tags=["Simplification"])


class ChunkSimplifyRequest(BaseModel):
    text: str


@router.post("/chunk", status_code=status.HTTP_200_OK)
async def simplify_single_chunk(payload: ChunkSimplifyRequest):
    """Simplify a single provided text chunk using Google Gemini API."""
    if not payload.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text cannot be empty."
        )
    try:
        result = await simplify_text_chunk(payload.text)
        return result
    except GeminiQuotaExceededError as qe:
        logger.error(f"Quota error in simplify_single_chunk: {qe}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(qe)
        )
    except Exception as e:
        logger.error(f"Error in simplify_single_chunk: {e}", exc_info=True)
        err_msg = str(e)
        if "quota" in err_msg.lower() or "429" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Gemini API quota exceeded. Please wait until your quota resets or use a different API key."
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Text simplification failed: {err_msg}"
        )


@router.post("/{file_id}", status_code=status.HTTP_200_OK)
async def simplify_pdf_document(file_id: str):
    """Simplify all chunks of an uploaded PDF document chunk by chunk."""
    logger.info(f"[Stage 9] Simplify endpoint receives file_id: {file_id}")
    try:
        result = await simplify_document(file_id)
        return result
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve)
        )
    except GeminiQuotaExceededError as qe:
        logger.error(f"Quota error in simplify_pdf_document: {qe}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(qe)
        )
    except Exception as e:
        logger.error(f"Error in simplify_pdf_document: {e}", exc_info=True)
        err_msg = str(e)
        if "quota" in err_msg.lower() or "429" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Gemini API quota exceeded. Please wait until your quota resets or use a different API key."
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document simplification failed: {err_msg}"
        )


@router.get("/{file_id}", status_code=status.HTTP_200_OK)
async def get_simplified_pdf(file_id: str):
    """Retrieve existing simplified text results for a PDF file."""
    data = get_simplified_document(file_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No simplified result found for PDF ID {file_id}."
        )
    return data


@router.get("/{file_id}/download")
async def download_simplified_pdf(file_id: str):
    """Generate and download the rewritten output as a PDF file."""
    simplified_data = get_simplified_document(file_id)
    if not simplified_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No simplified result found for PDF ID {file_id}. Please run simplification first."
        )

    pdf_info = get_extracted_pdf(file_id)
    original_filename = pdf_info.get("filename", "document.pdf") if pdf_info else "document.pdf"
    download_filename = f"simplified_{original_filename}"

    pdf_bytes = create_simplified_pdf(
        filename=original_filename,
        full_text=simplified_data["full_text"],
        chunks=simplified_data.get("chunks", [])
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{download_filename}"'
        }
    )

