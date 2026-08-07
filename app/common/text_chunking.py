import re
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class DocumentChunk:
    chunk_id: str
    index: int
    total: int
    start_char: int
    end_char: int
    text: str


def split_text_for_llm(document_text: str, max_chars: int = 14000, overlap_chars: int = 1200) -> List[DocumentChunk]:
    text = re.sub(r"\r\n?", "\n", document_text or "").strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [DocumentChunk("chunk-001", 1, 1, 0, len(text), text)]

    ranges = []
    start = 0
    last_start = -1
    while start < len(text):
        hard_end = min(len(text), start + max_chars)
        end = hard_end
        if hard_end < len(text):
            end = _best_boundary(text, start, hard_end, max_chars)
        chunk_text = text[start:end].strip()
        if chunk_text:
            ranges.append((start, end, chunk_text))
        if end >= len(text):
            break
        next_start = max(0, end - overlap_chars)
        if next_start <= last_start or next_start <= start:
            next_start = end
        last_start = start
        start = next_start

    total = len(ranges)
    return [
        DocumentChunk(
            chunk_id=f"chunk-{index:03d}",
            index=index,
            total=total,
            start_char=start_char,
            end_char=end_char,
            text=chunk_text,
        )
        for index, (start_char, end_char, chunk_text) in enumerate(ranges, start=1)
    ]


def _best_boundary(text: str, start: int, hard_end: int, max_chars: int) -> int:
    min_reasonable = start + int(max_chars * 0.55)
    patterns = ("\nSection:", "\nTable ", "\n\n", "\n")
    for pattern in patterns:
        candidate = text.rfind(pattern, start, hard_end)
        if candidate >= min_reasonable:
            return candidate
    sentence_candidate = max(
        text.rfind(". ", start, hard_end),
        text.rfind("; ", start, hard_end),
    )
    if sentence_candidate >= min_reasonable:
        return sentence_candidate + 1
    return hard_end
