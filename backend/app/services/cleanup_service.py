"""Automatic background cleanup service for temporary PDF files and artifact stores."""

import asyncio
import logging
import time
from typing import Dict, Set
from app.services.pdf_extractor import extracted_pdf_store
from app.services.text_chunker import chunk_store
from app.services.simplifier_service import simplified_store

logger = logging.getLogger(__name__)

# TTL for temporary document artifacts (24 hours in seconds)
CLEANUP_TTL_SECONDS = 24 * 3600

# Set of active job file_ids currently being processed
active_jobs: Set[str] = set()


def mark_job_active(file_id: str):
    """Mark a document processing job as active."""
    active_jobs.add(file_id)


def mark_job_completed(file_id: str):
    """Mark a document processing job as completed."""
    active_jobs.discard(file_id)


def cleanup_expired_artifacts(ttl_seconds: int = CLEANUP_TTL_SECONDS) -> Dict[str, int]:
    """
    Scans in-memory stores and temporary files for entries older than 24 hours.
    Skips active jobs currently being processed.
    """
    now = time.time()
    deleted_count = 0

    # 1. Clean up extracted PDF store
    expired_pdf_ids = [
        fid for fid, data in extracted_pdf_store.items()
        if fid not in active_jobs and (now - data.get("created_at", now)) > ttl_seconds
    ]
    for fid in expired_pdf_ids:
        extracted_pdf_store.pop(fid, None)
        deleted_count += 1

    # 2. Clean up chunk store
    expired_chunk_ids = [
        fid for fid in chunk_store.keys()
        if fid not in active_jobs and fid not in extracted_pdf_store
    ]
    for fid in expired_chunk_ids:
        chunk_store.pop(fid, None)

    # 3. Clean up simplified store
    expired_simplified_ids = [
        fid for fid in simplified_store.keys()
        if fid not in active_jobs and fid not in extracted_pdf_store
    ]
    for fid in expired_simplified_ids:
        simplified_store.pop(fid, None)

    if deleted_count > 0:
        logger.info(f"Background cleanup task purged {deleted_count} expired PDF document artifacts (>24h old).")

    return {"deleted_count": deleted_count}


async def periodic_cleanup_task(interval_seconds: int = 3600):
    """Background task loop that runs cleanup every hour."""
    while True:
        try:
            cleanup_expired_artifacts()
        except Exception as exc:
            logger.error(f"Error during background cleanup execution: {exc}")
        await asyncio.sleep(interval_seconds)
