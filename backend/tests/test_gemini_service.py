"""Unit tests for GeminiService module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.gemini_service import GeminiService


@pytest.mark.asyncio
async def test_gemini_service_process_chunk_success():
    service = GeminiService(api_key="test_key", model="gemini-2.0-flash")

    mock_response = MagicMock()
    mock_response.text = "This is simplified text."
    mock_response.usage_metadata = MagicMock()
    mock_response.usage_metadata.total_token_count = 42

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

    with patch("app.services.gemini_service.genai.Client", return_value=mock_client):
        result = await service.process_chunk(
            chunk_text="Difficult original text.",
            system_prompt="Simplify this text.",
        )

        assert result["content"] == "This is simplified text."
        assert result["model"] == "gemini-2.0-flash"
        assert result["tokens_used"] == 42


@pytest.mark.asyncio
async def test_gemini_service_missing_api_key():
    service = GeminiService(api_key="", model="gemini-2.0-flash")
    with patch("app.services.gemini_service.settings.GEMINI_API_KEY", ""):
        with pytest.raises(ValueError, match="Gemini API key is not configured"):
            await service.process_chunk(
                chunk_text="Test",
                system_prompt="Test prompt",
            )
