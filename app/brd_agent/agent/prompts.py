import json
from typing import Any

from app.common.agent_runtime import document_context, to_json_text

BRD_REQUIRED_KEYS = ("demand_id", "filename", "titles", "resolved")
BRD_FACT_REQUIRED_KEYS = ("chunk_id", "chunk_summary", "facts", "source_coverage", "uncertainties")
BRD_MERGED_FACT_REQUIRED_KEYS = ("merged_facts", "source_coverage", "uncertainties")

BRD_JSON_CONTRACT = {
    "demand_id": "string",
    "filename": "string",
    "titles": {
        "1": "Executive Summary",
        "2": "Scope",
        "3": "Stakeholders",
        "4": "Current State",
        "5": "Future State",
        "6": "Gap Analysis",
        "7": "Functional Requirements",
        "8": "Non-Functional Requirements",
        "9": "Integrations",
        "10": "Dependencies",
        "11": "Risks, Assumptions, Issues, Decisions",
        "12": "Solution Approach",
        "13": "Functional Flow Diagram",
        "14": "Module Correlation Diagram",
        "15": "Acceptance Criteria & Testing",
        "16": "Rollout & Change Management",
        "17": "Governance & Sign-off",
        "18": "Version History",
    },
    "resolved": {
        "project_details": {
            "project_name": "string",
            "demand_id": "string",
            "project_code": "string or null",
            "affected_business_unit": "string or null",
            "sponsor": "string or null",
            "requester_name": "string or null",
            "it_owner": "string or null",
            "document_status": "Draft | Final | In Review",
            "issue_date": "YYYY-MM-DD or null",
            "classification": "string",
        },
        "executive_summary": {
            "business_rationale": "string",
            "expected_outcomes": ["string"],
            "indicative_business_case": [
                {"lever": "string", "direction": "up | down | neutral", "indicative_size": "string", "confidence": "low | medium | high"}
            ],
        },
        "scope": {
            "in_scope": ["string"],
            "out_of_scope": ["string"],
            "assumptions": ["string"],
        },
        "stakeholders": [
            {"role": "string", "function": "string", "raci": "A | R | C | I | null", "engagement": "string", "name": "string or null"}
        ],
        "current_state": {"summary": "string", "impacted_applications": ["string"], "pain_points": ["string"]},
        "future_state": {"capability_uplift": ["string"], "target_capabilities": ["string"]},
        "gap_analysis": [
            {"capability": "string", "current": "string", "target": "string", "gap": "string", "action": "string"}
        ],
        "functional_requirements": [
            {"req_id": "FR-001", "requirement": "string", "priority": "Must Have | Should Have | Could Have", "acceptance_criteria": "string"}
        ],
        "non_functional_requirements": [
            {"nfr_id": "NFR-001", "category": "string", "requirement": "string", "target_threshold": "string"}
        ],
        "integrations": [
            {"integration": "string", "source": "string", "target": "string", "type": "string", "frequency": "string", "notes": "string"}
        ],
        "dependencies": {"upstream": ["string"], "downstream": ["string"], "external": ["string"]},
        "raid": {
            "risks": [{"id": "R-01", "risk": "string", "likelihood": "low | medium | high", "impact": "low | medium | high", "mitigation": "string", "owner": "string"}],
            "assumptions": ["string"],
            "issues": ["string"],
            "decisions": ["string"],
        },
        "solution_approach": {
            "options_considered": [
                {"option": "string", "summary": "string", "indicative_tco": "string or null", "recommendation": "yes | no | partial"}
            ],
            "recommended_approach": "string",
        },
        "functional_flow": ["string"],
        "module_correlation": [
            {"module": "string", "depends_on": ["string"], "notes": "string"}
        ],
        "acceptance_criteria_testing": {
            "test_strategy_summary": ["string"],
            "uat_exit_criteria": ["string"],
        },
        "rollout_change_management": {
            "rollout_strategy": "string",
            "communication_plan": "string",
            "rollback_plan": "string",
        },
        "governance_signoff": {
            "gate_plan": [{"gate": "string", "entry": "string", "exit": "string", "target_date": "YYYY-MM-DD or null"}],
            "signoff_matrix": [{"role": "string", "name": "string or null", "decision": "Approve / Reject", "date": "YYYY-MM-DD or null"}],
        },
        "version_history": [
            {"version": "0.1", "date": "YYYY-MM-DD or null", "author": "string", "change_summary": "string"}
        ],
        "source_traceability": [
            {"section": "string", "source_evidence": "short quote or paraphrase", "confidence": "low | medium | high"}
        ],
    },
}

BRD_FACT_JSON_CONTRACT = {
    "chunk_id": "chunk-001",
    "chunk_summary": "short grounded summary of this chunk only",
    "facts": {
        "project_details": [{"field": "string", "value": "string", "evidence": "short quote/paraphrase"}],
        "business_rationale": [{"fact": "string", "evidence": "short quote/paraphrase"}],
        "scope": [{"type": "in_scope | out_of_scope | assumption", "item": "string", "evidence": "short quote/paraphrase"}],
        "stakeholders": [{"role": "string", "function": "string or null", "raci": "string or null", "engagement": "string or null", "name": "string or null", "evidence": "short quote/paraphrase"}],
        "current_state": [{"fact": "string", "evidence": "short quote/paraphrase"}],
        "future_state": [{"fact": "string", "evidence": "short quote/paraphrase"}],
        "gap_analysis": [{"capability": "string", "current": "string", "target": "string", "gap": "string", "action": "string", "evidence": "short quote/paraphrase"}],
        "functional_requirements": [{"req_id": "string or null", "requirement": "string", "priority": "string or null", "acceptance_criteria": "string or null", "evidence": "short quote/paraphrase"}],
        "non_functional_requirements": [{"nfr_id": "string or null", "category": "string", "requirement": "string", "target_threshold": "string or null", "evidence": "short quote/paraphrase"}],
        "integrations": [{"integration": "string", "source": "string", "target": "string", "type": "string or null", "frequency": "string or null", "notes": "string", "evidence": "short quote/paraphrase"}],
        "dependencies": [{"type": "upstream | downstream | external", "dependency": "string", "evidence": "short quote/paraphrase"}],
        "risks": [{"id": "string or null", "risk": "string", "likelihood": "string or null", "impact": "string or null", "mitigation": "string or null", "owner": "string or null", "evidence": "short quote/paraphrase"}],
        "assumptions": [{"assumption": "string", "evidence": "short quote/paraphrase"}],
        "issues": [{"issue": "string", "evidence": "short quote/paraphrase"}],
        "decisions": [{"decision": "string", "evidence": "short quote/paraphrase"}],
        "solution_approach": [{"fact": "string", "evidence": "short quote/paraphrase"}],
        "functional_flow": [{"step": "string", "evidence": "short quote/paraphrase"}],
        "module_correlation": [{"module": "string", "depends_on": ["string"], "evidence": "short quote/paraphrase"}],
        "acceptance_testing": [{"item": "string", "evidence": "short quote/paraphrase"}],
        "rollout_change": [{"item": "string", "evidence": "short quote/paraphrase"}],
        "governance_signoff": [{"item": "string", "gate": "string or null", "date": "YYYY-MM-DD or null", "evidence": "short quote/paraphrase"}],
        "version_history": [{"version": "string", "date": "YYYY-MM-DD or null", "author": "string or null", "change_summary": "string", "evidence": "short quote/paraphrase"}],
    },
    "source_coverage": {
        "contains_tables": True,
        "section_headings_found": ["string"],
        "important_ids_found": ["FR-001", "NFR-001"],
        "source_char_range": "0-1000",
    },
    "uncertainties": ["items that were unclear or incomplete in this chunk"],
}

BRD_MERGED_FACT_JSON_CONTRACT = {
    "merged_facts": BRD_FACT_JSON_CONTRACT["facts"],
    "source_coverage": {
        "chunks_merged": ["chunk-001"],
        "section_headings_found": ["string"],
        "important_ids_found": ["FR-001", "NFR-001"],
        "coverage_notes": ["string"],
    },
    "uncertainties": ["string"],
}


def brd_prompt(document_text: str, filename: str = "workflow-brd.docx") -> str:
    context = document_context(document_text, 22000)
    return (
        "You are the BRD Agent in a PMO document generation workflow. "
        "Create a complete, business-accurate Business Requirements Document from the source document or project brief. "
        "Return exactly one valid JSON object and nothing else. Never use markdown or code fences. "
        "Ground content in the source text. If a field is not present, use null, an empty array, or a clearly marked assumption. "
        "Do not omit important source sections such as stakeholders, scope, functional requirements, non-functional requirements, "
        "integrations, dependencies, risks, governance, rollout, and acceptance criteria. "
        "The response must match this JSON shape and include every top-level key:\n"
        f"{json.dumps(BRD_JSON_CONTRACT, ensure_ascii=False, indent=2)}\n\n"
        f"Use this output filename unless the source clearly specifies another filename: {filename}\n\n"
        f"Source document content:\n{context}"
    )


def brd_chunk_fact_prompt(chunk_text: str, chunk_id: str, total_chunks: int, source_range: str) -> str:
    return (
        "You are the BRD Agent extraction step. Extract grounded facts from this document chunk only. "
        "Return exactly one valid JSON object and nothing else. Never use markdown or code fences. "
        "Do not infer across chunks. Do not invent missing facts. If the chunk does not contain a category, return an empty array for that category. "
        "Preserve IDs, names, dates, requirement text, table rows, dependencies, risks, governance gates, sign-off details, and acceptance criteria exactly when possible. "
        "Every non-empty fact must include evidence as a short quote or precise paraphrase from this chunk. "
        "Use the source chunk id in chunk_id and record source_char_range. "
        "The response must match this JSON shape and include every top-level key:\n"
        f"{json.dumps(BRD_FACT_JSON_CONTRACT, ensure_ascii=False, indent=2)}\n\n"
        f"Chunk id: {chunk_id}\n"
        f"Total chunks: {total_chunks}\n"
        f"Source char range: {source_range}\n\n"
        f"Chunk content:\n{chunk_text}"
    )


def brd_chunk_fact_repair_prompt(
    chunk_text: str,
    chunk_id: str,
    total_chunks: int,
    source_range: str,
    invalid_response: Any,
    error: str,
) -> str:
    return (
        "Your previous BRD chunk extraction response failed JSON/schema validation. "
        f"Validation error: {error}\n\n"
        "Return a corrected response as exactly one valid JSON object and nothing else. "
        "Use only facts present in this chunk. Do not invent or fill gaps from outside the chunk. "
        "Include chunk_id, chunk_summary, facts, source_coverage, and uncertainties. "
        "Return empty arrays for categories absent in the chunk.\n\n"
        f"Required JSON shape:\n{json.dumps(BRD_FACT_JSON_CONTRACT, ensure_ascii=False, indent=2)}\n\n"
        f"Chunk id: {chunk_id}\n"
        f"Total chunks: {total_chunks}\n"
        f"Source char range: {source_range}\n\n"
        f"Previous invalid response:\n{to_json_text(invalid_response, 3500)}\n\n"
        f"Chunk content:\n{chunk_text}"
    )


def brd_fact_merge_prompt(fact_bundle_text: str, batch_label: str) -> str:
    return (
        "You are the BRD Agent fact merge step. Merge extracted fact JSON objects without adding unsupported information. "
        "Return exactly one valid JSON object and nothing else. Never use markdown or code fences. "
        "Deduplicate repeated facts, preserve unique requirements and table rows, preserve IDs and dates, and keep source evidence inside each fact. "
        "Do not summarize away requirements, integrations, dependencies, risks, governance gates, stakeholders, acceptance criteria, or version history. "
        "If two facts conflict, keep both and add an uncertainty note. "
        "The response must match this JSON shape and include every top-level key:\n"
        f"{json.dumps(BRD_MERGED_FACT_JSON_CONTRACT, ensure_ascii=False, indent=2)}\n\n"
        f"Batch label: {batch_label}\n\n"
        f"Extracted facts to merge:\n{fact_bundle_text}"
    )


def brd_fact_merge_repair_prompt(fact_bundle_text: str, batch_label: str, invalid_response: Any, error: str) -> str:
    return (
        "Your previous BRD fact merge response failed JSON/schema validation. "
        f"Validation error: {error}\n\n"
        "Return a corrected response as exactly one valid JSON object and nothing else. "
        "Include merged_facts, source_coverage, and uncertainties. Do not add facts unsupported by the extracted facts.\n\n"
        f"Required JSON shape:\n{json.dumps(BRD_MERGED_FACT_JSON_CONTRACT, ensure_ascii=False, indent=2)}\n\n"
        f"Batch label: {batch_label}\n\n"
        f"Previous invalid response:\n{to_json_text(invalid_response, 3500)}\n\n"
        f"Extracted facts to merge:\n{fact_bundle_text}"
    )


def brd_from_facts_prompt(fact_bundle_text: str, filename: str = "workflow-brd.docx") -> str:
    return (
        "You are the BRD Agent synthesis step. Create the final Business Requirements Document from extracted source facts. "
        "Return exactly one valid JSON object and nothing else. Never use markdown or code fences. "
        "Use only the provided extracted facts as source material. Do not invent requirements, dates, stakeholders, costs, systems, risks, or sign-offs. "
        "If something is not supported by extracted facts, use null, an empty array, or a clearly marked assumption in the relevant field. "
        "Preserve as much detail as possible: do not collapse many functional requirements, NFRs, integrations, dependencies, risks, gates, or acceptance criteria into generic bullets. "
        "Carry source evidence into source_traceability so reviewers can see where the BRD content came from. "
        "The response must match this JSON shape and include every top-level key:\n"
        f"{json.dumps(BRD_JSON_CONTRACT, ensure_ascii=False, indent=2)}\n\n"
        f"Use this output filename unless extracted facts clearly specify another filename: {filename}\n\n"
        f"Extracted facts:\n{fact_bundle_text}"
    )


def brd_from_facts_repair_prompt(fact_bundle_text: str, invalid_response: Any, error: str, filename: str = "workflow-brd.docx") -> str:
    return (
        "Your previous BRD synthesis response failed JSON/schema validation. "
        f"Validation error: {error}\n\n"
        "Return a corrected response as exactly one valid JSON object and nothing else. "
        "Include demand_id, filename, titles, and resolved. Use only the extracted facts; do not invent missing content.\n\n"
        f"Required JSON shape:\n{json.dumps(BRD_JSON_CONTRACT, ensure_ascii=False, indent=2)}\n\n"
        f"Use this output filename if no better source filename exists: {filename}\n\n"
        f"Previous invalid response:\n{to_json_text(invalid_response, 3500)}\n\n"
        f"Extracted facts:\n{fact_bundle_text}"
    )


def brd_repair_prompt(document_text: str, invalid_response: Any, error: str, filename: str = "workflow-brd.docx") -> str:
    context = document_context(document_text, 22000)
    return (
        "Your previous BRD Agent response failed JSON/schema validation. "
        f"Validation error: {error}\n\n"
        "Return a corrected response as exactly one valid JSON object and nothing else. "
        "Include demand_id, filename, titles, and resolved. The resolved object must contain all BRD sections from the contract. "
        "Do not wrap the JSON in markdown. Do not add prose outside the JSON. "
        "Use null or empty arrays only where the source truly lacks the detail.\n\n"
        f"Required JSON shape:\n{json.dumps(BRD_JSON_CONTRACT, ensure_ascii=False, indent=2)}\n\n"
        f"Use this output filename if no better source filename exists: {filename}\n\n"
        f"Previous invalid response:\n{to_json_text(invalid_response, 3500)}\n\n"
        f"Source document content:\n{context}"
    )
