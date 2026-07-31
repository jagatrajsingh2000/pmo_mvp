from typing import Any
import json
import re

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

CONTEXT_KEYWORDS = [
    "project details",
    "executive summary",
    "scope",
    "stakeholders",
    "current state",
    "future state",
    "gap analysis",
    "functional requirements",
    "non-functional requirements",
    "integrations",
    "dependencies",
    "risks",
    "assumptions",
    "issues",
    "decisions",
    "solution approach",
    "acceptance criteria",
    "testing",
    "rollout",
    "change management",
    "governance",
    "sign-off",
    "gate plan",
    "resource",
    "milestone",
    "version history",
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


def _document_context(document_text: str, max_chars: int) -> str:
    text = re.sub(r"\r\n?", "\n", document_text or "").strip()
    if len(text) <= max_chars:
        return text

    chunks = [text[:5000], text[-2500:]]
    lowered = text.lower()
    window = 1800
    for keyword in CONTEXT_KEYWORDS:
        start = lowered.find(keyword)
        if start == -1:
            continue
        left = max(0, start - 500)
        right = min(len(text), start + window)
        chunks.append(text[left:right])

    result = []
    seen = set()
    used = 0
    for chunk in chunks:
        normalized = re.sub(r"\s+", " ", chunk).strip()[:160]
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        if used + len(chunk) + 20 > max_chars:
            remaining = max_chars - used - 20
            if remaining <= 0:
                break
            chunk = chunk[:remaining]
        result.append(chunk)
        used += len(chunk) + 20
    return "\n\n--- source section ---\n\n".join(result)


def generator_prompt(document_text: str) -> str:
    keys = ", ".join(ARTIFACT_KEYS)
    source_context = _document_context(document_text, 20000)
    return (
        "Create PMO timeline planning artifacts from the project document. "
        "Return exactly one JSON object and nothing else. "
        f"The top-level JSON object must contain at minimum these planner artifact keys: {keys}. "
        "Never wrap the JSON in markdown. Never include explanatory text outside the JSON. "
        "If a value cannot be determined, use null, an empty array, or a clearly marked assumption. "
        "Infer reasonable status and priority values from the document where possible. "
        "Do not compress the WBS into only high-level phases when the BRD contains requirements, integrations, "
        "dependencies, testing, rollout, governance, or compliance detail. "
        "For a substantial BRD, create 8 to 15 WBS rows and align the project_schedule rows to those WBS tasks. "
        "The WBS should cover discovery/requirements, architecture/design, integrations, build/configuration, "
        "security/compliance, testing/SIT/UAT, rollout/change, governance/sign-off, and hypercare/benefits when supported. "
        "Use timeline_risks entries with likelihood and impact values from 1 to 5 when possible. "
        "Extract table content from the document when present, especially stakeholders, functional requirements, "
        "non-functional requirements, risks, dependencies, integrations, governance gates, and sign-off rows. "
        "Include source_traceability, stakeholder_mapping, requirements_quality, and audit_readiness fields. "
        "Use source_evidence only when supported by the document text. "
        "Use this JSON shape:\n"
        f"{json.dumps(GENERATOR_JSON_CONTRACT, ensure_ascii=False, indent=2)}\n\n"
        f"Document content:\n\n{source_context}"
    )


def generator_retry_prompt(document_text: str, invalid_response: Any, error: str) -> str:
    invalid_text = invalid_response if isinstance(invalid_response, str) else json.dumps(invalid_response, ensure_ascii=False)
    source_context = _document_context(document_text, 20000)
    return (
        "Your previous response failed validation for the PMO timeline planner. "
        f"Validation error: {error}\n\n"
        "Return a corrected response as exactly one valid JSON object and nothing else. "
        "Do not include markdown, code fences, comments, or prose. "
        "If the WBS or schedule was too shallow, expand it using the source sections and table rows. "
        "For a substantial BRD, return 8 to 15 grounded WBS rows with matching schedule tasks. "
        "Do not invent unsupported scope; derive rows from source requirements, integrations, dependencies, "
        "testing, rollout, governance, compliance, and stakeholder content. "
        "The object must match this shape and include every top-level key:\n"
        f"{json.dumps(GENERATOR_JSON_CONTRACT, ensure_ascii=False, indent=2)}\n\n"
        f"Previous invalid response:\n{invalid_text[:3000]}\n\n"
        f"Original document content:\n{source_context}"
    )


def reviewer_prompt(document_text: str, generated: Any) -> str:
    gen_text = generated if isinstance(generated, str) else json.dumps(generated, ensure_ascii=False)
    source_context = _document_context(document_text, 14000)
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
        f"Original document snippet:\n{source_context}\n\n"
        f"Generated outputs:\n{gen_text}"
    )
