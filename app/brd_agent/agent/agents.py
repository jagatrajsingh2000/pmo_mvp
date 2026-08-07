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

COUNT_CATEGORIES = (
    "functional_requirements",
    "non_functional_requirements",
    "risks",
    "assumptions",
    "issues",
    "dependencies",
    "decisions",
    "integrations",
    "stakeholders",
    "milestones",
    "resource_items",
    "budget_items",
)


def _validate_brd(payload: Dict[str, Any]) -> None:
    resolved = payload.get("resolved")
    if not isinstance(resolved, dict):
        raise RuntimeError("BRD Agent response resolved must be an object.")
    required_sections = (
        "project_details",
        "executive_summary",
        "scope",
        "stakeholders",
        "current_state",
        "future_state",
        "gap_analysis",
        "functional_requirements",
        "non_functional_requirements",
        "integrations",
        "dependencies",
        "raid",
        "roadmap_milestones",
        "resource_model",
        "budget_commercial",
        "governance_signoff",
        "missing_information",
        "source_coverage_review",
    )
    missing = [section for section in required_sections if section not in resolved]
    if missing:
        raise RuntimeError("BRD Agent resolved object missing sections: " + ", ".join(missing))
    dependencies = resolved.get("dependencies")
    if not isinstance(dependencies, dict):
        raise RuntimeError("BRD Agent dependencies must be categorized as an object.")
    dependency_categories = ("technical", "business", "vendor", "compliance", "testing", "data")
    missing_dependency_categories = [category for category in dependency_categories if category not in dependencies]
    if missing_dependency_categories:
        raise RuntimeError(
            "BRD Agent dependencies missing required categories: "
            + ", ".join(missing_dependency_categories)
        )
    verification = resolved.get("source_coverage_review")
    if not isinstance(verification, dict):
        raise RuntimeError("BRD Agent source_coverage_review must be an object.")
    for key in (
        "extracted_counts_considered",
        "output_counts",
        "coverage_gaps",
        "unsupported_values_removed",
        "verification_notes",
    ):
        if key not in verification:
            raise RuntimeError(f"BRD Agent source_coverage_review missing {key}.")


def _validate_brd_with_expected_counts(payload: Dict[str, Any], expected_counts: Dict[str, int]) -> None:
    _validate_brd(payload)
    output_counts = _count_output_items(payload.get("resolved", {}))
    missing_counts = []
    for category, expected_count in expected_counts.items():
        if expected_count <= 0:
            continue
        output_count = output_counts.get(category, 0)
        if output_count < expected_count:
            missing_counts.append(f"{category}: expected at least {expected_count}, got {output_count}")
    if missing_counts:
        raise RuntimeError(
            "BRD Agent final output dropped extracted source items. "
            + "; ".join(missing_counts)
            + ". Add every extracted item instead of summarizing representative examples."
        )


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


def _count_extracted_facts(fact_sets: list[Dict[str, Any]]) -> Dict[str, int]:
    unique_items = {category: set() for category in COUNT_CATEGORIES}
    for fact_set in fact_sets:
        facts = fact_set.get("facts") or fact_set.get("merged_facts") or {}
        _add_unique(unique_items["functional_requirements"], facts.get("functional_requirements"), ("req_id", "requirement"))
        _add_unique(unique_items["non_functional_requirements"], facts.get("non_functional_requirements"), ("nfr_id", "requirement"))
        _add_unique(unique_items["risks"], facts.get("risks"), ("id", "risk"))
        _add_unique(unique_items["assumptions"], facts.get("assumptions"), ("assumption",))
        _add_unique(unique_items["issues"], facts.get("issues"), ("issue",))
        _add_unique(unique_items["dependencies"], facts.get("dependencies"), ("category", "type", "dependency"))
        _add_unique(unique_items["decisions"], facts.get("decisions"), ("decision",))
        _add_unique(unique_items["integrations"], facts.get("integrations"), ("integration", "source", "target"))
        _add_unique(unique_items["stakeholders"], facts.get("stakeholders"), ("role", "name", "function"))
        _add_unique(unique_items["milestones"], facts.get("roadmap_milestones"), ("milestone", "target_date"))
        _add_unique(unique_items["milestones"], facts.get("governance_signoff"), ("gate", "item", "date"))
        _add_unique(unique_items["resource_items"], facts.get("resource_model"), ("role_or_team", "responsibility"))
        _add_unique(unique_items["budget_items"], facts.get("budget_commercial"), ("item",))
    return {category: len(values) for category, values in unique_items.items()}


def _count_output_items(resolved: Dict[str, Any]) -> Dict[str, int]:
    raid = resolved.get("raid") if isinstance(resolved.get("raid"), dict) else {}
    dependencies = resolved.get("dependencies") if isinstance(resolved.get("dependencies"), dict) else {}
    governance = resolved.get("governance_signoff") if isinstance(resolved.get("governance_signoff"), dict) else {}
    budget = resolved.get("budget_commercial") if isinstance(resolved.get("budget_commercial"), dict) else {}
    return {
        "functional_requirements": len(_as_list(resolved.get("functional_requirements"))),
        "non_functional_requirements": len(_as_list(resolved.get("non_functional_requirements"))),
        "risks": len(_as_list(raid.get("risks"))),
        "assumptions": len(_as_list(raid.get("assumptions"))),
        "issues": len(_as_list(raid.get("issues"))),
        "dependencies": sum(len(_as_list(dependencies.get(category))) for category in ("technical", "business", "vendor", "compliance", "testing", "data")),
        "decisions": len(_as_list(raid.get("decisions"))),
        "integrations": len(_as_list(resolved.get("integrations"))),
        "stakeholders": len(_as_list(resolved.get("stakeholders"))),
        "milestones": len(_as_list(resolved.get("roadmap_milestones"))) + len(_as_list(governance.get("gate_plan"))),
        "resource_items": len(_as_list(resolved.get("resource_model"))),
        "budget_items": (
            len(_as_list(budget.get("budget_information")))
            + len(_as_list(budget.get("commercial_assumptions")))
            + len(_as_list(budget.get("source_evidence")))
        ),
    }


def _add_unique(target: set[str], rows: Any, identity_fields: tuple[str, ...]) -> None:
    for row in _as_list(rows):
        fingerprint = _fingerprint(row, identity_fields)
        if fingerprint:
            target.add(fingerprint)


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _fingerprint(value: Any, fields: tuple[str, ...]) -> str:
    if isinstance(value, dict):
        parts = []
        for field in fields:
            field_value = value.get(field)
            if field_value is not None and str(field_value).strip():
                parts.append(str(field_value).strip().lower())
        if parts:
            return " | ".join(parts)
        return " | ".join(str(value.get(key, "")).strip().lower() for key in sorted(value.keys()) if value.get(key))
    if value is None:
        return ""
    return str(value).strip().lower()


def _generate_brd_direct(document_text: str, filename: str) -> Dict[str, Any]:
    result = generate_required_json(
        agent_name="brd_agent",
        prompt=brd_prompt(document_text, filename),
        required_keys=BRD_REQUIRED_KEYS,
        repair_prompt=lambda invalid, error: brd_repair_prompt(document_text, invalid, error, filename),
        validator=_validate_brd,
        max_tokens=14000,
    )
    _attach_source_coverage_counts(result)
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
    expected_counts = _count_extracted_facts(chunk_facts)
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
        validator=lambda payload: _validate_brd_with_expected_counts(payload, expected_counts),
        max_tokens=14000,
    )
    _attach_source_coverage_counts(result, expected_counts)
    result["ingestion_metadata"] = {
        "mode": "chunked",
        "source_text_chars": len(document_text or ""),
        "chunks": len(chunks),
        "chunk_size_chars": CHUNK_SIZE_CHARS,
        "chunk_overlap_chars": CHUNK_OVERLAP_CHARS,
        "fact_sets_after_merge": len(compacted_facts),
        "fact_bundle_chars": len(fact_bundle_text),
        "unique_extracted_counts": expected_counts,
        "final_output_counts": _count_output_items(result.get("resolved", {})),
    }
    return result


def _attach_source_coverage_counts(payload: Dict[str, Any], expected_counts: Dict[str, int] | None = None) -> None:
    resolved = payload.get("resolved")
    if not isinstance(resolved, dict):
        return
    review = resolved.setdefault("source_coverage_review", {})
    if not isinstance(review, dict):
        review = {}
        resolved["source_coverage_review"] = review
    if expected_counts is not None:
        review["extracted_counts_considered"] = expected_counts
    else:
        review.setdefault("extracted_counts_considered", {})
    review["output_counts"] = _count_output_items(resolved)
    review.setdefault("coverage_gaps", [])
    review.setdefault("unsupported_values_removed", [])
    review.setdefault("verification_notes", [])


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
