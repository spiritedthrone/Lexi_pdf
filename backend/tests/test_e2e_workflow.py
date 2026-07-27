"""End-to-end integration test for the entire pipeline using FastAPI ASGITransport."""

import pytest
import sys
from unittest.mock import patch, MagicMock, AsyncMock

if "fitz" not in sys.modules:
    sys.modules["fitz"] = MagicMock()

import httpx
from app.main import app


@pytest.mark.asyncio
async def test_full_e2e_workflow_gemini():
    """Verify Upload → Extract → Chunk → Simplify (Gemini) → Merge → Download PDF."""
    
    # 1. Mock PyMuPDF / fitz PDF extraction
    mock_doc = MagicMock()
    mock_doc.is_encrypted = False
    mock_page = MagicMock()
    mock_page.get_text.return_value = "This is a complex sentence that needs simplification."
    mock_doc.__iter__.return_value = [mock_page]
    mock_doc.__len__.return_value = 1
    mock_doc.__enter__.return_value = mock_doc
    mock_doc.__exit__.return_value = False

    # 2. Mock Gemini API response
    mock_gemini_res = {
        "content": "This is an easy sentence.",
        "model": "gemini-2.0-flash",
        "tokens_used": 15,
    }

    with patch("app.api.v1.upload.fitz.open", return_value=mock_doc), \
         patch("app.services.pdf_extractor.fitz.open", return_value=mock_doc), \
         patch("app.services.gemini_service.gemini_service.process_chunk", AsyncMock(return_value=mock_gemini_res)):

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
            # Stage 1: Upload PDF
            files = {"file": ("test_doc.pdf", b"%PDF-1.4...", "application/pdf")}
            upload_resp = await ac.post("/api/v1/upload/", files=files)
            assert upload_resp.status_code == 201
            data = upload_resp.json()
            file_id = data["id"]
            assert data["chunk_count"] == 1

            # Stage 2: Extract & Chunk Verification
            chunks_resp = await ac.get(f"/api/v1/upload/{file_id}/chunks")
            assert chunks_resp.status_code == 200
            assert len(chunks_resp.json()["chunks"]) == 1

            # Stage 3: Simplify via Gemini Service
            simplify_resp = await ac.post(f"/api/v1/simplify/{file_id}")
            assert simplify_resp.status_code == 200
            simp_data = simplify_resp.json()
            assert simp_data["file_id"] == file_id
            assert "This is an easy sentence." in simp_data["full_text"]

            # Stage 4: Download PDF
            download_resp = await ac.get(f"/api/v1/simplify/{file_id}/download")
            assert download_resp.status_code == 200
            assert download_resp.headers["content-type"] == "application/pdf"
            assert len(download_resp.content) > 0
