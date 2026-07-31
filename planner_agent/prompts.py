from typing import Any
import json

ARTIFACT_KEYS = [
    "wbs",
    "project_schedule",
    "sprint_plan",
    "milestone_plan",
    "critical_path",
    "dependency_map",
    "resource_allocation",
    "timeline_risks",
    "effort_estimation",
    "schedule_optimizations",
]


GENERATOR_JSON_CONTRACT = {
    "project_name": "string",
    "wbs": [{"code": "1.1", "deliverable": "string", "task_id": "T01", "status": "Not Started | In Progress | Done | At Risk"}],
    "project_schedule": [
        {
            "id": "T01",
            "name": "string",
            "owner_role": "string",
            "status": "Not Started | In Progress | Done | At Risk",
            "priority": "Low | Medium | High | Critical",
            "duration_days": 1,
            "start_date": "YYYY-MM-DD or null",
            "end_date": "YYYY-MM-DD or null",
            "dependencies": ["T00"],
        }
    ],
    "sprint_plan": [{"sprint": 1, "start_date": "YYYY-MM-DD or null", "end_date": "YYYY-MM-DD or null", "task_ids": ["T01"]}],
    "milestone_plan": [{"name": "string", "date": "YYYY-MM-DD or null"}],
    "critical_path": {"task_ids": ["T01"], "summary": "string"},
    "dependency_map": [{"task_id": "T01", "depends_on": ["T00"], "blocks": ["T02"]}],
    "resource_allocation": [{"role": "string", "available_count": 0, "assigned_task_ids": ["T01"]}],
    "timeline_risks": [{"risk": "string", "mitigation": "string", "likelihood": 1, "impact": 1}],
    "effort_estimation": {
        "total_duration_days": 0,
        "total_person_days": 0,
        "basis": "string",
        "by_role": [{"role": "string", "person_days": 0}],
    },
    "schedule_optimizations": ["string"],
    "source_traceability": [
        {
            "artifact": "string",
            "source_section": "string",
            "source_evidence": "short quote or paraphrase from source",
            "confidence": "low | medium | high",
        }
    ],
    "stakeholder_mapping": [
        {
            "role": "string",
            "name": "string or null",
            "raci": "A | R | C | I | null",
            "engagement": "string",
            "responsibility": "string",
        }
    ],
    "requirements_quality": {
        "functional_coverage": "string",
        "non_functional_coverage": "string",
        "acceptance_criteria_coverage": "string",
        "missing_requirements": ["string"],
    },
    "audit_readiness": {
        "approval_gates": ["string"],
        "signoffs_needed": ["string"],
        "compliance_items": ["string"],
        "evidence_gaps": ["string"],
    },
}


def generator_prompt(document_text: str) -> str:
    keys = ", ".join(ARTIFACT_KEYS)
    return (
        "Create PMO timeline planning artifacts from the project document. "
        "Return exactly one JSON object and nothing else. "
        f"The top-level JSON object must contain these exact keys: {keys}. "
        "Never wrap the JSON in markdown. Never include explanatory text outside the JSON. "
        "If a value cannot be determined, use null, an empty array, or a clearly marked assumption. "
        "Infer reasonable status and priority values from the document where possible. "
        "Use timeline_risks entries with likelihood and impact values from 1 to 5 when possible. "
        "Extract table content from the document when present, especially stakeholders, functional requirements, "
        "non-functional requirements, risks, dependencies, integrations, governance gates, and sign-off rows. "
        "Include source_traceability, stakeholder_mapping, requirements_quality, and audit_readiness fields. "
        "Use source_evidence only when supported by the document text. "
        "Use this JSON shape:\n"
        f"{json.dumps(GENERATOR_JSON_CONTRACT, ensure_ascii=False, indent=2)}\n\n"
        f"Document content:\n\n{document_text[:16000]}"
    )


def generator_retry_prompt(document_text: str, invalid_response: Any, error: str) -> str:
    invalid_text = invalid_response if isinstance(invalid_response, str) else json.dumps(invalid_response, ensure_ascii=False)
    return (
        "Your previous response failed validation for the PMO timeline planner. "
        f"Validation error: {error}\n\n"
        "Return a corrected response as exactly one valid JSON object and nothing else. "
        "Do not include markdown, code fences, comments, or prose. "
        "The object must match this shape and include every top-level key:\n"
        f"{json.dumps(GENERATOR_JSON_CONTRACT, ensure_ascii=False, indent=2)}\n\n"
        f"Previous invalid response:\n{invalid_text[:3000]}\n\n"
        f"Original document content:\n{document_text[:16000]}"
    )


def reviewer_prompt(document_text: str, generated: Any) -> str:
    gen_text = generated if isinstance(generated, str) else json.dumps(generated, ensure_ascii=False)
    quality_contract = {
        "issues": ["string"],
        "suggestions": ["string"],
        "confidence": "low | medium | high",
        "quality_scores": [
            {
                "category": "Input Grounding",
                "score": 0,
                "rationale": "string",
                "evidence": "string",
                "improvement": "string",
            }
        ],
        "overall_quality_score": 0,
    }
    categories = [
        "Input Grounding",
        "Business Accuracy",
        "Requirements Quality",
        "Hallucination Control",
        "Traceability",
        "Stakeholder Mapping",
        "Risk Management",
        "Technical Accuracy",
        "BRD Completeness",
        "Audit Readiness",
    ]
    return (
        "You are a senior project manager reviewing generated project timeline outputs. "
        "Return exactly one valid JSON object and nothing else. "
        "Score each quality category from 0 to 100, where 100 means excellent. "
        "Ground every score in the original document and generated output; do not invent unsupported evidence. "
        "Award higher scores when the generated output includes grounded source_traceability, stakeholder_mapping, "
        "requirements_quality, and audit_readiness details that match the original document. "
        "Do not penalize page-number traceability if the extracted DOCX text has no page numbers; score section/table traceability instead. "
        f"The quality_scores array must contain exactly these categories: {', '.join(categories)}. "
        "Use this JSON shape:\n"
        f"{json.dumps(quality_contract, ensure_ascii=False, indent=2)}\n\n"
        f"Original document snippet:\n{document_text[:8000]}\n\n"
        f"Generated outputs:\n{gen_text}"
    )
