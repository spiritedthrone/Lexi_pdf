"""Google Gemini API Service for PDF Text Processing & Simplification."""

import asyncio
import logging
import re
from typing import Optional, Dict, Any
from google import genai
from google.genai import types
from google.genai.errors import APIError
from app.core.config import settings

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT = (
    "You are an expert AI text processor. Summarize or simplify the provided PDF text chunk "
    "clearly and accurately while preserving key facts and details."
)

QUOTA_EXCEEDED_USER_MESSAGE = (
    "Gemini API quota exceeded. Please wait until your quota resets or use a different API key."
)


class GeminiQuotaExceededError(Exception):
    """Raised when Google Gemini API quota is exceeded."""

    def __init__(self, message: str = QUOTA_EXCEEDED_USER_MESSAGE, retry_after: Optional[float] = None):
        super().__init__(message)
        self.message = message
        self.retry_after = retry_after


def parse_retry_after(error_obj: Any) -> Optional[float]:
    """
    Parses Retry-After / retry delay duration in seconds if provided in response headers or error payload.
    Returns None if no specific retry delay duration is specified.
    """
    # 1. Check HTTP response headers if attached to exception
    if hasattr(error_obj, "headers") and error_obj.headers:
        headers = error_obj.headers
        for key in ("Retry-After", "retry-after", "retry_after"):
            if key in headers:
                try:
                    val = float(headers[key])
                    if val > 0:
                        return val
                except (ValueError, TypeError):
                    pass

    # 2. Check string representation / error message for retry duration patterns
    err_str = str(error_obj)

    # Pattern: "Please retry in 38.355944677s" or "retry in 38s"
    match = re.search(r"retry\s+in\s+([0-9]+(?:\.[0-9]+)?)s", err_str, re.IGNORECASE)
    if match:
        return float(match.group(1))

    # Pattern: "'retryDelay': '38s'" or "'retryDelay': 38"
    match = re.search(r"['\"]?retryDelay['\"]?\s*:\s*['\"]?([0-9]+(?:\.[0-9]+)?)s?['\"]?", err_str, re.IGNORECASE)
    if match:
        return float(match.group(1))

    # Pattern: "retryAfter: 38"
    match = re.search(r"retryAfter\s*:\s*([0-9]+(?:\.[0-9]+)?)", err_str, re.IGNORECASE)
    if match:
        return float(match.group(1))

    return None


def is_quota_error(exc: Exception) -> bool:
    """Detects whether an exception corresponds to an HTTP 429 / Quota / Rate-limit error."""
    if isinstance(exc, APIError):
        code_str = str(getattr(exc, "code", ""))
        if "429" in code_str or "RESOURCE_EXHAUSTED" in code_str.upper():
            return True
    err_str = str(exc).lower()
    return "429" in err_str or "resource_exhausted" in err_str or "quota exceeded" in err_str


class GeminiService:
    """Modular Google Gemini API client for single chunk processing with retry & rate-limit handling."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self._custom_api_key = api_key
        self._custom_model = model

    @property
    def api_key(self) -> str:
        return self._custom_api_key or settings.resolved_api_key

    @property
    def model(self) -> str:
        return self._custom_model or settings.active_model

    def _get_client(self) -> genai.Client:
        api_key = self.api_key
        if not api_key:
            raise ValueError(
                "Gemini API key is not configured. Set GEMINI_API_KEY in your .env file."
            )
        return genai.Client(api_key=api_key)

    async def process_chunk(
        self,
        chunk_text: str,
        system_prompt: str,
        user_prefix: str = "Process the following text:\n\n",
        max_retries: int = 3,
        initial_backoff: float = 1.0,
    ) -> Dict[str, Any]:
        """Sends ONE text chunk to Google Gemini API for processing/simplification."""
        client = self._get_client()
        model_name = self.model

        prompt_content = f"{user_prefix}{chunk_text}"
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.3,
        )

        logger.info("--- GEMINI REQUEST START ---")
        logger.info(f"Model: {model_name}")
        logger.info(f"Prompt length: {len(prompt_content)} chars")

        last_exception = None

        for attempt in range(1, max_retries + 1):
            try:
                response = await client.aio.models.generate_content(
                    model=model_name,
                    contents=prompt_content,
                    config=config,
                )

                result_content = response.text.strip() if response.text else ""
                tokens_used = 0
                if hasattr(response, "usage_metadata") and response.usage_metadata:
                    tokens_used = getattr(response.usage_metadata, "total_token_count", 0) or 0

                logger.info(f"--- GEMINI RESPONSE (Attempt {attempt}) ---")
                logger.info(f"Content length: {len(result_content)} chars | Tokens used: {tokens_used}")

                return {
                    "content": result_content,
                    "model": model_name,
                    "tokens_used": tokens_used,
                }

            except GeminiQuotaExceededError:
                # Already a clean user-facing error — re-raise immediately
                raise

            except Exception as exc:
                # Requirement 5: Log full API response in the backend for debugging
                logger.error(
                    f"Full Gemini API Exception on attempt {attempt}/{max_retries}: {repr(exc)} | Details: {str(exc)}",
                    exc_info=True,
                )
                last_exception = str(exc)

                # Requirement 1 & 2: Detect HTTP 429 quota errors — raise immediately, never retry
                if is_quota_error(exc):
                    retry_delay = parse_retry_after(exc)
                    logger.error(
                        f"HTTP 429 Quota Error detected. retry_after={retry_delay}s. "
                        "Raising GeminiQuotaExceededError immediately (no retry on quota errors)."
                    )
                    # Requirement 3 & 4: Raise clean user-facing exception, never expose raw API message
                    raise GeminiQuotaExceededError(
                        message=QUOTA_EXCEEDED_USER_MESSAGE,
                        retry_after=retry_delay,
                    )

                # For non-quota transient errors only: exponential backoff retry
                if attempt < max_retries:
                    backoff = initial_backoff * (2 ** (attempt - 1))
                    logger.warning(f"Transient Gemini error. Retrying in {backoff}s (attempt {attempt + 1}/{max_retries})...")
                    await asyncio.sleep(backoff)

        raise RuntimeError(f"Gemini API processing failed: {last_exception}")

    async def summarize_chunk(
        self,
        chunk_text: str,
        custom_prompt: Optional[str] = None,
        max_retries: int = 3,
        initial_backoff: float = 1.0,
    ) -> Dict[str, Any]:
        """Sends ONE text chunk to Gemini API for summarization."""
        prompt = custom_prompt or DEFAULT_SYSTEM_PROMPT
        result = await self.process_chunk(
            chunk_text=chunk_text,
            system_prompt=prompt,
            user_prefix="Summarize the following text:\n\n",
            max_retries=max_retries,
            initial_backoff=initial_backoff,
        )
        return {
            "summary": result["content"],
            "model": result["model"],
            "tokens_used": result["tokens_used"],
        }


gemini_service = GeminiService()

