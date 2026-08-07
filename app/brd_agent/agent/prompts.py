import json
from typing import Any

from app.common.agent_runtime import document_context, to_json_text

BRD_REQUIRED_KEYS = ("demand_id", "filename", "titles", "resolved")
BRD_FACT_REQUIRED_KEYS = ("chunk_id", "chunk_summary", "facts", "source_coverage", "uncertainties")
BRD_MERGED_FACT_REQUIRED_KEYS = ("merged_facts", "source_coverage", "uncertainties")

BA_BRD_RULES = (
    "You are a Senior Business Analyst and Product Owner generating a stakeholder-ready BRD from source artifacts. "
    "Your primary objective is complete and accurate extraction before summarization. "
    "Do not merely copy extracted information into a template; analyze, synthesize, and explain business meaning. "
    "Never sacrifice source coverage to improve readability. "
    "Never leave a section blank if relevant source information exists. "
    "Do not output 'No Entries' when information can be derived from the provided artifacts. "
    "Do not invent project metadata such as Demand IDs, classifications, project codes, owners, dates, recommendations, statuses, or identifiers. "
    "If metadata is not provided, explicitly state 'Not provided in source'. "
    "Do not invent values, dates, costs, thresholds, SLAs, owners, recommendations, or decisions not explicitly supported by source evidence. "
    "Every requirement present in the source must appear in the BRD. Do not drop requirements because they seem repetitive, detailed, or low priority. "
    "Preserve all FRs, NFRs, dependencies, risks, assumptions, issues, decisions, gaps, milestones, roadmap items, integrations, resource data, budget data, and stakeholder information. "
    "Do not reduce a list of multiple items into a single representative example. If the source contains 9 requirements, output 9 requirements; if it contains 8 dependencies, output 8 dependencies. "
    "Build meaningful Current State and Future State sections using SOPs, stakeholder input, process flows, workshop notes, and requirements. "
    "Stakeholder sections must include expectations, concerns, approval responsibilities, and impacts, not only names and roles. "
    "Categorize dependencies as Technical, Business, Vendor, Compliance, Testing, or Data. "
    "Keep Risks, Assumptions, Issues, Dependencies, Decisions, and Gaps separate. "
    "Surface every explicit gap or ambiguity with business impact and required action. "
    "Include integrations, testing strategy, governance, milestones, roadmap, resource model, and budget/commercial information whenever present. "
    "Do not convert architecture discussions into approved recommendations unless the source explicitly states a recommendation was made. "
    "Do not mark an option as recommended, selected, approved, or accepted unless explicitly supported by source evidence. "
    "Do not output placeholder content merely to avoid empty sections; first search all provided source artifacts/chunks for relevant information. "
    "Before stating 'Not provided in source', verify that the information does not exist elsewhere in the provided source artifacts. "
    "If information is missing, state 'Not provided in source' and explain the impact instead of leaving the section empty. "
    "Prefer complete extraction with traceability over aggressive summarization. "
    "Before final output, verify from extracted content that no requirements were dropped, no source categories were partially extracted, "
    "no unsupported values were added, and no self-certification statement is included unless validated against actual extracted content. "
    "Missing information is acceptable. Missing extracted information is not."
)

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
            {
                "role": "string",
                "function": "string",
                "raci": "A | R | C | I | null",
                "engagement": "string",
                "name": "string or null",
                "expectations": ["string"],
                "concerns": ["string"],
                "approval_responsibilities": ["string"],
                "business_impact": "string",
                "source_evidence": "short quote or paraphrase",
            }
        ],
        "current_state": {
            "business_narrative": "string",
            "process_context": ["string"],
            "impacted_applications": ["string"],
            "pain_points": ["string"],
            "business_impacts": ["string"],
            "source_evidence": ["short quote or paraphrase"],
        },
        "future_state": {
            "business_narrative": "string",
            "capability_uplift": ["string"],
            "target_capabilities": ["string"],
            "operational_benefits": ["string"],
            "source_evidence": ["short quote or paraphrase"],
        },
        "gap_analysis": [
            {
                "capability": "string",
                "current": "string",
                "target": "string",
                "gap": "string",
                "business_impact": "string",
                "required_action": "string",
                "source_evidence": "short quote or paraphrase",
            }
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
        "dependencies": {
            "technical": [{"dependency": "string", "impact": "string", "required_action": "string", "source_evidence": "short quote or paraphrase"}],
            "business": [{"dependency": "string", "impact": "string", "required_action": "string", "source_evidence": "short quote or paraphrase"}],
            "vendor": [{"dependency": "string", "impact": "string", "required_action": "string", "source_evidence": "short quote or paraphrase"}],
            "compliance": [{"dependency": "string", "impact": "string", "required_action": "string", "source_evidence": "short quote or paraphrase"}],
            "testing": [{"dependency": "string", "impact": "string", "required_action": "string", "source_evidence": "short quote or paraphrase"}],
            "data": [{"dependency": "string", "impact": "string", "required_action": "string", "source_evidence": "short quote or paraphrase"}],
        },
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
        "roadmap_milestones": [
            {"milestone": "string", "target_date": "YYYY-MM-DD or null", "business_value": "string", "source_evidence": "short quote or paraphrase"}
        ],
        "resource_model": [
            {"role_or_team": "string", "responsibility": "string", "capacity_or_count": "string or Not provided in source", "impact_if_missing": "string", "source_evidence": "short quote or paraphrase"}
        ],
        "budget_commercial": {
            "budget_information": ["string"],
            "commercial_assumptions": ["string"],
            "missing_information_impact": ["string"],
            "source_evidence": ["short quote or paraphrase"],
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
        "missing_information": [
            {"area": "string", "status": "Not provided in source", "impact": "string", "required_action": "string"}
        ],
        "source_coverage_review": {
            "extracted_counts_considered": {
                "functional_requirements": 0,
                "non_functional_requirements": 0,
                "risks": 0,
                "assumptions": 0,
                "issues": 0,
                "dependencies": 0,
                "decisions": 0,
                "integrations": 0,
                "stakeholders": 0,
                "milestones": 0,
                "resource_items": 0,
                "budget_items": 0,
            },
            "output_counts": {
                "functional_requirements": 0,
                "non_functional_requirements": 0,
                "risks": 0,
                "assumptions": 0,
                "issues": 0,
                "dependencies": 0,
                "decisions": 0,
                "integrations": 0,
                "stakeholders": 0,
                "milestones": 0,
                "resource_items": 0,
                "budget_items": 0,
            },
            "coverage_gaps": ["string"],
            "unsupported_values_removed": ["string"],
            "verification_notes": ["string"],
        },
    },
}

BRD_FACT_JSON_CONTRACT = {
    "chunk_id": "chunk-001",
    "chunk_summary": "short grounded summary of this chunk only",
    "facts": {
        "project_details": [{"field": "string", "value": "string", "evidence": "short quote/paraphrase"}],
        "business_rationale": [{"fact": "string", "evidence": "short quote/paraphrase"}],
        "scope": [{"type": "in_scope | out_of_scope | assumption", "item": "string", "evidence": "short quote/paraphrase"}],
        "stakeholders": [{"role": "string", "function": "string or null", "raci": "string or null", "engagement": "string or null", "name": "string or null", "expectations": ["string"], "concerns": ["string"], "approval_responsibilities": ["string"], "impact": "string", "evidence": "short quote/paraphrase"}],
        "current_state": [{"fact": "string", "business_impact": "string", "evidence": "short quote/paraphrase"}],
        "future_state": [{"fact": "string", "business_value": "string", "evidence": "short quote/paraphrase"}],
        "gap_analysis": [{"capability": "string", "current": "string", "target": "string", "gap": "string", "business_impact": "string", "required_action": "string", "evidence": "short quote/paraphrase"}],
        "functional_requirements": [{"req_id": "string or null", "requirement": "string", "priority": "string or null", "acceptance_criteria": "string or null", "evidence": "short quote/paraphrase"}],
        "non_functional_requirements": [{"nfr_id": "string or null", "category": "string", "requirement": "string", "target_threshold": "string or null", "evidence": "short quote/paraphrase"}],
        "integrations": [{"integration": "string", "source": "string", "target": "string", "type": "string or null", "frequency": "string or null", "notes": "string", "evidence": "short quote/paraphrase"}],
        "dependencies": [{"category": "Technical | Business | Vendor | Compliance | Testing | Data", "dependency": "string", "impact": "string", "required_action": "string", "evidence": "short quote/paraphrase"}],
        "risks": [{"id": "string or null", "risk": "string", "likelihood": "string or null", "impact": "string or null", "mitigation": "string or null", "owner": "string or null", "evidence": "short quote/paraphrase"}],
        "assumptions": [{"assumption": "string", "evidence": "short quote/paraphrase"}],
        "issues": [{"issue": "string", "evidence": "short quote/paraphrase"}],
        "decisions": [{"decision": "string", "evidence": "short quote/paraphrase"}],
        "solution_approach": [{"fact": "string", "evidence": "short quote/paraphrase"}],
        "functional_flow": [{"step": "string", "evidence": "short quote/paraphrase"}],
        "module_correlation": [{"module": "string", "depends_on": ["string"], "evidence": "short quote/paraphrase"}],
        "acceptance_testing": [{"item": "string", "evidence": "short quote/paraphrase"}],
        "roadmap_milestones": [{"milestone": "string", "target_date": "YYYY-MM-DD or null", "business_value": "string", "evidence": "short quote/paraphrase"}],
        "resource_model": [{"role_or_team": "string", "responsibility": "string", "capacity_or_count": "string or null", "evidence": "short quote/paraphrase"}],
        "budget_commercial": [{"item": "string", "evidence": "short quote/paraphrase"}],
        "rollout_change": [{"item": "string", "evidence": "short quote/paraphrase"}],
        "governance_signoff": [{"item": "string", "gate": "string or null", "date": "YYYY-MM-DD or null", "evidence": "short quote/paraphrase"}],
        "version_history": [{"version": "string", "date": "YYYY-MM-DD or null", "author": "string or null", "change_summary": "string", "evidence": "short quote/paraphrase"}],
        "missing_information": [{"area": "string", "status": "Not provided in source", "impact": "string", "required_action": "string", "evidence": "short quote/paraphrase"}],
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
        f"{BA_BRD_RULES}\n\n"
        "You are the BRD Agent in a PMO document generation workflow. "
        "Create a complete, business-accurate Business Requirements Document from the source document or project brief. "
        "Return exactly one valid JSON object and nothing else. Never use markdown or code fences. "
        "Ground content in the source text. If a field is not present, state 'Not provided in source' and explain the impact in missing_information. "
        "Do not omit important source sections such as stakeholders, scope, functional requirements, non-functional requirements, "
        "integrations, categorized dependencies, risks, assumptions, issues, decisions, gaps, governance, rollout, and acceptance criteria. "
        "Retain every requirement and row-level source item. Never collapse multiple source items into one representative entry. "
        "Write executive_summary, current_state, future_state, gap_analysis, stakeholders, and solution_approach as business analysis, not raw extraction. "
        "The response must match this JSON shape and include every top-level key:\n"
        f"{json.dumps(BRD_JSON_CONTRACT, ensure_ascii=False, indent=2)}\n\n"
        f"Use this output filename unless the source clearly specifies another filename: {filename}\n\n"
        f"Source document content:\n{context}"
    )


def brd_chunk_fact_prompt(chunk_text: str, chunk_id: str, total_chunks: int, source_range: str) -> str:
    return (
        f"{BA_BRD_RULES}\n\n"
        "You are the BRD Agent extraction step. Extract grounded facts from this document chunk only. "
        "Return exactly one valid JSON object and nothing else. Never use markdown or code fences. "
        "Do not infer across chunks. Do not invent missing facts. If the chunk does not contain a category, return an empty array for that category. "
        "Preserve IDs, names, dates, requirement text, table rows, dependencies, risks, governance gates, sign-off details, and acceptance criteria exactly when possible. "
        "Extract every row/item in this chunk; do not output top examples only. "
        "Capture stakeholder expectations, concerns, approvals, and impacts whenever the chunk supports them. "
        "Classify dependencies as Technical, Business, Vendor, Compliance, Testing, or Data whenever possible. "
        "Extract explicit gaps and ambiguities with business impact and required action. "
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
        f"{BA_BRD_RULES}\n\n"
        "Your previous BRD chunk extraction response failed JSON/schema validation. "
        f"Validation error: {error}\n\n"
        "Return a corrected response as exactly one valid JSON object and nothing else. "
        "Use only facts present in this chunk. Do not invent or fill gaps from outside the chunk. "
        "Classify dependencies and preserve stakeholder expectations, gaps, ambiguities, requirements, and evidence. "
        "Do not collapse multiple source items into a single representative item. "
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
        f"{BA_BRD_RULES}\n\n"
        "You are the BRD Agent fact merge step. Merge extracted fact JSON objects without adding unsupported information. "
        "Return exactly one valid JSON object and nothing else. Never use markdown or code fences. "
        "Deduplicate only exact repeats or overlap duplicates, preserve unique requirements and table rows, preserve IDs and dates, and keep source evidence inside each fact. "
        "Do not summarize away requirements, integrations, categorized dependencies, risks, assumptions, issues, decisions, gaps, governance gates, stakeholders, acceptance criteria, roadmap, resource model, commercial details, or version history. "
        "Do not merge distinct source rows merely because they are similar. "
        "If two facts conflict, keep both and add an uncertainty note. "
        "The response must match this JSON shape and include every top-level key:\n"
        f"{json.dumps(BRD_MERGED_FACT_JSON_CONTRACT, ensure_ascii=False, indent=2)}\n\n"
        f"Batch label: {batch_label}\n\n"
        f"Extracted facts to merge:\n{fact_bundle_text}"
    )


def brd_fact_merge_repair_prompt(fact_bundle_text: str, batch_label: str, invalid_response: Any, error: str) -> str:
    return (
        f"{BA_BRD_RULES}\n\n"
        "Your previous BRD fact merge response failed JSON/schema validation. "
        f"Validation error: {error}\n\n"
        "Return a corrected response as exactly one valid JSON object and nothing else. "
        "Include merged_facts, source_coverage, and uncertainties. Do not add facts unsupported by the extracted facts. Preserve gaps and all categorized dependencies. "
        "Do not collapse distinct source facts into representative examples.\n\n"
        f"Required JSON shape:\n{json.dumps(BRD_MERGED_FACT_JSON_CONTRACT, ensure_ascii=False, indent=2)}\n\n"
        f"Batch label: {batch_label}\n\n"
        f"Previous invalid response:\n{to_json_text(invalid_response, 3500)}\n\n"
        f"Extracted facts to merge:\n{fact_bundle_text}"
    )


def brd_from_facts_prompt(fact_bundle_text: str, filename: str = "workflow-brd.docx") -> str:
    return (
        f"{BA_BRD_RULES}\n\n"
        "You are the BRD Agent synthesis step. Create the final Business Requirements Document from extracted source facts. "
        "Return exactly one valid JSON object and nothing else. Never use markdown or code fences. "
        "Use only the provided extracted facts as source material. Do not invent requirements, dates, stakeholders, costs, systems, risks, or sign-offs. "
        "If something is not supported by extracted facts, state 'Not provided in source' and explain the impact in missing_information. "
        "Preserve as much detail as possible: do not collapse many functional requirements, NFRs, integrations, dependencies, risks, assumptions, issues, decisions, gaps, gates, or acceptance criteria into generic bullets. "
        "The output count for each major category must match or exceed the unique extracted count; overlap duplicates are already handled before validation. "
        "Dependencies must be categorized into technical, business, vendor, compliance, testing, and data groups. "
        "Write business-facing narrative for executives, PMO teams, business stakeholders, and delivery teams. "
        "Carry source evidence into source_traceability so reviewers can see where the BRD content came from. "
        "Populate source_coverage_review with extracted counts considered, output counts, any coverage gaps, unsupported values removed, and verification notes based on the actual extracted facts. "
        "The response must match this JSON shape and include every top-level key:\n"
        f"{json.dumps(BRD_JSON_CONTRACT, ensure_ascii=False, indent=2)}\n\n"
        f"Use this output filename unless extracted facts clearly specify another filename: {filename}\n\n"
        f"Extracted facts:\n{fact_bundle_text}"
    )


def brd_from_facts_repair_prompt(fact_bundle_text: str, invalid_response: Any, error: str, filename: str = "workflow-brd.docx") -> str:
    return (
        f"{BA_BRD_RULES}\n\n"
        "Your previous BRD synthesis response failed JSON/schema validation. "
        f"Validation error: {error}\n\n"
        "Return a corrected response as exactly one valid JSON object and nothing else. "
        "Include demand_id, filename, titles, and resolved. Use only the extracted facts; do not invent missing content. "
        "If validation reports that a final category count is lower than extracted facts, add the missing extracted items instead of explaining them away. "
        "State missing content as 'Not provided in source' with impact in missing_information.\n\n"
        f"Required JSON shape:\n{json.dumps(BRD_JSON_CONTRACT, ensure_ascii=False, indent=2)}\n\n"
        f"Use this output filename if no better source filename exists: {filename}\n\n"
        f"Previous invalid response:\n{to_json_text(invalid_response, 3500)}\n\n"
        f"Extracted facts:\n{fact_bundle_text}"
    )


def brd_repair_prompt(document_text: str, invalid_response: Any, error: str, filename: str = "workflow-brd.docx") -> str:
    context = document_context(document_text, 22000)
    return (
        f"{BA_BRD_RULES}\n\n"
        "Your previous BRD Agent response failed JSON/schema validation. "
        f"Validation error: {error}\n\n"
        "Return a corrected response as exactly one valid JSON object and nothing else. "
        "Include demand_id, filename, titles, and resolved. The resolved object must contain all BRD sections from the contract. "
        "Do not wrap the JSON in markdown. Do not add prose outside the JSON. "
        "Use 'Not provided in source' and missing_information impact entries where the source truly lacks detail.\n\n"
        f"Required JSON shape:\n{json.dumps(BRD_JSON_CONTRACT, ensure_ascii=False, indent=2)}\n\n"
        f"Use this output filename if no better source filename exists: {filename}\n\n"
        f"Previous invalid response:\n{to_json_text(invalid_response, 3500)}\n\n"
        f"Source document content:\n{context}"
    )
