import json
from typing import Any

from app.common.agent_runtime import document_context, to_json_text

BRD_REQUIRED_KEYS = ("demand_id", "filename", "titles", "resolved")

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

