"""Application Configuration Settings."""

import os
import logging
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    PROJECT_NAME: str = "PDF Summarizer API"
    API_V1_STR: str = "/api/v1"
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # Runtime-resolved model override if set dynamically
    _resolved_model: Optional[str] = None

    model_config = ConfigDict(
        case_sensitive=True,
        env_file=(".env", "../.env", "backend/.env"),
        extra="ignore"
    )

    @property
    def resolved_api_key(self) -> str:
        """Resolve API key from settings or environment variable."""
        return self.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")

    @property
    def active_model(self) -> str:
        """Return the active Gemini model."""
        return self._resolved_model or self.GEMINI_MODEL or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    def set_resolved_model(self, model_id: str) -> None:
        """Set the runtime-resolved model."""
        object.__setattr__(self, '_resolved_model', model_id)


settings = Settings()

