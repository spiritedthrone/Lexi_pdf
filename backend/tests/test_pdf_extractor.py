"""Unit tests for PDF Text Extractor Service."""

import sys
from unittest.mock import MagicMock, patch

# Ensure fitz mock exists in sys.modules if not installed globally
mock_fitz = MagicMock()
if "fitz" not in sys.modules:
    sys.modules["fitz"] = mock_fitz

from app.services.pdf_extractor import extract_pdf_text, get_extracted_pdf


def test_extract_pdf_text_success():
    file_id = "test_file_123"

    mock_page_1 = MagicMock()
    mock_page_1.get_text.return_value = "Page 1 content about science."

    mock_page_2 = MagicMock()
    mock_page_2.get_text.return_value = "Page 2 content about math."

    mock_doc = MagicMock()
    mock_doc.__iter__.return_value = [mock_page_1, mock_page_2]
    mock_doc.__len__.return_value = 2
    mock_doc.__enter__.return_value = mock_doc
    mock_doc.__exit__.return_value = False

    with patch("app.services.pdf_extractor.fitz") as mock_fitz_svc:
        mock_fitz_svc.open.return_value = mock_doc
        mock_fitz_svc.TEXT_DEHYPHENATE = 1

        result = extract_pdf_text(file_id, b"%PDF-1.4...", "test.pdf")

        assert result["file_id"] == file_id
        assert result["total_pages"] == 2
        assert len(result["pages"]) == 2
        assert result["pages"][0]["page_number"] == 1
        assert "science" in result["pages"][0]["text"]
        assert result["pages"][1]["page_number"] == 2
        assert "math" in result["pages"][1]["text"]

        retrieved = get_extracted_pdf(file_id)
        assert retrieved is not None
        assert retrieved["file_id"] == file_id
