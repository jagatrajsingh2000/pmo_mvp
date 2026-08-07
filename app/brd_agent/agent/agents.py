import logging
import os
from typing import Any, Dict

from app.common.agent_runtime import generate_required_json, to_json_text
from app.common.text_chunking import DocumentChunk, split_text_for_llm

from .prompts import (
    BRD_FACT_REQUIRED_KEYS,
    BRD_MERGED_FACT_REQUIRED_KEYS,
    BRD_REQUIRED_KEYS,
    brd_chunk_fact_prompt,
    brd_chunk_fact_repair_prompt,
    brd_fact_merge_prompt,
    brd_fact_merge_repair_prompt,
    brd_from_facts_prompt,
    brd_from_facts_repair_prompt,
    brd_prompt,
    brd_repair_prompt,
)

logger = logging.getLogger(__name__)

DIRECT_MAX_CHARS = int(os.environ.get("BRD_DIRECT_MAX_CHARS", "20000"))
CHUNK_SIZE_CHARS = int(os.environ.get("BRD_CHUNK_SIZE_CHARS", "14000"))
CHUNK_OVERLAP_CHARS = int(os.environ.get("BRD_CHUNK_OVERLAP_CHARS", "1200"))
FACT_BUNDLE_MAX_CHARS = int(os.environ.get("BRD_FACT_BUNDLE_MAX_CHARS", "42000"))
FACT_BATCH_MAX_CHARS = int(os.environ.get("BRD_FACT_BATCH_MAX_CHARS", "26000"))


def _validate_brd(payload: Dict[str, Any]) -> None:
    resolved = payload.get("resolved")
    if not isinstance(resolved, dict):
        raise RuntimeError("BRD Agent response resolved must be an object.")
    required_sections = (
        "project_details",
        "executive_summary",
        "scope",
        "stakeholders",
        "functional_requirements",
        "non_functional_requirements",
        "integrations",
        "dependencies",
        "raid",
        "governance_signoff",
    )
    missing = [section for section in required_sections if section not in resolved]
    if missing:
        raise RuntimeError("BRD Agent resolved object missing sections: " + ", ".join(missing))


def _validate_chunk_facts(payload: Dict[str, Any]) -> None:
    if not isinstance(payload.get("facts"), dict):
        raise RuntimeError("BRD chunk extraction facts must be an object.")
    if not isinstance(payload.get("source_coverage"), dict):
        raise RuntimeError("BRD chunk extraction source_coverage must be an object.")
    if not isinstance(payload.get("uncertainties"), list):
        raise RuntimeError("BRD chunk extraction uncertainties must be an array.")


def _validate_merged_facts(payload: Dict[str, Any]) -> None:
    if not isinstance(payload.get("merged_facts"), dict):
        raise RuntimeError("BRD merged facts must include merged_facts object.")
    if not isinstance(payload.get("source_coverage"), dict):
        raise RuntimeError("BRD merged facts source_coverage must be an object.")
    if not isinstance(payload.get("uncertainties"), list):
        raise RuntimeError("BRD merged facts uncertainties must be an array.")


def _generate_brd_direct(document_text: str, filename: str) -> Dict[str, Any]:
    result = generate_required_json(
        agent_name="brd_agent",
        prompt=brd_prompt(document_text, filename),
        required_keys=BRD_REQUIRED_KEYS,
        repair_prompt=lambda invalid, error: brd_repair_prompt(document_text, invalid, error, filename),
        validator=_validate_brd,
        max_tokens=14000,
    )
    return result


def _extract_chunk_facts(chunk: DocumentChunk) -> Dict[str, Any]:
    source_range = f"{chunk.start_char}-{chunk.end_char}"
    logger.info(
        "BRD chunk extraction starting chunk_id=%s index=%s/%s chars=%s range=%s",
        chunk.chunk_id,
        chunk.index,
        chunk.total,
        len(chunk.text),
        source_range,
    )
    result = generate_required_json(
        agent_name=f"brd_agent_extract_{chunk.chunk_id}",
        prompt=brd_chunk_fact_prompt(chunk.text, chunk.chunk_id, chunk.total, source_range),
        required_keys=BRD_FACT_REQUIRED_KEYS,
        repair_prompt=lambda invalid, error: brd_chunk_fact_repair_prompt(
            chunk.text,
            chunk.chunk_id,
            chunk.total,
            source_range,
            invalid,
            error,
        ),
        validator=_validate_chunk_facts,
        max_tokens=8000,
    )
    result["chunk_id"] = chunk.chunk_id
    result.setdefault("source_coverage", {})["source_char_range"] = source_range
    logger.info("BRD chunk extraction completed chunk_id=%s fact_categories=%s", chunk.chunk_id, sorted(result.get("facts", {}).keys()))
    return result


def _merge_fact_batch(fact_batch: list[Dict[str, Any]], batch_label: str) -> Dict[str, Any]:
    fact_bundle_text = to_json_text(fact_batch)
    logger.info("BRD fact merge starting batch=%s facts_chars=%s items=%s", batch_label, len(fact_bundle_text), len(fact_batch))
    result = generate_required_json(
        agent_name=f"brd_agent_merge_{batch_label}",
        prompt=brd_fact_merge_prompt(fact_bundle_text, batch_label),
        required_keys=BRD_MERGED_FACT_REQUIRED_KEYS,
        repair_prompt=lambda invalid, error: brd_fact_merge_repair_prompt(fact_bundle_text, batch_label, invalid, error),
        validator=_validate_merged_facts,
        max_tokens=10000,
    )
    logger.info("BRD fact merge completed batch=%s merged_categories=%s", batch_label, sorted(result.get("merged_facts", {}).keys()))
    return result


def _batch_facts_by_size(fact_sets: list[Dict[str, Any]], max_chars: int) -> list[list[Dict[str, Any]]]:
    batches: list[list[Dict[str, Any]]] = []
    current: list[Dict[str, Any]] = []
    current_chars = 0
    for fact_set in fact_sets:
        item_chars = len(to_json_text(fact_set))
        if current and current_chars + item_chars > max_chars:
            batches.append(current)
            current = []
            current_chars = 0
        current.append(fact_set)
        current_chars += item_chars
    if current:
        batches.append(current)
    return batches


def _compact_facts_if_needed(fact_sets: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    compacted = fact_sets
    pass_number = 1
    while len(to_json_text(compacted)) > FACT_BUNDLE_MAX_CHARS and len(compacted) > 1:
        batches = _batch_facts_by_size(compacted, FACT_BATCH_MAX_CHARS)
        logger.info(
            "BRD fact bundle too large; merge pass=%s input_items=%s batches=%s chars=%s",
            pass_number,
            len(compacted),
            len(batches),
            len(to_json_text(compacted)),
        )
        compacted = [
            _merge_fact_batch(batch, f"pass-{pass_number}-batch-{index:02d}")
            for index, batch in enumerate(batches, start=1)
        ]
        pass_number += 1
    return compacted


def _generate_brd_from_chunks(document_text: str, filename: str) -> Dict[str, Any]:
    chunks = split_text_for_llm(document_text, max_chars=CHUNK_SIZE_CHARS, overlap_chars=CHUNK_OVERLAP_CHARS)
    if not chunks:
        raise RuntimeError("BRD Agent received no extractable document text.")

    logger.info(
        "BRD large-document mode starting text_chars=%s chunks=%s chunk_size=%s overlap=%s",
        len(document_text or ""),
        len(chunks),
        CHUNK_SIZE_CHARS,
        CHUNK_OVERLAP_CHARS,
    )
    chunk_facts = [_extract_chunk_facts(chunk) for chunk in chunks]
    compacted_facts = _compact_facts_if_needed(chunk_facts)
    fact_bundle_text = to_json_text(compacted_facts)
    logger.info(
        "BRD synthesis from facts starting original_chunks=%s fact_sets=%s fact_chars=%s",
        len(chunks),
        len(compacted_facts),
        len(fact_bundle_text),
    )
    result = generate_required_json(
        agent_name="brd_agent_synthesis",
        prompt=brd_from_facts_prompt(fact_bundle_text, filename),
        required_keys=BRD_REQUIRED_KEYS,
        repair_prompt=lambda invalid, error: brd_from_facts_repair_prompt(fact_bundle_text, invalid, error, filename),
        validator=_validate_brd,
        max_tokens=14000,
    )
    result["ingestion_metadata"] = {
        "mode": "chunked",
        "source_text_chars": len(document_text or ""),
        "chunks": len(chunks),
        "chunk_size_chars": CHUNK_SIZE_CHARS,
        "chunk_overlap_chars": CHUNK_OVERLAP_CHARS,
        "fact_sets_after_merge": len(compacted_facts),
        "fact_bundle_chars": len(fact_bundle_text),
    }
    return result


def generate_brd_preview(document_text: str, filename: str = "workflow-brd.docx") -> Dict[str, Any]:
    text_chars = len(document_text or "")
    logger.info("BRD agent starting text_chars=%s filename=%s direct_max_chars=%s", text_chars, filename, DIRECT_MAX_CHARS)
    if text_chars <= DIRECT_MAX_CHARS:
        result = _generate_brd_direct(document_text, filename)
        result["ingestion_metadata"] = {
            "mode": "direct",
            "source_text_chars": text_chars,
            "direct_max_chars": DIRECT_MAX_CHARS,
        }
    else:
        result = _generate_brd_from_chunks(document_text, filename)
    logger.info(
        "BRD agent completed demand_id=%s mode=%s resolved_sections=%s",
        result.get("demand_id"),
        result.get("ingestion_metadata", {}).get("mode"),
        sorted(result["resolved"].keys()),
    )
    return result
