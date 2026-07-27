"""AI Output Merger Service to preserve sequence, headings, paragraphs, and chapters."""

import re
from typing import List, Dict, Any


def preserve_heading_formatting(text: str) -> str:
    """Ensure headings (e.g., Chapter X, Section Y, ALL CAPS headers) maintain Markdown heading style."""
    lines = text.split("\n")
    processed_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            processed_lines.append("")
            continue

        # If line looks like a Chapter title, make it H2
        if re.match(r'^(Chapter|UNIT|SECTION)\s+\d+.*', stripped, re.IGNORECASE):
            if not stripped.startswith("#"):
                processed_lines.append(f"## {stripped}")
            else:
                processed_lines.append(stripped)
        # If line looks like a major section heading (ALL CAPS short line)
        elif stripped.isupper() and len(stripped) < 60 and not stripped.startswith("#"):
            processed_lines.append(f"### {stripped.title()}")
        else:
            processed_lines.append(line)

    return "\n".join(processed_lines)


def merge_ai_outputs(chunks: List[Dict[str, Any]], text_key: str = "simplified_text") -> Dict[str, Any]:
    """
    Sequentially merges processed chunk outputs while preserving exact chunk order,
    paragraph spacing, heading structure, and chapter breaks.
    """
    if not chunks:
        return {
            "merged_text": "",
            "total_words": 0,
            "total_paragraphs": 0,
            "chapters_found": [],
        }

    # 1. Sort chunks by chunk_index to strictly preserve page/reading order
    sorted_chunks = sorted(chunks, key=lambda c: c.get("chunk_index", 0))

    merged_sections: List[str] = []
    chapters_found: List[str] = []

    for chunk in sorted_chunks:
        raw_text = chunk.get(text_key, chunk.get("text", "")).strip()
        if not raw_text:
            continue

        # Format headings and preserve paragraph breaks
        formatted_text = preserve_heading_formatting(raw_text)

        # Detect any chapter titles in this chunk
        for line in formatted_text.split("\n"):
            if re.match(r'^#{1,3}\s+(Chapter|UNIT|SECTION)\s+\d+', line, re.IGNORECASE):
                chapters_found.append(line.replace("#", "").strip())

        merged_sections.append(formatted_text)

    # Combine sections with clear paragraph spacing
    full_merged_text = "\n\n".join(merged_sections)

    # Normalize multiple blank lines to double newlines (preserving paragraphs)
    full_merged_text = re.sub(r'\n{3,}', '\n\n', full_merged_text)

    # Count statistics
    paragraphs = [p for p in full_merged_text.split("\n\n") if p.strip()]
    word_count = len(full_merged_text.split())

    return {
        "merged_text": full_merged_text,
        "total_words": word_count,
        "total_paragraphs": len(paragraphs),
        "chapters_found": chapters_found,
    }
