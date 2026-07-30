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
    "wbs": [{"code": "1.1", "deliverable": "string", "task_id": "T01"}],
    "project_schedule": [
        {
            "id": "T01",
            "name": "string",
            "owner_role": "string",
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
    "timeline_risks": [{"risk": "string", "mitigation": "string"}],
    "effort_estimation": {"total_duration_days": 0, "total_person_days": 0, "basis": "string"},
    "schedule_optimizations": ["string"],
}


def generator_prompt(document_text: str) -> str:
    keys = ", ".join(ARTIFACT_KEYS)
    return (
        "Create PMO timeline planning artifacts from the project document. "
        "Return exactly one JSON object and nothing else. "
        f"The top-level JSON object must contain these exact keys: {keys}. "
        "Never wrap the JSON in markdown. Never include explanatory text outside the JSON. "
        "If a value cannot be determined, use null, an empty array, or a clearly marked assumption. "
        "Use this JSON shape:\n"
        f"{json.dumps(GENERATOR_JSON_CONTRACT, ensure_ascii=False, indent=2)}\n\n"
        f"Document content:\n\n{document_text[:8000]}"
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
        f"Original document content:\n{document_text[:8000]}"
    )


def reviewer_prompt(document_text: str, generated: Any) -> str:
    gen_text = generated if isinstance(generated, str) else json.dumps(generated, ensure_ascii=False)
    return (
        "You are a senior project manager reviewing generated project timeline outputs. "
        "Return exactly one valid JSON object and nothing else. "
        "The object must contain: issues, suggestions, confidence.\n\n"
        f"Original document snippet:\n{document_text[:3000]}\n\n"
        f"Generated outputs:\n{gen_text}"
    )
