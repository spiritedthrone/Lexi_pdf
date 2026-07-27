"""Unit tests for Output Merger Service."""

from app.services.output_merger import merge_ai_outputs, preserve_heading_formatting


def test_preserve_heading_formatting():
    input_text = "Chapter 1 Introduction\n\nThis is paragraph one.\n\nMAIN OVERVIEW"
    formatted = preserve_heading_formatting(input_text)

    assert "## Chapter 1 Introduction" in formatted
    assert "### Main Overview" in formatted


def test_merge_ai_outputs():
    chunks = [
        {
            "chunk_index": 1,
            "simplified_text": "Chapter 2 Details\n\nThis is part two.",
        },
        {
            "chunk_index": 0,
            "simplified_text": "Chapter 1 Basics\n\nThis is part one.",
        },
    ]

    result = merge_ai_outputs(chunks, text_key="simplified_text")

    # Order must be sorted by chunk_index (0 before 1)
    assert result["total_paragraphs"] == 4
    assert result["merged_text"].index("Chapter 1 Basics") < result["merged_text"].index("Chapter 2 Details")
    assert len(result["chapters_found"]) == 2
