"""Unit tests for automatic cleanup service."""

import time
from app.services.cleanup_service import (
    cleanup_expired_artifacts,
    mark_job_active,
    mark_job_completed,
)
from app.services.pdf_extractor import extracted_pdf_store
from app.services.text_chunker import chunk_store
from app.services.simplifier_service import simplified_store


def test_cleanup_expired_artifacts():
    now = time.time()
    old_time = now - 90000  # 25 hours ago

    # Setup expired entry
    extracted_pdf_store["expired_doc"] = {"file_id": "expired_doc", "created_at": old_time}
    chunk_store["expired_doc"] = [{"chunk_id": "c1"}]
    simplified_store["expired_doc"] = {"full_text": "text"}

    # Setup recent entry (<24h)
    extracted_pdf_store["recent_doc"] = {"file_id": "recent_doc", "created_at": now}
    chunk_store["recent_doc"] = [{"chunk_id": "c2"}]

    # Setup active job entry (old timestamp, but active)
    extracted_pdf_store["active_doc"] = {"file_id": "active_doc", "created_at": old_time}
    mark_job_active("active_doc")

    # Execute cleanup
    result = cleanup_expired_artifacts(ttl_seconds=86400)

    assert result["deleted_count"] == 1
    assert "expired_doc" not in extracted_pdf_store
    assert "recent_doc" in extracted_pdf_store
    assert "active_doc" in extracted_pdf_store

    # Cleanup test state
    mark_job_completed("active_doc")
    extracted_pdf_store.clear()
    chunk_store.clear()
    simplified_store.clear()
