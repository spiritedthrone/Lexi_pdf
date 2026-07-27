"""AI Text Simplification Service using Google Gemini API."""

import asyncio
from typing import Dict, Any
from app.services.gemini_service import gemini_service
from app.services.text_chunker import get_chunks
from app.services.output_merger import merge_ai_outputs

SIMPLIFIER_SYSTEM_PROMPT = """You are an expert textbook editor.

Rewrite the text into simpler English.

Rules:
- Never summarize.
- Never remove information.
- Keep easy sentences almost unchanged.
- Rewrite only difficult sentences.
- Simplify difficult words.
- Explain technical terms only when necessary.
- Do not explain every sentence.
- Keep figures, tables, equations and references unchanged.
- Preserve chapter flow.
- Return only rewritten text."""

# Storage for simplified text results
simplified_store: Dict[str, Dict[str, Any]] = {}

MAX_CONCURRENT_CHUNKS = 3
chunk_semaphore = asyncio.Semaphore(MAX_CONCURRENT_CHUNKS)


async def simplify_text_chunk(chunk_text: str) -> Dict[str, Any]:
    """Simplifies a single text chunk according to textbook editor rules."""
    result = await gemini_service.process_chunk(
        chunk_text=chunk_text,
        system_prompt=SIMPLIFIER_SYSTEM_PROMPT,
        user_prefix="Rewrite the following text into simpler English:\n\n"
    )
    return {
        "simplified_text": result["content"],
        "model": result["model"],
        "tokens_used": result["tokens_used"],
    }


async def simplify_text_chunk_bounded(chunk: Dict[str, Any]) -> Dict[str, Any]:
    """Process a chunk under concurrency semaphore control."""
    async with chunk_semaphore:
        res = await simplify_text_chunk(chunk["text"])
        return {
            "chunk_id": chunk["chunk_id"],
            "chunk_index": chunk["chunk_index"],
            "start_page": chunk["start_page"],
            "end_page": chunk["end_page"],
            "original_text": chunk["text"],
            "simplified_text": res["simplified_text"],
        }


import logging
logger = logging.getLogger(__name__)

async def simplify_document(file_id: str) -> Dict[str, Any]:
    """
    Simplifies document chunks in parallel (bounded concurrency=3) for high performance,
    then merges output sequentially preserving exact document order.
    """
    chunks = get_chunks(file_id)
    logger.info(f"[Stage 10] Number of retrieved chunks: {len(chunks)}")
    if not chunks:

        raise ValueError(f"No text chunks found for PDF file_id: {file_id}")


    # Process all chunks concurrently up to semaphore limit
    tasks = [simplify_text_chunk_bounded(chunk) for chunk in chunks]
    simplified_chunks = await asyncio.gather(*tasks)

    # Sort chunks by index to guarantee preserved sequence
    sorted_chunks = sorted(list(simplified_chunks), key=lambda c: c["chunk_index"])

    # Merge AI outputs preserving sequence, headings, paragraphs, and chapters
    merged_data = merge_ai_outputs(sorted_chunks, text_key="simplified_text")

    result_data = {
        "file_id": file_id,
        "total_chunks": len(sorted_chunks),
        "full_text": merged_data["merged_text"],
        "total_words": merged_data["total_words"],
        "total_paragraphs": merged_data["total_paragraphs"],
        "chapters_found": merged_data["chapters_found"],
        "chunks": sorted_chunks,
    }

    simplified_store[file_id] = result_data
    return result_data


def get_simplified_document(file_id: str) -> Dict[str, Any]:
    """Retrieve simplified document results."""
    return simplified_store.get(file_id)
