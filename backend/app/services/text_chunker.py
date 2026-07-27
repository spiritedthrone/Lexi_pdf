"""Dynamic Token-Based Text Chunking Service for PDF Summarizer."""

import re
from typing import Dict, List, Any

# Pre-compiled regex for fast sentence splitting
SENTENCE_SPLIT_REGEX = re.compile(r'(?<=[.!?])\s+')

# In-memory storage for document chunks indexed by file_id
chunk_store: Dict[str, List[Dict[str, Any]]] = {}

MAX_CHUNK_TOKENS = 2000  # Target maximum tokens per chunk


def estimate_tokens(text: str) -> int:
    """Estimate token count for a string (~4 characters per token)."""
    if not text:
        return 0
    return max(1, int(len(text) / 4.0))


def split_into_sentences(text: str) -> List[str]:
    """Split text into complete sentences, preserving sentence boundaries."""
    if not text or not text.strip():
        return []
    sentences = SENTENCE_SPLIT_REGEX.split(text)
    cleaned = [s.strip() for s in sentences if s.strip()]
    if not cleaned and text.strip():
        return [text.strip()]
    return cleaned


def create_chunks(
    file_id: str,
    pages: List[Dict[str, Any]],
    max_tokens: int = MAX_CHUNK_TOKENS
) -> List[Dict[str, Any]]:
    """
    Dynamically groups page text into chunks up to ~2000 tokens based on text density.
    Never splits sentences across chunk boundaries and preserves page sequence.
    """
    if not pages:
        return []

    chunks: List[Dict[str, Any]] = []
    current_sentences: List[str] = []
    current_tokens = 0
    start_page = pages[0]["page_number"]
    current_end_page = start_page
    chunk_index = 0

    for page in pages:
        page_num = page["page_number"]
        page_text = page.get("text", "").strip()
        if not page_text:
            continue

        page_sentences = split_into_sentences(page_text)

        for sentence in page_sentences:
            sentence_tokens = estimate_tokens(sentence)

            # If adding this sentence exceeds target token limit and we already have content
            if current_tokens + sentence_tokens > max_tokens and current_sentences:
                full_chunk_text = " ".join(current_sentences)
                chunks.append({
                    "chunk_id": f"{file_id}_chunk_{chunk_index}",
                    "chunk_index": chunk_index,
                    "start_page": start_page,
                    "end_page": current_end_page,
                    "sentences_count": len(current_sentences),
                    "word_count": len(full_chunk_text.split()),
                    "character_count": len(full_chunk_text),
                    "estimated_tokens": current_tokens,
                    "text": full_chunk_text,
                })
                chunk_index += 1

                # Reset for next chunk
                current_sentences = [sentence]
                current_tokens = sentence_tokens
                start_page = page_num
                current_end_page = page_num
            else:
                current_sentences.append(sentence)
                current_tokens += sentence_tokens
                current_end_page = page_num

    # Flush any remaining sentences in final chunk
    if current_sentences:
        full_chunk_text = " ".join(current_sentences)
        chunks.append({
            "chunk_id": f"{file_id}_chunk_{chunk_index}",
            "chunk_index": chunk_index,
            "start_page": start_page,
            "end_page": current_end_page,
            "sentences_count": len(current_sentences),
            "word_count": len(full_chunk_text.split()),
            "character_count": len(full_chunk_text),
            "estimated_tokens": current_tokens,
            "text": full_chunk_text,
        })

    import logging
    logger = logging.getLogger(__name__)
    # Store chunks
    chunk_store[file_id] = chunks
    logger.info(f"[Stage 8] Chunks stored for file_id: {file_id}: count={len(chunks)}")
    return chunks



def get_chunks(file_id: str) -> List[Dict[str, Any]]:
    """Retrieve stored text chunks for a given file_id, auto-generating from extracted text if absent."""
    chunks = chunk_store.get(file_id, [])
    if not chunks:
        from app.services.pdf_extractor import get_extracted_pdf
        pdf_data = get_extracted_pdf(file_id)
        if pdf_data and pdf_data.get("pages"):
            chunks = create_chunks(file_id, pdf_data["pages"])
    return chunks

