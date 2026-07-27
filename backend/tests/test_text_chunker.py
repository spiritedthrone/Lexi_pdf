"""Unit tests for Text Chunker Service."""

from app.services.text_chunker import create_chunks, split_into_sentences, estimate_tokens, get_chunks


def test_split_into_sentences():
    text = "This is sentence one. This is sentence two! Is this sentence three?"
    sentences = split_into_sentences(text)
    assert len(sentences) == 3
    assert sentences[0] == "This is sentence one."
    assert sentences[1] == "This is sentence two!"
    assert sentences[2] == "Is this sentence three?"


def test_estimate_tokens():
    text = "A" * 400
    assert estimate_tokens(text) == 100


def test_create_chunks_dynamic_token_limit():
    pages = [
        {"page_number": 1, "text": "First page text. " + ("Word " * 200)},
        {"page_number": 2, "text": "Second page text. " + ("Data " * 200)},
        {"page_number": 3, "text": "Third page text. " + ("Info " * 200)},
    ]
    file_id = "chunk_token_test"

    # Set low max_tokens limit (50 tokens) to trigger multi-chunk splitting
    chunks = create_chunks(file_id, pages, max_tokens=50)

    assert len(chunks) > 1
    assert "estimated_tokens" in chunks[0]
    assert chunks[0]["start_page"] == 1
    assert get_chunks(file_id) == chunks
