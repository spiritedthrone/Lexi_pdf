"""Backend Integration Tests for FastAPI Endpoints."""

import pytest
import sys
from unittest.mock import patch, MagicMock

# Ensure fitz mock exists in sys.modules if not installed globally
if "fitz" not in sys.modules:
    sys.modules["fitz"] = MagicMock()

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

from app.main import app


@pytest.mark.skipif(not HAS_HTTPX, reason="httpx module not installed in host environment")
@pytest.mark.asyncio
async def test_health_check_endpoint():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


@pytest.mark.skipif(not HAS_HTTPX, reason="httpx module not installed in host environment")
@pytest.mark.asyncio
async def test_upload_pdf_integration():
    mock_doc = MagicMock()
    mock_doc.is_encrypted = False
    mock_page = MagicMock()
    mock_page.get_text.return_value = "Sample text for integration test."
    mock_doc.__iter__.return_value = [mock_page]
    mock_doc.__len__.return_value = 1
    mock_doc.__enter__.return_value = mock_doc
    mock_doc.__exit__.return_value = False

    with patch("app.api.v1.upload.fitz.open", return_value=mock_doc), \
         patch("app.services.pdf_extractor.fitz.open", return_value=mock_doc):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
            files = {"file": ("test_doc.pdf", b"%PDF-1.4...", "application/pdf")}
            response = await ac.post("/api/v1/upload/", files=files)

            assert response.status_code == 201
            data = response.json()
            assert "id" in data
            assert data["filename"] == "test_doc.pdf"
            assert data["page_count"] == 1

            file_id = data["id"]

            # Test GET text
            text_res = await ac.get(f"/api/v1/upload/{file_id}/text")
            assert text_res.status_code == 200
            assert text_res.json()["file_id"] == file_id

            # Test GET chunks
            chunks_res = await ac.get(f"/api/v1/upload/{file_id}/chunks")
            assert chunks_res.status_code == 200
            assert chunks_res.json()["chunk_count"] == 1


@pytest.mark.skipif(not HAS_HTTPX, reason="httpx module not installed in host environment")
@pytest.mark.asyncio
async def test_invalid_file_upload_rejection():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        files = {"file": ("invalid.txt", b"Plain text content", "text/plain")}
        response = await ac.post("/api/v1/upload/", files=files)
        assert response.status_code == 400
        assert "Invalid file format" in response.json()["detail"]
